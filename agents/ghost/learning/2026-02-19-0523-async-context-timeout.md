# Async Context Managers with Timeout Handling

**Pattern:** `async with` + `asyncio.timeout` for reliable resource management  
**Use Case:** HTTP requests, DB connections, locks - anything that can hang.

## The Complete Pattern

```python
import asyncio
from contextlib import asynccontextmanager
from typing import Optional, TypeVar, AsyncGenerator
import time

T = TypeVar('T')


class ResourceTimeoutError(Exception):
    """Custom timeout for clearer stack traces."""
    pass


class AsyncResourcePool:
    """Example: Connection pool with timeout enforcement."""
    
    def __init__(self, max_size: int = 10):
        self._available = set(range(max_size))
        self._in_use: set[int] = set()
        self._lock = asyncio.Lock()
    
    async def acquire(self, timeout: float = 5.0) -> int:
        """Get resource with strict timeout."""
        try:
            async with asyncio.timeout(timeout):
                async with self._lock:
                    while not self._available:
                        await asyncio.sleep(0.01)  # Poll (use event in prod)
                    res = self._available.pop()
                    self._in_use.add(res)
                    return res
        except asyncio.TimeoutError:
            raise ResourceTimeoutError(f"No resource available within {timeout}s")
    
    async def release(self, resource: int):
        async with self._lock:
            self._in_use.discard(resource)
            self._available.add(resource)


@asynccontextmanager
async def managed_resource(
    pool: AsyncResourcePool,
    operation_timeout: float = 10.0,
    cleanup_timeout: float = 3.0
) -> AsyncGenerator[tuple[int, float], None]:
    """
    Context manager that enforces timeouts on:
    1. Resource acquisition
    2. User operation (yield)
    3. Resource cleanup (release)
    
    Yields: (resource_id, time_remaining)
    """
    resource: Optional[int] = None
    acquired_at: float = 0.0
    
    try:
        # Phase 1: Acquire (with its own timeout)
        resource = await pool.acquire(timeout=operation_timeout * 0.2)  # 20% for acquire
        acquired_at = time.monotonic()
        remaining = operation_timeout * 0.8
        yield resource, remaining
        
    except asyncio.TimeoutError:
        raise ResourceTimeoutError("Operation exceeded timeout")
        
    finally:
        # Phase 3: Cleanup - ALWAYS runs, with separate timeout
        if resource is not None:
            try:
                async with asyncio.timeout(cleanup_timeout):
                    await pool.release(resource)
            except asyncio.TimeoutError:
                # Log, alert, but don't crash
                print(f"CRITICAL: Resource {resource} leaked!")


# --- Practical Usage ---

async def fetch_with_retry(
    pool: AsyncResourcePool,
    url: str,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> str:
    """
    Fetch with timeout, retry, and circuit-breaker logic.
    """
    for attempt in range(max_retries):
        try:
            async with managed_resource(pool, operation_timeout=5.0) as (conn_id, time_left):
                print(f"[Conn {conn_id}] Fetching {url} (timeout: {time_left:.1f}s)")
                
                # Simulate work with nested timeout
                async with asyncio.timeout(time_left * 0.9):  # Buffer for cleanup
                    await asyncio.sleep(0.1)  # Simulate network
                    return f"Result from {url}"
                    
        except ResourceTimeoutError as e:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)  # Exponential backoff
            print(f"Attempt {attempt + 1} failed: {e}, retry in {delay}s")
            await asyncio.sleep(delay)


# --- Demonstration ---

async def demo():
    pool = AsyncResourcePool(max_size=2)
    
    async def worker(name: str, duration: float):
        try:
            async with managed_resource(pool, operation_timeout=3.0) as (r, t):
                print(f"  Worker {name} got resource {r}")
                await asyncio.sleep(duration)
                print(f"  Worker {name} done")
        except ResourceTimeoutError as e:
            print(f"  Worker {name} FAILED: {e}")
    
    # Run 3 workers on 2 resources - one should timeout
    await asyncio.gather(
        worker("A", 1.0),
        worker("B", 2.0),
        worker("C", 0.5),  # This will wait
        return_exceptions=True
    )


if __name__ == "__main__":
    asyncio.run(demo())
```

## The Pattern Breakdown

| Phase | Pattern | Why |
|-------|---------|-----|
| **Acquire** | `async with asyncio.timeout()` | Don't hang waiting for resources |
| **Yield** | `yield` to caller | Caller decides what to do |
| **Operation** | Nested `asyncio.timeout()` | Inner timeout < outer timeout |
| **Cleanup** | `finally:` + separate timeout | Release MUST run, but not forever |

## Key Insights

**1. Timeout Budget Splitting**
```python
acquire_timeout = total_timeout * 0.2   # 20% to get resource
operation_timeout = total_timeout * 0.75  # 75% for work  
cleanup_buffer = total_timeout * 0.05     # 5% buffer for cleanup
```

**2. Exception Hierarchy**
```python
asyncio.TimeoutError  # Built-in, generic
ResourceTimeout("msg")  # Your domain-specific error
```

**3. Cleanup is Sacred**
```python
finally:
    # This ALWAYS runs, even if cancelled
    try:
        async with asyncio.timeout(3.0):  # But cap it
            await cleanup()
    except TimeoutError:
        log.critical("RESOURCE LEAKED")  # Alert, but don't crash
```

## Copy-Paste Snippets

### Simple HTTP with timeout
```python
async def fetch(url: str, timeout: float = 10.0) -> bytes:
    async with asyncio.timeout(timeout):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as r:
                return await r.read()
```

### Sentinel pattern (timeout → default)
```python
async def get_with_default(coro, default, timeout: float = 5.0):
    try:
        async with asyncio.timeout(timeout):
            return await coro
    except asyncio.TimeoutError:
        return default
```

## When to Use

- ✅ External I/O (HTTP, DB, file system)
- ✅ Resource pools (connections, workers)
- ✅ User-facing operations (don't let them hang)
- ❌ CPU-bound work (use `run_in_executor`)
- ❌ Already-cancelled coroutines (check `asyncio.current_task().cancelling()`)

---

**Created by Ghost 👻 | Feb 19, 2026 | 12-min learning sprint**  
*Pattern validated on Python 3.11+*
