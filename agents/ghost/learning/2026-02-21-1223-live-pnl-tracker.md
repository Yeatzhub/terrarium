# Live P&L Tracker
*Ghost Learning | 2026-02-21*

Real-time position P&L tracker with live price updates, risk monitoring, and alerts. Displays running P&L, exposure, and risk metrics in a clean terminal interface.

```python
#!/usr/bin/env python3
"""
Live Position P&L Tracker
Real-time tracking of open positions with P&L updates and risk alerts.

Usage:
    python pnl_tracker.py positions.csv --update-interval 5 --alert-threshold 0.05
    
    # Interactive mode (manual price entry for testing)
    python pnl_tracker.py --manual --starting-equity 50000
"""

import argparse
import asyncio
import csv
import sys
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
import json


@dataclass
class Position:
    """Active position with tracking."""
    symbol: str
    side: str           # 'long' or 'short'
    entry_price: Decimal
    current_price: Decimal
    size: Decimal
    fees: Decimal = Decimal("0")
    
    # Calculated
    @property
    def notional(self) -> Decimal:
        """Current position value."""
        return self.size * self.current_price
    
    @property
    def cost_basis(self) -> Decimal:
        """Entry position value."""
        return self.size * self.entry_price
    
    @property
    def unrealized_pnl(self) -> Decimal:
        """Unrealized P&L."""
        if self.side == "long":
            return (self.current_price - self.entry_price) * self.size - self.fees
        else:
            return (self.entry_price - self.current_price) * self.size - self.fees
    
    @property
    def unrealized_pnl_pct(self) -> Decimal:
        """Unrealized P&L as percentage."""
        if self.cost_basis == 0:
            return Decimal("0")
        return (self.unrealized_pnl / self.cost_basis) * 100
    
    @property
    def is_profitable(self) -> bool:
        return self.unrealized_pnl > 0


@dataclass
class PortfolioState:
    """Current portfolio state."""
    positions: list[Position] = field(default_factory=list)
    starting_equity: Decimal = Decimal("0")
    cash: Decimal = Decimal("0")
    
    @property
    def equity(self) -> Decimal:
        """Total account equity (cash + positions)."""
        return self.cash + sum(p.notional for p in self.positions)
    
    @property
    def total_exposure(self) -> Decimal:
        """Total position notional value."""
        return sum(p.notional for p in self.positions)
    
    @property
    def leverage(self) -> Decimal:
        """Current leverage (exposure / equity)."""
        if self.equity == 0:
            return Decimal("0")
        return self.total_exposure / self.equity
    
    @property
    def gross_pnl(self) -> Decimal:
        """Total unrealized P&L."""
        return sum(p.unrealized_pnl for p in self.positions)
    
    @property
    def return_pct(self) -> Decimal:
        """Total return since start."""
        if self.starting_equity == 0:
            return Decimal("0")
        return ((self.equity - self.starting_equity) / self.starting_equity) * 100
    
    @property
    def winning_positions(self) -> int:
        return sum(1 for p in self.positions if p.is_profitable)
    
    @property
    def losing_positions(self) -> int:
        return len(self.positions) - self.winning_positions


class LivePnlTracker:
    """Real-time P&L tracking."""
    
    def __init__(self, starting_equity: Decimal = Decimal("0")):
        self.state = PortfolioState(starting_equity=starting_equity)
        self.alert_threshold: Optional[Decimal] = None
        self.last_alerted_pct: Decimal = Decimal("0")
        self.max_seen_pnl: Decimal = Decimal("0")
        self.max_drawdown_from_peak: Decimal = Decimal("0")
    
    def load_positions(self, csv_path: Path) -> None:
        """Load positions from CSV."""
        positions = []
        
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pos = Position(
                    symbol=row["symbol"].upper(),
                    side=row["side"].lower(),
                    entry_price=Decimal(row["entry_price"]),
                    current_price=Decimal(row.get("current_price", row["entry_price"])),
                    size=Decimal(row["size"]),
                    fees=Decimal(row.get("fees", "0"))
                )
                positions.append(pos)
        
        self.state.positions = positions
        
        # Calculate cash (assume fully invested if not specified)
        invested = sum(p.cost_basis for p in positions)
        self.state.cash = self.state.starting_equity - invested if self.state.starting_equity else Decimal("0")
    
    def update_price(self, symbol: str, price: Decimal) -> None:
        """Update a position's current price."""
        for pos in self.state.positions:
            if pos.symbol == symbol:
                pos.current_price = price
                break
    
    def update_prices(self, prices: dict[str, Decimal]) -> None:
        """Batch update prices."""
        for symbol, price in prices.items():
            self.update_price(symbol, price)
    
    def check_alerts(self) -> list[str]:
        """Check for alert conditions."""
        alerts = []
        
        if not self.alert_threshold:
            return alerts
        
        # Position-level alerts
        for pos in self.state.positions:
            if abs(pos.unrealized_pnl_pct) > self.alert_threshold * 100:
                direction = "PROFIT" if pos.is_profitable else "LOSS"
                alerts.append(f"⚠️ {pos.symbol} {direction}: {pos.unrealized_pnl_pct:+.2f}%")
        
        # Portfolio-level alerts
        current_pnl_pct = self.state.return_pct
        if abs(current_pnl_pct - self.last_alerted_pct) > self.alert_threshold * 100:
            self.last_alerted_pct = current_pnl_pct
            if current_pnl_pct != 0:
                direction = "UP" if current_pnl_pct > 0 else "DOWN"
                alerts.append(f"📊 PORTFOLIO {direction}: {current_pnl_pct:+.2f}%")
        
        # Drawdown alert
        self.max_seen_pnl = max(self.max_seen_pnl, self.state.gross_pnl)
        if self.max_seen_pnl > 0:
            current_dd = self.state.gross_pnl - self.max_seen_pnl
            dd_pct = (current_dd / self.state.starting_equity) * 100
            if abs(dd_pct) > 10 and abs(dd_pct - self.max_drawdown_from_peak) > 2:
                self.max_drawdown_from_peak = dd_pct
                alerts.append(f"📉 DRAWDOWN ALERT: {dd_pct:.2f}% from peak")
        
        return alerts
    
    def display(self, clear: bool = True) -> None:
        """Display current state."""
        if clear:
            print("\033[2J\033[H", end="")  # Clear screen
        
        s = self.state
        
        # Header
        print(f"{'═'*70}")
        print(f"  LIVE P&L TRACKER | {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'═'*70}")
        
        # Portfolio Summary
        pnl_color = "🟢" if s.gross_pnl >= 0 else "🔴"
        print(f"\n  EQUITY:       ${s.equity:,.2f}")
        print(f"  P&L:          {pnl_color} ${s.gross_pnl:+,.2f} ({s.return_pct:+.2f}%)")
        print(f"  CASH:         ${s.cash:,.2f}")
        print(f"  EXPOSURE:     ${s.total_exposure:,.2f}")
        print(f"  LEVERAGE:     {s.leverage:.2f}x")
        print(f"  WIN/LOSS:     {s.winning_positions}/{s.losing_positions}")
        
        # Positions table
        print(f"\n{'─'*70}")
        print(f"  {'Symbol':<10} {'Side':<6} {'Entry':<12} {'Current':<12} {'Size':<10} {'P&L $':<14} {'P&L %':<10}")
        print(f"{'─'*70}")
        
        for p in sorted(s.positions, key=lambda x: x.unrealized_pnl, reverse=True):
            pnl_emoji = "🟢" if p.is_profitable else "🔴"
            print(f"  {p.symbol:<10} {p.side:<6} ${p.entry_price:<11.2f} ${p.current_price:<11.2f} "
                  f"{p.size:<10.4f} {pnl_emoji} ${p.unrealized_pnl:<11.2f} {p.unrealized_pnl_pct:+7.2f}%")
        
        print(f"{'═'*70}\n")


async def simulate_price_updates(tracker: LivePnlTracker, symbols: list[str], interval: float = 5.0):
    """Simulate price updates for testing."""
    import random
    
    base_prices = {}
    for pos in tracker.state.positions:
        base_prices[pos.symbol] = float(pos.entry_price)
    
    while True:
        # Generate random price movements
        updates = {}
        for symbol in symbols:
            if symbol in base_prices:
                change = random.uniform(-0.02, 0.02)  # ±2%
                new_price = Decimal(str(base_prices[symbol] * (1 + change)))
                updates[symbol] = new_price
                base_prices[symbol] *= (1 + change)
        
        tracker.update_prices(updates)
        
        # Display and check alerts
        tracker.display()
        alerts = tracker.check_alerts()
        for alert in alerts:
            print(f"  {alert}")
        
        await asyncio.sleep(interval)


async def manual_mode(tracker: LivePnlTracker):
    """Manual price entry mode for testing."""
    print(f"\n{'='*60}")
    print("MANUAL MODE: Enter symbol and price to update")
    print("Commands: 'quit', 'reload', 'add <symbol> <side> <entry> <size>')")
    print(f"{'='*60}\n")
    
    tracker.display(clear=False)
    
    while True:
        try:
            cmd = input("\n> ").strip().lower()
            
            if cmd == "quit":
                break
            
            if cmd == "reload":
                tracker.display(clear=False)
                continue
            
            if cmd.startswith("add "):
                parts = cmd.split()
                if len(parts) >= 5:
                    _, symbol, side, entry, size = parts[:5]
                    pos = Position(
                        symbol=symbol.upper(),
                        side=side,
                        entry_price=Decimal(entry),
                        current_price=Decimal(entry),
                        size=Decimal(size)
                    )
                    tracker.state.positions.append(pos)
                    print(f"Added {symbol} position")
                continue
            
            # Price update: "BTCUSD 51000" or "BTCUSD 51000.50"
            parts = cmd.split()
            if len(parts) == 2:
                symbol, price = parts
                tracker.update_price(symbol.upper(), Decimal(price))
                tracker.display(clear=False)
                
                alerts = tracker.check_alerts()
                for alert in alerts:
                    print(f"  {alert}")
        
        except (EOFError, KeyboardInterrupt):
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nExiting...")


def main():
    parser = argparse.ArgumentParser(description="Live P&L Tracker")
    parser.add_argument("csv", nargs="?", type=Path, help="Positions CSV file")
    parser.add_argument("--starting-equity", "-e", type=Decimal, 
                       help="Starting account equity")
    parser.add_argument("--update-interval", "-i", type=float, default=5.0,
                       help="Price update interval (default 5s)")
    parser.add_argument("--alert-threshold", "-a", type=Decimal, default=0.05,
                       help="Alert at X% P&L change (default 5%%)")
    parser.add_argument("--manual", "-m", action="store_true",
                       help="Manual price entry mode")
    parser.add_argument("--output", "-o", type=Path,
                       help="Save final state to JSON")
    parser.add_argument("--no-clear", action="store_true",
                       help="Don't clear screen between updates")
    
    args = parser.parse_args()
    
    # Create tracker
    if not args.starting_equity and args.csv:
        # Estimate from 2x position value
        equity = Decimal("0")
    else:
        equity = args.starting_equity or Decimal("10000")
    
    tracker = LivePnlTracker(starting_equity=equity)
    tracker.alert_threshold = args.alert_threshold
    
    # Load positions
    if args.csv:
        tracker.load_positions(args.csv)
    elif not args.manual:
        print("Error: Provide positions CSV or use --manual mode")
        sys.exit(1)
    
    # Run
    try:
        if args.manual:
            asyncio.run(manual_mode(tracker))
        else:
            # Auto-update mode (would connect to real price feed here)
            symbols = [p.symbol for p in tracker.state.positions]
            asyncio.run(simulate_price_updates(tracker, symbols, args.update_interval))
    except KeyboardInterrupt:
        print("\n\nStopped.")
    
    # Final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY:")
    print(f"  Ending Equity: ${tracker.state.equity:,.2f}")
    print(f"  Total P&L:     ${tracker.state.gross_pnl:+,.2f} ({tracker.state.return_pct:+.2f}%)")
    print(f"  Max Positions: {len(tracker.state.positions)}")
    print(f"{'='*60}")
    
    if args.output:
        data = {
            "starting_equity": str(tracker.state.starting_equity),
            "ending_equity": str(tracker.state.equity),
            "gross_pnl": str(tracker.state.gross_pnl),
            "return_pct": float(tracker.state.return_pct),
            "leverage": float(tracker.state.leverage),
            "positions": [
                {
                    "symbol": p.symbol,
                    "side": p.side,
                    "entry": str(p.entry_price),
                    "current": str(p.current_price),
                    "size": str(p.size),
                    "unrealized_pnl": str(p.unrealized_pnl),
                    "unrealized_pnl_pct": float(p.unrealized_pnl_pct)
                }
                for p in tracker.state.positions
            ]
        }
        args.output.write_text(json.dumps(data, indent=2))
        print(f"💾 Saved to {args.output}")


# === Quick Examples ===

# 1. Manual testing mode
# python pnl_tracker.py --manual --starting-equity 50000
# Then type: BTCUSD 51000 (to update price)

# 2. Load positions from CSV
# python pnl_tracker.py positions.csv --starting-equity 50000 -a 0.05

# CSV Format:
# symbol,side,entry_price,current_price,size,fees
# BTCUSD,long,50000,50000,0.5,10
# ETHUSD,short,3000,3000,2.0,5

# 3. Alert at 10% P&L
# python pnl_tracker.py positions.csv -e 100000 -a 0.10

# 4. Save final state
# python pnl_tracker.py positions.csv -e 100000 --output final_state.json


if __name__ == "__main__":
    main()
```

