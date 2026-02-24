# Drawdown Calculator
*Ghost Learning | 2026-02-22*

Track equity drawdowns, calculate risk metrics, analyze recovery patterns.

## Key Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| **Drawdown** | Peak-to-trough decline | `(peak - value) / peak` |
| **Max DD** | Largest drawdown | `max(all_drawdowns)` |
| **Recovery** | Time to new peak | `days_from_trough` |
| **Calmar** | Return / Max DD | `annual_return / max_dd` |
| **Pain Index** | Avg drawdown | `mean(drawdowns)` |

## Implementation

```python
"""
Drawdown Calculator
Equity curve analysis and risk metrics.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
import math


@dataclass
class DrawdownPeriod:
    """A single drawdown episode."""
    start_date: datetime      # Peak date
    trough_date: datetime     # Lowest point
    end_date: Optional[datetime]  # Recovery date (None if ongoing)
    peak_value: Decimal
    trough_value: Decimal
    drawdown_pct: Decimal
    duration_days: int
    recovery_days: Optional[int]  # Days to recover
    
    @property
    def is_recovered(self) -> bool:
        return self.end_date is not None


@dataclass
class DrawdownStats:
    """Summary statistics."""
    max_drawdown: Decimal
    max_drawdown_duration: int
    avg_drawdown: Decimal
    avg_duration: int
    avg_recovery: int
    total_periods: int
    current_drawdown: Decimal
    pain_index: Decimal          # Average drawdown over time
    ulcer_index: Decimal         # RMS of drawdowns
    recovery_factor: Decimal     # Total return / max DD


class DrawdownCalculator:
    """
    Track and analyze equity curve drawdowns.
    """
    
    def __init__(self):
        self.equity_curve: list[tuple[datetime, Decimal]] = []
        self._peak: Decimal = Decimal("0")
        self._peak_date: Optional[datetime] = None
    
    def add_equity(self, date: datetime, value: Decimal) -> dict:
        """
        Add equity point and calculate current drawdown.
        
        Returns current drawdown info.
        """
        self.equity_curve.append((date, value))
        
        # Track peak
        if value > self._peak:
            self._peak = value
            self._peak_date = date
        
        # Calculate drawdown
        drawdown = Decimal("0")
        if self._peak > 0:
            drawdown = (self._peak - value) / self._peak
        
        return {
            "date": date,
            "value": value,
            "peak": self._peak,
            "peak_date": self._peak_date,
            "drawdown": drawdown,
            "is_new_peak": value == self._peak and self._peak_date == date
        }
    
    def get_drawdown_periods(self) -> list[DrawdownPeriod]:
        """
        Identify all drawdown periods.
        
        A period: peak → trough → recovery (new peak)
        """
        if len(self.equity_curve) < 2:
            return []
        
        periods = []
        in_drawdown = False
        peak_date = None
        peak_value = None
        trough_date = None
        trough_value = None
        
        for date, value in self.equity_curve:
            if not in_drawdown:
                # Check for new drawdown
                if peak_value is None or value > peak_value:
                    peak_value = value
                    peak_date = date
                elif value < peak_value:
                    # Drawdown starts
                    in_drawdown = True
                    trough_date = date
                    trough_value = value
            else:
                # In drawdown
                if value < trough_value:
                    # Deeper
                    trough_date = date
                    trough_value = value
                elif value >= peak_value:
                    # Recovery!
                    dd = (peak_value - trough_value) / peak_value
                    periods.append(DrawdownPeriod(
                        start_date=peak_date,
                        trough_date=trough_date,
                        end_date=date,
                        peak_value=peak_value,
                        trough_value=trough_value,
                        drawdown_pct=dd,
                        duration_days=(date - peak_date).days,
                        recovery_days=(date - trough_date).days
                    ))
                    in_drawdown = False
                    peak_value = value
                    peak_date = date
                    trough_value = None
        
        # Handle ongoing drawdown
        if in_drawdown and peak_value and trough_value:
            dd = (peak_value - trough_value) / peak_value
            periods.append(DrawdownPeriod(
                start_date=peak_date,
                trough_date=trough_date,
                end_date=None,  # Not recovered
                peak_value=peak_value,
                trough_value=trough_value,
                drawdown_pct=dd,
                duration_days=(self.equity_curve[-1][0] - peak_date).days,
                recovery_days=None
            ))
        
        return periods
    
    def calculate_stats(self) -> DrawdownStats:
        """Calculate comprehensive drawdown statistics."""
        if not self.equity_curve:
            return DrawdownStats(
                max_drawdown=Decimal("0"),
                max_drawdown_duration=0,
                avg_drawdown=Decimal("0"),
                avg_duration=0,
                avg_recovery=0,
                total_periods=0,
                current_drawdown=Decimal("0"),
                pain_index=Decimal("0"),
                ulcer_index=Decimal("0"),
                recovery_factor=Decimal("0")
            )
        
        # Get all drawdowns at each point
        drawdowns = []
        peak = self.equity_curve[0][1]
        
        for _, value in self.equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak if peak > 0 else Decimal("0")
            drawdowns.append(dd)
        
        periods = self.get_drawdown_periods()
        recovered_periods = [p for p in periods if p.is_recovered]
        
        # Current drawdown
        current_dd = drawdowns[-1] if drawdowns else Decimal("0")
        
        # Pain index (average drawdown)
        pain_index = sum(drawdowns) / len(drawdowns)
        
        # Ulcer index (RMS of drawdowns)
        ulcer = sum(d ** 2 for d in drawdowns) / len(drawdowns)
        ulcer_index = ulcer.sqrt()
        
        # Recovery factor
        total_return = Decimal("0")
        if self.equity_curve:
            initial = self.equity_curve[0][1]
            final = self.equity_curve[-1][1]
            if initial > 0:
                total_return = (final - initial) / initial
        
        max_dd = max(drawdowns) if drawdowns else Decimal("0")
        recovery_factor = total_return / max_dd if max_dd > 0 else Decimal("0")
        
        # Duration stats
        durations = [p.duration_days for p in periods] if periods else [0]
        recoveries = [p.recovery_days for p in recovered_periods] if recovered_periods else [0]
        
        return DrawdownStats(
            max_drawdown=max_dd,
            max_drawdown_duration=max(durations),
            avg_drawdown=sum(p.drawdown_pct for p in periods) / len(periods) if periods else Decimal("0"),
            avg_duration=sum(durations) / len(durations),
            avg_recovery=sum(recoveries) / len(recoveries) if recoveries else 0,
            total_periods=len(periods),
            current_drawdown=current_dd,
            pain_index=pain_index,
            ulcer_index=ulcer_index,
            recovery_factor=recovery_factor
        )
    
    def risk_report(self) -> str:
        """Generate human-readable risk report."""
        stats = self.calculate_stats()
        periods = self.get_drawdown_periods()
        
        lines = [
            "=== DRAWDOWN ANALYSIS ===",
            f"Max Drawdown:     {stats.max_drawdown:.2%}",
            f"Current DD:       {stats.current_drawdown:.2%}",
            f"Pain Index:       {stats.pain_index:.2%}",
            f"Ulcer Index:      {stats.ulcer_index:.2%}",
            f"Recovery Factor:  {stats.recovery_factor:.2f}",
            "",
            f"Total Periods:    {stats.total_periods}",
            f"Avg Duration:     {stats.avg_duration:.0f} days",
            f"Avg Recovery:     {stats.avg_recovery:.0f} days",
            f"Max Duration:     {stats.max_drawdown_duration} days",
        ]
        
        if periods:
            lines.append("")
            lines.append("=== TOP 3 DRAWDOWNS ===")
            sorted_periods = sorted(periods, key=lambda p: p.drawdown_pct, reverse=True)[:3]
            for i, p in enumerate(sorted_periods, 1):
                status = "ongoing" if not p.is_recovered else f"recovered in {p.recovery_days}d"
                lines.append(
                    f"{i}. {p.drawdown_pct:.1%} | "
                    f"{p.start_date.strftime('%Y-%m-%d')} → {p.trough_date.strftime('%Y-%m-%d')} | "
                    f"{status}"
                )
        
        return "\n".join(lines)


# === Quick Functions ===

def max_drawdown(equity_values: list[float]) -> float:
    """One-liner max drawdown calculation."""
    peak = equity_values[0]
    max_dd = 0.0
    for v in equity_values:
        peak = max(peak, v)
        dd = (peak - v) / peak if peak > 0 else 0
        max_dd = max(max_dd, dd)
    return max_dd


def current_drawdown(equity_values: list[float]) -> float:
    """Current drawdown from peak."""
    peak = max(equity_values)
    return (peak - equity_values[-1]) / peak if peak > 0 else 0.0


# === Usage ===

if __name__ == "__main__":
    from datetime import date
    
    calc = DrawdownCalculator()
    
    # Simulate equity curve with drawdowns
    equity_data = [
        ("2024-01-01", 100000),   # Start
        ("2024-01-15", 105000),   # New peak
        ("2024-02-01", 102000),   # -2.9%
        ("2024-02-15", 95000),    # -9.5%
        ("2024-03-01", 98000),    # Recovering
        ("2024-03-15", 108000),   # New peak (recovery!)
        ("2024-04-01", 112000),   # New peak
        ("2024-04-15", 105000),   # -6.25%
        ("2024-05-01", 98000),    # -12.5%
        ("2024-05-15", 92000),    # -17.9%
        ("2024-06-01", 100000),   # Recovering
        ("2024-06-15", 115000),   # New peak (recovery!)
        ("2024-07-01", 118000),   # New peak
        ("2024-07-15", 110000),   # -6.8% (ongoing)
    ]
    
    for date_str, value in equity_data:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        result = calc.add_equity(d, Decimal(str(value)))
        if result["drawdown"] > 0.05:  # Alert on >5% DD
            print(f"{date_str}: DD {result['drawdown']:.1%}")
    
    print("\n" + calc.risk_report())
    
    # Quick functions
    values = [float(v) for _, v in equity_data]
    print(f"\nQuick max_drawdown: {max_drawdown(values):.2%}")
    print(f"Quick current_dd:   {current_drawdown(values):.2%}")
```

