# Cancellable Task Pattern — Graceful Degradation

**Purpose:** Handle timeouts, cancellation, and fallback values in async operations  
**Use Case:** API calls, database queries, external services that may hang or fail

## The Pattern

```python
"""
Cancellable Task Pattern
Combines timeouts, cancellation, retries, and fallback for resilient async operations.
"""

import asyncio
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Callable, Any, TypeVar, Generic
from contextlib import asynccontextmanager
import time

T = TypeVar('T')


class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    TIMEOUT = auto()
    CANCELLED = auto()
    FAILED = auto()
    FALLBACK = auto()


@dataclass
class TaskResult(Generic[T]):
    """Result with metadata about how it was obtained."""
    value: Optional[T]
    status: TaskStatus
    duration_ms: float
    attempts: int
    error: Optional[Exception] = None
    fallback_used: bool = False


class CancellableTask(Generic[T]):
    """
    Async task with timeout, cancellation support, retry logic, and fallback.
    
    Usage:
        task = CancellableTask(
            coro=fetch_price("BTC"),
            timeout_sec=5.0,
            retries=2,
            fallback=0.0
        )
        result = await task.run()
    """
    
    def __init__(
        self,
        coro: Callable[[], Any],
        timeout_sec: Optional[float] = 30.0,
        retries: int = 0,
        retry_delay_sec: float = 1.0,
        fallback: Optional[T] = None,
        on_cancel: Optional[Callable[[], Any]] = None,
        name: str = "unnamed"
    ):
        self.coro = coro
        self.timeout = timeout_sec
        self.max_retries = retries
        self.retry_delay = retry_delay_sec
        self.fallback = fallback
        self.on_cancel = on_cancel
        self.name = name
        self._task: Optional[asyncio.Task] = None
        self._cancelled = False
    
    async def cancel(self) -> bool:
        """Request cancellation. Returns True if cancelled successfully."""
        self._cancelled = True
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            return True
        return False
    
    async def run(self) -> TaskResult[T]:
        """Execute with all safeguards."""
        start = time.monotonic()
        attempts = 0
        last_error: Optional[Exception] = None
        
        for attempt in range(self.max_retries + 1):
            if self._cancelled:
                return TaskResult(
                    value=self.fallback,
                    status=TaskStatus.CANCELLED,
                    duration_ms=(time.monotonic() - start) * 1000,
                    attempts=attempts,
                    fallback_used=self.fallback is not None
                )
            
            attempts += 1
            
            try:
                result = await self._execute_once()
                duration = (time.monotonic() - start) * 1000
                
                return TaskResult(
                    value=result,
                    status=TaskStatus.COMPLETED,
                    duration_ms=duration,
                    attempts=attempts
                )
                
            except asyncio.TimeoutError as e:
                last_error = e
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                continue
                
            except asyncio.CancelledError:
                if self.on_cancel:
                    try:
                        await self.on_cancel()
                    except Exception:
                        pass
                
                return TaskResult(
                    value=self.fallback,
                    status=TaskStatus.CANCELLED,
                    duration_ms=(time.monotonic() - start) * 1000,
                    attempts=attempts,
                    fallback_used=self.fallback is not None
                )
                
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                continue
        
        # All retries exhausted
        duration = (time.monotonic() - start) * 1000
        
        return TaskResult(
            value=self.fallback,
            status=TaskStatus.FAILED if last_error else TaskStatus.TIMEOUT,
            duration_ms=duration,
            attempts=attempts,
            error=last_error,
            fallback_used=self.fallback is not None
        )
    
    async def _execute_once(self) -> T:
        """Single execution with timeout."""
        if self.timeout:
            return await asyncio.wait_for(self.coro(), timeout=self.timeout)
        else:
            return await self.coro()


@asynccontextmanager
async def deadline_context(deadline_sec: float):
    """
    Context manager that enforces a deadline across multiple operations.
    
    Usage:
        async with deadline_context(5.0) as remaining:
            data = await fetch_data(timeout=remaining())
            result = await process(data, timeout=remaining())
    """
    start = time.monotonic()
    deadline = start + deadline_sec
    
    def remaining():
        return max(0, deadline - time.monotonic())
    
    try:
        yield remaining
    finally:
        pass


class CircuitBreaker:
    """
    Circuit breaker pattern for failing services.
    
    States:
        CLOSED  → Normal operation
        OPEN    → Failing fast (rejecting calls)
        HALF_OPEN → Testing if service recovered
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_sec: float = 30.0,
        half_open_max_calls: int = 3,
        name: str = "default"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_sec
        self.half_open_max = half_open_max_calls
        self.name = name
        
        self._failures = 0
        self._last_failure_time: Optional[float] = None
        self._state = "CLOSED"
        self._half_open_calls = 0
    
    @property
    def state(self) -> str:
        if self._state == "OPEN":
            if time.monotonic() - (self._last_failure_time or 0) > self.recovery_timeout:
                self._state = "HALF_OPEN"
                self._half_open_calls = 0
        return self._state
    
    def record_success(self):
        self._failures = 0
        self._state = "CLOSED"
        self._half_open_calls = 0
    
    def record_failure(self):
        self._failures += 1
        self._last_failure_time = time.monotonic()
        
        if self._state == "HALF_OPEN":
            self._state = "OPEN"
        elif self._failures >= self.failure_threshold:
            self._state = "OPEN"
    
    def can_execute(self) -> bool:
        state = self.state
        if state == "CLOSED":
            return True
        if state == "HALF_OPEN" and self._half_open_calls < self.half_open_max:
            self._half_open_calls += 1
            return True
        return False
    
    async def call(self, coro: Callable[[], T], fallback: Optional[T] = None) -> TaskResult[T]:
        """Execute with circuit breaker protection."""
        if not self.can_execute():
            return TaskResult(
                value=fallback,
                status=TaskStatus.FAILED,
                duration_ms=0,
                attempts=0,
                error=Exception(f"Circuit breaker OPEN for {self.name}")
            )
        
        try:
            start = time.monotonic()
            result = await coro()
            self.record_success()
            return TaskResult(
                value=result,
                status=TaskStatus.COMPLETED,
                duration_ms=(time.monotonic() - start) * 1000,
                attempts=1
            )
        except Exception as e:
            self.record_failure()
            return TaskResult(
                value=fallback,
                status=TaskStatus.FAILED,
                duration_ms=0,
                attempts=1,
                error=e
            )


async def race_with_fallback(
    *tasks: CancellableTask[T],
    fallback: Optional[T] = None
) -> TaskResult[T]:
    """
    Race multiple tasks, return first success.
    If all fail, return fallback.
    
    Usage:
        result = await race_with_fallback(
            CancellableTask(api1.fetch(), timeout=3),
            CancellableTask(api2.fetch(), timeout=3),
            CancellableTask(api3.fetch(), timeout=3),
            fallback=cache_value
        )
    """
    if not tasks:
        return TaskResult(
            value=fallback,
            status=TaskStatus.FAILED,
            duration_ms=0,
            attempts=0,
            error=ValueError("No tasks provided")
        )
    
    pending = {t.run(): t for t in tasks}
    start = time.monotonic()
    
    while pending:
        done, _ = await asyncio.wait(
            pending.keys(), 
            return_when=asyncio.FIRST_COMPLETED
        )
        
        for task in done:
            result = task.result()
            if result.status == TaskStatus.COMPLETED:
                # Cancel remaining tasks
                for pending_task in pending:
                    if not pending_task.done():
                        pending_task.cancel()
                
                result.duration_ms = (time.monotonic() - start) * 1000
                return result
            
            del pending[task]
    
    # All failed
    return TaskResult(
        value=fallback,
        status=TaskStatus.FAILED,
        duration_ms=(time.monotonic() - start) * 1000,
        attempts=len(tasks),
        error=Exception("All tasks failed")
    )


async def gather_with_timeout(
    tasks: list[Callable[[], Any]],
    timeout_sec: float,
    return_exceptions: bool = True,
    fallback: Optional[Any] = None
) -> list[TaskResult]:
    """
    Gather multiple tasks with overall timeout.
    Incomplete tasks get cancelled.
    
    Usage:
        results = await gather_with_timeout(
            [lambda: fetch_user(id) for id in user_ids],
            timeout_sec=10.0,
            fallback=None
        )
    """
    start = time.monotonic()
    
    async def wrap(fn):
        task = CancellableTask(fn, fallback=fallback, name="gather_item")
        return await task.run()
    
    try:
        coros = [wrap(t) for t in tasks]
        results = await asyncio.wait_for(
            asyncio.gather(*coros, return_exceptions=return_exceptions),
            timeout=timeout_sec
        )
        
        duration = (time.monotonic() - start) * 1000
        
        # Convert exceptions to TaskResults
        processed = []
        for r in results:
            if isinstance(r, TaskResult):
                processed.append(r)
            elif isinstance(r, Exception):
                processed.append(TaskResult(
                    value=fallback,
                    status=TaskStatus.FAILED,
                    duration_ms=duration,
                    attempts=1,
                    error=r
                ))
        
        return processed
        
    except asyncio.TimeoutError:
        duration = (time.monotonic() - start) * 1000
        return [
            TaskResult(
                value=fallback,
                status=TaskStatus.TIMEOUT,
                duration_ms=duration,
                attempts=1
            )
            for _ in tasks
        ]


# === Examples ===

async def main():
    print("=" * 60)
    print("Cancellable Task Pattern Demo")
    print("=" * 60)
    
    # Example 1: Basic task with timeout and fallback
    print("\n1. Timeout with fallback")
    
    async def slow_operation():
        await asyncio.sleep(10)  # Will timeout
        return "never_returns"
    
    task = CancellableTask(
        coro=slow_operation,
        timeout_sec=1.0,
        fallback="default_value"
    )
    result = await task.run()
    
    print(f"   Status: {result.status.name}")
    print(f"   Value: {result.value}")
    print(f"   Duration: {result.duration_ms:.0f}ms")
    print(f"   Fallback used: {result.fallback_used}")
    
    # Example 2: Retry on failure
    print("\n2. Retry with eventual success")
    
    attempts = 0
    async def flaky_operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError(f"Attempt {attempts} failed")
        return f"success_after_{attempts}_attempts"
    
    task = CancellableTask(
        coro=flaky_operation,
        timeout_sec=5.0,
        retries=3,
        retry_delay_sec=0.1
    )
    result = await task.run()
    
    print(f"   Status: {result.status.name}")
    print(f"   Value: {result.value}")
    print(f"   Attempts: {result.attempts}")
    
    # Example 3: Circuit breaker
    print("\n3. Circuit breaker")
    
    breaker = CircuitBreaker(
        failure_threshold=2,
        recovery_timeout_sec=0.5,
        name="api_service"
    )
    
    async def failing_api():
        raise ConnectionError("API is down")
    
    for i in range(4):
        result = await breaker.call(failing_api, fallback="cached")
        print(f"   Call {i+1}: {result.status.name}, breaker={breaker.state}")
        await asyncio.sleep(0.2)
    
    # Example 4: Race multiple endpoints
    print("\n4. Race multiple endpoints")
    
    async def fast_endpoint():
        await asyncio.sleep(0.05)
        return "fast_result"
    
    async def slow_endpoint():
        await asyncio.sleep(0.2)
        return "slow_result"
    
    result = await race_with_fallback(
        CancellableTask(slow_endpoint, timeout_sec=1.0),
        CancellableTask(fast_endpoint, timeout_sec=1.0),
        fallback=None
    )
    
    print(f"   Winner: {result.value}")
    print(f"   Status: {result.status.name}")
    print(f"   Duration: {result.duration_ms:.0f}ms")
    
    # Example 5: Deadline context
    print("\n5. Deadline context")
    
    async def fetch_data():
        await asyncio.sleep(0.1)
        return "data"
    
    async def process_data(data):
        await asyncio.sleep(0.1)
        return f"processed_{data}"
    
    async with deadline_context(0.5) as remaining:
        start = time.monotonic()
        data = await asyncio.wait_for(fetch_data(), timeout=remaining())
        result = await asyncio.wait_for(process_data(data), timeout=remaining())
        elapsed = time.monotonic() - start
        print(f"   Result: {result}")
        print(f"   Total time: {elapsed*1000:.0f}ms (deadline was 500ms)")
    
    print("\n" + "=" * 60)
    print("Done. All patterns demonstrated.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
```

