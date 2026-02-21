# Async Retry with Exponential Backoff Pattern
*Ghost Learning | 2026-02-21*

Robust async retry decorator with exponential backoff, jitter, circuit breaker, and selective retry on specific exceptions. Battle-tested for API calls.

```python
"""
Async retry decorator with exponential backoff, jitter, and circuit breaker.
Usage: @retry(max_attempts=3, base_delay=1.0, exceptions=(aiohttp.ClientError,))
"""

import asyncio
import random
import functools
from dataclasses import dataclass, field
from typing import TypeVar, Callable, Optional, Tuple, Type
from datetime import datetime, timedelta


T = TypeVar("T")


@dataclass
class RetryConfig:
    """Retry configuration."""
    max_attempts: int = 3
    base_delay: float = 1.0          # Initial delay in seconds
    max_delay: float = 60.0          # Cap delay at this value
    exponential_base: float = 2.0   # 1, 2, 4, 8...
    jitter: bool = True             # Add randomness to prevent thundering herd
    jitter_max: float = 1.0         # Max jitter in seconds
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
    on_retry: Optional[Callable[[Exception, int], None]] = None  # Callback(attempt_num)
    on_giveup: Optional[Callable[[Exception], None]] = None


class CircuitOpenError(Exception):
    """Circuit breaker is open — too many failures."""
    pass


@dataclass
class CircuitBreaker:
    """Circuit breaker pattern — fail fast after repeated failures."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    
    _failures: int = field(default=0, repr=False)
    _last_failure_time: Optional[datetime] = field(default=None, repr=False)
    _state: str = field(default="closed", repr=False)  # closed, open, half_open
    
    def record_success(self) -> None:
        """Reset on success."""
        self._failures = 0
        self._state = "closed"
        self._last_failure_time = None
    
    def record_failure(self) -> None:
        """Increment failures, open circuit if threshold reached."""
        self._failures += 1
        self._last_failure_time = datetime.utcnow()
        
        if self._failures >= self.failure_threshold:
            self._state = "open"
    
    def can_execute(self) -> bool:
        """Check if execution should proceed."""
        if self._state == "closed":
            return True
        
        if self._state == "open":
            # Check if recovery timeout passed
            if self._last_failure_time:
                elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self._state = "half_open"
                    return True
            return False
        
        return True  # half_open allows one attempt


def calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay with exponential backoff and jitter."""
    # Exponential: base * (2 ^ attempt)
    delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        # Add random jitter: +/- 50% of jitter_max
        jitter = random.uniform(-config.jitter_max / 2, config.jitter_max / 2)
        delay = max(0, delay + jitter)
    
    return delay


def retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    jitter_max: float = 1.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    circuit_breaker: Optional[CircuitBreaker] = None,
    on_retry: Optional[Callable[[Exception, int], None]] = None,
    on_giveup: Optional[Callable[[Exception], None]] = None,
):
    """Async retry decorator with exponential backoff."""
    
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
        jitter_max=jitter_max,
        exceptions=exceptions,
        on_retry=on_retry,
        on_giveup=on_giveup,
    )
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Check circuit breaker
            if circuit_breaker and not circuit_breaker.can_execute():
                raise CircuitOpenError(f"Circuit breaker open for {func.__name__}")
            
            last_exception: Optional[Exception] = None
            
            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)
                    
                    # Record success for circuit breaker
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    
                    return result
                    
                except config.exceptions as e:
                    last_exception = e
                    
                    # Record failure for circuit breaker
                    if circuit_breaker:
                        circuit_breaker.record_failure()
                        if not circuit_breaker.can_execute():
                            raise CircuitOpenError(f"Circuit opened after {attempt} failures") from e
                    
                    # Don't retry on last attempt
                    if attempt == config.max_attempts:
                        break
                    
                    # Callback
                    if config.on_retry:
                        config.on_retry(e, attempt)
                    
                    # Calculate and sleep
                    delay = calculate_delay(attempt, config)
                    await asyncio.sleep(delay)
            
            # All retries exhausted
            if config.on_giveup:
                config.on_giveup(last_exception)
            
            raise last_exception
        
        return wrapper
    return decorator


# === Usage Examples ===

import aiohttp

# 1. Basic retry on network errors
@retry(
    max_attempts=3,
    base_delay=1.0,
    exceptions=(aiohttp.ClientError, asyncio.TimeoutError)
)
async def fetch_price(symbol: str) -> dict:
    """Fetch with auto-retry on network failures."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.exchange.com/price/{symbol}", timeout=10) as resp:
            return await resp.json()


# 2. With circuit breaker for failing endpoints
circuit = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

@retry(
    max_attempts=3,
    circuit_breaker=circuit,
    exceptions=(aiohttp.ClientError,)
)
async def place_order(order: dict) -> dict:
    """Fail fast if exchange is down."""
    async with aiohttp.ClientSession() as session:
        async with session.post("https://api.exchange.com/order", json=order) as resp:
            return await resp.json()


# 3. With callbacks for logging/metrics
async def log_retry(exception: Exception, attempt: int):
    print(f"[Attempt {attempt}] Retrying after: {type(exception).__name__}")

async def log_giveup(exception: Exception):
    print(f"[GIVE UP] All retries failed: {exception}")

@retry(
    max_attempts=5,
    base_delay=0.5,
    max_delay=30.0,
    on_retry=log_retry,
    on_giveup=log_giveup,
    exceptions=(ConnectionError,)
)
async def connect_websocket(url: str):
    """WebSocket connection with logging."""
    # Connection logic here
    pass


# 4. Selective retry (don't retry 4xx errors)
class NonRetryableError(Exception):
    """Don't retry client errors like 400, 401, 403."""
    pass

async def api_call_with_selective_retry():
    @retry(
        max_attempts=3,
        base_delay=1.0,
        exceptions=(aiohttp.ClientConnectionError, asyncio.TimeoutError),  # Retry only these
    )
    async def _call():
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.example.com/data") as resp:
                if resp.status == 429:  # Rate limited
                    raise asyncio.TimeoutError("Rate limited, will retry")
                if resp.status >= 500:  # Server error
                    raise aiohttp.ClientConnectionError(f"Server error {resp.status}")
                if resp.status >= 400:  # Client error — don't retry
                    raise NonRetryableError(f"Client error {resp.status}")
                return await resp.json()
    
    return await _call()


# 5. Different strategies for different endpoints
price_circuit = CircuitBreaker(failure_threshold=3)  # Fast fail for price
order_circuit = CircuitBreaker(failure_threshold=10)  # More tolerant for orders

@retry(max_attempts=5, base_delay=0.5, circuit_breaker=price_circuit)
async def get_market_data():
    pass  # Price feeds: fast retry

@retry(max_attempts=3, base_delay=2.0, circuit_breaker=order_circuit)
async def submit_order():
    pass  # Orders: slower retry, more failures allowed


# 6. Test the delays
async def test_delays():
    config = RetryConfig(base_delay=1.0, exponential_base=2.0, jitter=False)
    
    for attempt in range(1, 6):
        delay = calculate_delay(attempt, config)
        print(f"Attempt {attempt}: {delay:.2f}s delay")
    
    # Output:
    # Attempt 1: 1.00s
    # Attempt 2: 2.00s
    # Attempt 3: 4.00s
    # Attempt 4: 8.00s
    # Attempt 5: 16.00s


# Run test
# asyncio.run(test_delays())
```

