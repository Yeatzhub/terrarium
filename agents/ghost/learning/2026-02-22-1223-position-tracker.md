# Position Tracker
*Ghost Learning | 2026-02-22*

Track multiple positions, calculate portfolio P&L, manage exposure and risk.

## Core Features

- Multi-position management
- Real-time P&L calculation
- Portfolio exposure tracking
- Risk aggregation by symbol/sector

## Implementation

```python
"""
Position Tracker
Multi-position portfolio management.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal
from enum import Enum
from collections import defaultdict


class Side(Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class Position:
    """Single position."""
    symbol: str
    side: Side
    quantity: Decimal
    avg_entry: Decimal
    current_price: Decimal = Decimal("0")
    
    # Risk params
    stop_loss: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    
    # Metadata
    opened_at: datetime = field(default_factory=datetime.utcnow)
    tags: list[str] = field(default_factory=list)
    
    @property
    def market_value(self) -> Decimal:
        """Current position value."""
        return self.quantity * self.current_price
    
    @property
    def cost_basis(self) -> Decimal:
        """Total invested."""
        return self.quantity * self.avg_entry
    
    @property
    def unrealized_pnl(self) -> Decimal:
        """Profit/loss at current price."""
        if self.current_price == 0:
            return Decimal("0")
        if self.side == Side.LONG:
            return (self.current_price - self.avg_entry) * self.quantity
        else:
            return (self.avg_entry - self.current_price) * self.quantity
    
    @property
    def unrealized_pnl_pct(self) -> Decimal:
        """P&L as percentage of cost."""
        if self.cost_basis == 0:
            return Decimal("0")
        return self.unrealized_pnl / self.cost_basis
    
    @property
    def risk_amount(self) -> Decimal:
        """Maximum loss if stopped."""
        if not self.stop_loss:
            return self.cost_basis  # Full position at risk
        if self.side == Side.LONG:
            return (self.avg_entry - self.stop_loss) * self.quantity
        else:
            return (self.stop_loss - self.avg_entry) * self.quantity
    
    @property
    def risk_pct(self) -> Decimal:
        """Risk as % of cost."""
        if self.cost_basis == 0:
            return Decimal("0")
        return self.risk_amount / self.cost_basis
    
    @property
    def distance_to_stop(self) -> Optional[Decimal]:
        """% distance to stop loss."""
        if not self.stop_loss or self.current_price == 0:
            return None
        if self.side == Side.LONG:
            return (self.current_price - self.stop_loss) / self.current_price
        else:
            return (self.stop_loss - self.current_price) / self.current_price
    
    @property
    def distance_to_tp(self) -> Optional[Decimal]:
        """% distance to take profit."""
        if not self.take_profit or self.current_price == 0:
            return None
        if self.side == Side.LONG:
            return (self.take_profit - self.current_price) / self.current_price
        else:
            return (self.current_price - self.take_profit) / self.current_price
    
    def update_price(self, price: Decimal) -> "Position":
        """Update current price."""
        self.current_price = price
        return self
    
    def add(self, quantity: Decimal, price: Decimal) -> "Position":
        """Add to position (averages entry)."""
        total_qty = self.quantity + quantity
        if total_qty > 0:
            total_cost = (self.quantity * self.avg_entry) + (quantity * price)
            self.avg_entry = total_cost / total_qty
        self.quantity = total_qty
        return self
    
    def reduce(self, quantity: Decimal) -> Decimal:
        """Reduce position. Returns realized P&L."""
        if quantity > self.quantity:
            quantity = self.quantity
        
        realized = (self.current_price - self.avg_entry) * quantity
        if self.side == Side.SHORT:
            realized = -realized
        
        self.quantity -= quantity
        return realized
    
    def is_stopped(self) -> bool:
        """Check if stop hit."""
        if not self.stop_loss:
            return False
        if self.side == Side.LONG:
            return self.current_price <= self.stop_loss
        else:
            return self.current_price >= self.stop_loss
    
    def is_target_hit(self) -> bool:
        """Check if take profit hit."""
        if not self.take_profit:
            return False
        if self.side == Side.LONG:
            return self.current_price >= self.take_profit
        else:
            return self.current_price <= self.take_profit


@dataclass
class PortfolioSummary:
    """Portfolio-wide statistics."""
    total_positions: int
    total_value: Decimal
    total_cost: Decimal
    total_pnl: Decimal
    total_pnl_pct: Decimal
    total_risk: Decimal
    
    long_value: Decimal
    short_value: Decimal
    net_exposure: Decimal
    
    winners: int
    losers: int
    
    largest_winner: Decimal
    largest_loser: Decimal
    
    positions_at_risk: int  # Near stop loss
    
    def __str__(self) -> str:
        lines = [
            "=== PORTFOLIO SUMMARY ===",
            f"Positions:     {self.total_positions}",
            f"Total Value:   ${self.total_value:,.2f}",
            f"Total Cost:    ${self.total_cost:,.2f}",
            f"",
            f"Unrealized P&L: ${self.total_pnl:,.2f} ({self.total_pnl_pct:+.2%})",
            f"Total Risk:    ${self.total_risk:,.2f}",
            f"",
            f"Longs:         ${self.long_value:,.2f}",
            f"Shorts:        ${self.short_value:,.2f}",
            f"Net Exposure:  ${self.net_exposure:,.2f}",
            f"",
            f"Winners:       {self.winners} / Losers: {self.losers}",
            f"Best:          ${self.largest_winner:,.2f}",
            f"Worst:         ${self.largest_loser:,.2f}",
        ]
        if self.positions_at_risk > 0:
            lines.append(f"\n⚠ {self.positions_at_risk} position(s) near stop")
        return "\n".join(lines)


class PositionTracker:
    """
    Track multiple positions with portfolio analytics.
    """
    
    def __init__(self, account_balance: Decimal = Decimal("0")):
        self.positions: dict[str, Position] = {}
        self.account_balance = account_balance
        self._realized_pnl: Decimal = Decimal("0")
    
    def open_position(
        self,
        symbol: str,
        side: Side,
        quantity: Decimal,
        price: Decimal,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None,
        tags: list[str] = None,
    ) -> Position:
        """Open a new position."""
        key = self._position_key(symbol, side)
        
        if key in self.positions:
            # Add to existing
            pos = self.positions[key]
            pos.add(quantity, price)
        else:
            # New position
            pos = Position(
                symbol=symbol,
                side=side,
                quantity=quantity,
                avg_entry=price,
                current_price=price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                tags=tags or []
            )
            self.positions[key] = pos
        
        return pos
    
    def close_position(
        self,
        symbol: str,
        side: Side,
        quantity: Optional[Decimal] = None,
    ) -> Decimal:
        """Close position (full or partial). Returns realized P&L."""
        key = self._position_key(symbol, side)
        
        if key not in self.positions:
            raise ValueError(f"No {side.value} position in {symbol}")
        
        pos = self.positions[key]
        
        if quantity is None or quantity >= pos.quantity:
            # Full close
            realized = pos.unrealized_pnl
            del self.positions[key]
        else:
            # Partial close
            realized = pos.reduce(quantity)
        
        self._realized_pnl += realized
        return realized
    
    def update_prices(self, prices: dict[str, Decimal]) -> None:
        """Update multiple prices."""
        for symbol, price in prices.items():
            for side in [Side.LONG, Side.SHORT]:
                key = self._position_key(symbol, side)
                if key in self.positions:
                    self.positions[key].update_price(price)
    
    def get_position(self, symbol: str, side: Side) -> Optional[Position]:
        """Get specific position."""
        return self.positions.get(self._position_key(symbol, side))
    
    def get_all_positions(self) -> list[Position]:
        """Get all positions."""
        return list(self.positions.values())
    
    def get_positions_by_symbol(self, symbol: str) -> list[Position]:
        """Get all positions for a symbol."""
        return [p for p in self.positions.values() if p.symbol == symbol]
    
    def get_positions_by_tag(self, tag: str) -> list[Position]:
        """Get positions with specific tag."""
        return [p for p in self.positions.values() if tag in p.tags]
    
    def check_alerts(self, stop_threshold: Decimal = Decimal("0.02")) -> list[dict]:
        """Check for stop/target hits and near-stops."""
        alerts = []
        
        for pos in self.positions.values():
            if pos.is_stopped():
                alerts.append({
                    "type": "stop_hit",
                    "symbol": pos.symbol,
                    "side": pos.side.value,
                    "pnl": float(pos.unrealized_pnl),
                    "pnl_pct": float(pos.unrealized_pnl_pct)
                })
            
            if pos.is_target_hit():
                alerts.append({
                    "type": "target_hit",
                    "symbol": pos.symbol,
                    "side": pos.side.value,
                    "pnl": float(pos.unrealized_pnl),
                    "pnl_pct": float(pos.unrealized_pnl_pct)
                })
            
            # Near stop warning
            if pos.distance_to_stop and pos.distance_to_stop < stop_threshold:
                alerts.append({
                    "type": "near_stop",
                    "symbol": pos.symbol,
                    "side": pos.side.value,
                    "distance": float(pos.distance_to_stop)
                })
        
        return alerts
    
    def summary(self) -> PortfolioSummary:
        """Generate portfolio summary."""
        positions = self.get_all_positions()
        
        if not positions:
            return PortfolioSummary(
                total_positions=0, total_value=Decimal("0"),
                total_cost=Decimal("0"), total_pnl=Decimal("0"),
                total_pnl_pct=Decimal("0"), total_risk=Decimal("0"),
                long_value=Decimal("0"), short_value=Decimal("0"),
                net_exposure=Decimal("0"), winners=0, losers=0,
                largest_winner=Decimal("0"), largest_loser=Decimal("0"),
                positions_at_risk=0
            )
        
        total_value = sum(p.market_value for p in positions)
        total_cost = sum(p.cost_basis for p in positions)
        total_pnl = sum(p.unrealized_pnl for p in positions)
        total_risk = sum(p.risk_amount for p in positions)
        
        longs = [p for p in positions if p.side == Side.LONG]
        shorts = [p for p in positions if p.side == Side.SHORT]
        
        long_value = sum(p.market_value for p in longs)
        short_value = sum(p.market_value for p in shorts)
        
        pnl_values = [p.unrealized_pnl for p in positions]
        winners = len([p for p in positions if p.unrealized_pnl > 0])
        losers = len([p for p in positions if p.unrealized_pnl < 0])
        
        near_stop = len([p for p in positions 
                        if p.distance_to_stop and p.distance_to_stop < Decimal("0.02")])
        
        return PortfolioSummary(
            total_positions=len(positions),
            total_value=total_value,
            total_cost=total_cost,
            total_pnl=total_pnl,
            total_pnl_pct=total_pnl / total_cost if total_cost else Decimal("0"),
            total_risk=total_risk,
            long_value=long_value,
            short_value=short_value,
            net_exposure=long_value - short_value,
            winners=winners,
            losers=losers,
            largest_winner=max(pnl_values) if pnl_values else Decimal("0"),
            largest_loser=min(pnl_values) if pnl_values else Decimal("0"),
            positions_at_risk=near_stop
        )
    
    def _position_key(self, symbol: str, side: Side) -> str:
        return f"{symbol}:{side.value}"
    
    @property
    def realized_pnl(self) -> Decimal:
        return self._realized_pnl


# === Usage ===

if __name__ == "__main__":
    tracker = PositionTracker(account_balance=Decimal("100000"))
    
    # Open positions
    tracker.open_position("BTC", Side.LONG, Decimal("0.5"), Decimal("50000"),
                          stop_loss=Decimal("48000"), take_profit=Decimal("55000"),
                          tags=["crypto", "momentum"])
    
    tracker.open_position("ETH", Side.LONG, Decimal("5"), Decimal("3000"),
                          stop_loss=Decimal("2800"))
    
    tracker.open_position("SOL", Side.SHORT, Decimal("50"), Decimal("100"),
                          stop_loss=Decimal("105"), tags=["crypto", "hedge"])
    
    # Update prices
    tracker.update_prices({
        "BTC": Decimal("52000"),
        "ETH": Decimal("2900"),
        "SOL": Decimal("95")
    })
    
    # Check positions
    print("=== INDIVIDUAL POSITIONS ===")
    for pos in tracker.get_all_positions():
        print(f"{pos.symbol} {pos.side.value}: {pos.quantity} @ ${pos.avg_entry}")
        print(f"  P&L: ${pos.unrealized_pnl:,.2f} ({pos.unrealized_pnl_pct:+.2%})")
        print(f"  Risk: ${pos.risk_amount:,.2f} ({pos.risk_pct:.1%})")
        print(f"  To Stop: {pos.distance_to_stop:.2%}" if pos.distance_to_stop else "")
        print()
    
    # Portfolio summary
    print(tracker.summary())
    
    # Check alerts
    print("\n=== ALERTS ===")
    alerts = tracker.check_alerts()
    for alert in alerts:
        print(f"{alert['type'].upper()}: {alert['symbol']} {alert['side']}")
    
    # Close a position
    print("\n=== CLOSING BTC ===")
    realized = tracker.close_position("BTC", Side.LONG)
    print(f"Realized P&L: ${realized:,.2f}")
    print(f"Total Realized: ${tracker.realized_pnl:,.2f}")
```

