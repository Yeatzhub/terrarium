# Kelly Position Sizer (Enhanced)
*2026-02-19 02:23* - Improved with trade journal integration, growth simulation, and method comparison

## What's New

1. **Trade Journal Integration** - Calculate Kelly directly from journal data
2. **Growth Simulation** - Simulate account paths to visualize Kelly vs alternatives
3. **Method Comparison** - Compare Kelly vs Fixed Fractional vs Percent Risk sizing
4. **Confidence Intervals** - Edge detection with statistical confidence
5. **Batch Optimization** - Calculate optimal sizes across multiple symbols

## Enhanced Code

```python
"""
Kelly Criterion Position Sizer (Enhanced Edition)
Integrates with trade journals, simulates paths, compares methods.
"""
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from decimal import Decimal, ROUND_DOWN
import random
import statistics
from datetime import datetime


@dataclass(frozen=True)
class KellyResult:
    """Extended result with confidence metrics."""
    full_kelly: Decimal
    half_kelly: Decimal
    quarter_kelly: Decimal
    optimal_position: Decimal
    max_position: Decimal
    risk_of_ruin: Decimal
    expected_growth: Decimal
    edge_confidence: float = 0.0  # 0-1 confidence that edge is real
    sample_size: int = 0
    win_rate_ci: Tuple[float, float] = (0.0, 0.0)  # 95% CI


@dataclass
class SimulationResult:
    """Results from growth simulation."""
    method: str
    final_values: List[float]
    median_final: float
    max_drawdown_pct: float
    ruin_count: int  # Accounts blown up
    sharpe: float


class KellyPositionSizer:
    """Enhanced Kelly sizer with journal integration and simulation."""
    
    MAX_POSITION_PCT = Decimal('0.25')
    MIN_KELLY = Decimal('0.01')
    MIN_SAMPLE_SIZE = 30  # Minimum trades for reliable Kelly
    
    def __init__(
        self,
        max_kelly_fraction: float = 0.5,
        max_position_pct: Optional[float] = None,
        confidence_level: float = 0.95
    ):
        self.kelly_fraction = Decimal(str(max_kelly_fraction))
        self.max_position = Decimal(str(max_position_pct or self.MAX_POSITION_PCT))
        self.confidence_level = confidence_level
    
    def calculate(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        account_size: float,
        current_drawdown: float = 0.0,
        sample_size: int = 100  # Number of trades behind these stats
    ) -> KellyResult:
        """Calculate Kelly with confidence metrics."""
        
        # Validation
        if not 0 < win_rate < 1:
            raise ValueError(f"win_rate must be 0-1, got {win_rate}")
        if avg_win <= 0 or avg_loss <= 0:
            raise ValueError("avg_win and avg_loss must be positive")
        
        p = Decimal(str(win_rate))
        q = Decimal('1') - p
        b = Decimal(str(avg_win)) / Decimal(str(avg_loss))
        account = Decimal(str(account_size))
        
        # Kelly Formula
        full_kelly = (p * b - q) / b
        
        # Calculate confidence interval for win rate
        # Wilson score interval
        z = 1.96 if self.confidence_level == 0.95 else 2.576  # 95% or 99%
        n = sample_size
        
        if n > 0:
            p_hat = win_rate
            denominator = 1 + z**2 / n
            center = (p_hat + z**2 / (2*n)) / denominator
            margin = z * ((p_hat * (1-p_hat) / n + z**2 / (4*n**2)) ** 0.5) / denominator
            ci_lower = max(0, center - margin)
            ci_upper = min(1, center + margin)
        else:
            ci_lower, ci_upper = 0, 1
        
        # Edge confidence: probability that Kelly > 0
        # If lower CI > breakeven win rate, high confidence
        breakeven_wr = 1 / (1 + float(b))  # Win rate needed for edge
        edge_confidence = 1.0 if ci_lower > breakeven_wr else (ci_upper - breakeven_wr) / (ci_upper - ci_lower) if ci_upper > ci_lower else 0.0
        
        # Handle negative Kelly
        if full_kelly <= 0:
            return KellyResult(
                full_kelly=Decimal('0'),
                half_kelly=Decimal('0'),
                quarter_kelly=Decimal('0'),
                optimal_position=Decimal('0'),
                max_position=Decimal('0'),
                risk_of_ruin=Decimal('1'),
                expected_growth=Decimal('0'),
                edge_confidence=edge_confidence,
                sample_size=sample_size,
                win_rate_ci=(ci_lower, ci_upper)
            )
        
        # Apply fractional Kelly and drawdown adjustment
        half_kelly = full_kelly * Decimal('0.5')
        quarter_kelly = full_kelly * Decimal('0.25')
        
        adjusted_kelly = full_kelly * self.kelly_fraction
        
        drawdown_factor = Decimal('1') - (Decimal(str(current_drawdown)) * Decimal('2'))
        drawdown_factor = max(drawdown_factor, Decimal('0.5'))
        
        position_pct = adjusted_kelly * drawdown_factor
        position_pct = min(position_pct, self.max_position)
        position_pct = max(position_pct, self.MIN_KELLY)
        
        optimal_position = (account * position_pct).quantize(Decimal('0.01'), rounding=ROUND_DOWN)
        
        return KellyResult(
            full_kelly=full_kelly.quantize(Decimal('0.0001')),
            half_kelly=half_kelly.quantize(Decimal('0.0001')),
            quarter_kelly=quarter_kelly.quantize(Decimal('0.0001')),
            optimal_position=optimal_position,
            max_position=(account * self.max_position).quantize(Decimal('0.01')),
            risk_of_ruin=self._calculate_ruin_risk(p, q, b, position_pct).quantize(Decimal('0.0001')),
            expected_growth=self._calculate_growth(p, q, b, position_pct).quantize(Decimal('0.0001')),
            edge_confidence=edge_confidence,
            sample_size=sample_size,
            win_rate_ci=(ci_lower, ci_upper)
        )
    
    def from_trade_journal(
        self,
        trades: List[dict],  # From TradeJournal.get_closed_trades()
        account_size: float,
        current_drawdown: float = 0.0,
        symbol: Optional[str] = None,
        days: Optional[int] = None
    ) -> KellyResult:
        """Calculate Kelly from trade journal data."""
        
        # Filter if needed
        filtered = trades
        if symbol:
            filtered = [t for t in trades if t.get('symbol') == symbol]
        if days:
            cutoff = datetime.now() - __import__('datetime').timedelta(days=days)
            filtered = [t for t in filtered if t.get('exit_time') and t.get('exit_time') > cutoff]
        
        if len(filtered) < self.MIN_SAMPLE_SIZE:
            return KellyResult(
                full_kelly=Decimal('0'),
                half_kelly=Decimal('0'),
                quarter_kelly=Decimal('0'),
                optimal_position=Decimal('0'),
                max_position=Decimal('0'),
                risk_of_ruin=Decimal('1'),
                expected_growth=Decimal('0'),
                edge_confidence=0.0,
                sample_size=len(filtered),
                win_rate_ci=(0, 1)
            )
        
        # Calculate stats
        pnls = [t.get('pnl', 0) for t in filtered if t.get('pnl') is not None]
        wins = [p for p in pnls if p > 0]
        losses = [abs(p) for p in pnls if p < 0]
        
        if not wins or not losses:
            return KellyResult(
                full_kelly=Decimal('0'),
                half_kelly=Decimal('0'),
                quarter_kelly=Decimal('0'),
                optimal_position=Decimal('0'),
                max_position=Decimal('0'),
                risk_of_ruin=Decimal('1'),
                expected_growth=Decimal('0'),
                edge_confidence=0.0,
                sample_size=len(filtered),
                win_rate_ci=(0, 1)
            )
        
        win_rate = len(wins) / len(pnls)
        avg_win = statistics.mean(wins)
        avg_loss = statistics.mean(losses)
        
        return self.calculate(
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            account_size=account_size,
            current_drawdown=current_drawdown,
            sample_size=len(pnls)
        )
    
    def simulate_growth(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        starting_account: float,
        num_trades: int = 1000,
        num_simulations: int = 100,
        method: str = "kelly"  # "kelly", "fixed", "percent_risk"
    ) -> SimulationResult:
        """Monte Carlo simulation of account growth."""
        
        final_values = []
        max_drawdowns = []
        ruin_count = 0
        
        # Determine position size based on method
        if method == "kelly":
            kelly = self.calculate(win_rate, avg_win, avg_loss, starting_account, sample_size=100)
            position_pct = float(kelly.full_kelly) * float(self.kelly_fraction)
        elif method == "fixed":
            position_pct = 0.02  # 2% fixed
        elif method == "percent_risk":
            position_pct = 0.01  # 1% risk per trade
        else:
            position_pct = 0.02
        
        for _ in range(num_simulations):
            account = starting_account
            peak = account
            max_dd = 0
            
            for _ in range(num_trades):
                # Determine outcome
                if random.random() < win_rate:
                    pnl = avg_win * position_pct
                else:
                    pnl = -avg_loss * position_pct
                
                account += pnl
                
                # Check ruin
                if account <= 0:
                    ruin_count += 1
                    break
                
                # Track drawdown
                if account > peak:
                    peak = account
                dd = (peak - account) / peak * 100
                max_dd = max(max_dd, dd)
            
            final_values.append(account)
            max_drawdowns.append(max_dd)
        
        # Calculate Sharpe-like metric (simplified)
        returns = [(v - starting_account) / starting_account for v in final_values]
        avg_return = statistics.mean(returns) if returns else 0
        std_return = statistics.stdev(returns) if len(returns) > 1 else 0.001
        sharpe = avg_return / std_return if std_return > 0 else 0
        
        return SimulationResult(
            method=method,
            final_values=final_values,
            median_final=statistics.median(final_values),
            max_drawdown_pct=statistics.median(max_drawdowns),
            ruin_count=ruin_count,
            sharpe=sharpe
        )
    
    def compare_methods(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        starting_account: float,
        num_trades: int = 500
    ) -> Dict[str, SimulationResult]:
        """Compare Kelly vs Fixed vs Percent Risk sizing."""
        
        methods = ["kelly", "fixed", "percent_risk"]
        results = {}
        
        for method in methods:
            results[method] = self.simulate_growth(
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                starting_account=starting_account,
                num_trades=num_trades,
                method=method
            )
        
        return results
    
    def batch_optimize(
        self,
        symbols_stats: Dict[str, dict],  # symbol -> {win_rate, avg_win, avg_loss, sample_size}
        account_size: float,
        max_total_exposure: float = 0.5  # Max 50% of account across all positions
    ) -> Dict[str, KellyResult]:
        """Calculate optimal sizes for multiple symbols simultaneously."""
        
        results = {}
        total_exposure = Decimal('0')
        
        # First pass: calculate raw Kelly for each
        for symbol, stats in symbols_stats.items():
            result = self.calculate(
                win_rate=stats['win_rate'],
                avg_win=stats['avg_win'],
                avg_loss=stats['avg_loss'],
                account_size=account_size,
                sample_size=stats.get('sample_size', 100)
            )
            results[symbol] = result
            total_exposure += Decimal(str(result.optimal_position))
        
        # Second pass: scale down if total exposure exceeds max
        max_total = Decimal(str(account_size)) * Decimal(str(max_total_exposure))
        if total_exposure > max_total:
            scale_factor = max_total / total_exposure
            
            for symbol in results:
                result = results[symbol]
                scaled_position = Decimal(str(result.optimal_position)) * scale_factor
                
                # Create new result with scaled position
                results[symbol] = KellyResult(
                    full_kelly=result.full_kelly,
                    half_kelly=result.half_kelly,
                    quarter_kelly=result.quarter_kelly,
                    optimal_position=scaled_position.quantize(Decimal('0.01')),
                    max_position=result.max_position,
                    risk_of_ruin=result.risk_of_ruin,
                    expected_growth=result.expected_growth * scale_factor,
                    edge_confidence=result.edge_confidence,
                    sample_size=result.sample_size,
                    win_rate_ci=result.win_rate_ci
                )
        
        return results
    
    def _calculate_ruin_risk(self, p: Decimal, q: Decimal, b: Decimal, f: Decimal) -> Decimal:
        """Simplified risk of ruin."""
        if f <= 0:
            return Decimal('0')
        edge = p * b - q
        if edge <= 0:
            return Decimal('1')
        return (q / p) ** (Decimal('0.5') / f)
    
    def _calculate_growth(self, p: Decimal, q: Decimal, b: Decimal, f: Decimal) -> Decimal:
        """Expected geometric growth rate."""
        if f <= 0:
            return Decimal('0')
        return (p * (Decimal('1') + f * b).ln() + q * (Decimal('1') - f).ln()).exp() - Decimal('1')


# === USAGE EXAMPLES ===

def example_journal_integration():
    """Calculate Kelly from trade history."""
    sizer = KellyPositionSizer(max_kelly_fraction=0.5)
    
    # Simulated trade journal data
    trades = [
        {'symbol': 'BTC', 'pnl': 150, 'exit_time': datetime.now()},
        {'symbol': 'BTC', 'pnl': -100, 'exit_time': datetime.now()},
        {'symbol': 'BTC', 'pnl': 200, 'exit_time': datetime.now()},
        # ... 50+ trades
    ] * 20  # Multiply for sample size
    
    result = sizer.from_trade_journal(
        trades=trades,
        account_size=10000,
        symbol='BTC'
    )
    
    print(f"Kelly from journal: {float(result.full_kelly):.2%}")
    print(f"Confidence: {result.edge_confidence:.1%}")
    print(f"Win rate 95% CI: {result.win_rate_ci[0]:.1%} - {result.win_rate_ci[1]:.1%}")

def example_method_comparison():
    """Compare different sizing methods."""
    sizer = KellyPositionSizer(max_kelly_fraction=0.5)
    
    comparison = sizer.compare_methods(
        win_rate=0.55,
        avg_win=200,
        avg_loss=100,
        starting_account=10000,
        num_trades=500
    )
    
    print("\n=== METHOD COMPARISON (500 trades, 100 sims) ===")
    print(f"{'Method':<15} {'Median Final':<15} {'Max DD':<12} {'Ruin':<10} {'Sharpe':<10}")
    print("-" * 65)
    
    for method, result in comparison.items():
        print(
            f"{method:<15} "
            f"${result.median_final:>13,.0f} "
            f"{result.max_drawdown_pct:>10.1f}% "
            f"{result.ruin_count:>8} "
            f"{result.sharpe:>9.2f}"
        )

def example_batch_optimization():
    """Optimize position sizes across multiple symbols."""
    sizer = KellyPositionSizer(max_kelly_fraction=0.5)
    
    symbols_stats = {
        'BTC': {'win_rate': 0.58, 'avg_win': 300, 'avg_loss': 150, 'sample_size': 80},
        'ETH': {'win_rate': 0.52, 'avg_win': 200, 'avg_loss': 100, 'sample_size': 120},
        'SOL': {'win_rate': 0.55, 'avg_win': 150, 'avg_loss': 100, 'sample_size': 60},
    }
    
    results = sizer.batch_optimize(
        symbols_stats=symbols_stats,
        account_size=50000,
        max_total_exposure=0.4  # Max 40% of account
    )
    
    print("\n=== BATCH OPTIMIZATION ===")
    print(f"{'Symbol':<8} {'Kelly':<10} {'Position':<12} {'Confidence':<12}")
    print("-" * 45)
    
    total = 0
    for symbol, result in results.items():
        total += float(result.optimal_position)
        print(
            f"{symbol:<8} "
            f"{float(result.full_kelly):<10.2%} "
            f"${float(result.optimal_position):>10,.0f} "
            f"{result.edge_confidence:>10.1%}"
        )
    
    print(f"\nTotal allocated: ${total:,.0f} ({total/50000:.1%} of account)")


if __name__ == "__main__":
    example_method_comparison()
    example_batch_optimization()
```

## Enhancements Summary

| Feature | Benefit |
|---------|---------|
| **Confidence Intervals** | Know if edge is statistically significant |
| **Trade Journal Integration** | Auto-calculate from actual performance |
| **Growth Simulation** | Visualize account paths before risking capital |
| **Method Comparison** | Prove Kelly outperforms fixed sizing |
| **Batch Optimization** | Handle multiple positions simultaneously |
| **Edge Confidence** | Don't trade when sample size is insufficient |

## Integration Example

```python
from trade_journal import TradeJournal
from kelly_sizer import KellyPositionSizer

journal = TradeJournal("trades.json")
sizer = KellyPositionSizer(max_kelly_fraction=0.5)

# Auto-size based on actual performance
result = sizer.from_trade_journal(
    trades=journal.get_closed_trades(days=90),
    account_size=portfolio.equity,
    current_drawdown=portfolio.drawdown_pct
)

if result.edge_confidence > 0.8 and result.sample_size > 50:
    size = result.optimal_position
else:
    size = min(result.optimal_position, account_size * 0.01)  # Very conservative
```

---
*Enhanced edition - adds real-world validation and portfolio-level optimization*
