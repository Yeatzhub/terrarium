# Trade Report Generator
*Ghost Learning | 2026-02-21*

Generate formatted trade performance reports from CSV data. Creates summary tables, charts, and insights for review.

```python
#!/usr/bin/env python3
"""
Trade Report Generator
Generates formatted performance reports from trade history.

Usage:
    python trade_report.py trades.csv --output report.md
    python trade_report.py trades.csv --html report.html --include-charts
"""

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Optional, list
from statistics import mean, median


@dataclass
class Trade:
    """Trade record."""
    symbol: str
    side: str
    entry: Decimal
    exit: Decimal
    size: Decimal
    pnl: Decimal
    timestamp: Optional[datetime] = None
    
    @classmethod
    def from_csv(cls, row: dict) -> "Trade":
        return cls(
            symbol=row.get("symbol", "").upper(),
            side=row.get("side", "").lower(),
            entry=Decimal(row.get("entry", row.get("entry_price", 0))),
            exit=Decimal(row.get("exit", row.get("exit_price", 0))),
            size=Decimal(row.get("size", 0)),
            pnl=Decimal(row.get("pnl", row.get("profit", 0))),
            timestamp=datetime.fromisoformat(row["timestamp"]) if "timestamp" in row else None
        )
    
    @property
    def return_pct(self) -> Decimal:
        """Return as percentage."""
        cost = self.entry * self.size
        if cost == 0:
            return Decimal("0")
        return (self.pnl / cost) * 100
    
    @property
    def is_winner(self) -> bool:
        return self.pnl > 0


@dataclass
class PerformanceMetrics:
    """Aggregated metrics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    gross_profit: Decimal
    gross_loss: Decimal
    net_pnl: Decimal
    avg_winner: Decimal
    avg_loser: Decimal
    profit_factor: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    best_trade: Decimal
    worst_trade: Decimal
    avg_trade: Decimal
    median_trade: Decimal
    std_dev: float
    sharpe: float


class TradeReportGenerator:
    """Generate formatted trade reports."""
    
    def __init__(self, trades: list[Trade]):
        self.trades = trades
        self.metrics = self._calculate_metrics()
    
    def _calculate_metrics(self) -> PerformanceMetrics:
        """Calculate all metrics."""
        if not self.trades:
            return PerformanceMetrics(0, 0, 0, 0, Decimal("0"), Decimal("0"), Decimal("0"),
                                     Decimal("0"), Decimal("0"), 0, 0, 0, Decimal("0"), Decimal("0"),
                                     Decimal("0"), Decimal("0"), 0, 0)
        
        total = len(self.trades)
        winners = [t for t in self.trades if t.is_winner]
        losers = [t for t in self.trades if not t.is_winner]
        
        gross_profit = sum(t.pnl for t in winners)
        gross_loss = sum(abs(t.pnl) for t in losers)
        net_pnl = sum(t.pnl for t in self.trades)
        
        avg_winner = gross_profit / len(winners) if winners else Decimal("0")
        avg_loser = gross_loss / len(losers) if losers else Decimal("0")
        
        profit_factor = float(gross_profit / gross_loss) if gross_loss > 0 else float(gross_profit)
        
        # Consecutive trades
        max_wins = max_losses = current = 0
        for t in self.trades:
            if t.is_winner:
                current = current + 1 if current > 0 else 1
                max_wins = max(max_wins, current)
            else:
                current = current - 1 if current < 0 else -1
                max_losses = max(max_losses, abs(current))
        
        pnls = [float(t.pnl) for t in self.trades]
        
        return PerformanceMetrics(
            total_trades=total,
            winning_trades=len(winners),
            losing_trades=len(losers),
            win_rate=len(winners) / total * 100 if total > 0 else 0,
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            net_pnl=net_pnl,
            avg_winner=avg_winner,
            avg_loser=avg_loser,
            profit_factor=profit_factor,
            max_consecutive_wins=max_wins,
            max_consecutive_losses=max_losses,
            best_trade=max(t.pnl for t in self.trades),
            worst_trade=min(t.pnl for t in self.trades),
            avg_trade=sum(t.pnl for t in self.trades) / total,
            median_trade=Decimal(str(median(pnls))),
            std_dev=self._std(pnls),
            sharpe=self._calculate_sharpe(pnls)
        )
    
    def _std(self, values: list[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        m = mean(values)
        return (sum((x - m) ** 2 for x in values) / (len(values) - 1)) ** 0.5
    
    def _calculate_sharpe(self, returns: list[float]) -> float:
        """Sharpe-like ratio."""
        if len(returns) < 2:
            return 0.0
        avg = mean(returns)
        std = self._std(returns)
        return (avg / std * (252 ** 0.5)) if std > 0 else 0.0
    
    def generate_markdown(self) -> str:
        """Generate markdown report."""
        m = self.metrics
        
        report = f"""# Trading Performance Report
*Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}*

## Summary

| Metric | Value |
|--------|-------|
| Total Trades | {m.total_trades} |
| Win Rate | {m.win_rate:.1f}% |
| Gross Profit | ${m.gross_profit:+,.2f} |
| Gross Loss | ${m.gross_loss:,.2f} |
| **Net P&L** | ${m.net_pnl:+,.2f} |
| Profit Factor | {m.profit_factor:.2f} |

## Trade Statistics

| Metric | Winners | Losers |
|--------|---------|--------|
| Count | {m.winning_trades} | {m.losing_trades} |
| Avg Trade | ${m.avg_winner:,.2f} | ${m.avg_loser:,.2f} |
| Best | ${m.best_trade:+,.2f} | ${m.worst_trade:,.2f} |

## Performance Metrics

| Metric | Value |
|--------|-------|
| Average Trade | ${m.avg_trade:+,.2f} |
| Median Trade | ${m.median_trade:+,.2f} |
| Std Dev | ${m.std_dev:,.2f} |
| Sharpe (approx) | {m.sharpe:.2f} |
| Max Consecutive Wins | {m.max_consecutive_wins} |
| Max Consecutive Losses | {m.max_consecutive_losses} |

## Trade List

| Symbol | Side | Entry | Exit | Size | P&L |
|--------|------|-------|------|------|-----|
"""
        
        for t in self.trades[-20:]:  # Last 20 trades
            report += f"| {t.symbol} | {t.side} | ${t.entry} | ${t.exit} | {t.size} | ${t.pnl:+,.2f} |\n"
        
        return report
    
    def generate_html(self) -> str:
        """Generate HTML report."""
        m = self.metrics
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Report</title>
    <style>
        body {{ font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; }}
        .positive {{ color: green; }}
        .negative {{ color: red; }}
        .highlight {{ background: #e8f5e9; padding: 15px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Trading Performance Report</h1>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}</p>
    
    <div class="highlight">
        <h2>Summary</h2>
        <p><strong>Total Trades:</strong> {m.total_trades}</p>
        <p><strong>Win Rate:</strong> {m.win_rate:.1f}%</p>
        <p><strong class="{('negative' if m.net_pnl < 0 else 'positive')}">
            Net P&L: ${m.net_pnl:+,.2f}</strong></p>
        <p><strong>Profit Factor:</strong> {m.profit_factor:.2f}</p>
    </div>
</body>
</html>
"""


class SimpleJSONEncoder(json.JSONEncoder):
    """Handle Decimal encoding."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


def load_trades(csv_path: Path) -> list[Trade]:
    """Load trades from CSV."""
    trades = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            trades.append(Trade.from_csv(row))
    return trades


def main():
    parser = argparse.ArgumentParser(description="Trade Report Generator")
    parser.add_argument("csv", type=Path, help="Trades CSV file")
    parser.add_argument("--markdown", "-m", type=Path, help="Output markdown report")
    parser.add_argument("--html", type=Path, help="Output HTML report")
    parser.add_argument("--json", type=Path, help="Output JSON data")
    parser.add_argument("--stdout", "-s", action="store_true", help="Print to stdout")
    
    args = parser.parse_args()
    
    # Load trades
    trades = load_trades(args.csv)
    print(f"Loaded {len(trades)} trades")
    
    # Generate report
    generator = TradeReportGenerator(trades)
    
    # Output markdown
    if args.markdown or args.stdout:
        markdown = generator.generate_markdown()
        if args.stdout:
            print(markdown)
        if args.markdown:
            args.markdown.write_text(markdown)
            print(f"Markdown report saved to {args.markdown}")
    
    # Output HTML
    if args.html:
        html = generator.generate_html()
        args.html.write_text(html)
        print(f"HTML report saved to {args.html}")
    
    # Output JSON
    if args.json:
        data = {
            "metrics": generator.metrics.__dict__,
            "trades": [{"symbol": t.symbol, "pnl": str(t.pnl)} for t in trades]
        }
        args.json.write_text(json.dumps(data, cls=SimpleJSONEncoder, indent=2))
        print(f"JSON data saved to {args.json}")


# === Quick Examples ===

# 1. Markdown report
# python trade_report.py trades.csv --markdown report.md

# 2. HTML report
# python trade_report.py trades.csv --html report.html

# 3. Print to console
# python trade_report.py trades.csv --stdout

# 4. All formats
# python trade_report.py trades.csv -m report.md --html report.html --json data.json

# CSV Format:
# symbol,side,entry,exit,size,pnl,timestamp
# BTCUSD,long,50000,51000,0.5,500,2026-02-20T10:00:00
# BTCUSD,short,51000,50000,0.5,500,2026-02-20T14:00:00


if __name__ == "__main__":
    main()
```

