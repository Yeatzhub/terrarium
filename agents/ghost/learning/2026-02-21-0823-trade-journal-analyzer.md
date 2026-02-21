# Trade Journal P&L Analyzer CLI
*Ghost Learning | 2026-02-21*

Analyze trade history CSVs to calculate P&L, win rates, drawdowns, and performance metrics. Lightning-fast terminal utility.

```python
#!/usr/bin/env python3
"""
Trade Journal P&L Analyzer
Usage: python trade_analyzer.py trades.csv
       python trade_analyzer.py trades.csv --symbol BTCUSD
       python trade_analyzer.py trades.csv --by-month --output report.json

Expected CSV format:
  symbol,entry_price,exit_price,size,side,entry_time,exit_time
  BTCUSD,50000,51000,0.5,long,2026-01-15T10:00:00,2026-01-15T14:00:00
"""

import sys
import argparse
import csv
import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Iterator
from collections import defaultdict


@dataclass(frozen=True, slots=True)
class Trade:
    """Parsed trade record."""
    symbol: str
    entry_price: Decimal
    exit_price: Decimal
    size: Decimal
    side: str  # 'long' or 'short'
    entry_time: datetime
    exit_time: datetime
    fees: Decimal = Decimal("0")
    
    @property
    def pnl(self) -> Decimal:
        """Gross profit/loss before fees."""
        if self.side == "long":
            return (self.exit_price - self.entry_price) * self.size
        else:
            return (self.entry_price - self.exit_price) * self.size
    
    @property
    def net_pnl(self) -> Decimal:
        """Net P&L after fees (fees subtracted from profit, added to loss)."""
        return self.pnl - self.fees
    
    @property
    def pnl_pct(self) -> Decimal:
        """Return as percentage of position value."""
        position_value = self.entry_price * self.size
        if position_value == 0:
            return Decimal("0")
        return (self.pnl / position_value) * 100
    
    @property
    def duration_minutes(self) -> int:
        """Trade duration in minutes."""
        return int((self.exit_time - self.entry_time).total_seconds() / 60)
    
    @property
    def is_winner(self) -> bool:
        return self.net_pnl > 0


@dataclass
class PerformanceSummary:
    """Aggregated performance metrics."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    gross_pnl: Decimal = Decimal("0")
    net_pnl: Decimal = Decimal("0")
    total_fees: Decimal = Decimal("0")
    total_return_pct: Decimal = Decimal("0")
    
    # Calculated fields
    win_rate: Decimal = field(init=False)
    loss_rate: Decimal = field(init=False)
    avg_winner: Decimal = field(init=False)
    avg_loser: Decimal = field(init=False)
    profit_factor: Decimal = field(init=False)
    expectancy: Decimal = field(init=False)
    max_drawdown: Decimal = Decimal("0")
    max_drawdown_pct: Decimal = Decimal("0")
    avg_trade_duration: int = 0
    
    def __post_init__(self):
        self.win_rate = (Decimal(self.winning_trades) / self.total_trades * 100) if self.total_trades else Decimal("0")
        self.loss_rate = (Decimal(self.losing_trades) / self.total_trades * 100) if self.total_trades else Decimal("0")
        self.avg_winner = (self.gross_pnl / self.winning_trades) if self.winning_trades else Decimal("0")
        self.avg_loser = (self.total_loss / self.losing_trades) if self.losing_trades else Decimal("0")
        gross_loss = abs(self.total_loss)
        self.profit_factor = (self.total_wins / gross_loss) if gross_loss else Decimal("0")
        self.expectancy = self.net_pnl / self.total_trades if self.total_trades else Decimal("0")
    
    @property
    def total_wins(self) -> Decimal:
        return sum([t.net_pnl for t in self._trades if t.is_winner]) if hasattr(self, '_trades') else Decimal("0")
    
    @property
    def total_loss(self) -> Decimal:
        return sum([t.net_pnl for t in self._trades if not t.is_winner]) if hasattr(self, '_trades') else Decimal("0")


class TradeAnalyzer:
    """Analyze trade history and compute metrics."""
    
    def __init__(self):
        self.trades: list[Trade] = []
    
    def load_csv(self, path: Path) -> None:
        """Load trades from CSV file."""
        if not path.exists():
            raise FileNotFoundError(f"CSV not found: {path}")
        
        with open(path, "r", newline="") as f:
            reader = csv.DictReader(f)
            self.trades = []
            for i, row in enumerate(reader, 1):
                try:
                    self.trades.append(self._parse_trade(row))
                except Exception as e:
                    print(f"Row {i}: Error parsing - {e}", file=sys.stderr)
        
        # Sort by exit time for drawdown calculation
        self.trades.sort(key=lambda t: t.exit_time)
    
    def _parse_trade(self, row: dict) -> Trade:
        """Parse CSV row into Trade object."""
        return Trade(
            symbol=row.get("symbol", "").upper().strip(),
            entry_price=Decimal(row["entry_price"]),
            exit_price=Decimal(row["exit_price"]),
            size=Decimal(row["size"]),
            side=row["side"].lower().strip(),
            entry_time=datetime.fromisoformat(row["entry_time"]),
            exit_time=datetime.fromisoformat(row["exit_time"]),
            fees=Decimal(row.get("fees", "0"))
        )
    
    def filter_by_symbol(self, symbol: str) -> "TradeAnalyzer":
        """Return new analyzer with filtered trades."""
        new = TradeAnalyzer()
        new.trades = [t for t in self.trades if t.symbol == symbol.upper()]
        return new
    
    def filter_by_month(self, year: int, month: int) -> "TradeAnalyzer":
        """Return new analyzer with trades for specific month."""
        new = TradeAnalyzer()
        new.trades = [t for t in self.trades if t.exit_time.year == year and t.exit_time.month == month]
        return new
    
    def summarize(self) -> PerformanceSummary:
        """Compute performance summary."""
        if not self.trades:
            return PerformanceSummary()
        
        summary = PerformanceSummary()
        summary.total_trades = len(self.trades)
        summary.winning_trades = sum(1 for t in self.trades if t.is_winner)
        summary.losing_trades = summary.total_trades - summary.winning_trades
        summary.gross_pnl = sum(t.pnl for t in self.trades)
        summary.total_fees = sum(t.fees for t in self.trades)
        summary.net_pnl = sum(t.net_pnl for t in self.trades)
        summary.total_return_pct = sum(t.pnl_pct for t in self.trades)
        summary.avg_trade_duration = int(sum(t.duration_minutes for t in self.trades) / len(self.trades))
        
        # Store trades for calculated properties
        summary._trades = self.trades
        
        # Calculate drawdown
        max_drawdown = Decimal("0")
        max_drawdown_pct = Decimal("0")
        peak = Decimal("0")
        running_pnl = Decimal("0")
        
        for trade in self.trades:
            running_pnl += trade.net_pnl
            if running_pnl > peak:
                peak = running_pnl
            drawdown = peak - running_pnl
            drawdown_pct = (drawdown / peak * 100) if peak else Decimal("0")
            if drawdown > max_drawdown:
                max_drawdown = drawdown
                max_drawdown_pct = drawdown_pct
        
        summary.max_drawdown = max_drawdown
        summary.max_drawdown_pct = max_drawdown_pct
        
        # Re-init to recalculate derived fields with _trades set
        summary.__post_init__()
        
        return summary
    
    def by_symbol(self) -> dict[str, "TradeAnalyzer"]:
        """Split analyzer by symbol."""
        symbols = set(t.symbol for t in self.trades)
        return {sym: self.filter_by_symbol(sym) for sym in symbols}
    
    def by_month(self) -> dict[tuple[int, int], "TradeAnalyzer"]:
        """Split analyzer by month."""
        months = set((t.exit_time.year, t.exit_time.month) for t in self.trades)
        result = {}
        for yr, mo in months:
            result[(yr, mo)] = self.filter_by_month(yr, mo)
        return result


def print_summary(summary: PerformanceSummary, title: str = "Performance Summary"):
    """Print formatted summary table."""
    print(f"\n{'═'*60}")
    print(f"  {title}")
    print(f"{'═'*60}")
    print(f"  {'Total Trades:':<25} {summary.total_trades}")
    print(f"  {'Winning Trades:':<25} {summary.winning_trades} ({summary.win_rate:.1f}%)")
    print(f"  {'Losing Trades:':<25} {summary.losing_trades} ({summary.loss_rate:.1f}%)")
    print(f"{'─'*60}")
    print(f"  {'Gross P&L:':<25} ${summary.gross_pnl:+,.2f}")
    print(f"  {'Fees:':<25} ${summary.total_fees:,.2f}")
    print(f"  {'Net P&L:':<25} ${summary.net_pnl:+,.2f}")
    print(f"{'─'*60}")
    print(f"  {'Avg Winner:':<25} ${summary.avg_winner:,.2f}")
    print(f"  {'Avg Loser:':<25} ${summary.avg_loser:,.2f}")
    print(f"  {'Profit Factor:':<25} {summary.profit_factor:.2f}")
    print(f"  {'Expectancy:':<25} ${summary.expectancy:+,.2f} per trade")
    print(f"{'─'*60}")
    print(f"  {'Max Drawdown:':<25} ${summary.max_drawdown:,.2f} ({summary.max_drawdown_pct:.1f}%)")
    print(f"  {'Avg Trade Duration:':<25} {summary.avg_trade_duration} min")
    print(f"{'═'*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Trade Journal P&L Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
CSV Format:
  symbol,entry_price,exit_price,size,side,entry_time,exit_time[,fees]

Example:
  BTCUSD,50000,51000,0.5,long,2026-01-15T10:00:00,2026-01-15T14:00:00,5.00
  BTCUSD,51000,50000,0.3,short,2026-01-16T09:00:00,2026-01-16T12:00:00,3.00
  ETHUSD,3000,3200,5.0,long,2026-01-15T11:00:00,2026-01-15T15:00:00,10.00
""")
    parser.add_argument("csv", type=Path, help="Path to trade history CSV")
    parser.add_argument("--symbol", "-s", help="Filter by symbol (e.g., BTCUSD)")
    parser.add_argument("--by-symbol", action="store_true", help="Group results by symbol")
    parser.add_argument("--by-month", action="store_true", help="Group results by month")
    parser.add_argument("--output", "-o", type=Path, help="Output results to JSON file")
    parser.add_argument("--top", type=int, default=10, help="Show top N trades")
    
    args = parser.parse_args()
    
    # Load and analyze
    analyzer = TradeAnalyzer()
    analyzer.load_csv(args.csv)
    
    if args.symbol:
        analyzer = analyzer.filter_by_symbol(args.symbol)
    
    if args.by_symbol:
        print(f"\n📊 Analysis by Symbol ({len(analyzer.trades)} total trades)")
        for symbol, sub_analyzer in sorted(analyzer.by_symbol().items()):
            summary = sub_analyzer.summarize()
            print_summary(summary, f"{symbol} ({summary.total_trades} trades)")
    
    elif args.by_month:
        print(f"\n📅 Analysis by Month ({len(analyzer.trades)} total trades)")
        for (yr, mo), sub_analyzer in sorted(analyzer.by_month().items()):
            summary = sub_analyzer.summarize()
            print_summary(summary, f"{yr}-{mo:02d} ({summary.total_trades} trades)")
    
    else:
        # Default: overall summary
        summary = analyzer.summarize()
        print(f"\n📈 Overall Analysis ({len(analyzer.trades)} trades)")
        print_summary(summary)
        
        # Top trades
        if analyzer.trades:
            print("🏆 Top Trades by P&L:")
            top_trades = sorted(analyzer.trades, key=lambda t: t.net_pnl, reverse=True)[:args.top]
            for i, t in enumerate(top_trades, 1):
                print(f"  {i}. {t.symbol} ${t.net_pnl:+,.2f} ({t.pnl_pct:+.2f}%) {t.exit_time.date()}")
            print()
    
    # JSON output
    if args.output:
        data = {
            "total_trades": len(analyzer.trades),
            "summary": {
                "total_trades": summary.total_trades,
                "winning_trades": summary.winning_trades,
                "losing_trades": summary.losing_trades,
                "win_rate": float(summary.win_rate),
                "net_pnl": str(summary.net_pnl),
                "gross_pnl": str(summary.gross_pnl),
                "total_fees": str(summary.total_fees),
                "profit_factor": float(summary.profit_factor),
                "expectancy": str(summary.expectancy),
                "max_drawdown": str(summary.max_drawdown),
                "max_drawdown_pct": float(summary.max_drawdown_pct),
                "avg_trade_duration_minutes": summary.avg_trade_duration
            },
            "trades": [
                {
                    "symbol": t.symbol,
                    "side": t.side,
                    "entry_price": str(t.entry_price),
                    "exit_price": str(t.exit_price),
                    "size": str(t.size),
                    "pnl": str(t.net_pnl),
                    "pnl_pct": float(t.pnl_pct),
                    "duration_minutes": t.duration_minutes,
                    "entry_time": t.entry_time.isoformat(),
                    "exit_time": t.exit_time.isoformat()
                }
                for t in analyzer.trades
            ]
        }
        args.output.write_text(json.dumps(data, indent=2))
        print(f"💾 Results saved to {args.output}")


# === Quick Examples ===

# 1. Overall summary
# python trade_analyzer.py trades.csv

# 2. Filter to one symbol
# python trade_analyzer.py trades.csv --symbol BTCUSD

# 3. Group by symbol
# python trade_analyzer.py trades.csv --by-symbol

# 4. Monthly breakdown
# python trade_analyzer.py trades.csv --by-month

# 5. Export to JSON
# python trade_analyzer.py trades.csv --output report.json

# 6. Sample CSV:
# echo "symbol,entry_price,exit_price,size,side,entry_time,exit_time,fees
# BTCUSD,50000,51000,0.5,long,2026-01-15T10:00:00,2026-01-15T14:00:00,5.00
# BTCUSD,51000,50500,0.5,short,2026-01-16T09:00:00,2026-01-16T12:00:00,3.00" > trades.csv


if __name__ == "__main__":
    main()
```

