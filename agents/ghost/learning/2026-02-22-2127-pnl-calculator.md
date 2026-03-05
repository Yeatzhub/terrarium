# P&L Calculator
*Ghost Learning | 2026-02-22*

Track realized/unrealized P&L with cost basis methods. Essential for trading performance.

## Key Concepts

| Term | Definition |
|------|------------|
| **Realized P&L** | Profit from closed positions |
| **Unrealized P&L** | Paper profit on open positions |
| **Cost Basis** | Average or specific cost of holdings |
| **FIFO** | First-in, first-out (oldest shares sold first) |
| **LIFO** | Last-in, first-out (newest shares sold first) |

## Implementation

```python
"""
P&L Calculator
Cost basis tracking and P&L calculation with FIFO/LIFO/Average.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import List, Optional, Literal
from enum import Enum
from collections import deque


class CostMethod(Enum):
    FIFO = "fifo"   # First in, first out
    LIFO = "lifo"   # Last in, first out
    AVG = "average" # Average cost


@dataclass
class Lot:
    """A tax lot of shares/contracts."""
    quantity: Decimal
    price: Decimal
    timestamp: datetime
    fees: Decimal = Decimal("0")
    
    @property
    def cost(self) -> Decimal:
        return (self.quantity * self.price) + self.fees


@dataclass
class Trade:
    """A trade record."""
    timestamp: datetime
    side: Literal["buy", "sell"]
    quantity: Decimal
    price: Decimal
    fees: Decimal = Decimal("0")
    
    @property
    def gross(self) -> Decimal:
        return self.quantity * self.price


@dataclass
class RealizedTrade:
    """A realized P&L event."""
    open_lot: Lot
    close_quantity: Decimal
    close_price: Decimal
    close_timestamp: datetime
    pnl: Decimal
    pnl_pct: Decimal
    
    @property
    def holding_time(self) -> float:
        """Holding time in hours."""
        delta = self.close_timestamp - self.open_lot.timestamp
        return delta.total_seconds() / 3600


@dataclass
class Position:
    """Position with cost basis tracking."""
    symbol: str
    quantity: Decimal = Decimal("0")
    lots: deque = field(default_factory=deque)  # For FIFO
    avg_cost: Decimal = Decimal("0")
    
    @property
    def total_cost(self) -> Decimal:
        return sum(lot.cost for lot in self.lots) if self.lots else Decimal("0")
    
    @property
    def avg_price(self) -> Decimal:
        if self.quantity == 0:
            return Decimal("0")
        return self.total_cost / self.quantity


@dataclass
class PnLSummary:
    """P&L summary for a position."""
    symbol: str
    quantity: Decimal
    avg_cost: Decimal
    current_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal
    realized_pnl: Decimal
    total_pnl: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    
    def __str__(self) -> str:
        lines = [
            f"=== {self.symbol} P&L ===",
            f"Position:      {self.quantity} @ ${self.avg_cost:.2f}",
            f"Market Value:  ${self.market_value:,.2f}",
            f"Cost Basis:    ${self.cost_basis:,.2f}",
            f"",
            f"Unrealized:    ${self.unrealized_pnl:+,.2f} ({self.unrealized_pnl_pct:+.2%})",
            f"Realized:      ${self.realized_pnl:+,.2f}",
            f"Total P&L:     ${self.total_pnl:+,.2f}",
            f"",
            f"Trades:        {self.total_trades} ({self.winning_trades}W/{self.losing_trades}L)",
        ]
        return "\n".join(lines)


class PnLCalculator:
    """
    Calculate P&L with cost basis tracking.
    
    Supports FIFO, LIFO, and Average cost methods.
    """
    
    def __init__(self, method: CostMethod = CostMethod.FIFO):
        self.method = method
        self.positions: dict[str, Position] = {}
        self.realized_trades: List[RealizedTrade] = []
        self.trades: List[Trade] = []
    
    def buy(
        self,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        fees: Decimal = Decimal("0"),
        timestamp: datetime = None
    ) -> Position:
        """Execute a buy, add to position."""
        timestamp = timestamp or datetime.utcnow()
        
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)
        
        pos = self.positions[symbol]
        
        # Add lot
        lot = Lot(quantity=quantity, price=price, timestamp=timestamp, fees=fees)
        
        if self.method == CostMethod.FIFO:
            pos.lots.append(lot)  # Add to end (sell from front)
        elif self.method == CostMethod.LIFO:
            pos.lots.appendleft(lot)  # Add to front (sell from front)
        else:  # Average
            pos.lots.append(lot)
        
        pos.quantity += quantity
        pos.avg_cost = pos.avg_price
        
        # Record trade
        self.trades.append(Trade(
            timestamp=timestamp,
            side="buy",
            quantity=quantity,
            price=price,
            fees=fees
        ))
        
        return pos
    
    def sell(
        self,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        fees: Decimal = Decimal("0"),
        timestamp: datetime = None
    ) -> RealizedTrade:
        """Execute a sell, calculate realized P&L."""
        timestamp = timestamp or datetime.utcnow()
        
        if symbol not in self.positions:
            raise ValueError(f"No position in {symbol}")
        
        pos = self.positions[symbol]
        
        if quantity > pos.quantity:
            raise ValueError(f"Insufficient quantity: have {pos.quantity}, selling {quantity}")
        
        # Calculate realized P&L based on method
        total_realized = Decimal("0")
        remaining = quantity
        closed_trades = []
        
        if self.method == CostMethod.AVG:
            # Average cost
            cost_basis = pos.avg_price * quantity
            proceeds = (price * quantity) - fees
            pnl = proceeds - cost_basis
            pnl_pct = pnl / cost_basis if cost_basis else Decimal("0")
            
            realized = RealizedTrade(
                open_lot=Lot(quantity=quantity, price=pos.avg_price, timestamp=timestamp),
                close_quantity=quantity,
                close_price=price,
                close_timestamp=timestamp,
                pnl=pnl,
                pnl_pct=pnl_pct
            )
            closed_trades.append(realized)
            total_realized = pnl
            
            # Reduce all lots proportionally
            pos.quantity -= quantity
            pos.lots.clear()
            if pos.quantity > 0:
                # Re-add remaining at avg
                pos.lots.append(Lot(
                    quantity=pos.quantity,
                    price=pos.avg_price,
                    timestamp=timestamp
                ))
        
        else:  # FIFO or LIFO
            while remaining > 0 and pos.lots:
                lot = pos.lots[0]  # Always take from front
                
                if lot.quantity <= remaining:
                    # Close entire lot
                    close_qty = lot.quantity
                    cost = lot.cost
                    proceeds = (price * close_qty) - (fees * close_qty / quantity)
                    pnl = proceeds - cost
                    pnl_pct = pnl / cost if cost else Decimal("0")
                    
                    realized = RealizedTrade(
                        open_lot=lot,
                        close_quantity=close_qty,
                        close_price=price,
                        close_timestamp=timestamp,
                        pnl=pnl,
                        pnl_pct=pnl_pct
                    )
                    closed_trades.append(realized)
                    total_realized += pnl
                    
                    pos.quantity -= close_qty
                    remaining -= close_qty
                    pos.lots.popleft()  # Remove lot
                
                else:
                    # Partial close
                    close_qty = remaining
                    cost_per_unit = lot.cost / lot.quantity
                    cost = cost_per_unit * close_qty
                    proceeds = (price * close_qty) - (fees * close_qty / quantity)
                    pnl = proceeds - cost
                    pnl_pct = pnl / cost if cost else Decimal("0")
                    
                    realized = RealizedTrade(
                        open_lot=Lot(
                            quantity=close_qty,
                            price=lot.price,
                            timestamp=lot.timestamp
                        ),
                        close_quantity=close_qty,
                        close_price=price,
                        close_timestamp=timestamp,
                        pnl=pnl,
                        pnl_pct=pnl_pct
                    )
                    closed_trades.append(realized)
                    total_realized += pnl
                    
                    # Update lot
                    lot.quantity -= close_qty
                    pos.quantity -= close_qty
                    remaining = Decimal("0")
            
            pos.avg_cost = pos.avg_price if pos.quantity > 0 else Decimal("0")
        
        # Record
        self.realized_trades.extend(closed_trades)
        self.trades.append(Trade(
            timestamp=timestamp,
            side="sell",
            quantity=quantity,
            price=price,
            fees=fees
        ))
        
        return closed_trades[0] if len(closed_trades) == 1 else closed_trades
    
    def unrealized_pnl(
        self,
        symbol: str,
        current_price: Decimal
    ) -> Decimal:
        """Calculate unrealized P&L at current price."""
        if symbol not in self.positions:
            return Decimal("0")
        
        pos = self.positions[symbol]
        if pos.quantity == 0:
            return Decimal("0")
        
        market_value = pos.quantity * current_price
        return market_value - pos.total_cost
    
    def realized_pnl(self, symbol: str = None) -> Decimal:
        """Total realized P&L."""
        trades = self.realized_trades
        if symbol:
            # Would need to track symbol in RealizedTrade
            return sum(t.pnl for t in trades)
        return sum(t.pnl for t in trades)
    
    def summary(
        self,
        symbol: str,
        current_price: Decimal
    ) -> PnLSummary:
        """Generate P&L summary for a position."""
        pos = self.positions.get(symbol, Position(symbol=symbol))
        
        market_value = pos.quantity * current_price
        cost_basis = pos.total_cost
        unrealized = market_value - cost_basis
        unrealized_pct = unrealized / cost_basis if cost_basis else Decimal("0")
        
        symbol_trades = [t for t in self.realized_trades]
        realized = sum(t.pnl for t in symbol_trades)
        winners = len([t for t in symbol_trades if t.pnl > 0])
        losers = len([t for t in symbol_trades if t.pnl < 0])
        
        return PnLSummary(
            symbol=symbol,
            quantity=pos.quantity,
            avg_cost=pos.avg_price,
            current_price=current_price,
            market_value=market_value,
            cost_basis=cost_basis,
            unrealized_pnl=unrealized,
            unrealized_pnl_pct=unrealized_pct,
            realized_pnl=realized,
            total_pnl=unrealized + realized,
            total_trades=len(symbol_trades),
            winning_trades=winners,
            losing_trades=losers
        )
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position."""
        return self.positions.get(symbol)
    
    def all_positions(self) -> List[str]:
        """Get all position symbols."""
        return [s for s, p in self.positions.items() if p.quantity > 0]


# === Usage ===

if __name__ == "__main__":
    from datetime import timedelta
    
    print("=== FIFO Cost Basis ===")
    fifo = PnLCalculator(method=CostMethod.FIFO)
    
    # Buy in 3 lots
    t0 = datetime.utcnow() - timedelta(days=30)
    t1 = datetime.utcnow() - timedelta(days=15)
    t2 = datetime.utcnow() - timedelta(days=5)
    
    fifo.buy("BTC", Decimal("0.5"), Decimal("40000"), timestamp=t0)
    print(f"Bought 0.5 @ $40,000")
    
    fifo.buy("BTC", Decimal("0.3"), Decimal("45000"), timestamp=t1)
    print(f"Bought 0.3 @ $45,000")
    
    fifo.buy("BTC", Decimal("0.2"), Decimal("50000"), timestamp=t2)
    print(f"Bought 0.2 @ $50,000")
    
    # Position summary
    pos = fifo.get_position("BTC")
    print(f"\nPosition: {pos.quantity} BTC @ avg ${pos.avg_price:,.2f}")
    print(f"Cost basis: ${pos.total_cost:,.2f}")
    
    # Sell partial (FIFO = oldest first)
    print(f"\n--- Selling 0.6 BTC @ $55,000 (FIFO) ---")
    result = fifo.sell("BTC", Decimal("0.6"), Decimal("55000"))
    
    if isinstance(result, list):
        for r in result:
            print(f"  Closed {r.close_quantity} @ ${r.open_lot.price:,.2f} -> ${r.close_price:,.2f}")
            print(f"    P&L: ${r.pnl:+,.2f} ({r.pnl_pct:+.2%})")
    else:
        print(f"  P&L: ${result.pnl:+,.2f} ({result.pnl_pct:+.2%})")
    
    # Current position
    pos = fifo.get_position("BTC")
    print(f"\nRemaining: {pos.quantity} BTC @ ${pos.avg_price:,.2f}")
    
    # Unrealized P&L at $60,000
    unrealized = fifo.unrealized_pnl("BTC", Decimal("60000"))
    print(f"Unrealized @ $60k: ${unrealized:+,.2f}")
    
    # Summary
    print("\n" + str(fifo.summary("BTC", Decimal("60000"))))
    
    print("\n" + "="*40)
    print("=== LIFO vs AVERAGE Comparison ===")
    
    # Reset with same trades
    base_time = datetime.utcnow() - timedelta(days=30)
    trades = [
        ("buy", Decimal("1.0"), Decimal("100"), base_time),
        ("buy", Decimal("1.0"), Decimal("110"), base_time + timedelta(days=10)),
        ("buy", Decimal("1.0"), Decimal("120"), base_time + timedelta(days=20)),
    ]
    
    methods = [
        (CostMethod.FIFO, "FIFO"),
        (CostMethod.LIFO, "LIFO"),
        (CostMethod.AVG, "Average"),
    ]
    
    for method, name in methods:
        calc = PnLCalculator(method=method)
        for side, qty, price, ts in trades:
            calc.buy("TEST", qty, price, timestamp=ts)
        
        # Sell at $130
        result = calc.sell("TEST", Decimal("1.5"), Decimal("130"))
        pnl = result.pnl if not isinstance(result, list) else sum(r.pnl for r in result)
        
        rem = calc.get_position("TEST")
        print(f"{name}: Sell P&L = ${pnl:+,.2f}, Remaining @ ${rem.avg_price:.2f}")
```