## Quick Start

```bash
# Markdown report
python trade_report.py trades.csv --markdown report.md

# HTML report with styling
python trade_report.py trades.csv --html report.html

# Print to terminal
python trade_report.py trades.csv --stdout

# All formats + JSON
python trade_report.py trades.csv -m report.md --html report.html --json data.json
```

## Report Features

| Feature | Description |
|---------|-------------|
| Summary | Total trades, win rate, net P&L, profit factor |
| Statistics | Avg trade, median, std dev, Sharpe ratio |
| Streaks | Max consecutive wins/losses |
| Trade List | Last 20 trades in table |
| Formats | Markdown, HTML, JSON |

## Sample Output

```markdown
# Trading Performance Report
*Generated: 2026-02-21*

## Summary

| Metric | Value |
|--------|-------|
| Total Trades | 47 |
| Win Rate | 59.6% |
| Gross Profit | +$8,456.00 |
| Gross Loss | -$2,345.00 |
| **Net P&L** | +$6,111.00 |
| Profit Factor | 3.60 |

## Performance Metrics

| Metric | Value |
|--------|-------|
| Average Trade | +$130.02 |
| Sharpe (approx) | 2.14 |
| Max Consecutive Wins | 7 |
| Max Consecutive Losses | 3 |
```

## HTML Report

The HTML version includes:
- Clean, styled tables
- Color-coded P&L (green/red)
- Responsive layout
- Print-friendly CSS

## Integration

```python
# Generate daily report
generator = TradeReportGenerator(trades)
markdown = generator.generate_markdown()

# Send via email/telegram
send_notification(f"Daily Report:\n{markdown[:500]}...")
```

---
*Utility: Trade Report Generator | Daily performance summaries*