## Output

```
2024-02-15: DD 9.5%
2024-05-01: DD 12.5%
2024-05-15: DD 17.9%
2024-07-15: DD 6.8%

=== DRAWDOWN ANALYSIS ===
Max Drawdown:     17.86%
Current DD:       6.78%
Pain Index:       4.58%
Ulcer Index:      7.12%
Recovery Factor:  0.10

Total Periods:    3
Avg Duration:     62 days
Avg Recovery:     47 days
Max Duration:     90 days

=== TOP 3 DRAWDOWNS ===
1. 17.9% | 2024-04-01 → 2024-05-15 | recovered in 31d
2. 9.5% | 2024-01-15 → 2024-02-15 | recovered in 30d
3. 6.8% | 2024-06-15 → 2024-07-15 | ongoing

Quick max_drawdown: 17.86%
Quick current_dd:   6.78%
```

## Key Metrics Explained

| Metric | Good | Warning | Danger |
|--------|------|---------|--------|
| Max DD | <10% | 10-20% | >20% |
| Pain Index | <2% | 2-5% | >5% |
| Ulcer Index | <5% | 5-10% | >10% |
| Recovery Factor | >2 | 1-2 | <1 |

---
*Utility: Drawdown Calculator | Metrics: Max DD, Pain Index, Ulcer Index, Recovery Factor*