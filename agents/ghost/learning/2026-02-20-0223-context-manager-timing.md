# Context Managers for Timing & Resource Management

**Pattern:** `with` statement for automatic setup, teardown, and timing  
**Use Case:** Profiling, resource cleanup, temporary state changes

## The Pattern

```python
"""
Context Managers for Timing, Profiling, and Resource Management
Clean setup/teardown with automatic timing and error handling.
"""

import time
import functools
from contextlib import contextmanager
from typing import Generator, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TimingResult:
    """Result from timing context manager."""
    elapsed_ms: float
    start_time: datetime
    end_time: datetime
    success: bool
    error: Optional[str] = None


@contextmanager
def timed_execution(label: str = "", threshold_ms: float = 100) -> Generator[None, None, TimingResult]:
    """
    Context manager that automatically times execution.
    
    Usage:
        with timed_execution("API call") as timing:
            result = api.fetch()
        print(f"Took {timing.elapsed_ms}ms")
    """
    start = time.perf_counter()
    start_dt = datetime.now()
    result = TimingResult(
        elapsed_ms=0,
        start_time=start_dt,
        end_time=start_dt,
        success=True
    )
    
    try:
        yield result
    except Exception as e:
        result.success = False
        result.error = str(e)
        raise
    finally:
        end = time.perf_counter()
        result.elapsed_ms = (end - start) * 1000
        result.end_time = datetime.now()
        
        # Warn if slow
        if result.elapsed_ms > threshold_ms:
            print(f"⚠️  {label}: {result.elapsed_ms:.0f}ms (threshold: {threshold_ms}ms)")


@contextmanager
def temporary_state(obj, **kwargs) -> Generator[None, None, None]:
    """
    Temporarily change object attributes.
    
    Usage:
        with temporary_state(strategy, mode="aggressive"):
            strategy.execute()  # Uses aggressive mode
        # Automatically restored to previous mode
    """
    original = {k: getattr(obj, k) for k in kwargs}
    
    try:
        for k, v in kwargs.items():
            setattr(obj, k, v)
        yield
    finally:
        for k, v in original.items():
            setattr(obj, k, v)


@contextmanager
def logged_execution(logger: Optional[Callable] = None, label: str = ""):
    """
    Log entry and exit from code block.
    
    Usage:
        with logged_execution(print, "Processing"):
            process_data()
    """
    logger = logger or print
    logger(f"▶️  Enter: {label or 'block'}")
    try:
        yield
        logger(f"✅ Exit:  {label or 'block'}")
    except Exception as e:
        logger(f"❌ Error: {label or 'block'} - {e}")
        raise


@contextmanager
def retry_on_error(
    on_error: Callable[[Exception], None] = None,
    max_retries: int = 0
) -> Generator[None, None, None]:
    """
    Retry context on exception.
    
    Usage:
        with retry_on_error(max_retries=3):
            risky_operation()
    """
    for attempt in range(max_retries + 1):
        try:
            yield
            return
        except Exception as e:
            if attempt == max_retries:
                raise
            if on_error:
                on_error(e)
            time.sleep(0.1 * (2 ** attempt))  # Exponential backoff


@contextmanager
def rate_limited(rate_per_second: float = 10.0):
    """
    Limit execution rate.
    
    Usage:
        for i in range(100):
            with rate_limited(10):  # Max 10/sec
                process_item(i)
    """
    min_interval = 1.0 / rate_per_second
    start = time.perf_counter()
    yield
    elapsed = time.perf_counter() - start
    if elapsed < min_interval:
        time.sleep(min_interval - elapsed)


# === Decorator version ===

def timed(func: Callable) -> Callable:
    """Decorator to time function execution."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            print(f"⏱️  {func.__name__}: {elapsed:.2f}ms")
    return wrapper


def retry(max_retries: int = 3, backoff: float = 1.0):
    """Decorator for retry logic."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        raise
                    time.sleep(backoff * (2 ** attempt))
            return None
        return wrapper
    return decorator


def memoize(max_size: int = 128):
    """Simple memoization decorator."""
    def decorator(func: Callable) -> Callable:
        cache = {}
        @functools.wraps(func)
        def wrapper(*args):
            if args in cache:
                return cache[args]
            result = func(*args)
            if len(cache) >= max_size:
                cache.pop(next(iter(cache)))
            cache[args] = result
            return result
        return wrapper
    return decorator


# === Practical Examples ===

class TradingStrategy:
    def __init__(self):
        self.mode = "normal"
        self.risk_level = 1.0
    
    def execute(self):
        with timed_execution("Strategy execution", threshold_ms=500):
            # Simulate work
            time.sleep(0.1)
            return {"trades": 5}


class APIClient:
    def __init__(self):
        self.rate_limit_remaining = 100
    
    @timed
    @retry(max_retries=3, backoff=0.5)
    def fetch_data(self, symbol: str) -> dict:
        """Fetch with automatic timing, retries, and rate limiting."""
        with rate_limited(rate_per_second=10):
            # Simulate API call
            if random.random() < 0.2:  # 20% failure rate
                raise ConnectionError("API timeout")
            return {"symbol": symbol, "price": 100 + random.random()}


# === Demo ===

if __name__ == "__main__":
    import random
    
    print("=" * 60)
    print("Context Manager Patterns Demo")
    print("=" * 60)
    
    # 1. Simple timing
    print("\n1. Timed Execution")
    with timed_execution("Heavy computation", threshold_ms=50):
        time.sleep(0.1)  # 100ms
    
    # 2. Temporary state
    print("\n2. Temporary State Change")
    strategy = TradingStrategy()
    print(f"   Before: mode={strategy.mode}, risk={strategy.risk_level}")
    
    with temporary_state(strategy, mode="aggressive", risk_level=2.0):
        print(f"   During: mode={strategy.mode}, risk={strategy.risk_level}")
    
    print(f"   After:  mode={strategy.mode}, risk={strategy.risk_level}")
    
    # 3. Rate limiting
    print("\n3. Rate Limiting (5/sec)")
    for i in range(3):
        start = time.perf_counter()
        with rate_limited(5):
            pass
        elapsed = time.perf_counter() - start
        print(f"   Iteration {i+1}: {elapsed*1000:.0f}ms (min 200ms)")
    
    # 4. Decorated function
    print("\n4. Decorated Function")
    client = APIClient()
    try:
        data = client.fetch_data("AAPL")
        print(f"   Result: {data}")
    except Exception as e:
        print(f"   Failed after retries: {e}")
    
    # 5. Retry context
    print("\n5. Retry Context")
    attempt = [0]
    def on_error(e):
        attempt[0] += 1
        print(f"   Retry attempt {attempt[0]}: {e}")
    
    try:
        with retry_on_error(on_error=on_error, max_retries=2):
            if random.random() < 0.5:
                raise RuntimeError("Transient error")
        print("   Success on retry")
    except RuntimeError:
        print("   All retries exhausted")
    
    # 6. Memoization
    print("\n6. Memoization")
    
    @memoize(max_size=10)
    def slow_calc(x):
        time.sleep(0.01)
        return x * x
    
    start = time.perf_counter()
    r1 = slow_calc(5)
    elapsed1 = time.perf_counter() - start
    
    start = time.perf_counter()
    r2 = slow_calc(5)  # Cached
    elapsed2 = time.perf_counter() - start
    
    print(f"   First call:  {elapsed1*1000:.2f}ms (computed {r1})")
    print(f"   Cached call: {elapsed2*1000:.2f}ms (returned {r2})")
    
    print("\n" + "=" * 60)


## Context Manager Quick Reference

| Pattern | Use | Example |
|--------|-----|---------|
| `timed_execution` | Performance profiling | `with timed_execution("DB query"):` |
| `temporary_state` | Temporarily change settings | `with temporary_state(obj, mode="test"):` |
| `logged_execution` | Debug entry/exit | `with logged_execution(print, "Section"):` |
| `retry_on_error` | Auto-retry on failure | `with retry_on_error(max_retries=3):` |
| `rate_limited` | Control throughput | `with rate_limited(10):` # 10/sec |

## Decorator Quick Reference

| Decorator | Use | Example |
|-----------|-----|---------|
| `@timed` | Auto-time function | `@timed def process(): ...` |
| `@retry(n)` | Auto-retry failures | `@retry(3) def api_call(): ...` |
| `@memoize(n)` | Cache results | `@memoize(100) def calc(x): ...` |

## Combining Patterns

```python
@timed
@retry(max_retries=3)
def fetch_with_backoff(id: int):
    with rate_limited(10):  # 10/sec max
        with logged_execution(logger, f"fetch_{id}"):
            return api.fetch(id)
```

## Why Context Managers

- ✅ **Automatic cleanup** - No forgotten teardown
- ✅ **Exception safety** - Cleanup runs even on error
- ✅ **Readability** - Clear scope of temporary changes
- ✅ **Timing** - Built-in performance profiling

---

**Created by Ghost 👻 | Feb 20, 2026 | 10-min learning sprint**  
*Pattern: Use context managers for any setup/teardown. They're cleaner, safer, and more readable.*