## Quick Start

```bash
# Make executable and run
chmod +x trade_analyzer.py

# Basic summary
python trade_analyzer.py trades.csv

# Filter by symbol
python trade_analyzer.py trades.csv --symbol BTCUSD

# Group breakdowns
python trade_analyzer.py trades.csv --by-symbol
python trade_analyzer.py trades.csv --by-month

# Export JSON
python trade_analyzer.py trades.csv --output report.json
```

## CSV Format

```csv
symbol,entry_price,exit_price,size,side,entry_time,exit_time,fees
BTCUSD,50000,51000,0.5,long,2026-01-15T10:00:00,2026-01-15T14:00:00,5.00
BTCUSD,51000,50000,0.3,short,2026-01-16T09:00:00,2026-01-16T12:00:00,3.00
ETHUSD,3000,3200,5.0,long,2026-01-15T11:00:00,2026-01-15T15:00:00,10.00
```

## Metrics Explained

| Metric | Meaning |
|--------|---------|
| Win Rate | % of profitable trades |
| Net P&L | Total profit minus fees |
| Profit Factor | Gross profit / Gross loss (>1.0 = profitable) |
| Expectancy | Average $ per trade (includes losses) |
| Max Drawdown | Largest peak-to-trough decline |
| Avg Trade Duration | How long positions are held |

## Sample Output

```
════════════════════════════════════════════════════════════
  Performance Summary
════════════════════════════════════════════════════════════
  Total Trades:              47
  Winning Trades:            28 (59.6%)
  Losing Trades:             19 (40.4%)
──────────────────────────────────────────────────────────
  Gross P&L:                 $+12,456.78
  Fees:                      $235.50
  Net P&L:                   $+12,221.28
──────────────────────────────────────────────────────────
  Avg Winner:                $523.45
  Avg Loser:                 -$178.23
  Profit Factor:             2.35
  Expectancy:                $+259.92 per trade
──────────────────────────────────────────────────────────
  Max Drawdown:              $2,150.00 (14.7%)
  Avg Trade Duration:        127 min
════════════════════════════════════════════════════════════
```

## Key Features

- ✅ **Decimal arithmetic** — no float precision errors
- ✅ **Long/short support** — correct P&L calculation for both
- ✅ **Drawdown tracking** — max drawdown in $ and %
- ✅ **Flexible grouping** — by symbol, by month, or overall
- ✅ **JSON export** — for integration with dashboards
- ✅ **Error handling** — skips bad rows, continues processing

---
*Utility: Trade Journal P&L Analyzer | Ready to use*
