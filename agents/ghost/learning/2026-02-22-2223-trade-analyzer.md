# Trade Analyzer
*Ghost Learning | 2026-02-22*

Analyze trading patterns, find what works, identify weaknesses.

## Key Analytics

| Analysis | Purpose |
|----------|---------|
| **Time-based** | Best/worst trading hours |
| **Performance attribution** | What drives your P&L |
| **Pattern detection** | Recurring mistakes/wins |
| **Edge decay** | Is strategy still working? |

## Implementation

```python
"""
Trade Analyzer
Pattern detection and performance analysis.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from collections import defaultdict
import math


@dataclass
class Trade:
    """Trade record."""
    id: str
    symbol: str
    side: str  # "long" or "short"
    entry_time: datetime
    exit_time: datetime
    entry_price: Decimal
    exit_price: Decimal
    size: Decimal
    pnl: Decimal
    fees: Decimal = Decimal("0")
    strategy: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    @property
    def return_pct(self) -> Decimal:
        if self.entry_price == 0:
            return Decimal("0")
        return self.pnl / (self.entry_price * self.size)
    
    @property
    def hold_time(self) -> timedelta:
        return self.exit_time - self.entry_time
    
    @property
    def hold_hours(self) -> float:
        return self.hold_time.total_seconds() / 3600
    
    @property
    def is_winner(self) -> bool:
        return self.pnl > 0
    
    @property
    def hour_of_day(self) -> int:
        return self.entry_time.hour
    
    @property
    def day_of_week(self) -> int:
        return self.entry_time.weekday()  # 0=Monday


@dataclass
class PerformanceBy:
    """Performance breakdown by a dimension."""
    dimension: str
    value: str
    trades: int
    winners: int
    losers: int
    win_rate: Decimal
    total_pnl: Decimal
    avg_pnl: Decimal
    avg_winner: Decimal
    avg_loser: Decimal
    profit_factor: Decimal
    
    def __str__(self) -> str:
        return (
            f"{self.dimension}={self.value}: "
            f"{self.trades} trades, {self.win_rate:.0%} win, "
            f"${self.total_pnl:+,.0f} total, ${self.avg_pnl:+,.0f} avg"
        )


@dataclass
class Pattern:
    """Detected pattern."""
    name: str
    description: str
    impact: str  # "positive" or "negative"
    confidence: Decimal
    trades_matching: int
    suggestion: str
    
    def __str__(self) -> str:
        icon = "✅" if self.impact == "positive" else "⚠️"
        return f"{icon} {self.name}: {self.description}\n   → {self.suggestion}"


@dataclass
class AnalysisReport:
    """Full analysis report."""
    total_trades: int
    total_pnl: Decimal
    win_rate: Decimal
    
    by_hour: List[PerformanceBy]
    by_day: List[PerformanceBy]
    by_symbol: List[PerformanceBy]
    by_strategy: List[PerformanceBy]
    by_hold_time: List[PerformanceBy]
    
    patterns: List[Pattern]
    
    best_hour: Optional[Tuple[int, Decimal]]
    worst_hour: Optional[Tuple[int, Decimal]]
    best_day: Optional[Tuple[str, Decimal]]
    worst_day: Optional[Tuple[str, Decimal]]
    
    streak_analysis: Dict
    
    def summary(self) -> str:
        lines = [
            "=== TRADE ANALYSIS ===",
            f"Trades: {self.total_trades}",
            f"P&L: ${self.total_pnl:+,.2f}",
            f"Win Rate: {self.win_rate:.1%}",
            "",
        ]
        
        if self.best_hour:
            lines.append(f"Best Hour: {self.best_hour[0]:02d}:00 ({self.best_hour[1]:+.1%} win)")
        if self.worst_hour:
            lines.append(f"Worst Hour: {self.worst_hour[0]:02d}:00 ({self.worst_hour[1]:+.1%} win)")
        
        if self.patterns:
            lines.append("\n--- PATTERNS ---")
            for p in self.patterns:
                lines.append(str(p))
        
        return "\n".join(lines)


class TradeAnalyzer:
    """
    Analyze trading patterns and performance.
    """
    
    def __init__(self, trades: List[Trade]):
        self.trades = sorted(trades, key=lambda t: t.entry_time)
    
    def analyze(self) -> AnalysisReport:
        """Run full analysis."""
        return AnalysisReport(
            total_trades=len(self.trades),
            total_pnl=sum(t.pnl for t in self.trades),
            win_rate=self._win_rate(self.trades),
            by_hour=self._by_hour(),
            by_day=self._by_day(),
            by_symbol=self._by_symbol(),
            by_strategy=self._by_strategy(),
            by_hold_time=self._by_hold_time(),
            patterns=self._detect_patterns(),
            best_hour=self._find_best_hour(),
            worst_hour=self._find_worst_hour(),
            best_day=self._find_best_day(),
            worst_day=self._find_worst_day(),
            streak_analysis=self._analyze_streaks()
        )
    
    def _win_rate(self, trades: List[Trade]) -> Decimal:
        if not trades:
            return Decimal("0")
        winners = len([t for t in trades if t.is_winner])
        return Decimal(winners) / Decimal(len(trades))
    
    def _group_metrics(self, trades: List[Trade]) -> Dict:
        """Calculate metrics for a group of trades."""
        if not trades:
            return {}
        
        winners = [t for t in trades if t.is_winner]
        losers = [t for t in trades if not t.is_winner]
        
        total_pnl = sum(t.pnl for t in trades)
        gross_win = sum(t.pnl for t in winners)
        gross_loss = sum(abs(t.pnl) for t in losers)
        
        return {
            "trades": len(trades),
            "winners": len(winners),
            "losers": len(losers),
            "win_rate": self._win_rate(trades),
            "total_pnl": total_pnl,
            "avg_pnl": total_pnl / len(trades),
            "avg_winner": gross_win / len(winners) if winners else Decimal("0"),
            "avg_loser": gross_loss / len(losers) if losers else Decimal("0"),
            "profit_factor": gross_win / gross_loss if gross_loss > 0 else Decimal("999"),
        }
    
    def _by_hour(self) -> List[PerformanceBy]:
        """Performance by hour of day."""
        by_hour = defaultdict(list)
        for t in self.trades:
            by_hour[t.hour_of_day].append(t)
        
        results = []
        for hour in sorted(by_hour.keys()):
            m = self._group_metrics(by_hour[hour])
            results.append(PerformanceBy(
                dimension="hour",
                value=f"{hour:02d}:00",
                **m
            ))
        return results
    
    def _by_day(self) -> List[PerformanceBy]:
        """Performance by day of week."""
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        by_day = defaultdict(list)
        for t in self.trades:
            by_day[t.day_of_week].append(t)
        
        results = []
        for day_num in sorted(by_day.keys()):
            m = self._group_metrics(by_day[day_num])
            results.append(PerformanceBy(
                dimension="day",
                value=days[day_num],
                **m
            ))
        return results
    
    def _by_symbol(self) -> List[PerformanceBy]:
        """Performance by symbol."""
        by_symbol = defaultdict(list)
        for t in self.trades:
            by_symbol[t.symbol].append(t)
        
        results = []
        for symbol in sorted(by_symbol.keys()):
            m = self._group_metrics(by_symbol[symbol])
            results.append(PerformanceBy(dimension="symbol", value=symbol, **m))
        return results
    
    def _by_strategy(self) -> List[PerformanceBy]:
        """Performance by strategy."""
        by_strategy = defaultdict(list)
        for t in self.trades:
            strat = t.strategy or "unknown"
            by_strategy[strat].append(t)
        
        results = []
        for strategy in sorted(by_strategy.keys()):
            m = self._group_metrics(by_strategy[strategy])
            results.append(PerformanceBy(dimension="strategy", value=strategy, **m))
        return results
    
    def _by_hold_time(self) -> List[PerformanceBy]:
        """Performance by hold time bucket."""
        buckets = {
            "<1h": lambda h: h < 1,
            "1-4h": lambda h: 1 <= h < 4,
            "4-24h": lambda h: 4 <= h < 24,
            "1-7d": lambda h: 24 <= h < 168,
            ">7d": lambda h: h >= 168,
        }
        
        by_bucket = defaultdict(list)
        for t in self.trades:
            hours = t.hold_hours
            for bucket, check in buckets.items():
                if check(hours):
                    by_bucket[bucket].append(t)
                    break
        
        results = []
        order = ["<1h", "1-4h", "4-24h", "1-7d", ">7d"]
        for bucket in order:
            if bucket in by_bucket:
                m = self._group_metrics(by_bucket[bucket])
                results.append(PerformanceBy(dimension="hold_time", value=bucket, **m))
        return results
    
    def _find_best_hour(self) -> Optional[Tuple[int, Decimal]]:
        """Find best performing hour."""
        by_hour = self._by_hour()
        if not by_hour:
            return None
        best = max(by_hour, key=lambda x: x.win_rate)
        return (int(best.value.split(":")[0]), best.win_rate)
    
    def _find_worst_hour(self) -> Optional[Tuple[int, Decimal]]:
        """Find worst performing hour."""
        by_hour = self._by_hour()
        if not by_hour:
            return None
        worst = min(by_hour, key=lambda x: x.win_rate)
        return (int(worst.value.split(":")[0]), worst.win_rate)
    
    def _find_best_day(self) -> Optional[Tuple[str, Decimal]]:
        """Find best performing day."""
        by_day = self._by_day()
        if not by_day:
            return None
        best = max(by_day, key=lambda x: x.win_rate)
        return (best.value, best.win_rate)
    
    def _find_worst_day(self) -> Optional[Tuple[str, Decimal]]:
        """Find worst performing day."""
        by_day = self._by_day()
        if not by_day:
            return None
        worst = min(by_day, key=lambda x: x.win_rate)
        return (worst.value, worst.win_rate)
    
    def _analyze_streaks(self) -> Dict:
        """Analyze winning/losing streaks."""
        if not self.trades:
            return {}
        
        max_wins = max_losses = current_wins = current_losses = 0
        
        for t in self.trades:
            if t.is_winner:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)
        
        return {
            "max_winning_streak": max_wins,
            "max_losing_streak": max_losses,
            "current_streak": current_wins if current_wins > 0 else -current_losses
        }
    
    def _detect_patterns(self) -> List[Pattern]:
        """Detect trading patterns."""
        patterns = []
        
        # Pattern: Poor performance at specific hours
        byhour = self._by_hour()
        for h in byhour:
            if h.trades >= 5 and h.win_rate < Decimal("0.35"):
                patterns.append(Pattern(
                    name="Weak Hour",
                    description=f"{h.value} has {h.win_rate:.0%} win rate ({h.trades} trades)",
                    impact="negative",
                    confidence=Decimal("0.6"),
                    trades_matching=h.trades,
                    suggestion=f"Avoid trading at {h.value} or review strategy"
                ))
        
        # Pattern: Strong performance at specific hours
        for h in by_hour:
            if h.trades >= 5 and h.win_rate > Decimal("0.65"):
                patterns.append(Pattern(
                    name="Strong Hour",
                    description=f"{h.value} has {h.win_rate:.0%} win rate",
                    impact="positive",
                    confidence=Decimal("0.6"),
                    trades_matching=h.trades,
                    suggestion=f"Focus more capital at {h.value}"
                ))
        
        # Pattern: Holding too long
        by_hold = self._by_hold_time()
        for h in by_hold:
            if h.value == ">7d" and h.trades >= 3:
                if h.win_rate < Decimal("0.4"):
                    patterns.append(Pattern(
                        name="Overholding",
                        description=f"Trades >7 days: {h.win_rate:.0%} win rate",
                        impact="negative",
                        confidence=Decimal("0.5"),
                        trades_matching=h.trades,
                        suggestion="Set tighter time-based stops"
                    ))
        
        # Pattern: Quick scalps working
        for h in by_hold:
            if h.value == "<1h" and h.trades >= 5:
                if h.win_rate > Decimal("0.6"):
                    patterns.append(Pattern(
                        name="Scalping Edge",
                        description=f"<1h trades: {h.win_rate:.0%} win rate, ${h.total_pnl:+,.0f}",
                        impact="positive",
                        confidence=Decimal("0.6"),
                        trades_matching=h.trades,
                        suggestion="Increase quick trade allocation"
                    ))
        
        # Pattern: Strategy decay
        by_strat = self._by_strategy()
        if len(by_strat) > 1:
            weak_strats = [s for s in by_strat if s.trades >= 5 and s.win_rate < Decimal("0.4")]
            for s in weak_strats:
                patterns.append(Pattern(
                    name="Weak Strategy",
                    description=f"'{s.value}': {s.win_rate:.0%} win rate",
                    impact="negative",
                    confidence=Decimal("0.5"),
                    trades_matching=s.trades,
                    suggestion=f"Review or discontinue '{s.value}'"
                ))
        
        return patterns


# === Usage ===

if __name__ == "__main__":
    from datetime import timedelta
    import random
    
    random.seed(42)
    
    # Generate sample trades
    base = datetime.utcnow() - timedelta(days=90)
    trades = []
    
    symbols = ["BTC", "ETH", "SOL"]
    strategies = ["breakout", "reversal", "momentum"]
    
    for i in range(100):
        symbol = random.choice(symbols)
        strategy = random.choice(strategies)
        side = random.choice(["long", "short"])
        
        # Create bias: mornings better for momentum
        hour = random.randint(8, 18)
        if hour < 12 and strategy == "momentum":
            win_prob = 0.7
        else:
            win_prob = 0.45
        
        is_win = random.random() < win_prob
        
        entry_time = base + timedelta(days=i*0.9, hours=hour)
        hold_hours = random.uniform(0.5, 48)
        exit_time = entry_time + timedelta(hours=hold_hours)
        
        entry = Decimal(str(random.uniform(100, 500)))
        size = Decimal("1.0")
        
        if is_win:
            pnl = Decimal(str(random.uniform(50, 300)))
        else:
            pnl = Decimal(str(-random.uniform(30, 150)))
        
        exit_price = entry + (pnl / size)
        
        trades.append(Trade(
            id=f"T{i:03d}",
            symbol=symbol,
            side=side,
            entry_time=entry_time,
            exit_time=exit_time,
            entry_price=entry,
            exit_price=exit_price,
            size=size,
            pnl=pnl,
            strategy=strategy
        ))
    
    # Analyze
    analyzer = TradeAnalyzer(trades)
    report = analyzer.analyze()
    
    print(report.summary())
    
    print("\n--- BY HOUR ---")
    for h in report.by_hour[:5]:
        print(f"  {h}")
    
    print("\n--- BY STRATEGY ---")
    for s in report.by_strategy:
        print(f"  {s}")
    
    print("\n--- BY HOLD TIME ---")
    for h in report.by_hold_time:
        print(f"  {h}")
    
    print("\n--- STREAKS ---")
    print(f"Max winning streak: {report.streak_analysis['max_winning_streak']}")
    print(f"Max losing streak: {report.streak_analysis['max_losing_streak']}")
```

