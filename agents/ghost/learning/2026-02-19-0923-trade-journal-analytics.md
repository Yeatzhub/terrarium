# Trade Journal & Performance Analytics

**Purpose:** Log trades, calculate performance metrics, identify edge degradation  
**Output:** Sharpe ratio, win rate by setup, equity curve, max consecutive losses

## The Code

```python
"""
Trade Journal with Performance Analytics
Track trades, calculate metrics, detect strategy decay.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, Literal, Callable
from collections import defaultdict
import json
import math
from pathlib import Path


@dataclass
class Trade:
    """Single trade record."""
    symbol: str
    direction: Literal["long", "short"]
    entry_price: float
    exit_price: float
    size: float
    entry_time: datetime
    exit_time: datetime
    setup: str = "default"  # Pattern/strategy name
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: str = ""
    
    @property
    def pnl(self) -> float:
        mult = 1 if self.direction == "long" else -1
        return (self.exit_price - self.entry_price) * self.size * mult
    
    @property
    def duration_minutes(self) -> float:
        return (self.exit_time - self.entry_time).total_seconds() / 60
    
    @property
    def risk_amount(self) -> float:
        if self.stop_loss is None:
            return abs(self.pnl)  # Use actual as proxy
        mult = 1 if self.direction == "long" else -1
        return abs(self.entry_price - self.stop_loss) * self.size * mult
    
    @property
    def r_multiple(self) -> float:
        """Trade result in R units."""
        risk = self.risk_amount
        return self.pnl / risk if risk > 0 else 0
    
    @property
    def mae(self) -> float:
        """Maximum adverse excursion (worst drawdown during trade)."""
        # Simplified: assume entry was worst point for winners
        if self.pnl > 0:
            return -self.risk_amount * 0.3  # Estimate
        return self.pnl
    
    @property
    def mfe(self) -> float:
        """Maximum favorable excursion (best price during trade)."""
        if self.pnl > 0:
            return self.pnl * 1.2  # Estimate
        return self.pnl * 0.5


@dataclass
class PerformanceMetrics:
    """Calculated performance statistics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_winner: float
    avg_loser: float
    profit_factor: float
    expectancy: float  # Expected value per trade in R
    expectancy_dollar: float
    sharpe_ratio: float
    max_drawdown_pct: float
    max_consecutive_losses: int
    avg_trade_duration_min: float
    total_pnl: float
    avg_daily_pnl: float
    best_day: float
    worst_day: float
    r_squared: float  # Consistency of returns


class TradeJournal:
    """
    Log trades and generate performance analytics.
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.trades: list[Trade] = []
        self.initial_capital: float = 0
        self.current_capital: float = 0
    
    def set_capital(self, amount: float):
        """Set starting capital."""
        if not self.initial_capital:
            self.initial_capital = amount
        self.current_capital = amount
    
    def add_trade(self, trade: Trade):
        """Record a completed trade."""
        self.trades.append(trade)
        self.current_capital += trade.pnl
    
    def calculate_metrics(self, lookback_days: Optional[int] = None) -> PerformanceMetrics:
        """Calculate all performance statistics."""
        trades = self._filter_trades(lookback_days)
        
        if not trades:
            raise ValueError("No trades to analyze")
        
        wins = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in trades)
        
        # Win/loss stats
        win_rate = len(wins) / len(trades) if trades else 0
        avg_winner = sum(t.pnl for t in wins) / len(wins) if wins else 0
        avg_loser = sum(t.pnl for t in losses) / len(losses) if losses else 0
        
        # Profit factor
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Expectancy in R
        r_values = [t.r_multiple for t in trades]
        expectancy = sum(r_values) / len(r_values) if r_values else 0
        
        # Expectancy in dollars
        avg_risk = sum(t.risk_amount for t in trades) / len(trades)
        expectancy_dollar = expectancy * avg_risk
        
        # Sharpe (simplified, assuming daily returns)
        daily_pnls = self._daily_pnls(trades)
        sharpe = self._calculate_sharpe(daily_pnls)
        
        # Drawdown
        max_dd = self._calculate_max_drawdown(trades)
        
        # Consecutive losses
        max_cons_losses = self._max_consecutive_losses(trades)
        
        # Duration
        avg_duration = sum(t.duration_minutes for t in trades) / len(trades)
        
        # Daily stats
        avg_daily = sum(daily_pnls) / len(daily_pnls) if daily_pnls else 0
        best_day = max(daily_pnls) if daily_pnls else 0
        worst_day = min(daily_pnls) if daily_pnls else 0
        
        # R-squared (consistency metric)
        r_squared = self._calculate_r_squared(r_values)
        
        return PerformanceMetrics(
            total_trades=len(trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=win_rate,
            avg_winner=avg_winner,
            avg_loser=avg_loser,
            profit_factor=profit_factor,
            expectancy=expectancy,
            expectancy_dollar=expectancy_dollar,
            sharpe_ratio=sharpe,
            max_drawdown_pct=max_dd,
            max_consecutive_losses=max_cons_losses,
            avg_trade_duration_min=avg_duration,
            total_pnl=total_pnl,
            avg_daily_pnl=avg_daily,
            best_day=best_day,
            worst_day=worst_day,
            r_squared=r_squared
        )
    
    def _filter_trades(self, lookback_days: Optional[int]) -> list[Trade]:
        """Filter trades by date range."""
        if not lookback_days:
            return self.trades
        
        cutoff = datetime.now() - __import__('datetime').timedelta(days=lookback_days)
        return [t for t in self.trades if t.exit_time >= cutoff]
    
    def _daily_pnls(self, trades: list[Trade]) -> list[float]:
        """Aggregate P&L by day."""
        daily = defaultdict(float)
        for t in trades:
            day = t.exit_time.date()
            daily[day] += t.pnl
        return list(daily.values())
    
    def _calculate_sharpe(self, daily_returns: list[float], risk_free: float = 0) -> float:
        """Annualized Sharpe ratio."""
        if len(daily_returns) < 2:
            return 0.0
        
        avg_return = sum(daily_returns) / len(daily_returns)
        variance = sum((r - avg_return) ** 2 for r in daily_returns) / (len(daily_returns) - 1)
        std_dev = math.sqrt(variance)
        
        if std_dev == 0:
            return 0.0
        
        # Annualize (252 trading days)
        return (avg_return / std_dev) * math.sqrt(252)
    
    def _calculate_max_drawdown(self, trades: list[Trade]) -> float:
        """Maximum drawdown from equity peak (%)."""
        equity = self.initial_capital
        peak = equity
        max_dd = 0.0
        
        for t in sorted(trades, key=lambda x: x.exit_time):
            equity += t.pnl
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak * 100
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _max_consecutive_losses(self, trades: list[Trade]) -> int:
        """Longest losing streak."""
        max_streak = 0
        current_streak = 0
        
        for t in sorted(trades, key=lambda x: x.exit_time):
            if t.pnl <= 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def _calculate_r_squared(self, r_values: list[float]) -> float:
        """Variance of R multiples (lower = more consistent)."""
        if len(r_values) < 2:
            return 0.0
        avg = sum(r_values) / len(r_values)
        variance = sum((r - avg) ** 2 for r in r_values) / len(r_values)
        return variance
    
    def analyze_by_setup(self) -> dict:
        """Performance breakdown by strategy/setup."""
        setups = defaultdict(list)
        for t in self.trades:
            setups[t.setup].append(t)
        
        results = {}
        for setup, trades in setups.items():
            wins = [t for t in trades if t.pnl > 0]
            total_pnl = sum(t.pnl for t in trades)
            
            results[setup] = {
                "trades": len(trades),
                "win_rate": len(wins) / len(trades) if trades else 0,
                "total_pnl": total_pnl,
                "avg_pnl": total_pnl / len(trades),
                "avg_r": sum(t.r_multiple for t in trades) / len(trades),
                "best_trade": max(t.pnl for t in trades) if trades else 0,
                "worst_trade": min(t.pnl for t in trades) if trades else 0
            }
        
        return results
    
    def detect_decay(self, window: int = 20) -> Optional[str]:
        """
        Detect if strategy is degrading.
        Returns warning message if decay detected.
        """
        if len(self.trades) < window * 2:
            return None
        
        # Compare recent vs older performance
        recent = self.trades[-window:]
        older = self.trades[-window*2:-window]
        
        recent_win_rate = len([t for t in recent if t.pnl > 0]) / len(recent)
        older_win_rate = len([t for t in older if t.pnl > 0]) / len(older)
        
        recent_exp = sum(t.r_multiple for t in recent) / len(recent)
        older_exp = sum(t.r_multiple for t in older) / len(older)
        
        warnings = []
        if recent_win_rate < older_win_rate * 0.7:
            warnings.append(f"Win rate dropped {older_win_rate:.1%} → {recent_win_rate:.1%}")
        if recent_exp < older_exp * 0.5:
            warnings.append(f"Expectancy dropped {older_exp:.2f}R → {recent_exp:.2f}R")
        
        return " | ".join(warnings) if warnings else None
    
    def save(self, path: Path):
        """Save journal to JSON."""
        data = {
            "name": self.name,
            "initial_capital": self.initial_capital,
            "current_capital": self.current_capital,
            "trades": [
                {
                    "symbol": t.symbol,
                    "direction": t.direction,
                    "entry": t.entry_price,
                    "exit": t.exit_price,
                    "pnl": t.pnl,
                    "r": t.r_multiple,
                    "setup": t.setup,
                    "entry_time": t.entry_time.isoformat(),
                    "exit_time": t.exit_time.isoformat(),
                }
                for t in self.trades
            ]
        }
        path.write_text(json.dumps(data, indent=2))
    
    def print_report(self, metrics: PerformanceMetrics):
        """Print formatted performance report."""
        print("=" * 50)
        print(f"Performance Report: {self.name}")
        print("=" * 50)
        print(f"Total Trades:    {metrics.total_trades}")
        print(f"Win Rate:        {metrics.win_rate:.1%}")
        print(f"Profit Factor:   {metrics.profit_factor:.2f}")
        print(f"Expectancy:      {metrics.expectancy:.2f}R (${metrics.expectancy_dollar:.2f})")
        print(f"Sharpe Ratio:    {metrics.sharpe_ratio:.2f}")
        print(f"Max Drawdown:    {metrics.max_drawdown_pct:.1f}%")
        print(f"Max Consecutive: {metrics.max_consecutive_losses} losses")
        print(f"Total P&L:       ${metrics.total_pnl:,.2f}")
        print(f"Avg Daily:       ${metrics.avg_daily_pnl:,.2f}")
        print("=" * 50)


# --- Example Usage ---

if __name__ == "__main__":
    from datetime import timedelta
    
    journal = TradeJournal("Breakout Strategy")
    journal.set_capital(50000)
    
    # Simulate 30 days of trades
    import random
    random.seed(42)
    
    base_time = datetime(2024, 1, 1, 9, 30)
    
    for i in range(50):
        is_win = random.random() < 0.45  # 45% win rate
        r = random.uniform(2.0, 4.0) if is_win else random.uniform(-0.8, -1.2)
        
        direction = "long" if random.random() > 0.5 else "short"
        entry = 100 + random.uniform(-10, 10)
        risk = 100  # $100 risk per trade
        
        # Calculate exit based on R
        if direction == "long":
            exit_p = entry + (r * 1)  # $1 per share risk
        else:
            exit_p = entry - (r * 1)
        
        trade = Trade(
            symbol=random.choice(["AAPL", "MSFT", "NVDA"]),
            direction=direction,
            entry_price=entry,
            exit_price=exit_p,
            size=100,
            entry_time=base_time + timedelta(days=i//2, hours=random.randint(0, 6)),
            exit_time=base_time + timedelta(days=i//2, hours=random.randint(1, 8)),
            setup=random.choice(["breakout", "pullback", "reversal"]),
            stop_loss=entry - 1 if direction == "long" else entry + 1
        )
        
        journal.add_trade(trade)
    
    # Generate report
    metrics = journal.calculate_metrics()
    journal.print_report(metrics)
    
    # Setup analysis
    print("\nBy Setup:")
    for setup, stats in journal.analyze_by_setup().items():
        print(f"  {setup}: {stats['trades']} trades, {stats['win_rate']:.0%} WR, ${stats['total_pnl']:.0f}")
    
    # Decay check
    decay = journal.detect_decay(window=10)
    if decay:
        print(f"\n⚠️  DECAY DETECTED: {decay}")
    else:
        print("\n✓ No decay detected")
```

## Key Metrics Explained

| Metric | What It Tells You | Good Value |
|--------|-------------------|------------|
| **Expectancy** | Expected R per trade | > 0.5R |
| **Profit Factor** | Gross profit / gross loss | > 1.5 |
| **Sharpe** | Risk-adjusted returns | > 1.0 |
| **Max Consecutive** | Worst losing streak | Know your psychology limit |
| **R-Squared** | Consistency of results | Lower = more consistent |

## Decay Detection

```python
warning = journal.detect_decay(window=20)
if warning:
    print(f"Strategy failing: {warning}")
    # Actions: Reduce size, pause, or review market conditions
```

Checks for:
- Win rate drop > 30% from baseline
- Expectancy drop > 50% from baseline

## When to Use

- **Daily:** Log all trades, check expectancy trend
- **Weekly:** Full metrics review, setup analysis
- **Monthly:** Save to file, long-term decay detection

---

**Created by Ghost 👻 | Feb 19, 2026 | 15-min learning sprint**  
*Pattern: Measure everything, detect decay early, cut losers fast*
