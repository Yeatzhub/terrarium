# Drawdown Analyzer CLI
*Ghost Learning | 2026-02-21*

Analyze equity curves to find max drawdown, underwater periods, and recovery metrics. Essential for backtest validation and live trading performance review.

```python
#!/usr/bin/env python3
"""
Drawdown Analyzer
Analyzes equity curves to calculate drawdowns, underwater periods, and recovery metrics.

Usage:
    python drawdown_analyzer.py equity.csv
    python drawdown_analyzer.py equity.csv --plot-data dd_chart.json
    python drawdown_analyzer.py equity.csv --threshold 0.10 --find-recoveries
"""

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Iterator, NamedTuple, Optional
import json


class DrawdownPoint(NamedTuple):
    """Single point in drawdown series."""
    timestamp: datetime
    equity: Decimal
    peak: Decimal
    drawdown: Decimal           # Absolute $ drawdown
    drawdown_pct: Decimal       # Drawdown as % of peak
    is_underwater: bool         # True if below previous peak


@dataclass
class DrawdownPeriod:
    """A single drawdown period (peak to trough to recovery)."""
    start_time: datetime        # Peak time (start of DD)
    trough_time: datetime       # Lowest point
    end_time: Optional[datetime] # Recovery time (None if not recovered)
    peak_equity: Decimal
    trough_equity: Decimal
    recovery_equity: Optional[Decimal]
    
    @property
    def max_drawdown(self) -> Decimal:
        """Maximum drawdown in dollars."""
        return self.trough_equity - self.peak_equity
    
    @property
    def max_drawdown_pct(self) -> Decimal:
        """Maximum drawdown as percentage."""
        if self.peak_equity == 0:
            return Decimal("0")
        return (self.max_drawdown / self.peak_equity) * 100
    
    @property
    def duration(self) -> timedelta:
        """Total duration from peak to recovery (or now if not recovered)."""
        end = self.end_time or datetime.utcnow()
        return end - self.start_time
    
    @property
    def recovery_duration(self) -> Optional[timedelta]:
        """Time from trough to recovery."""
        if self.end_time and self.end_time > self.trough_time:
            return self.end_time - self.trough_time
        return None
    
    @property
    def is_active(self) -> bool:
        """True if still in drawdown (not recovered)."""
        return self.end_time is None
    
    def to_dict(self) -> dict:
        return {
            "start_time": self.start_time.isoformat(),
            "trough_time": self.trough_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "peak_equity": str(self.peak_equity),
            "trough_equity": str(self.trough_equity),
            "recovery_equity": str(self.recovery_equity) if self.recovery_equity else None,
            "max_drawdown": str(self.max_drawdown),
            "max_drawdown_pct": float(self.max_drawdown_pct),
            "duration_days": self.duration.days,
            "recovery_days": self.recovery_duration.days if self.recovery_duration else None,
            "is_active": self.is_active
        }


@dataclass
class DrawdownSummary:
    """Summary statistics for drawdown analysis."""
    max_drawdown: Decimal
    max_drawdown_pct: Decimal
    max_drawdown_date: datetime
    current_drawdown: Decimal
    current_drawdown_pct: Decimal
    avg_drawdown: Decimal
    avg_drawdown_pct: Decimal
    total_underwater_days: int
    underwater_pct: Decimal       # % of time spent underwater
    num_drawdowns: int
    num_recoveries: int
    num_active: int
    avg_recovery_days: Optional[int]
    longest_drawdown_days: int
    longest_recovery_days: Optional[int]
    calmar_ratio: Decimal          # Annual return / Max DD
    
    def to_dict(self) -> dict:
        return {
            "max_drawdown": str(self.max_drawdown),
            "max_drawdown_pct": float(self.max_drawdown_pct),
            "max_drawdown_date": self.max_drawdown_date.isoformat(),
            "current_drawdown": str(self.current_drawdown),
            "current_drawdown_pct": float(self.current_drawdown_pct),
            "avg_drawdown": str(self.avg_drawdown),
            "avg_drawdown_pct": float(self.avg_drawdown_pct),
            "total_underwater_days": self.total_underwater_days,
            "underwater_pct": float(self.underwater_pct),
            "num_drawdowns": self.num_drawdowns,
            "num_recoveries": self.num_recoveries,
            "num_active": self.num_active,
            "avg_recovery_days": self.avg_recovery_days,
            "longest_drawdown_days": self.longest_drawdown_days,
            "longest_recovery_days": self.longest_recovery_days,
            "calmar_ratio": float(self.calmar_ratio) if self.calmar_ratio else None
        }


class DrawdownAnalyzer:
    """Analyze equity curves for drawdown statistics."""
    
    def __init__(self):
        self.points: list[DrawdownPoint] = []
        self.periods: list[DrawdownPeriod] = []
    
    def load_csv(self, path: Path, timestamp_col: str = "timestamp", 
                 equity_col: str = "equity") -> None:
        """Load equity curve from CSV."""
        points = []
        
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ts = datetime.fromisoformat(row[timestamp_col])
                    equity = Decimal(str(row[equity_col]))
                    points.append((ts, equity))
                except (KeyError, ValueError) as e:
                    print(f"Skipping invalid row: {e}")
        
        self._process_points(points)
    
    def load_data(self, data: list[tuple[datetime, Decimal]]) -> None:
        """Load equity curve from list of (timestamp, equity) tuples."""
        self._process_points(data)
    
    def _process_points(self, points: list[tuple[datetime, Decimal]]) -> None:
        """Calculate drawdown series from equity points."""
        points = sorted(points, key=lambda x: x[0])
        
        peak = Decimal("0")
        peak_time = None
        current_period: Optional[DrawdownPeriod] = None
        self.points = []
        self.periods = []
        
        for ts, equity in points:
            # Update peak
            if equity > peak:
                peak = equity
                peak_time = ts
                
                # End current drawdown period if exists
                if current_period:
                    current_period.end_time = ts
                    current_period.recovery_equity = equity
                    current_period = None
            
            # Calculate drawdown
            dd = equity - peak
            dd_pct = (dd / peak * 100) if peak > 0 else Decimal("0")
            is_underwater = equity < peak
            
            self.points.append(DrawdownPoint(
                timestamp=ts,
                equity=equity,
                peak=peak,
                drawdown=dd,
                drawdown_pct=dd_pct,
                is_underwater=is_underwater
            ))
            
            # Track drawdown period
            if is_underwater and current_period is None:
                # New drawdown starts
                current_period = DrawdownPeriod(
                    start_time=peak_time,
                    trough_time=ts,
                    end_time=None,
                    peak_equity=peak,
                    trough_equity=equity,
                    recovery_equity=None
                )
                self.periods.append(current_period)
            elif is_underwater and current_period:
                # Update trough if lower
                if equity < current_period.trough_equity:
                    current_period.trough_time = ts
                    current_period.trough_equity = equity
        
        # Close any open period
        if current_period:
            current_period.end_time = None
    
    def summarize(self) -> DrawdownSummary:
        """Calculate summary statistics."""
        if not self.points:
            return DrawdownSummary(
                max_drawdown=Decimal("0"), max_drawdown_pct=Decimal("0"),
                max_drawdown_date=datetime.utcnow(),
                current_drawdown=Decimal("0"), current_drawdown_pct=Decimal("0"),
                avg_drawdown=Decimal("0"), avg_drawdown_pct=Decimal("0"),
                total_underwater_days=0, underwater_pct=Decimal("0"),
                num_drawdowns=0, num_recoveries=0, num_active=0,
                avg_recovery_days=None, longest_drawdown_days=0,
                longest_recovery_days=None, calmar_ratio=Decimal("0")
            )
        
        underwater_points = [p for p in self.points if p.is_underwater]
        total_days = len(self.points) if len(self.points) > 0 else 1
        
        # Find max drawdown
        max_dd_point = min(self.points, key=lambda p: p.drawdown)
        current_dd = self.points[-1].drawdown if self.points else Decimal("0")
        current_dd_pct = self.points[-1].drawdown_pct if self.points else Decimal("0")
        
        # Calculate averages
        if underwater_points:
            avg_dd = sum(p.drawdown for p in underwater_points) / len(underwater_points)
            avg_dd_pct = sum(p.drawdown_pct for p in underwater_points) / len(underwater_points)
        else:
            avg_dd = Decimal("0")
            avg_dd_pct = Decimal("0")
        
        # Recovery stats
        completed_periods = [p for p in self.periods if p.end_time]
        active_periods = [p for p in self.periods if p.is_active]
        
        recovery_days = [p.duration.days for p in completed_periods]
        recovery_duration_days = [p.recovery_duration.days for p in completed_periods 
                                   if p.recovery_duration]
        
        avg_recovery = int(sum(recovery_days) / len(recovery_days)) if recovery_days else None
        
        # Calmar ratio (annual return / max drawdown)
        if self.points and len(self.points) > 1 and max_dd_point.drawdown_pct != 0:
            total_return = ((self.points[-1].equity - self.points[0].equity) / 
                          self.points[0].equity * 100)
            days_span = (self.points[-1].timestamp - self.points[0].timestamp).days
            years = days_span / 365 if days_span > 0 else 1
            annual_return = total_return / Decimal(str(years)) if years > 0 else Decimal("0")
            calmar = abs(annual_return / max_dd_point.drawdown_pct)
        else:
            calmar = Decimal("0")
        
        return DrawdownSummary(
            max_drawdown=max_dd_point.drawdown,
            max_drawdown_pct=max_dd_point.drawdown_pct,
            max_drawdown_date=max_dd_point.timestamp,
            current_drawdown=current_dd,
            current_drawdown_pct=current_dd_pct,
            avg_drawdown=avg_dd,
            avg_drawdown_pct=avg_dd_pct,
            total_underwater_days=len(underwater_points) if underwater_points else 0,
            underwater_pct=(Decimal(len(underwater_points)) / Decimal(total_days)) * 100,
            num_drawdowns=len(self.periods),
            num_recoveries=len(completed_periods),
            num_active=len(active_periods),
            avg_recovery_days=avg_recovery,
            longest_drawdown_days=max(recovery_days) if recovery_days else 0,
            longest_recovery_days=max(recovery_duration_days) if recovery_duration_days else None,
            calmar_ratio=calmar
        )
    
    def find_drawdowns_above(self, threshold_pct: Decimal) -> list[DrawdownPeriod]:
        """Find all drawdowns exceeding threshold."""
        return [p for p in self.periods if abs(p.max_drawdown_pct) >= threshold_pct * 100]
    
    def export_chart_data(self, path: Path) -> None:
        """Export drawdown series for charting."""
        data = {
            "series": [
                {
                    "timestamp": p.timestamp.isoformat(),
                    "equity": str(p.equity),
                    "peak": str(p.peak),
                    "drawdown_pct": float(p.drawdown_pct)
                }
                for p in self.points
            ],
            "periods": [p.to_dict() for p in self.periods]
        }
        path.write_text(json.dumps(data, indent=2))


def fmt_currency(d: Decimal) -> str:
    return f"${d:,.2f}"


def fmt_pct(d: Decimal) -> str:
    return f"{d:.2f}%"


def print_summary(summary: DrawdownSummary):
    """Print formatted summary."""
    print(f"\n{'═'*60}")
    print(f"  DRAWDOWN ANALYSIS SUMMARY")
    print(f"{'═'*60}")
    print(f"  {'Total Drawdowns:':<25} {summary.num_drawdowns}")
    print(f"  {'Full Recoveries:':<25} {summary.num_recoveries}")
    print(f"  {'Active Drawdowns:':<25} {summary.num_active}")
    print(f"{'─'*60}")
    print(f"  {'Max Drawdown:':<25} {fmt_currency(summary.max_drawdown)} ({fmt_pct(summary.max_drawdown_pct)})")
    print(f"  {'Max Drawdown Date:':<25} {summary.max_drawdown_date.date()}")
    print(f"  {'Current Drawdown:':<25} {fmt_currency(summary.current_drawdown)} ({fmt_pct(summary.current_drawdown_pct)})")
    print(f"{'─'*60}")
    print(f"  {'Avg Drawdown:':<25} {fmt_currency(summary.avg_drawdown)} ({fmt_pct(summary.avg_drawdown_pct)})")
    print(f"  {'Avg Recovery (days):':<25} {summary.avg_recovery_days or 'N/A'}")
    print(f"  {'Longest DD (days):':<25} {summary.longest_drawdown_days}")
    print(f"  {'Longest Recovery (days):':<25} {summary.longest_recovery_days or 'N/A'}")
    print(f"{'─'*60}")
    print(f"  {'Underwater Time:':<25} {summary.total_underwater_days} days ({fmt_pct(summary.underwater_pct)})")
    print(f"  {'Calmar Ratio:':<25} {float(summary.calmar_ratio):.2f}")
    print(f"{'═'*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Drawdown Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CSV Format:
    timestamp,equity
    2026-01-01T00:00:00,10000
    2026-01-02T00:00:00,10200

Examples:
    python drawdown_analyzer.py equity.csv
    python drawdown_analyzer.py equity.csv --plot-data chart.json
    python drawdown_analyzer.py equity.csv --threshold 0.10 --find-recoveries
""")
    parser.add_argument("csv", type=Path, help="Equity curve CSV file")
    parser.add_argument("--timestamp-col", default="timestamp", help="Timestamp column name")
    parser.add_argument("--equity-col", default="equity", help="Equity column name")
    parser.add_argument("--plot-data", type=Path, help="Export drawdown series to JSON")
    parser.add_argument("--threshold", type=Decimal, default=Decimal("0.05"),
                       help="Threshold for significant drawdowns (default 5%%)")
    parser.add_argument("--find-recoveries", action="store_true",
                       help="Show recovery patterns for significant drawdowns")
    parser.add_argument("--output", "-o", type=Path, help="Save summary to JSON")
    
    args = parser.parse_args()
    
    # Analyze
    analyzer = DrawdownAnalyzer()
    analyzer.load_csv(args.csv, args.timestamp_col, args.equity_col)
    summary = analyzer.summarize()
    
    # Print summary
    print_summary(summary)
    
    # Significant drawdowns
    significant = analyzer.find_drawdowns_above(args.threshold)
    if significant:
        print(f"📉 DRAWNDOWNS > {args.threshold*100}%:")
        print(f"{'Start Date':<12} {'Trough':<12} {'Max DD':<15} {'Duration':<12} {'Recovered?'}")
        print("-" * 70)
        for dd in significant:
            recovered = "✓" if dd.end_time else "✗ ACTIVE"
            duration = f"{dd.duration.days}d"
            print(f"{str(dd.start_time.date()):<12} {str(dd.trough_time.date()):<12} "
                  f"{fmt_pct(dd.max_drawdown_pct):<15} {duration:<12} {recovered}")
        print()
    
    # Recovery analysis
    if args.find_recoveries and significant:
        completed = [dd for dd in significant if dd.recovery_duration]
        if completed:
            avg_recovery = sum(dd.recovery_duration.days for dd in completed) / len(completed)
            print(f"📈 RECOVERY ANALYSIS:")
            print(f"  Average recovery time: {avg_recovery:.0f} days")
            print(f"  Fastest recovery: {min(dd.recovery_duration.days for dd in completed)} days")
            print(f"  Slowest recovery: {max(dd.recovery_duration.days for dd in completed)} days")
            print()
    
    # Export chart data
    if args.plot_data:
        analyzer.export_chart_data(args.plot_data)
        print(f"💾 Chart data saved to {args.plot_data}")
    
    # JSON output
    if args.output:
        args.output.write_text(json.dumps(summary.to_dict(), indent=2))
        print(f"💾 Summary saved to {args.output}")


# === Quick Examples ===

# 1. Basic analysis
# python drawdown_analyzer.py backtest_equity.csv

# 2. Find all drawdowns > 10%
# python drawdown_analyzer.py equity.csv --threshold 0.10 --find-recoveries

# 3. Export for charting
# python drawdown_analyzer.py equity.csv --plot-data dd_data.json

# 4. Sample CSV:
# echo "timestamp,equity
# 2026-01-01,10000
# 2026-01-02,10500
# 2026-01-03,9800
# 2026-01-04,9600
# 2026-01-05,10200
# 2026-01-06,11000" > equity.csv


if __name__ == "__main__":
    main()
```