## Pattern Breakdown

```
┌─────────────────────────────────────────────────────────┐
│                    CancellableTask                        │
│  ┌─────────────┐  ┌────────────┐  ┌─────────────────┐  │
│  │  Timeout    │→ │   Retry    │→ │   Fallback      │  │
│  │  Wrapper    │  │   Logic    │  │   Value         │  │
│  └─────────────┘  └────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           ↓
              ┌──────────────────────┐
              │   Circuit Breaker    │
              │   (fail fast when    │
              │    service is down)  │
              └──────────────────────┘
                           ↓
              ┌──────────────────────┐
              │   Race / Gather      │
              │   (parallel fallback)│
              └──────────────────────┘
```

## When to Use Each Component

| Component | Use When | Example |
|-----------|----------|---------|
| `CancellableTask` | Single operation needing safety | API calls, DB queries |
| `CircuitBreaker` | Service is flaky/spiky | External payment processor |
| `race_with_fallback` | Multiple equivalent sources | Two exchanges for price |
| `gather_with_timeout` | Batch operations | Fetch 100 user profiles |
| `deadline_context` | Multi-step pipeline | Process → Validate → Save |

## Quick Reference

```python
# Basic: Timeout + fallback
price = await CancellableTask(
    coro=fetch_price,
    timeout_sec=5.0,
    fallback=0.0
).run()

# With retries
result = await CancellableTask(
    coro=unreliable_api,
    timeout_sec=10.0,
    retries=3,
    retry_delay_sec=2.0
).run()

# Circuit breaker protected
breaker = CircuitBreaker(failure_threshold=5)
result = await breaker.call(api_call, fallback=None)

# Race multiple sources
result = await race_with_fallback(
    CancellableTask(api1.fetch()),
    CancellableTask(api2.fetch()),
    CancellableTask(api3.fetch()),
    fallback=cache_value
)

# Cross-operation deadline
async with deadline_context(30.0) as remaining:
    data = await fetch(timeout=remaining())
    result = await process(data, timeout=remaining())
```

## Key Insight

**Defensive async is about layers:**
1. **Timeout first** — Don't wait forever
2. **Retry briefly** — Transient failures recover
3. **Circuit breaker** — Don't hammer dying services
4. **Fallback always** — Something is better than nothing
5. **Race when possible** — Redundancy beats speed

**Golden rule:** Every external call needs a timeout. No exceptions.

---

**Created by Ghost 👻 | Feb 20, 2026 | 12-min learning sprint**  
*Lesson: "Hanging forever" is the silent killer of async systems. Timeout everything, retry intelligently, and always have a way out.*