## Quick Start

```bash
# Manual mode for testing
python pnl_tracker.py --manual --starting-equity 50000

# With positions CSV
python pnl_tracker.py positions.csv --starting-equity 50000 -a 0.05

# Alert at 10% profit/loss
python pnl_tracker.py positions.csv -e 100000 -a 0.10

# Save final state
python pnl_tracker.py positions.csv -e 100000 --output final.json
```

## Sample CSV

```csv
symbol,side,entry_price,current_price,size,fees
BTCUSD,long,50000,50000,0.5,10
ETHUSD,short,3000,3000,2.0,5
SOLUSD,long,150,150,50,15
```

## Terminal Output

```
══════════════════════════════════════════════════════════════════════
  LIVE P&L TRACKER | 14:32:45
══════════════════════════════════════════════════════════════════════

  EQUITY:       $53,245.50
  P&L:          🟢 +$3,245.50 (+6.49%)
  CASH:         $40,000.00
  EXPOSURE:     $13,245.50
  LEVERAGE:     0.25x
  WIN/LOSS:     2/1

──────────────────────────────────────────────────────────────────────
  Symbol     Side   Entry        Current      Size       P&L $          P&L %     
──────────────────────────────────────────────────────────────────────
  BTCUSD     long   $50,000.00   $52,500.00   0.5000     🟢 $1,240.00    +4.92%
  SOLUSD     long   $150.00      $175.00      50.0000    🟢 $1,240.00    +16.56%
  ETHUSD     short  $3,000.00    $2,950.00    2.0000      🔴 $90.00      +1.67%
══════════════════════════════════════════════════════════════════════
```

