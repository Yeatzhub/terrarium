# Python Async Error Handling & Resilience Patterns

**Date:** 2026-02-18 19:23  
**Topic:** Production-ready async error handling for API clients, scrapers, and trading bots

---

## 1. Asyncio.Gather() with Graceful Error Handling

**Problem:** One failing coroutine kills the entire batch.  
**Solution:** Use `return_exceptions=True` + result filtering.

```python
import asyncio
from typing import Tuple, Any

async def fetch_with_gather(urls: list[str]) -> Tuple[list[Any], list[Exception]]:
    """
    Fetch multiple URLs concurrently.
    Returns: (successful_results, exceptions)
    """
    tasks = [fetch_one(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successes = []
    failures = []
    
    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            failures.append(result)
            print(f"✗ {url}: {result}")
        else:
            successes.append(result)
            print(f"✓ {url}: {len(result)} bytes")
    
    return successes, failures
```

---

## 2. Timeout Pattern with Exponential Backoff

**Use case:** External APIs with variable latency.

```python
import asyncio
from functools import wraps

def with_timeout_and_retry(max_retries=3, base_delay=1.0, timeout=10.0):
    """Decorator for resilient async API calls."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await asyncio.wait_for(
                        func(*args, **kwargs),
                        timeout=timeout
                    )
                except asyncio.TimeoutError:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    print(f"Timeout, retrying in {delay}s... ({attempt + 1}/{max_retries})")
                    await asyncio.sleep(delay)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(base_delay * (2 ** attempt))
            return None
        return wrapper
    return decorator

# Usage
@with_timeout_and_retry(max_retries=3, timeout=5.0)
async def fetch_market_data(symbol: str) -> dict:
    # Your API call here
    pass
```

---

## 3. Circuit Breaker Pattern

**Prevents:** Cascading failures when external service is down.

```python
import asyncio
import time
from enum import Enum
from typing import Optional, Callable

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject fast
    HALF_OPEN = "half_open"  # Testing if recovered

class CircuitBreaker:
    """Simple circuit breaker for async operations."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if self._last_failure_time and \
               time.time() - self._last_failure_time > self.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                print("Circuit entering HALF_OPEN state")
        return self._state
    
    async def call(self, func: Callable, *args, **kwargs):
        async with self._lock:
            current_state = self.state
            
            if current_state == CircuitState.OPEN:
                raise Exception("Circuit breaker OPEN - service unavailable")
            
            try:
                result = await func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise
    
    def _on_success(self):
        self._failure_count = 0
        self._last_failure_time = None
        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.CLOSED
            print("Circuit CLOSED - service recovered")
    
    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.time()
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            print(f"Circuit OPEN - {self._failure_count} failures")

# Usage
breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=10.0)

async def resilient_api_call():
    return await breaker.call(fetch_market_data, "BTC-USD")
```

---

## 4. Resource Cleanup with Async Context Managers

**Guarantees:** Resources released even on crash.

```python
from contextlib import asynccontextmanager
import aiohttp
import asyncio

@asynccontextmanager
async def managed_session(timeout: float = 30.0):
    """Managed aiohttp session with automatic cleanup."""
    connector = aiohttp.TCPConnector(
        limit=100,
        limit_per_host=10,
        ttl_dns_cache=300,
        use_dns_cache=True,
    )
    timeout = aiohttp.ClientTimeout(total=timeout)
    
    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        raise_for_status=True
    ) as session:
        try:
            yield session
        finally:
            print("Session cleanup complete")

@asynccontextmanager
async def rate_limited_worker(max_concurrent: int = 10):
    """Semaphore-based rate limiting."""
    semaphore = asyncio.Semaphore(max_concurrent)
    active = 0
    
    async def guarded_execute(coro):
        nonlocal active
        async with semaphore:
            active += 1
            try:
                return await coro
            finally:
                active -= 1
    
    try:
        yield guarded_execute
    finally:
        print(f"Worker pool shutdown (was handling {active} tasks)")

# Usage
async def batch_fetch(urls: list[str]):
    async with managed_session() as session:
        async with rate_limited_worker(max_concurrent=5) as worker:
            tasks = [worker(fetch_url(session, url)) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
```

---

## 5. Complete Production Pattern: Resilient API Client

```python
import asyncio
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class ApiResult:
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0

class ResilientApiClient:
    """Production-ready async API client with full error handling."""
    
    def __init__(
        self,
        timeout: float = 10.0,
        max_retries: int = 3,
        circuit_threshold: int = 5,
        rate_limit: int = 10
    ):
        self.timeout = timeout
        self.max_retries = max_retries
        self.breaker = CircuitBreaker(
            failure_threshold=circuit_threshold,
            recovery_timeout=60.0
        )
        self.semaphore = asyncio.Semaphore(rate_limit)
        self._stats = {'success': 0, 'failure': 0, 'timeout': 0}
    
    async def call(
        self,
        func: Callable,
        *args,
        fallback_value: Any = None,
        **kwargs
    ) -> ApiResult:
        """Execute with full resilience stack."""
        start = asyncio.get_event_loop().time()
        
        async with self.semaphore:
            for attempt in range(self.max_retries):
                try:
                    result = await asyncio.wait_for(
                        self.breaker.call(func, *args, **kwargs),
                        timeout=self.timeout
                    )
                    self._stats['success'] += 1
                    return ApiResult(
                        success=True,
                        data=result,
                        duration_ms=(asyncio.get_event_loop().time() - start) * 1000
                    )
                    
                except asyncio.TimeoutError:
                    self._stats['timeout'] += 1
                    if attempt == self.max_retries - 1:
                        return ApiResult(
                            success=False,
                            error="Max retries exceeded (timeout)",
                            duration_ms=(asyncio.get_event_loop().time() - start) * 1000
                        )
                    await asyncio.sleep(2 ** attempt)
                    
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        self._stats['failure'] += 1
                        return ApiResult(
                            success=False,
                            error=str(e),
                            data=fallback_value,
                            duration_ms=(asyncio.get_event_loop().time() - start) * 1000
                        )
                    await asyncio.sleep(2 ** attempt)
        
        return ApiResult(success=False, error="Unknown failure")
    
    def get_stats(self) -> dict:
        total = sum(self._stats.values())
        return {
            **self._stats,
            'total': total,
            'success_rate': self._stats['success'] / total if total > 0 else 0
        }

# Usage
client = ResilientApiClient(timeout=5.0, max_retries=3)

async def get_prices(symbols: list[str]):
    tasks = [
        client.call(fetch_price, sym, fallback_value=0.0)
        for sym in symbols
    ]
    results = await asyncio.gather(*tasks)
    return {sym: r.data for sym, r in zip(symbols, results) if r.success}
```

---

## Quick Reference

| Pattern | Use When | Key Benefit |
|---------|----------|-------------|
| `return_exceptions=True` | Batch operations | Don't let one failure kill the batch |
| `wait_for()` | External APIs | Prevent indefinite hangs |
| Exponential backoff | Retrying | Don't hammer failing services |
| Circuit breaker | Cascading failures | Fail fast, protect resources |
| Context managers | Resource management | Guaranteed cleanup |
| Semaphores | Rate limiting | Respect API limits |

---

**Production tip:** Always log at circuit state changes and retry attempts. Use structured logging (JSON) for observability.