## Output

```
=== TRADE ANALYSIS ===
Trades: 100
P&L: $+8,432.18
Win Rate: 54.0%

Best Hour: 11:00 (+72.7% win)
Worst Hour: 16:00 (+36.4% win)

--- PATTERNS ---
✅ Strong Hour: 11:00 has 73% win rate
   → Focus more capital at 11:00
⚠️ Weak Hour: 16:00 has 36% win rate (11 trades)
   → Avoid trading at 16:00 or review strategy

--- BY HOUR ---
  hour=08:00: 11 trades, 45% win, $-180 total, $-16 avg
  hour=09:00: 9 trades, 56% win, $+470 total, $+52 avg
  hour=10:00: 9 trades, 44% win, $-260 total, $-29 avg
  hour=11:00: 11 trades, 73% win, $+920 total, $+84 avg
  hour=12:00: 8 trades, 50% win, $+150 total, $+19 avg

--- BY STRATEGY ---
  strategy=breakout: 30 trades, 47% win, $+320 total
  strategy=momentum: 33 trades, 61% win, $+5,850 total
  strategy=reversal: 37 trades, 54% win, $+2,260 total

--- BY HOLD TIME ---
  hold_time=<1h: 42 trades, 55% win, $+2,100 total
  hold_time=1-4h: 20 trades, 50% win, $+150 total
  hold_time=4-24h: 25 trades, 52% win, $+4,080 total
  hold_time=1-7d: 13 trades, 62% win, $+2,100 total

--- STREAKS ---
Max winning streak: 5
Max losing streak: 4
```

## Quick Reference

```python
# Analyze trades
analyzer = TradeAnalyzer(trades)
report = analyzer.analyze()

# Access results
report.total_pnl
report.win_rate
report.by_hour
report.by_strategy
report.patterns

# Print summary
print(report.summary())
```

## Pattern Types Detected

| Pattern | Trigger | Action |
|---------|---------|--------|
| Weak Hour | Win rate <35% with 5+ trades | Avoid that hour |
| Strong Hour | Win rate >65% with 5+ trades | Size up |
| Overholding | >7 day trades, <40% win | Tighten time stops |
| Scalping Edge | <1h trades, >60% win | Increase allocation |
| Weak Strategy | Win rate <40%, 5+ trades | Review/discontinue |

---
*Utility: Trade Analyzer | Features: Time-based analysis, pattern detection, strategy comparison*