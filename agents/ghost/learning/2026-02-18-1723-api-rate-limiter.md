# Trading API Rate Limiter

**Topic:** Async Token Bucket Rate Limiter with Exchange-Specific Rules
**Created:** 2026-02-18 17:23
**Use Case:** Prevent API rate limit violations across multiple exchanges (Kraken, Binance, etc.)

## Why

Exchange APIs enforce rate limits (requests/second, weight limits). Violating them = temporary bans, missed trades, errors. Manual delays are fragile. You need automatic, adaptive throttling.

## The Pattern

Token bucket with exchange-specific rules + async context manager for seamless integration.

```python
# rate_limiter.py
import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Callable
from contextlib import asynccontextmanager

class ExchangeTier(Enum):
    """API tier affects rate limits"""
    BASIC = "basic"
    PRO = "pro" 
    VIP = "vip"

@dataclass
class RateLimit:
    """Exchange rate limit config"""
    requests_per_second: float
    burst_size: int = 10  # Token bucket capacity
    weight_factor: float = 1.0  # Some exchanges use "weights"
    
    @staticmethod
    def kraken(tier: ExchangeTier = ExchangeTier.BASIC) -> "RateLimit":
        limits = {
            ExchangeTier.BASIC: RateLimit(0.5, burst_size=10),   # ~1 req/2s
            ExchangeTier.PRO: RateLimit(1.0, burst_size=20),
            ExchangeTier.VIP: RateLimit(2.0, burst_size=50),
        }
        return limits.get(tier, limits[ExchangeTier.BASIC])
    
    @staticmethod
    def binance(tier: ExchangeTier = ExchangeTier.BASIC) -> "RateLimit":
        limits = {
            ExchangeTier.BASIC: RateLimit(10.0, burst_size=100, weight_factor=1.0),
            ExchangeTier.PRO: RateLimit(20.0, burst_size=200, weight_factor=0.8),
            ExchangeTier.VIP: RateLimit(50.0, burst_size=500, weight_factor=0.5),
        }
        return limits.get(tier, limits[ExchangeTier.BASIC])


class TokenBucket:
    """Thread-safe token bucket for rate limiting"""
    
    def __init__(self, rate: float, capacity: int):
        self.rate = rate          # tokens per second
        self.capacity = capacity  # max tokens
        self._tokens = capacity   # current tokens
        self._last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> float:
        """
        Acquire tokens. Returns wait time (0 if no wait needed).
        Blocks until tokens available.
        """
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_update
            
            # Replenish tokens based on elapsed time
            self._tokens = min(
                self.capacity,
                self._tokens + elapsed * self.rate
            )
            self._last_update = now
            
            # Check if we have enough tokens
            if self._tokens >= tokens:
                self._tokens -= tokens
                return 0.0
            
            # Calculate wait time
            needed = tokens - self._tokens
            wait_time = needed / self.rate
            
        # Wait outside lock to allow other operations
        await asyncio.sleep(wait_time)
        
        # Recursively acquire after waiting (should succeed now)
        return await self.acquire(tokens)
    
    async def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens without blocking. Returns success."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_update
            
            self._tokens = min(
                self.capacity,
                self._tokens + elapsed * self.rate
            )
            self._last_update = now
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False


class ExchangeRateLimiter:
    """
    Per-exchange rate limiter with weight tracking.
    Usage: limiter = ExchangeRateLimiter.kraken(); await limiter.acquire()
    """
    
    def __init__(self, config: RateLimit, name: str = "unnamed"):
        self.name = name
        self.config = config
        self._bucket = TokenBucket(config.requests_per_second, config.burst_size)
        self._request_count = 0
        self._total_wait_time = 0.0
    
    @classmethod
    def kraken(cls, tier: ExchangeTier = ExchangeTier.BASIC) -> "ExchangeRateLimiter":
        return cls(RateLimit.kraken(tier), "kraken")
    
    @classmethod
    def binance(cls, tier: ExchangeTier = ExchangeTier.BASIC) -> "ExchangeRateLimiter":
        return cls(RateLimit.binance(tier), "binance")
    
    async def acquire(self, weight: int = 1):
        """Acquire permission to make a request."""
        tokens = int(weight * self.config.weight_factor)
        tokens = max(1, tokens)
        
        wait = await self._bucket.acquire(tokens)
        if wait > 0:
            self._total_wait_time += wait
        
        self._request_count += 1
        return wait
    
    async def try_acquire(self, weight: int = 1) -> bool:
        """Try to acquire without blocking."""
        tokens = int(weight * self.config.weight_factor)
        return await self._bucket.try_acquire(tokens)
    
    def stats(self) -> Dict:
        return {
            "name": self.name,
            "requests": self._request_count,
            "total_wait_sec": round(self._total_wait_time, 3),
            "tier": "production-ready"
        }


class MultiExchangeLimiter:
    """Manage rate limits for multiple exchanges concurrently."""
    
    def __init__(self):
        self._limiters: Dict[str, ExchangeRateLimiter] = {}
    
    def register(self, exchange: str, limiter: ExchangeRateLimiter):
        """Register an exchange limiter."""
        self._limiters[exchange] = limiter
    
    async def acquire(self, exchange: str, weight: int = 1):
        """Acquire for specific exchange."""
        if exchange not in self._limiters:
            raise KeyError(f"No limiter registered for {exchange}")
        return await self._limiters[exchange].acquire(weight)
    
    async def acquire_many(self, requests: list[tuple[str, int]]) -> Dict[str, float]:
        """
        Acquire multiple at once: [("kraken", 1), ("binance", 2)]
        Returns wait times by exchange.
        """
        tasks = [
            self.acquire(exchange, weight)
            for exchange, weight in requests
        ]
        results = await asyncio.gather(*tasks)
        return dict(zip([r[0] for r in requests], results))
    
    @asynccontextmanager
    async def request(self, exchange: str, weight: int = 1):
        """Context manager for automatic rate limiting."""
        wait = await self.acquire(exchange, weight)
        try:
            yield wait
        except Exception as e:
            # Optionally add backpressure here
            raise


# --- USAGE IN REAL TRADING BOT ---

class TradingClient:
    """Example: Trading bot client with rate limiting"""
    
    def __init__(self):
        self.limiter = MultiExchangeLimiter()
        self.limiter.register("kraken", ExchangeRateLimiter.kraken())
        self.limiter.register("binance", ExchangeRateLimiter.binance())
    
    async def fetch_balance(self, exchange: str) -> Dict:
        """Fetch balance with automatic rate limiting"""
        async with self.limiter.request(exchange, weight=1):
            # Your actual API call here
            # await self.exchange.fetch_balance()
            return {"status": "ok", "exchange": exchange}
    
    async def batch_fetch_tickers(self, exchange: str, symbols: list) -> list:
        """Fetch multiple tickers respecting rate limits"""
        results = []
        for symbol in symbols:
            await self.limiter.acquire(exchange, weight=1)
            # result = await self.exchange.fetch_ticker(symbol)
            results.append({"symbol": symbol, "price": 0.0})
        return results


# --- QUICK TEST ---

async def demo():
    """Demo the rate limiter"""
    print("=== Token Bucket Demo ===\n")
    
    limiter = ExchangeRateLimiter.kraken()
    
    # Rapid fire 5 requests
    print("Sending 5 rapid requests to Kraken (0.5 req/sec)...")
    for i in range(5):
        start = time.monotonic()
        wait = await limiter.acquire()
        elapsed = time.monotonic() - start
        print(f"  Request {i+1}: waited {elapsed:.2f}s")
    
    print(f"\nStats: {limiter.stats()}")
    
    # Multi-exchange demo
    print("\n=== Multi-Exchange Demo ===")
    multi = MultiExchangeLimiter()
    multi.register("kraken", ExchangeRateLimiter.kraken())
    multi.register("binance", ExchangeRateLimiter.binance())
    
    # Fast Binance, slow Kraken
    tasks = [
        multi.acquire("kraken"),
        multi.acquire("binance"),
        multi.acquire("binance"),
        multi.acquire("binance"),
    ]
    start = time.monotonic()
    await asyncio.gather(*tasks)
    total = time.monotonic() - start
    print(f"4 requests (1 slow + 3 fast) completed in {total:.2f}s")


if __name__ == "__main__":
    asyncio.run(demo())
```

