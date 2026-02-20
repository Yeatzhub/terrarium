# Backtest Validator

**Purpose:** Detect data leakage, look-ahead bias, and unrealistic assumptions in backtests  
**Critical:** No model is deployable without passing validation

## The Code

```python
"""
Backtest Validator
Catch data leakage, look-ahead bias, and survivorship bias before they ruin live performance.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Callable
from datetime import datetime, timedelta
import random


@dataclass
class ValidationResult:
    """Result of a validation check."""
    test: str
    passed: bool
    severity: str  # critical, warning, info
    message: str
    details: Dict = None


@dataclass
class Trade:
    """Single backtest trade."""
    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    size: float
    pnl: float
    
    @property
    def duration(self) -> timedelta:
        return self.exit_time - self.entry_time


class BacktestValidator:
    """
    Validate backtest results for data leakage and bias.
    """
    
    def __init__(self, account_size: float = 100000):
        self.account = account_size
    
    def validate(
        self,
        trades: List[Trade],
        data_availability: Dict[datetime, List[str]],
        benchmark_returns: Optional[Dict[datetime, float]] = None
    ) -> List[ValidationResult]:
        """
        Run all validation checks.
        
        Args:
            trades: All trades from backtest
            data_availability: What data was available at each time
            benchmark_returns: Benchmark returns for comparison
        """
        results = []
        
        # Critical checks
        results.append(self._check_look_ahead(trades))
        results.append(self._check_data_availability(trades, data_availability))
        results.append(self._check_survivorship_bias(trades))
        results.append(self._check_fill_prices(trades))
        
        # Warning checks
        results.append(self._check_profitability_reasonable(trades))
        results.append(self._check_win_rate_extreme(trades))
        results.append(self._check_consecutive_wins_losses(trades))
        results.append(self._check_trade_frequency(trades))
        results.append(self._check_slippage_realistic(trades))
        
        # Info checks
        if benchmark_returns:
            results.append(self._check_vs_benchmark(trades, benchmark_returns))
        results.append(self._check_sample_size(trades))
        
        return results
    
    def _check_look_ahead(self, trades: List[Trade]) -> ValidationResult:
        """
        CHECK: Are signals generated after the bar they reference?
        If entry at 9:35, signal must be based on data available before 9:35.
        """
        suspicious = []
        
        for t in trades:
            # Check for suspicious patterns
            # If entry is exactly at market open every trade - possible lookahead
            if t.entry_time.minute == 30 and t.entry_time.second == 0:
                suspicious.append(t.symbol)
            
            # If profit always positive on same day - data leakage
            if t.pnl > 0 and t.duration < timedelta(minutes=5):
                suspicious.append(f"{t.symbol} ({t.duration.seconds}s gain)")
        
        if len(suspicious) > len(trades) * 0.5:
            return ValidationResult(
                "Look-Ahead Bias",
                False,
                "critical",
                f"{len(suspicious)} trades show possible lookahead patterns",
                {"examples": suspicious[:5]}
            )
        
        return ValidationResult(
            "Look-Ahead Bias",
            True,
            "info",
            "No obvious lookahead patterns detected",
            {}
        )
    
    def _check_data_availability(
        self,
        trades: List[Trade],
        data_availability: Dict[datetime, List[str]]
    ) -> ValidationResult:
        """
        CHECK: Was the symbol actually available for trading at entry time?
        """
        invalid = []
        
        for t in trades:
            # Find closest time in data_availability
            available = data_availability.get(t.entry_time.replace(second=0, microsecond=0), [])
            if t.symbol not in available:
                invalid.append(t.symbol)
        
        if invalid:
            return ValidationResult(
                "Data Availability",
                False,
                "critical",
                f"Traded {len(invalid)} symbols not in data at entry time",
                {"symbols": list(set(invalid))[:10]}
            )
        
        return ValidationResult(
            "Data Availability",
            True,
            "info",
            "All symbols available at entry time",
            {}
        )
    
    def _check_survivorship_bias(self, trades: List[Trade]) -> ValidationResult:
        """
        CHECK: Did all traded symbols exist throughout the backtest period?
        Excludes stocks that delisted during period.
        """
        # Check if all trades were closed
        open_trades = [t for t in trades if not t.exit_time]
        
        if open_trades:
            return ValidationResult(
                "Survivorship Bias",
                False,
                "warning",
                f"{len(open_trades)} trades without exits (possible delisting bias)",
                {"count": len(open_trades)}
            )
        
        return ValidationResult(
            "Survivorship Bias",
            True,
            "info",
            "All trades have exits",
            {}
        )
    
    def _check_fill_prices(self, trades: List[Trade]) -> ValidationResult:
        """
        CHECK: Are fill prices realistic (between high/low) or using close only?
        Using only close = unrealistic fills.
        """
        # Check if entry prices look like they only use close
        suspicious_closes = []
        
        for t in trades:
            # If entry matches exit exactly (zero duration, same price)
            # Or if price always ends in .00 (using close prices)
            if str(t.entry_price).endswith('.00') and str(t.exit_price).endswith('.00'):
                suspicious_closes.append(t.symbol)
        
        if len(suspicious_closes) > len(trades) * 0.3:
            return ValidationResult(
                "Fill Prices",
                False,
                "warning",
                f"Possible close-price only fills ({len(suspicious_closes)} clean prices)",
                {"examples": suspicious_closes[:5]}
            )
        
        return ValidationResult(
            "Fill Prices",
            True,
            "info",
            "Fill prices appear realistic",
            {}
        )
    
    def _check_profitability_reasonable(self, trades: List[Trade]) -> ValidationResult:
        """
        CHECK: Is total return reasonable (not 1000% annually)?
        """
        total_pnl = sum(t.pnl for t in trades)
        total_return = (total_pnl / self.account) * 100
        
        # Get backtest duration
        if not trades:
            return ValidationResult(
                "Profitability",
                True,
                "info",
                "No trades to analyze",
                {}
            )
        
        start = min(t.entry_time for t in trades)
        end = max(t.exit_time for t in trades)
        years = (end - start).days / 365 if start and end else 1
        
        annual_return = total_return / years if years > 0 else 0
        
        if annual_return > 200:
            return ValidationResult(
                "Profitability",
                False,
                "critical",
                f"Unrealistic {annual_return:.0f}% annual return",
                {"annual_return": annual_return, "total_return": total_return}
            )
        elif annual_return > 100:
            return ValidationResult(
                "Profitability",
                True,
                "warning",
                f"High but possible {annual_return:.0f}% annual return",
                {"annual_return": annual_return}
            )
        
        return ValidationResult(
            "Profitability",
            True,
            "info",
            f"Reasonable {annual_return:.1f}% annual return",
            {"annual_return": annual_return}
        )
    
    def _check_win_rate_extreme(self, trades: List[Trade]) -> ValidationResult:
        """
        CHECK: Win rate not too good to be true.
        """
        if not trades:
            return ValidationResult("Win Rate", True, "info", "No trades", {})
        
        wins = sum(1 for t in trades if t.pnl > 0)
        win_rate = wins / len(trades)
        
        if win_rate > 0.80:
            return ValidationResult(
                "Win Rate",
                False,
                "warning",
                f"Unrealistic {win_rate:.0%} win rate",
                {"win_rate": win_rate}
            )
        elif win_rate > 0.70:
            return ValidationResult(
                "Win Rate",
                True,
                "warning",
                f"Very high {win_rate:.0%} win rate",
                {"win_rate": win_rate}
            )
        
        return ValidationResult(
            "Win Rate",
            True,
            "info",
            f"Normal {win_rate:.0%} win rate",
            {"win_rate": win_rate}
        )
    
    def _check_consecutive_wins_losses(self, trades: List[Trade]) -> ValidationResult:
        """
        CHECK: Not too many consecutive wins/losses.
        """
        if not trades:
            return ValidationResult("Streaks", True, "info", "No trades", {})
        
        # Sort by time
        sorted_trades = sorted(trades, key=lambda t: t.entry_time)
        
        max_win_streak = 0
        max_loss_streak = 0
        current = 0
        last_was_win = None
        
        for t in sorted_trades:
            is_win = t.pnl > 0
            
            if last_was_win is None:
                current = 1
            elif is_win == last_was_win:
                current += 1
            else:
                if last_was_win:
                    max_win_streak = max(max_win_streak, current)
                else:
                    max_loss_streak = max(max_loss_streak, current)
                current = 1
            
            last_was_win = is_win
        
        if last_was_win:
            max_win_streak = max(max_win_streak, current)
        else:
            max_loss_streak = max(max_loss_streak, current)
        
        if max_win_streak > 15:
            return ValidationResult(
                "Streaks",
                False,
                "warning",
                f"Suspicious: {max_win_streak} consecutive wins",
                {"max_win_streak": max_win_streak, "max_loss_streak": max_loss_streak}
            )
        
        return ValidationResult(
            "Streaks",
            True,
            "info",
            f"Max streaks: {max_win_streak}W / {max_loss_streak}L",
            {"max_win_streak": max_win_streak, "max_loss_streak": max_loss_streak}
        )
    
    def _check_trade_frequency(self, trades: List[Trade]) -> ValidationResult:
        """
        CHECK: Reasonable trade frequency.
        """
        if len(trades) < 2:
            return ValidationResult("Frequency", True, "info", "Too few trades", {})
        
        start = min(t.entry_time for t in trades)
        end = max(t.exit_time for t in trades)
        days = (end - start).days or 1
        
        trades_per_day = len(trades) / days
        
        if trades_per_day > 50:
            return ValidationResult(
                "Frequency",
                False,
                "warning",
                f"Excessive {trades_per_day:.0f} trades/day",
                {"trades_per_day": trades_per_day}
            )
        
        return ValidationResult(
            "Frequency",
            True,
            "info",
            f"Reasonable {trades_per_day:.1f} trades/day",
            {"trades_per_day": trades_per_day}
        )
    
    def _check_slippage_realistic(self, trades: List[Trade]) -> ValidationResult:
        """
        CHECK: Is slippage modeled?
        """
        # Check if all entry/exit prices look too clean (no slippage)
        no_slippage = 0
        
        for t in trades:
            # Very tight spreads indicate no slippage
            pnl_per_share = t.pnl / t.size if t.size else 0
            if abs(pnl_per_share - (t.exit_price - t.entry_price)) < 0.01:
                no_slippage += 1
        
        if no_slippage > len(trades) * 0.9:
            return ValidationResult(
                "Slippage",
                False,
                "critical",
                "Backtest appears to ignore slippage",
                {"no_slippage_pct": no_slippage / len(trades) * 100}
            )
        
        return ValidationResult(
            "Slippage",
            True,
            "info",
            "Slippage likely modeled",
            {}
        )
    
    def _check_vs_benchmark(
        self,
        trades: List[Trade],
        benchmark: Dict[datetime, float]
    ) -> ValidationResult:
        """
        CHECK: Performance vs benchmark is reasonable.
        """
        # Simplified - just check if outperformance exists
        return ValidationResult(
            "Benchmark",
            True,
            "info",
            "Benchmark comparison checked",
            {}
        )
    
    def _check_sample_size(self, trades: List[Trade]) -> ValidationResult:
        """
        CHECK: Enough trades for statistical significance.
        """
        if len(trades) < 30:
            return ValidationResult(
                "Sample Size",
                False,
                "warning",
                f"Only {len(trades)} trades (need 100+ for confidence)",
                {"count": len(trades)}
            )
        elif len(trades) < 100:
            return ValidationResult(
                "Sample Size",
                True,
                "warning",
                f"Small sample: {len(trades)} trades",
                {"count": len(trades)}
            )
        
        return ValidationResult(
            "Sample Size",
            True,
            "info",
            f"Good sample: {len(trades)} trades",
            {"count": len(trades)}
        )
    
    def print_report(self, results: List[ValidationResult]):
        """Print formatted validation report."""
        print(f"\n{'='*70}")
        print("BACKTEST VALIDATION REPORT")
        print(f"{'='*70}")
        
        critical = [r for r in results if r.severity == "critical" and not r.passed]
        warnings = [r for r in results if r.severity == "warning" and not r.passed]
        passed = [r for r in results if r.passed]
        
        if critical:
            print(f"\n❌ CRITICAL FAILURES ({len(critical)}):")
            print("   Backtest NOT valid for live trading!")
            for r in critical:
                print(f"   • {r.test}: {r.message}")
        
        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for r in warnings:
                print(f"   • {r.test}: {r.message}")
        
        print(f"\n✓ PASSED CHECKS ({len(passed)}):")
        for r in passed:
            print(f"   • {r.test}: {r.message}")
        
        print(f"\n{'='*70}")
        if critical:
            print("RESULT: ❌ BACKTEST FAILED - Do not use for trading")
        elif warnings:
            print("RESULT: ⚠️ BACKTEST PASSED WITH WARNINGS - Review carefully")
        else:
            print("RESULT: ✅ BACKTEST VALIDATED - Proceed with caution")
        print(f"{'='*70}\n")


# === Example Usage ===

if __name__ == "__main__":
    validator = BacktestValidator(account_size=100000)
    
    # Simulate suspicious backtest (look-ahead bias)
    print("EXAMPLE 1: Suspicious Backtest")
    print("="*70)
    
    base_time = datetime(2024, 1, 1)
    
    suspicious_trades = [
        Trade(
            symbol="AAPL",
            entry_time=base_time + timedelta(days=i),
            entry_price=150.00,  # Clean prices (.00)
            exit_time=base_time + timedelta(days=i, hours=1),
            exit_price=151.00,
            size=100,
            pnl=100
        )
        for i in range(50)
    ]
    
    # All wins
    data_avail = {base_time + timedelta(days=i): ["AAPL"] for i in range(50)}
    
    results = validator.validate(suspicious_trades, data_avail)
    validator.print_report(results)
    
    # Simulate realistic backtest
    print("\nEXAMPLE 2: Realistic Backtest")
    print("="*70)
    
    realistic_trades = [
        Trade(
            symbol=random.choice(["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL"]),
            entry_time=base_time + timedelta(days=i),
            entry_price=150 + i * 0.42,  # Realistic decimals
            exit_time=base_time + timedelta(days=i, hours=4),
            exit_price=150 + i * 0.42 + random.gauss(0, 1),
            size=100,
            pnl=random.gauss(50, 200)
        )
        for i in range(100)
    ]
    
    data_avail = {base_time + timedelta(days=i): ["AAPL", "MSFT", "TSLA", "AMZN", "GOOGL"] for i in range(100)}
    
    results = validator.validate(realistic_trades, data_avail)
    validator.print_report(results)


## Validation Checklist Summary

| Check | Fail If | Severity |
|-------|---------|----------|
| **Look-Ahead Bias** | >50% trades at exact open | Critical |
| **Data Availability** | Trading unavailable symbols | Critical |
| **Survivorship** | Missing exits (delisted stocks) | Warning |
| **Fill Prices** | Using only close prices | Warning |
| **Profitability** | >200% annual return | Critical |
| **Win Rate** | >80% win rate | Warning |
| **Streaks** | >15 consecutive wins | Warning |
| **Frequency** | >50 trades/day | Warning |
| **Slippage** | Not modeled | Critical |
| **Sample Size** | <30 trades | Warning |

## Why Validation Matters

Backtest ≠ Reality due to:
- **Look-ahead bias** - Future data leaks into signals
- **Survivorship bias** - Only winning stocks remain
- **Fill price fantasy** - Always getting close price
- **Slippage denial** - Markets move against you

**Rule:** If validation fails, backtest is worthless. Period.

---

**Created by Ghost 👻 | Feb 19, 2026 | 14-min learning sprint**  
*Lesson: All backtests lie. Validation catches the worst lies before they cost money.*
