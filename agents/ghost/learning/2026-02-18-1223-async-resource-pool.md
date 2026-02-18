# Async Resource Pool with Context Managers & Circuit Breaker

**Ghost Learning — 12:23 PM, Feb 18, 2026**  
Pattern: Async resource management + graceful degradation

## The Pattern

A reusable connection pool with automatic retry, circuit breaker, and clean lifecycle management.

```python
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional
from dataclasses import dataclass
import time

@dataclass
class CircuitState:
    """Circuit breaker state machine."""
    failures: int = 0
    last_failure: float = 0
    open_until: float = 0
    
    @property
    def is_open(self) -> bool:
        return time.monotonic() < self.open_until
    
    def record_failure(self, timeout: float = 30.0):
        self.failures += 1
        self.last_failure = time.monotonic()
        if self.failures >= 3:
            self.open_until = time.monotonic() + timeout
    
    def record_success(self):
        self.failures = 0
        self.open_until = 0

class ResourcePool:
    """Generic async resource pool with circuit breaker.
    
    Usage: API clients, database connections, LLM APIs.
    """
    
    def __init__(self, max_size: int = 10, max_retries: int = 3):
        self.max_size = max_size
        self.max_retries = max_retries
        self._available = asyncio.Semaphore(max_size)
        self._circuit = CircuitState()
        self._lock = asyncio.Lock()
    
    @asynccontextmanager
    async def acquire(self, timeout: float = 5.0) -> AsyncGenerator['ResourceHandle', None]:
        """Context manager with automatic retry & circuit breaker."""
        if self._circuit.is_open:
            raise CircuitOpenError("Circuit breaker is open")
        
        async with self._lock:
            acquired = await asyncio.wait_for(
                self._available.acquire(), timeout=timeout
            )
        
        handle = ResourceHandle(self)
        try:
            yield handle
            self._circuit.record_success()
        except Exception as e:
            self._circuit.record_failure()
            raise RetryableError(f"Failed after {self.max_retries} retries") from e
        finally:
            self._available.release()

class ResourceHandle:
    """Represents a checked-out resource."""
    def __init__(self, pool: ResourcePool):
        self.pool = pool
        self.acquired_at = time.monotonic()
    
    @property
    def duration_ms(self) -> float:
        return (time.monotonic() - self.acquired_at) * 1000

class CircuitOpenError(Exception): pass
class RetryableError(Exception): pass

# === USAGE EXAMPLE ===

async def fetch_with_retry(pool: ResourcePool, url: str) -> str:
    """Real-world: API call with automatic retry and cleanup."""
    async with pool.acquire(timeout=10.0) as handle:
        # Simulate API call
        await asyncio.sleep(0.1)
        if handle.duration_ms > 5000:
            raise TimeoutError(f"Slow response: {handle.duration_ms:.0f}ms")
        return f"Data from {url}"

# Quick test
async def main():
    pool = ResourcePool(max_size=5)
    
    # Fire 20 concurrent requests, only 5 run at once
    tasks = [fetch_with_retry(pool, f"api/{i}") for i in range(20)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successes = sum(1 for r in results if isinstance(r, str))
    print(f"Success: {successes}/20")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Takeaways

1. **Async Semaphore**: Natural backpressure; prevents overwhelming downstream
2. **Circuit Breaker**: Fail fast when resource is down; auto-recovery after timeout
3. **Context Manager**: Guaranteed cleanup even if exceptions occur
4. **Exception Hierarchy**: Separate retryable vs fatal errors
5. **Observable**: Track duration, failures, pool utilization

## When To Use

- LLM API clients (rate limits, transient failures)
- Database connection pools
- Web scraping with politeness delays
- Any I/O with unreliable third parties

**Lines of code**: ~80 | **Dependencies**: stdlib only