## Why This Pattern

| Problem | Solution |
|---------|----------|
| API flakiness | Exponential backoff gives servers time to recover |
| Thundering herd | Jitter randomizes retry times across clients |
| Cascading failures | Circuit breaker stops hammering failing services |
| Silent failures | Callbacks enable logging and alerting |
| Wrong retries | Selective exception types prevent pointless retries |

## Delay Formula

```
delay = min(base_delay * (exponential_base ^ (attempt - 1)), max_delay)
if jitter:
    delay += random.uniform(-jitter_max/2, +jitter_max/2)
```

## Circuit Breaker States

```
CLOSED  →  Execution succeeds → stay CLOSED
           Execution fails  → increment counter
           Counter >= threshold → OPEN

OPEN    →  Block execution
           Timeout elapsed → HALF_OPEN

HALF_OPEN →  One execution attempt
             Success → CLOSED
             Failure → OPEN (counter reset)
```

## Quick Config Recipes

```python
# Fast retry (API calls)
@retry(max_attempts=3, base_delay=0.5, max_delay=5.0)

# Slow retry (database connections)
@retry(max_attempts=5, base_delay=2.0, max_delay=60.0)

# Critical path (fail fast)
@retry(max_attempts=2, base_delay=0.1, circuit_breaker=circuit)

# Tolerant (keep trying)
@retry(max_attempts=10, base_delay=1.0, max_delay=30.0)
```

---
*Pattern: Async retry with exponential backoff + circuit breaker*