## Quick Start

```bash
# Basic analysis
python drawdown_analyzer.py backtest_equity.csv

# Find major drawdowns (>10%) with recovery analysis
python drawdown_analyzer.py equity.csv --threshold 0.10 --find-recoveries

# Export for charting (drawdown curve)
python drawdown_analyzer.py equity.csv --plot-data dd_chart.json

# Custom column names
python drawdown_analyzer.py trades.csv --timestamp-col date --equity-col account_value
```

## Sample Output

```
════════════════════════════════════════════════════════════
  DRAWDOWN ANALYSIS SUMMARY
════════════════════════════════════════════════════════════
  Total Drawdowns:           23
  Full Recoveries:           21
  Active Drawdowns:          2
──────────────────────────────────────────────────────────
  Max Drawdown:              -$3,450.00 (-15.20%)
  Max Drawdown Date:         2026-02-14
  Current Drawdown:          -$850.00 (-3.40%)
──────────────────────────────────────────────────────────
  Avg Drawdown:              -$650.00 (-2.80%)
  Avg Recovery (days):       5
  Longest DD (days):         18
  Longest Recovery (days):   12
──────────────────────────────────────────────────────────
  Underwater Time:           67 days (18.3%)
  Calmar Ratio:              1.45
════════════════════════════════════════════════════════════

📉 DRAWNDOWNS > 10.0%:
Start Date   Trough       Max DD          Duration     Recovered?
----------------------------------------------------------------------
2026-01-15   2026-02-14   -15.20%         30d          ✓
2026-01-03   2026-01-06   -12.50%         7d           ✗ ACTIVE
```