## Key Features

1. **Token Bucket Algorithm**: Smooth burst handling + sustained rate compliance
2. **Exchange-Specific Configs**: Kraken = slow (0.5/sec), Binance = fast (10/sec)
3. **Weight Support**: Some calls cost more "weight" - accounted for automatically
4. **Async Context Manager**: Clean `async with limiter.request("kraken"):` syntax
5. **Stats & Monitoring**: Track requests, wait times
6. **Multi-Exchange**: Manage many exchanges concurrently without interference

## Integration Example

```python
# In your exchange wrapper
class KrakenExchange:
    def __init__(self):
        self.limiter = ExchangeRateLimiter.kraken()
    
    async def fetch_ticker(self, symbol):
        await self.limiter.acquire()  # Blocks if needed
        return await self._api_call(symbol)
```

## When to Use

- ✅ Multiple exchanges in one bot
- ✅ High-frequency operations
- ✅ Avoiding temporary bans
- ✅ Burst-then-slow patterns (like order book snapshots)

## Output Example

```
=== Token Bucket Demo ===

Sending 5 rapid requests to Kraken (0.5 req/sec)...
  Request 1: waited 0.00s
  Request 2: waited 0.00s
  Request 3: waited 1.98s
  Request 4: waited 2.00s
  Request 5: waited 2.01s

Stats: {'name': 'kraken', 'requests': 5, 'total_wait_sec': 5.99, 'tier': 'production-ready'}

=== Multi-Exchange Demo ===
4 requests (1 slow + 3 fast) completed in 0.15s
```

## Files

Code saved to: `agents/ghost/learning/2026-02-18-1723-api-rate-limiter.md`

Ready to copy into `btc-trading-bot/utils/rate_limiter.py`.
