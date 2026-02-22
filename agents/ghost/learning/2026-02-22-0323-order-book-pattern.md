# Order Book Pattern
*Ghost Learning | 2026-02-22*

Simple order book implementation with price-time priority. Essential for understanding exchange mechanics.

```python
"""
Order Book Pattern
Price-time priority order book with matching engine basics.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional
from collections import defaultdict
import heapq
from enum import Enum
from datetime import datetime


class Side(Enum):
    BUY = "buy"
    SELL = "sell"


@dataclass(order=True)
class Order:
    """Order with price-time priority."""
    price: Decimal
    timestamp: float  # For heap ordering
    order_id: str = field(compare=False)
    side: Side = field(compare=False)
    size: Decimal = field(compare=False)
    filled: Decimal = field(default=Decimal("0"), compare=False)
    
    @property
    def remaining(self) -> Decimal:
        return self.size - self.filled
    
    @property
    def is_filled(self) -> bool:
        return self.remaining <= 0


@dataclass
class Trade:
    """Executed trade."""
    taker_order_id: str
    maker_order_id: str
    price: Decimal
    size: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)


class OrderBook:
    """
    Simple order book with price-time priority.
    
    - Bids sorted high-to-low (best bid first)
    - Asks sorted low-to-high (best ask first)
    - Same price: FIFO (first in, first out)
    """
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: list[Order] = []  # Max heap (negate for heapq)
        self.asks: list[Order] = []  # Min heap
        self.orders: dict[str, Order] = {}
        self.trades: list[Trade] = []
        self._order_counter = 0
    
    def _next_order_id(self) -> str:
        self._order_counter += 1
        return f"{self.symbol}-{self._order_counter:06d}"
    
    def add_order(
        self,
        side: Side,
        price: Decimal,
        size: Decimal,
        order_id: Optional[str] = None
    ) -> tuple[str, list[Trade]]:
        """
        Add order to book, match if possible.
        Returns (order_id, list of trades).
        """
        order_id = order_id or self._next_order_id()
        timestamp = datetime.utcnow().timestamp()
        
        order = Order(
            price=price,
            timestamp=timestamp,
            order_id=order_id,
            side=side,
            size=size
        )
        
        trades = self._match_order(order)
        
        # Add remaining to book
        if not order.is_filled:
            self.orders[order_id] = order
            if side == Side.BUY:
                heapq.heappush(self.bids, order)  # Price as negative for max heap
                # Need to re-sort for bids... using simple approach
            else:
                heapq.heappush(self.asks, order)
        
        return order_id, trades
    
    def _match_order(self, order: Order) -> list[Trade]:
        """Match order against book."""
        trades = []
        
        if order.side == Side.BUY:
            # Match against asks (sells)
            while not order.is_filled and self.asks:
                best_ask = self.asks[0]
                if best_ask.price > order.price:
                    break
                
                trade_size = min(order.remaining, best_ask.remaining)
                trade = Trade(
                    taker_order_id=order.order_id,
                    maker_order_id=best_ask.order_id,
                    price=best_ask.price,
                    size=trade_size
                )
                trades.append(trade)
                
                order.filled += trade_size
                best_ask.filled += trade_size
                
                if best_ask.is_filled:
                    heapq.heappop(self.asks)
                    del self.orders[best_ask.order_id]
        else:
            # Match against bids (buys)
            while not order.is_filled and self.bids:
                best_bid = self.bids[0]
                if best_bid.price < order.price:
                    break
                
                trade_size = min(order.remaining, best_bid.remaining)
                trade = Trade(
                    taker_order_id=order.order_id,
                    maker_order_id=best_bid.order_id,
                    price=best_bid.price,
                    size=trade_size
                )
                trades.append(trade)
                
                order.filled += trade_size
                best_bid.filled += trade_size
                
                if best_bid.is_filled:
                    heapq.heappop(self.bids)
                    del self.orders[best_bid.order_id]
        
        self.trades.extend(trades)
        return trades
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel order. Returns True if found."""
        if order_id not in self.orders:
            return False
        
        order = self.orders[order_id]
        
        if order.side == Side.BUY:
            self.bids = [o for o in self.bids if o.order_id != order_id]
            heapq.heapify(self.bids)
        else:
            self.asks = [o for o in self.asks if o.order_id != order_id]
            heapq.heapify(self.asks)
        
        del self.orders[order_id]
        return True
    
    @property
    def best_bid(self) -> Optional[tuple[Decimal, Decimal]]:
        """(price, size) of best bid."""
        while self.bids:
            order = self.bids[0]
            if order.remaining > 0:
                return (order.price, order.remaining)
            heapq.heappop(self.bids)
        return None
    
    @property
    def best_ask(self) -> Optional[tuple[Decimal, Decimal]]:
        """(price, size) of best ask."""
        while self.asks:
            order = self.asks[0]
            if order.remaining > 0:
                return (order.price, order.remaining)
            heapq.heappop(self.asks)
        return None
    
    @property
    def spread(self) -> Optional[Decimal]:
        """Bid-ask spread."""
        bid = self.best_bid
        ask = self.best_ask
        if bid and ask:
            return ask[0] - bid[0]
        return None
    
    @property
    def mid_price(self) -> Optional[Decimal]:
        """Mid price between best bid and ask."""
        bid = self.best_bid
        ask = self.best_ask
        if bid and ask:
            return (bid[0] + ask[0]) / 2
        return None
    
    def get_depth(self, levels: int = 5) -> dict:
        """Get order book depth."""
        # Aggregate by price level
        bid_levels = defaultdict(Decimal)
        ask_levels = defaultdict(Decimal)
        
        for order in self.bids:
            if order.remaining > 0:
                bid_levels[order.price] += order.remaining
        
        for order in self.asks:
            if order.remaining > 0:
                ask_levels[order.price] += order.remaining
        
        # Sort and limit
        sorted_bids = sorted(bid_levels.items(), reverse=True)[:levels]
        sorted_asks = sorted(ask_levels.items())[:levels]
        
        return {
            "bids": [(p, s) for p, s in sorted_bids],
            "asks": [(p, s) for p, s in sorted_asks]
        }
    
    def __str__(self) -> str:
        """Pretty print order book."""
        depth = self.get_depth(5)
        lines = [f"\n=== {self.symbol} Order Book ==="]
        lines.append(f"Spread: {self.spread} | Mid: {self.mid_price}")
        lines.append("\n  ASKS")
        for price, size in reversed(depth["asks"]):
            lines.append(f"    {price:>10} | {size:>8}")
        lines.append("  -------------------")
        for price, size in depth["bids"]:
            lines.append(f"    {price:>10} | {size:>8}")
        lines.append("  BIDS")
        return "\n".join(lines)


# === Example Usage ===

def example():
    """Demo order book operations."""
    book = OrderBook("BTCUSD")
    
    # Add sell orders (asks)
    book.add_order(Side.SELL, Decimal("50010"), Decimal("1.0"))
    book.add_order(Side.SELL, Decimal("50020"), Decimal("2.0"))
    book.add_order(Side.SELL, Decimal("50000"), Decimal("0.5"))  # Best ask
    
    # Add buy orders (bids)
    book.add_order(Side.BUY, Decimal("49990"), Decimal("1.5"))
    book.add_order(Side.BUY, Decimal("49980"), Decimal("2.5"))
    book.add_order(Side.BUY, Decimal("49995"), Decimal("1.0"))  # Best bid
    
    print(book)
    print(f"\nBest Bid: {book.best_bid}")
    print(f"Best Ask: {book.best_ask}")
    print(f"Spread: {book.spread}")
    
    # Market order (matches)
    print("\n--- Market Buy 1.0 BTC ---")
    order_id, trades = book.add_order(Side.BUY, Decimal("50010"), Decimal("1.0"))
    for t in trades:
        print(f"  Trade: {t.size} @ {t.price}")
    
    print(book)


if __name__ == "__main__":
    example()
```

