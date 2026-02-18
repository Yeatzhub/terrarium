# Position Sizing & Risk Utility

A lightweight Python CLI for disciplined trade planning. Copy-paste ready.

## Quick Start

```bash
python trade_util.py --account 10000 --risk 1 --entry 150 --stop 145
```

## The Code (`trade_util.py`)

```python
#!/usr/env/bin python3
"""Ghost Trade Utility v1.0 — Position sizing and risk calculator"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class TradePlan:
    symbol: str
    entry: float
    stop: float
    target: Optional[float] = None
    account_size: float = 10000.0
    risk_percent: float = 1.0
    timestamp: str = ""
    position_size: int = 0
    risk_amount: float = 0.0
    r_ratio: float = 0.0
    
    def __post_init__(self):
        self.timestamp = datetime.now().isoformat()
        self.calculate()
    
    def calculate(self):
        """Calculate position size based on risk tolerance."""
        stop_distance = abs(self.entry - self.stop)
        if stop_distance == 0:
            raise ValueError("Entry and stop must differ")
        
        self.risk_amount = self.account_size * (self.risk_percent / 100)
        shares = int(self.risk_amount / stop_distance)
        self.position_size = max(1, shares)  # At least 1 share
        
        if self.target:
            reward = abs(self.target - self.entry)
            risk = stop_distance
            self.r_ratio = round(reward / risk, 2) if risk else 0
    
    def summary(self) -> str:
        lines = [
            f"📊 Trade Plan: {self.symbol}",
            f"   Entry: ${self.entry:.2f} | Stop: ${self.stop:.2f}",
            f"   Position: {self.position_size} shares",
            f"   Risk: ${self.risk_amount:.2f} ({self.risk_percent}% of account)",
        ]
        if self.target:
            lines.append(f"   Target: ${self.target:.2f} | R:R = 1:{self.r_ratio}")
        target_size = self.position_size * self.entry
        lines.append(f"   Capital Required: ${target_size:.2f}")
        return "\n".join(lines)


class TradeJournal:
    """Simple JSON persistence for trade history."""
    
    def __init__(self, path: str = "trades.json"):
        self.path = Path(path)
        self.trades = self._load()
    
    def _load(self) -> list:
        if self.path.exists():
            return json.loads(self.path.read_text())
        return []
    
    def add(self, trade: TradePlan, outcome: Optional[str] = None):
        entry = asdict(trade)
        entry["outcome"] = outcome or "planned"
        self.trades.append(entry)
        self.path.write_text(json.dumps(self.trades, indent=2))
    
    def stats(self) -> str:
        """Quick win/loss overview."""
        completed = [t for t in self.trades if t.get("outcome") not in ("planned", None)]
        if not completed:
            return "No completed trades yet."
        
        wins = sum(1 for t in completed if t["outcome"] == "win")
        total = len(completed)
        win_rate = wins / total * 100 if total else 0
        
        return f"📈 Win Rate: {wins}/{total} ({win_rate:.1f}%) | Total Trades: {len(self.trades)}"


def main():
    parser = argparse.ArgumentParser(description="Ghost Trade Position Sizer")
    parser.add_argument("-a", "--account", type=float, default=10000, help="Account size ($)")
    parser.add_argument("-r", "--risk", type=float, default=1.0, help="Risk % per trade")
    parser.add_argument("-e", "--entry", type=float, required=True, help="Entry price")
    parser.add_argument("-s", "--stop", type=float, required=True, help="Stop loss")
    parser.add_argument("-t", "--target", type=float, help="Target price")
    parser.add_argument("--symbol", default="UNKNOWN", help="Ticker symbol")
    parser.add_argument("--save", action="store_true", help="Save to journal")
    parser.add_argument("--stats", action="store_true", help="Show journal stats")
    
    args = parser.parse_args()
    
    journal = TradeJournal()
    
    if args.stats:
        print(journal.stats())
        return
    
    plan = TradePlan(
        symbol=args.symbol.upper(),
        entry=args.entry,
        stop=args.stop,
        target=args.target,
        account_size=args.account,
        risk_percent=args.risk
    )
    
    print(plan.summary())
    
    if args.save:
        journal.add(plan)
        print(f"\n✓ Saved to {journal.path}")


if __name__ == "__main__":
    main()
```

## Usage Examples

```bash
# Basic calculation
python trade_util.py -e 150 -s 145

# Full plan with R:R
python trade_util.py -a 25000 -r 2 --entry 45.50 --stop 43.00 --target 52.00 --symbol AAPL --save

# Check history
python trade_util.py --stats

# Quick calculation (default $10k account, 1% risk)
python trade_util.py -e 300 -s 295
```

## Key Features

| Feature | Purpose |
|---------|---------|
| **Fixed % Risk** | Never blow up your account; 1-2% per trade is standard |
| **R:R Display** | Only take trades with 2:1+ reward-to-risk |
| **JSON Persistence** | Simple, portable trade history; grep/search friendly |
| **Zero Dependencies** | Uses only stdlib; works anywhere |

## Risk Rules Embedded

1. Position = `(Account × Risk%) / |Entry - Stop|`
2. Minimum 1 share (no fractional here)
3. Shows capital required before entry
4. Timestamped entries for review

## Integration Tips

- **With Excel**: `trades.json` imports directly
- **With Notion**: Use `cat trades.json | jq -r '.[] | "\(.symbol): \(.outcome)"'` for formatted logging
- **With brokers**: Copy-paste position size into your order ticket

---
*Ghost Trade Utility v1.0 | Created 2026-02-18 | 15-min sprint*
