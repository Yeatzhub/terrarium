# Utility Decorators for Trading Systems
*Ghost Learning | 2026-02-22*

Common decorators for trading bots: timing, retry, caching, validation. Copy-paste ready.

```python
"""
Utility Decorators for Trading Systems
Timing, retry, caching, deprecation, validation.
"""

import asyncio
import functools
import time
import hashlib
import json
from typing import Callable, Any, Optional, TypeVar, ParamSpec
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import OrderedDict


P = ParamSpec("P")
T = TypeVar("T")


# === 1. Timing Decorator ===

def timed(func: Callable[P, T]) -> Callable[P, T]:
    """Measure and log execution time."""
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs) -> T:
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"[{func.__name__}] {elapsed_ms:.2f}ms")
        return result
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs) -> T:
        start = time.perf_counter()
        result = await func(*args, **kwargs)
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"[{func.__name__}] {elapsed_ms:.2f}ms")
        return result
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


@timed
def fetch_prices():
    time.sleep(0.1)
    return {"BTC": 50000}


# === 2. Simple Cache Decorator ===

def cached(ttl_seconds: int = 60, max_size: int = 100):
    """Cache function results with TTL."""
    cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
    
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            # Create cache key
            key = hashlib.md5(
                json.dumps({"args": args, "kwargs": kwargs}, default=str).encode()
            ).hexdigest()
            
            # Check cache
            if key in cache:
                result, timestamp = cache[key]
                if time.time() - timestamp < ttl_seconds:
                    cache.move_to_end(key)  # LRU
                    return result
            
            # Execute and cache
            result = func(*args, **kwargs)
            cache[key] = (result, time.time())
            
            # Evict old
            while len(cache) > max_size:
                cache.popitem(last=False)
            
            return result
        return wrapper
    return decorator


@cached(ttl_seconds=30)
def get_market_price(symbol: str) -> float:
    # Expensive API call
    return 50000.0


# === 3. Retry Decorator (Sync) ===

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
):
    """Retry on failure (sync version)."""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
            raise last_error
        return wrapper
    return decorator


@retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError,))
def fetch_api():
    # Flaky API call
    pass


# === 4. Validation Decorator ===

def validate_inputs(*validators: Callable[[Any], bool], error_msg: str = "Validation failed"):
    """Validate function inputs."""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            for i, validator in enumerate(validators):
                if i < len(args) and not validator(args[i]):
                    raise ValueError(f"{error_msg}: arg {i}")
            result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator


@validate_inputs(
    lambda x: x > 0,  # size must be positive
    lambda x: 0 < x < 1,  # risk_pct must be 0-1
    error_msg="Invalid parameters"
)
def calculate_position(size: float, risk_pct: float) -> float:
    return size * risk_pct


# === 5. Deprecated Decorator ===

def deprecated(replacement: Optional[str] = None, version: str = ""):
    """Mark function as deprecated."""
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            msg = f"{func.__name__} is deprecated"
            if version:
                msg += f" (since {version})"
            if replacement:
                msg += f". Use {replacement} instead"
            print(f"⚠️  {msg}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


@deprecated(replacement="new_fetch_prices", version="2.0")
def old_fetch_prices():
    return {"BTC": 50000}


# === 6. Singleton Decorator ===

def singleton(cls):
    """Make a class a singleton."""
    instances = {}
    
    @functools.wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return get_instance


@singleton
class ExchangeClient:
    def __init__(self, api_key: str):
        self.api_key = api_key


# === 7. Rate Limit Decorator ===

def rate_limit(calls_per_second: float = 10):
    """Simple rate limiting."""
    min_interval = 1.0 / calls_per_second
    last_call = [0.0]
    
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            elapsed = time.time() - last_call[0]
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
            last_call[0] = time.time()
            return func(*args, **kwargs)
        return wrapper
    return decorator


@rate_limit(calls_per_second=5)
def call_api():
    return "response"


# === 8. Log Decorator ===

def logged(level: str = "INFO"):
    """Log function calls."""
    import logging
    logger = logging.getLogger("trading")
    
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            logger.log(getattr(logging, level), f"Calling {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.log(getattr(logging, level), f"{func.__name__} returned")
                return result
            except Exception as e:
                logger.error(f"{func.__name__} failed: {e}")
                raise
        return wrapper
    return decorator


# === 9. Memoize (One-Liner) ===

def memoize(func: Callable[P, T]) -> Callable[P, T]:
    """Simple memoization without TTL."""
    cache = {}
    
    @functools.wraps(func)
    def wrapper(*args):
        if args not in cache:
            cache[args] = func(*args)
        return cache[args]
    return wrapper


@memoize
def fibonacci(n: int) -> int:
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


# === USAGE ===

if __name__ == "__main__":
    # Timing
    prices = fetch_prices()  # [fetch_prices] 100.23ms
    
    # Caching
    print(get_market_price("BTC"))  # API call
    print(get_market_price("BTC"))  # Cached
    
    # Retry
    # @retry handles flaky APIs
    
    # Validation
    # calculate_position(-1, 0.02)  # Raises ValueError
    
    # Rate limiting
    for _ in range(10):
        call_api()  # Limited to 5/second
```

## Decorator Summary

| Decorator | Purpose | Example |
|-----------|---------|---------|
| `@timed` | Measure execution time | Performance monitoring |
| `@cached(ttl=60)` | Cache with TTL | API responses |
| `@retry(n=3)` | Retry on failure | Network calls |
| `@validate_inputs(...)` | Validate parameters | User input |
| `@deprecated(...)` | Mark deprecated | API migrations |
| `@singleton` | Single instance | Exchange client |
| `@rate_limit(n)` | Limit call rate | API quotas |
| `@logged` | Log calls | Debugging |
| `@memoize` | Cache forever | Expensive calculations |

## Quick Copy

```python
# Time a function
@timed
def expensive_calc(): ...

# Cache for 30 seconds
@cached(ttl_seconds=30)
def fetch_price(symbol): ...

# Retry 3 times
@retry(max_attempts=3, exceptions=(ConnectionError,))
def call_api(): ...

# Validate inputs
@validate_inputs(lambda x: x > 0)
def trade(size): ...

# Singleton class
@singleton
class ExchangeClient: ...
```

---
*Pattern: Utility Decorators | 9 common decorators for trading systems*