# Python Structural Pattern Matching (match/case)

**Ghost Learning | 2026-02-18 | 15 min read**

Python 3.10+ `match/case` is a game-changer for clean, readable data parsing. Here's the practical guide.

---

## 1. Basic Matching

```python
def handle_command(command: str) -> str:
    match command.lower().split():
        case ["buy", symbol, amount]:
            return f"Buying {amount} of {symbol}"
        case ["sell", symbol, amount]:
            return f"Selling {amount} of {symbol}"
        case ["status"]:
            return "System operational"
        case _:
            return f"Unknown command: {command}"

# Usage
print(handle_command("buy BTC 0.5"))   # Buying 0.5 of BTC
print(handle_command("status"))       # System operational
```

---

## 2. Dictionary Matching (JSON/API Parsing)

```python
def parse_exchange_data(data: dict) -> dict:
    """Parse various exchange message formats."""
    match data:
        case {"type": "trade", "price": float(p), "size": s, "symbol": sym}:
            return {"event": "trade", "symbol": sym, "price": p, "size": s}
        
        case {"type": "orderbook", "bids": list(bids), "asks": list(asks)}:
            return {"event": "snapshot", "bids": bids[:5], "asks": asks[:5]}
        
        case {"type": "error", "message": msg, **rest}:
            return {"event": "error", "message": msg, "details": rest}
        
        case _:
            return {"event": "unknown", "raw": data}

# Usage
messages = [
    {"type": "trade", "price": 50000.0, "size": 1.5, "symbol": "BTC/USD"},
    {"type": "orderbook", "bids": [[50000, 1], [49999, 2]], "asks": [[50001, 1]]},
    {"type": "error", "message": "Rate limit", "code": 429},
]

for msg in messages:
    print(parse_exchange_data(msg))
```

---

## 3. Class Instance Matching (Dataclasses)

```python
from dataclasses import dataclass
from typing import Union

@dataclass
class MarketOrder:
    symbol: str
    size: float

@dataclass 
class LimitOrder:
    symbol: str
    size: float
    price: float

@dataclass
class StopLossOrder:
    symbol: str
    size: float
    trigger: float

Order = Union[MarketOrder, LimitOrder, StopLossOrder]

def calculate_fees(order: Order) -> float:
    """Calculate fees based on order type."""
    match order:
        case MarketOrder(sym, size):
            return size * 0.005  # 0.5% market fee
        
        case LimitOrder(sym, size, price) if size * price > 10000:
            return size * price * 0.001  # 0.1% for large trades
        
        case LimitOrder(sym, size, price):
            return 0.0  # Free for small limit orders
        
        case StopLossOrder(sym, size, trigger):
            return size * trigger * 0.003  # 0.3%

# Usage
orders = [
    MarketOrder("BTC", 1.0),
    LimitOrder("ETH", 2.0, 3000.0),
    LimitOrder("BTC", 5.0, 50000.0),  # Large trade
    StopLossOrder("BTC", 1.0, 45000.0),
]

for order in orders:
    print(f"{order.__class__.__name__}: ${calculate_fees(order):.2f}")
```

---

## 4. Guard Clauses (Conditional Matching)

```python
def risk_check(position: dict) -> str:
    """Check position risk levels."""
    match position:
        case {"exposure": float(e), "leverage": float(l)} if e > 100000 and l > 5:
            return "CRITICAL: High exposure + high leverage"
        
        case {"exposure": float(e)} if e > 100000:
            return "WARNING: High exposure"
        
        case {"leverage": float(l)} if l > 10:
            return "WARNING: Extreme leverage"
        
        case {"exposure": _, "leverage": _}:
            return "OK: Within risk limits"
        
        case _:
            return "ERROR: Invalid position data"

# Usage
positions = [
    {"exposure": 200000.0, "leverage": 8.0},
    {"exposure": 50000.0, "leverage": 15.0},
    {"exposure": 200000.0, "leverage": 3.0},
]

for pos in positions:
    print(risk_check(pos))
```

---

## 5. Nested Structure Matching (Real-World)

```python
def parse_ws_message(raw: dict) -> dict | None:
    """Parse WebSocket messages from various exchanges."""
    match raw:
        # Binance format
        case {
            "e": "aggTrade",
            "s": symbol,
            "p": str(price),
            "q": str(qty),
            "T": timestamp,
        }:
            return {
                "exchange": "binance",
                "symbol": symbol,
                "price": float(price),
                "size": float(qty),
                "time": timestamp,
            }
        
        # Coinbase format
        case {
            "type": "match",
            "product_id": symbol,
            "price": str(price),
            "size": str(qty),
            "time": ts,
        }:
            return {
                "exchange": "coinbase",
                "symbol": symbol.replace("-", "/"),
                "price": float(price),
                "size": float(qty),
                "time": ts,
            }
        
        # Heartbeat - ignore
        case {"type": "heartbeat"} | {"e": "ping"}:
            return None
        
        # Catch-all
        case _:
            print(f"Unrecognized format: {raw.keys()}")
            return None

# Usage
binance_msg = {
    "e": "aggTrade",
    "s": "BTCUSDT",
    "p": "50000.00",
    "q": "1.50000000",
    "T": 123456789,
}

print(parse_ws_message(binance_msg))
# {'exchange': 'binance', 'symbol': 'BTCUSDT', 'price': 50000.0, 'size': 1.5, 'time': 123456789}
```

---

## Key Patterns Cheat Sheet

| Pattern | Meaning |
|---------|---------|
| `case x:` | Bind any value to `x` |
| `case "str":` | Match literal string |
| `case [a, b]:` | Match sequence of length 2, bind elements |
| `case [a, *rest]:` | Match sequence, capture tail |
| `case {"key": val}:` | Match dict with key, bind value |
| `case {"key": val, **rest}:` | Match + capture remaining keys |
| `case Class(a, b):` | Match dataclass/instance attributes |
| `case x if x > 10:` | Match with guard condition |
| `case _:` | Default/wildcard |

---

## When to Use `match/case` vs Legacy

| Use `match/case` | Use `if/elif` |
|------------------|---------------|
| Parsing JSON/API responses | Simple boolean conditions |
| Complex nested structures | 2-3 simple options |
| Multiple dataclass types | Performance-critical code (match slightly slower) |
| Command/action dispatch | Need fall-through (match doesn't have `break`) |

---

## Quick Takeaway

> **Pattern matching reduces 15-line `if/elif` chains to 5-line readable expressions.** 
> Perfect for: API parsers, message handlers, state machines, command processors.

**Next:** Try replacing one `if/elif` chain in your codebase with `match/case`. The clarity gain is immediate.