## Metrics Explained

| Metric | Meaning | Good Value |
|--------|---------|------------|
| Max Drawdown | Largest peak-to-trough decline | < 20% |
| Calmar Ratio | Annual return / Max DD | > 1.0 |
| Underwater % | Time spent below peaks | < 30% |
| Avg Recovery | Days to recover from drawdowns | Shorter = better |
| Longest DD | Worst drawdown duration | < 3 months |

## Calmar Ratio

Calmar Ratio = (Annual Return %) / (Max Drawdown %)

- > 3.0: Excellent
- 1.0-3.0: Good
- 0.5-1.0: Acceptable
- < 0.5: Poor risk-adjusted returns

## JSON Output Format

```json
{
  "max_drawdown": "-3450.00",
  "max_drawdown_pct": -15.2,
  "current_drawdown_pct": -3.4,
  "avg_recovery_days": 5,
  "calmar_ratio": 1.45,
  "underwater_pct": 18.3
}
```

## Chart Data Format

```json
{
  "series": [
    {"timestamp": "2026-01-01T00:00:00", "equity": "10000", "drawdown_pct": 0.0},
    {"timestamp": "2026-01-02T00:00:00", "equity": "9800", "drawdown_pct": -2.0}
  ],
  "periods": [{"start_time": "...", "trough_time": "...", "max_drawdown_pct": -15.2}]
}
```

## Why This Matters

Two strategies with same returns:
- Strategy A: 50% return, 50% max DD → Calmar = 1.0
- Strategy B: 30% return, 10% max DD → Calmar = 3.0

**Strategy B is superior** — achieves similar risk-adjusted returns with less pain.

---
*Utility: Drawdown Analyzer | Essential for backtest validation*