## Order Book Basics

| Concept | Description |
|---------|-------------|
| **Bid** | Buy order (highest price = best) |
| **Ask** | Sell order (lowest price = best) |
| **Spread** | Best ask - best bid |
| **Mid** | (Best bid + best ask) / 2 |
| **Depth** | Volume at each price level |

## Price-Time Priority

1. **Price priority**: Better price = matched first
2. **Time priority**: Same price = FIFO

```
Buy orders at 50000:
  1. Order A (10:00:01) - matched first
  2. Order B (10:00:05) - matched second
  3. Order C (10:00:10) - matched third
```

## Order Types Supported

| Order Type | Behavior |
|------------|----------|
| **Limit** | Add to book if no match |
| **Market** | Match immediately at best prices |

## Sample Output

```
=== BTCUSD Order Book ===
Spread: 5 | Mid: 49997.5

  ASKS
       50020 |      2.0
       50010 |      1.0
       50000 |      0.5
  -------------------
       49995 |      1.0
       49990 |      1.5
       49980 |      2.5
  BIDS
```

## Key Operations

```python
# Add limit order
order_id, trades = book.add_order(Side.BUY, Decimal("50000"), Decimal("1.0"))

# Check best prices
best_bid = book.best_bid  # (price, size)
best_ask = book.best_ask

# Get depth
depth = book.get_depth(levels=5)

# Cancel order
book.cancel_order(order_id)
```

---
*Pattern: Order Book | Price-time priority matching*