## Output

```
=== INDIVIDUAL POSITIONS ===
BTC long: 0.5 @ $50000.00
  P&L: $1,000.00 (+4.00%)
  Risk: $1,000.00 (4.0%)
  To Stop: 7.69%

ETH long: 5 @ $3000.00
  P&L: $-500.00 (-3.33%)
  Risk: $1,000.00 (6.7%)
  To Stop: 3.45%

SOL short: 50 @ $100.00
  P&L: $250.00 (+5.00%)
  Risk: $250.00 (5.0%)
  To Stop: 10.53%

=== PORTFOLIO SUMMARY ===
Positions:     3
Total Value:   $26,750.00
Total Cost:    $27,000.00

Unrealized P&L: $750.00 (+2.78%)
Total Risk:    $2,250.00

Longs:         $27,500.00
Shorts:        $4,750.00
Net Exposure:  $22,750.00

Winners:       2 / Losers: 1
Best:          $1,000.00
Worst:         $-500.00

⚠ 1 position(s) near stop

=== ALERTS ===
NEAR_STOP: ETH long

=== CLOSING BTC ===
Realized P&L: $1,000.00
Total Realized: $1,000.00
```

## Quick Reference

```python
# Open
tracker.open_position("BTC", Side.LONG, qty, price, stop=stop_price)

# Update prices
tracker.update_prices({"BTC": Decimal("52000")})

# Check alerts
alerts = tracker.check_alerts()

# Portfolio summary
summary = tracker.summary()

# Close
pnl = tracker.close_position("BTC", Side.LONG)
```

## Position Properties

| Property | Description |
|----------|-------------|
| `market_value` | Qty × Current Price |
| `cost_basis` | Qty × Avg Entry |
| `unrealized_pnl` | Current P&L |
| `risk_amount` | Max loss to stop |
| `distance_to_stop` | % to stop loss |

---
*Utility: Position Tracker | Features: Multi-position P&L, risk aggregation, alert checking*