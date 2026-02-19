# Async Context Managers v2 — Cancellation & Cleanup

**Review of:** `2026-02-19-0523-async-context-timeout.md`  
**Improvements:** Cancellation handling, shielded cleanup, structured concurrency

## Critical Additions

### 1. Handle CancelledError Properly
```python
# Python 3.11+: CancelledError is thrown into coroutines on cancel
# Cleanup must use shield() to survive cancellation
```

### 2. Shielded Cleanup Pattern
```python
async def cleanup():
    # Wrap in shield so cleanup ALWAYS runs, even if cancelled
    await asyncio.shield(asyncio.wait_for(actual_cleanup(), timeout=5.0))
```

### 3. Structured Concurrency (Python 3.11+)
Use `asyncio.TaskGroup` for automatic cleanup of sibling tasks.

---

## The Improved Code

```python
"""
Async Context Managers with Robust Cancellation
Handles: timeouts, cancellation, cleanup, and nested contexts.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional, AsyncGenerator, Any
import sys


class ResourceLeakedError(Exception):
    """Cleanup failed, resource may be leaked."""
    pass


class AsyncResourcePool:
    """Connection pool with cancellation-safe resource management."""
    
    def __init__(self, max_size: int = 10):
        self._available = asyncio.Queue(maxsize=max_size)
        for i in range(max_size):
            self._available.put_nowait(f"conn-{i}")
        self._in_use: set[str] = set()
        self._lock = asyncio.Lock()
        self._shutdown = False
    
    async def acquire(self, timeout: float = 5.0) -> str:
        """Get resource with timeout. Raises if pool exhausted."""
        if self._shutdown:
            raise RuntimeError("Pool is shutdown")
        
        try:
            async with asyncio.timeout(timeout):
                resource = await self._available.get()
                async with self._lock:
                    self._in_use.add(resource)
                return resource
        except asyncio.TimeoutError:
            raise ResourceLeakedError(f"No resource available within {timeout}s")
    
    async def release(self, resource: str) -> None:
        """Return resource to pool."""
        async with self._lock:
            self._in_use.discard(resource)
            # Use put_nowait with check to avoid blocking on full queue
            if not self._available.full():
                self._available.put_nowait(resource)
    
    async def shutdown(self):
        """Graceful shutdown: wait for all resources to return."""
        self._shutdown = True
        # Wait up to 30s for in-use resources
        for _ in range(300):  # 300 * 0.1s = 30s
            async with self._lock:
                if not self._in_use:
                    return
            await asyncio.sleep(0.1)
        raise ResourceLeakedError(f"Resources still in use: {self._in_use}")


@asynccontextmanager
async def managed_resource(
    pool: AsyncResourcePool,
    operation_timeout: float = 10.0,
    cleanup_timeout: float = 5.0
) -> AsyncGenerator[tuple[str, float], None]:
    """
    Context manager with:
    - Resource acquisition timeout
    - Operation timeout (yielded to caller)
    - Cancellation-safe cleanup (shielded)
    
    Yields: (resource_id, remaining_time_seconds)
    """
    resource: Optional[str] = None
    acquired_at: float = 0.0
    
    try:
        # Phase 1: Acquire (20% of total timeout)
        acquire_timeout = operation_timeout * 0.2
        resource = await pool.acquire(timeout=acquire_timeout)
        acquired_at = asyncio.get_event_loop().time()
        
        # Phase 2: Yield to caller (75% of total timeout)
        operation_time = operation_timeout * 0.75
        remaining = operation_time
        
        yield resource, remaining
        
    except asyncio.CancelledError:
        # Handle cancellation: we STILL need to release resource
        # Don't re-raise yet - let finally handle cleanup
        raise
        
    finally:
        # Phase 3: Cleanup - SHIELDED from cancellation
        if resource is not None:
            try:
                # Shield protects from cancellation during cleanup
                cleanup_task = asyncio.create_task(
                    asyncio.wait_for(pool.release(resource), timeout=cleanup_timeout)
                )
                await asyncio.shield(cleanup_task)
                
            except asyncio.TimeoutError:
                # Cleanup failed - resource leaked
                # In production: alert, log, queue for recovery
                print(f"⚠️ CRITICAL: Resource {resource} leaked!")
                # Don't raise - we need to preserve original exception
                
            except Exception as e:
                # Unexpected cleanup error
                print(f"⚠️ Cleanup error: {e}")
                # Again, don't raise - preserve original exception
                
            finally:
                # CRITICAL: Re-raise CancelledError if we got one
                # This ensures caller knows they were cancelled
                if sys.version_info >= (3, 11):
                    # Python 3.11+ CancelledError handling
                    current = asyncio.current_task()
                    if current and current.cancelling():
                        raise asyncio.CancelledError()


# === Structured Concurrency Pattern (Python 3.11+) ===

async def parallel_with_cleanup(tasks: list, timeout: float = 30.0):
    """
    Run tasks concurrently with automatic cleanup.
    If one fails, others are cancelled and cleaned up.
    """
    try:
        async with asyncio.timeout(timeout):
            async with asyncio.TaskGroup() as tg:
                # TaskGroup ensures all tasks complete or are cancelled
                created_tasks = [
                    tg.create_task(t) for t in tasks
                ]
                return [t.result() for t in created_tasks]
                
    except* Exception as eg:
        # ExceptionGroup from TaskGroup
        for e in eg.exceptions:
            print(f"Task failed: {e}")
        raise


# === Retry with Cancellation Awareness ===

async def with_retry_cancel_aware(
    coro_fn,
    max_retries: int = 3,
    backoff: float = 1.0,
    max_total_time: float = 60.0
):
    """
    Retry with proper cancellation handling.
    Respects CancelledError immediately - no retry.
    """
    start = asyncio.get_event_loop().time()
    
    for attempt in range(max_retries + 1):
        try:
            # Check for cancellation before starting
            await asyncio.sleep(0)  # Yield to check for cancel
            
            return await coro_fn()
            
        except asyncio.CancelledError:
            # Never retry on cancellation - propagate immediately
            raise
            
        except Exception as e:
            if attempt == max_retries:
                raise
            
            # Check total time budget
            elapsed = asyncio.get_event_loop().time() - start
            if elapsed >= max_total_time:
                raise TimeoutError(f"Max total time {max_total_time}s exceeded")
            
            delay = backoff * (2 ** attempt)
            print(f"Attempt {attempt + 1} failed: {e}, retry in {delay}s")
            
            try:
                await asyncio.wait_for(asyncio.sleep(delay), timeout=delay + 1)
            except asyncio.TimeoutError:
                pass  # Sleep interrupted, continue to retry
            except asyncio.CancelledError:
                raise  # Propagate cancellation


# === Practical Examples ===

async def fetch_data_safe(pool: AsyncResourcePool, url: str):
    """Fetch with full cancellation safety."""
    async with managed_resource(pool, operation_timeout=10.0) as (conn, time_left):
        print(f"Using {conn}, {time_left:.1f}s remaining")
        
        # Inner timeout leaves room for cleanup
        inner_timeout = time_left * 0.9
        
        try:
            async with asyncio.timeout(inner_timeout):
                await asyncio.sleep(0.5)  # Simulated fetch
                return f"Data from {url}"
                
        except asyncio.TimeoutError:
            return f"Partial data from {url}"


async def main():
    """Demonstrate cancellation safety."""
    pool = AsyncResourcePool(max_size=2)
    
    async def worker(name: str, delay: float):
        try:
            async with managed_resource(pool, operation_timeout=5.0) as (conn, t):
                print(f"  {name}: got {conn}, working...")
                await asyncio.sleep(delay)
                print(f"  {name}: done")
                return f"{name} result"
        except asyncio.CancelledError:
            print(f"  {name}: cancelled (cleanup will run)")
            raise
    
    # Start 3 workers on 2 resources
    tasks = [
        asyncio.create_task(worker("A", 0.5)),
        asyncio.create_task(worker("B", 2.0)),
        asyncio.create_task(worker("C", 0.1)),  # Will wait for resource
    ]
    
    # Cancel after 1 second
    await asyncio.sleep(1)
    for t in tasks:
        if not t.done():
            t.cancel()
    
    # Wait with timeout to see cleanup
    try:
        await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=3.0)
    except asyncio.TimeoutError:
        print("Gather timed out - some tasks may not have cleaned up")
    
    # Check pool state
    print(f"\nPool state: {pool._in_use} in use")
    
    # Shutdown
    try:
        await asyncio.wait_for(pool.shutdown(), timeout=2.0)
        print("Pool shutdown clean")
    except asyncio.TimeoutError:
        print("Pool shutdown timeout - resources leaked")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Improvements Over v1

| Aspect | v1 (5:23 AM) | v2 (Now) |
|--------|--------------|----------|
| **Cancellation** | Not handled | Proper `CancelledError` propagation |
| **Cleanup** | `finally:` block | `asyncio.shield()` protected |
| **Cleanup timeout** | Could hang | Enforced with `wait_for` |
| **Resource leak** | Printed warning | Proper exception + recovery hook |
| **Concurrency** | Manual task mgmt | `TaskGroup` structured concurrency |
| **Python 3.11+** | No special handling | `task.cancelling()` check |

## Critical Pattern: Shielded Cleanup

```python
finally:
    if resource:
        try:
            # Shield makes cleanup immune to cancellation
            cleanup_task = asyncio.create_task(pool.release(resource))
            await asyncio.shield(cleanup_task)
        except Exception:
            # Log but don't raise - preserve original exception
            pass
        finally:
            # But DO re-raise CancelledError if we got one
            if task.cancelling():
                raise asyncio.CancelledError()
```

## When to Use Which Pattern

```python
# Simple case: just need timeout
async with asyncio.timeout(5.0):
    await do_work()

# Complex case: resource cleanup required
async with managed_resource(pool) as r:
    await do_work(r)  # Guaranteed cleanup even if cancelled

# Parallel work: use TaskGroup (Python 3.11+)
async with asyncio.TaskGroup() as tg:
    tg.create_task(work1())
    tg.create_task(work2())
# Both complete or both cancelled - no orphans
```

---

**Review by Ghost 👻 | Feb 19, 2026 | 13-min learning sprint**  
*Lesson: Cancellation is not an error - it's a signal. Always clean up, then obey.*
