# Quick Reference: Python Trading Patterns
*Ghost Learning | 2026-02-22*

One-page reference for common trading code patterns. Copy-paste ready.

## Decimal Arithmetic (Always Use for Money)

```python
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

# Correct
price = Decimal("50000.50")
size = Decimal("0.001")
total = price * size  # Exact: 50.0005

# Rounding
total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)  # 50.00

# Never use float for money
wrong = 50000.50 * 0.001  # Float errors!
```

## Frozen Dataclass (Immutable, Thread-Safe)

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Position:
    symbol: str
    size: Decimal
    entry: Decimal
    
    @property
    def notional(self) -> Decimal:
        return self.size * self.entry
```

## Percentage Calculations

```python
# Return percentage
return_pct = (exit_price - entry_price) / entry_price * 100

# Risk per trade
risk_amount = account * Decimal("0.02")  # 2% risk

# Position size from risk
position_size = risk_amount / abs(entry - stop)
```

## Async with Timeout

```python
async def fetch_with_timeout(url: str, timeout: float = 10.0):
    async with asyncio.timeout(timeout):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                return await resp.json()
```

## Retry Decorator

```python
@retry(max_attempts=3, base_delay=1.0, exceptions=(ConnectionError,))
async def fetch_data():
    return await api.get()
```

## Structured Logging

```python
import logging
import json

logger = logging.getLogger("trading")
logger.info("Order placed", extra={"order_id": "123", "symbol": "BTCUSD"})
```

## Context Manager for Timing

```python
from contextlib import contextmanager
import time

@contextmanager
def timer(name: str):
    start = time.perf_counter()
    yield
    elapsed = (time.perf_counter() - start) * 1000
    print(f"{name}: {elapsed:.2f}ms")

with timer("fetch_prices"):
    prices = await fetch_all_prices()
```

## Safe Division

```python
def safe_divide(numerator: Decimal, denominator: Decimal, default: Decimal = Decimal("0")) -> Decimal:
    return numerator / denominator if denominator != 0 else default
```

## Win Rate & Profit Factor

```python
def calculate_metrics(trades: list[Decimal]) -> dict:
    winners = [t for t in trades if t > 0]
    losers = [t for t in trades if t < 0]
    
    win_rate = len(winners) / len(trades) * 100 if trades else 0
    gross_profit = sum(winners)
    gross_loss = sum(abs(t) for t in losers)
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    return {"win_rate": win_rate, "profit_factor": profit_factor}
```

## Rate Limiting

```python
import asyncio

class RateLimiter:
    def __init__(self, calls: int, period: float):
        self.calls = calls
        self.period = period
        self.times: list[float] = []
    
    async def acquire(self):
        now = time.time()
        self.times = [t for t in self.times if t > now - self.period]
        if len(self.times) >= self.calls:
            await asyncio.sleep(self.period - (now - self.times[0]))
        self.times.append(time.time())
```

## Common Imports

```python
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
import asyncio
import logging
```

---
*Quick Reference | Essential patterns for trading code*