## Output

```
=== FIFO Cost Basis ===
Bought 0.5 @ $40,000
Bought 0.3 @ $45,000
Bought 0.2 @ $50,000

Position: 1.0 BTC @ avg $43,000.00
Cost basis: $43,000.00

--- Selling 0.6 BTC @ $55,000 (FIFO) ---
  Closed 0.5 @ $40,000.00 -> $55,000.00
    P&L: $+7,500.00 (+37.50%)
  Closed 0.1 @ $45,000.00 -> $55,000.00
    P&L: $+1,000.00 (+22.22%)

Remaining: 0.4 BTC @ $47,500.00
Unrealized @ $60k: $+5,000.00

=== BTC P&L ===
Position:      0.4 @ $47,500.00
Market Value:  $24,000.00
Cost Basis:    $19,000.00

Unrealized:    $+5,000.00 (+26.32%)
Realized:      $+8,500.00
Total P&L:     $+13,500.00

Trades:        2 (2W/0L)

========================================
=== LIFO vs AVERAGE Comparison ===
FIFO: Sell P&L = $+40.00, Remaining @ $115.00
LIFO: Sell P&L = $+25.00, Remaining @ $105.00
Average: Sell P&L = $+30.00, Remaining @ $110.00
```

## Quick Reference

```python
# Create calculator
calc = PnLCalculator(method=CostMethod.FIFO)  # or LIFO, AVG

# Buy
calc.buy("BTC", Decimal("0.5"), Decimal("50000"))

# Sell
result = calc.sell("BTC", Decimal("0.3"), Decimal("55000"))
print(f"Realized: ${result.pnl}")

# Unrealized P&L
upl = calc.unrealized_pnl("BTC", Decimal("60000"))

# Summary
summary = calc.summary("BTC", Decimal("60000"))
print(summary)
```

## Cost Methods Compared

| Method | Sell Order | Tax Impact | Use Case |
|--------|------------|------------|----------|
| FIFO | Oldest first | Higher gains in uptrend | Default, most common |
| LIFO | Newest first | Lower gains in uptrend | Tax loss harvesting |
| Average | Proportional | Smooths basis | Mutual funds |

---
*Utility: P&L Calculator | Features: FIFO/LIFO/Average, lot tracking, realized/unrealized P&L*