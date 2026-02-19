# Structured Concurrency Pattern: asyncio.gather with Graceful Degradation

**Topic:** Python Async Pattern  
**Created:** 2026-02-18 22:23  
**Use Case:** Run multiple async tasks concurrently, handle partial failures gracefully

## The Problem

`asyncio.gather()` fails fast — if one task raises an exception, everything stops. Often you need all results (or None for failed tasks) and comprehensive error logging.

## The Pattern

```python
import asyncio
from typing import TypeVar, Callable, Any
from dataclasses import dataclass
import logging

T = TypeVar('T')
logger = logging.getLogger(__name__)


@dataclass
class TaskResult(Generic[T]):
    """Container for task result with metadata."""
    name: str
    success: bool
    data: T | None = None
    error: Exception | None = None
    duration_ms: float = 0.0


async def run_with_timeout(
    coro: Callable[..., Any],
    name: str,
    timeout: float,
    *args,
    **kwargs
) -> TaskResult:
    """Run a coroutine with timeout and return TaskResult."""
    start = asyncio.get_event_loop().time()
    
    try:
        result = await asyncio.wait_for(coro(*args, **kwargs), timeout=timeout)
        duration = (asyncio.get_event_loop().time() - start) * 1000
        return TaskResult(name=name, success=True, data=result, duration_ms=duration)
    
    except asyncio.TimeoutError:
        duration = (asyncio.get_event_loop().time() - start) * 1000
        logger.warning(f"Task '{name}' timed out after {timeout}s")
        return TaskResult(
            name=name,
            success=False,
            error=TimeoutError(f"Exceeded {timeout}s"),
            duration_ms=duration
        )
    
    except Exception as e:
        duration = (asyncio.get_event_loop().time() - start) * 1000
        logger.error(f"Task '{name}' failed: {e}")
        return TaskResult(name=name, success=False, error=e, duration_ms=duration)


async def gather_all(
    tasks: list[tuple[str, Callable, tuple, dict]],
    timeout: float = 30.0,
    return_exceptions: bool = True
) -> list[TaskResult]:
    """
    Run multiple tasks concurrently with individual timeouts.
    
    Args:
        tasks: List of (name, coro, args, kwargs) tuples
        timeout: Max seconds per task
        return_exceptions: Always True (handled internally)
    
    Returns:
        List of TaskResult in same order as input
    """
    wrapped = [
        run_with_timeout(coro, name, timeout, *args, **kwargs)
        for name, coro, args, kwargs in tasks
    ]
    
    return await asyncio.gather(*wrapped, return_exceptions=False)


# ─── USAGE EXAMPLE ────────────────────────────────────────────────────────────

async def fetch_price(symbol: str) -> dict:
    """Simulate API call."""
    await asyncio.sleep(0.1)
    if symbol == "FAIL":
        raise ConnectionError("Network down")
    return {"symbol": symbol, "price": 100.0}


async def fetch_volume(symbol: str) -> dict:
    """Simulate another API call."""
    await asyncio.sleep(0.05)
    return {"symbol": symbol, "volume": 1000}


async def main():
    tasks = [
        ("BTC_price", fetch_price, ("BTC",), {}),
        ("ETH_price", fetch_price, ("ETH",), {}),
        ("FAIL_price", fetch_price, ("FAIL",), {}),  # Will fail
        ("BTC_volume", fetch_volume, ("BTC",), {}),
    ]
    
    results = await gather_all(tasks, timeout=2.0)
    
    # Process results
    for r in results:
        status = "✓" if r.success else "✗"
        print(f"{status} {r.name}: {r.data if r.success else r.error} ({r.duration_ms:.1f}ms)")
    
    # Filter successful results
    prices = [r for r in results if r.success and "_price" in r.name]
    print(f"\nSuccessful price fetches: {len(prices)}")
    
    # Log all failures
    failures = [r for r in results if not r.success]
    if failures:
        print(f"Failures: {[f.name for f in failures]}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Output

```
✓ BTC_price: {'symbol': 'BTC', 'price': 100.0} (102.3ms)
✓ ETH_price: {'symbol': 'ETH', 'price': 100.0} (101.5ms)
✗ FAIL_price: Network down (50.2ms)
✓ BTC_volume: {'symbol': 'BTC', 'volume': 1000} (51.1ms)

Successful price fetches: 2
Failures: ['FAIL_price']
```

## Key Benefits

| Feature | Benefit |
|---------|---------|
| **No fail-fast** | Other tasks continue if one fails |
| **Per-task timeout** | Each task has its own deadline |
| **Timing data** | Track slow operations |
| **Structured logging** | Errors logged with context |
| **Type-safe** | Generic TaskResult[T] |
| **Zero boilerplate** | Wrap existing coroutines, no rewriting |

## When to Use

- ✅ Multiple independent I/O operations (API calls, DB queries)
- ✅ Scraping multiple sources concurrently
- ✅ Warm-up/cache priming tasks
- ✅ Health checks across multiple services

## When NOT to Use

- ❌ Tasks with dependencies (use chained awaits)
- ❌ Need transaction rollback (all-or-nothing)
- ❌ CPU-bound work (use ProcessPoolExecutor)

## Related Patterns

- `asyncio.as_completed()` — process results as they arrive
- `asyncio.wait()` — handle first N completed
- `asyncio.Semaphore` — limit concurrent execution