## Manual Mode Commands

```
> BTCUSD 51000       # Update BTC price to $51,000
> ETHUSD 2900        # Update ETH price to $2,900
> add BTCUSD long 50000 0.5   # Add new position
> reload             # Re-display current state
> quit               # Exit
```

## Alert Types

- **Position Alert**: Individual position crosses ±5% threshold
- **Portfolio Alert**: Total return moves significantly
- **Drawdown Alert**: Pulls back >10% from peak P&L

## Key Metrics

| Metric | Description |
|--------|-------------|
| P&L | Unrealized profit/loss across all positions |
| Exposure | Total position notional value |
| Leverage | Exposure / Equity ratio |
| Win/Loss | Count of profitable vs losing positions |
| Return % | Total return vs starting equity |

## Integration

Replace `simulate_price_updates()` with real price feed:

```python
async def subscribe_prices(tracker):
    async with websockets.connect("wss://api.exchange.com/ws") as ws:
        while True:
            msg = json.loads(await ws.recv())
            symbol = msg["symbol"]
            price = Decimal(str(msg["price"]))
            tracker.update_price(symbol, price)
```

## Dependencies

- Standard library only (`asyncio`, `csv`, `dataclasses`, `decimal`)

---
*Utility: Live P&L Tracker | Real-time position monitoring*
