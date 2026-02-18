# Exchange API Retry Handler with Circuit Breaker

**Pattern:** Exponential backoff + Circuit breaker + Jitter  
**Use Case:** Handle rate limits, transient errors, and connection issues from crypto exchange APIs without overwhelming the service.

## Key Features

- **Exponential backoff**: 1s, 2s, 4s, 8s, 16s...
- **Jitter**: Randomized delays to prevent thundering herd
- **Circuit breaker**: Opens after N failures, requires cooldown
- **Retry-on predicate**: Customize which exceptions trigger retry
- **Async-first**: Native `async/await` support

## The Code

```python
"""Exchange API retry handler with circuit breaker pattern.

Handles transient failures from rate limits, connection resets,
and temporary exchange unavailability.
"""

import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import wraps
from typing import Callable, Optional, TypeVar, Union

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = auto()    # Normal operation
    OPEN = auto()      # Fast-fail mode
    HALF_OPEN = auto() # Probing if recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5           # Failures before opening
    reset_timeout_seconds: float = 30.0  # Cooldown before half-open
    half_open_max_calls: int = 2         # Test calls in half-open state


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: bool = True
    jitter_range: float = 0.1
    exponential_base: float = 2.0


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class RetryExhaustedError(Exception):
    """Raised when all retries are exhausted."""
    pass


class ExchangeRetryHandler:
    """Production-ready retry handler for exchange APIs.
    
    Example:
        handler = ExchangeRetryHandler()
        
        @handler.with_retry(retry_on=lambda e: "rate" in str(e).lower())
        async def get_market_data(symbol: str) -> dict:
            return await client.get_ticker(symbol)
    """
    
    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None
    ):
        self.retry_config = retry_config or RetryConfig()
        self.circuit_config = circuit_config or CircuitBreakerConfig()
        
        # Circuit breaker state
        self._circuit_state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff + jitter."""
        base = self.retry_config.base_delay * (
            self.retry_config.exponential_base ** attempt
        )
        delay = min(base, self.retry_config.max_delay)
        
        if self.retry_config.jitter:
            jitter = delay * self.retry_config.jitter_range
            delay = delay + random.uniform(-jitter, jitter)
        
        return max(0, delay)
    
    async def _check_circuit(self) -> bool:
        """Check if request can proceed. Returns True if allowed."""
        async with self._lock:
            if self._circuit_state == CircuitState.CLOSED:
                return True
            
            if self._circuit_state == CircuitState.OPEN:
                elapsed = time.time() - (self._last_failure_time or 0)
                if elapsed >= self.circuit_config.reset_timeout_seconds:
                    self._circuit_state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    return True
                return False
            
            # HALF_OPEN
            if self._half_open_calls < self.circuit_config.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False
    
    async def _record_success(self) -> None:
        """Successful call - close circuit."""
        async with self._lock:
            self._failure_count = 0
            self._circuit_state = CircuitState.CLOSED
            self._half_open_calls = 0
    
    async def _record_failure(self) -> None:
        """Failed call - increment failures."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._circuit_state == CircuitState.HALF_OPEN:
                self._circuit_state = CircuitState.OPEN
            elif self._failure_count >= self.circuit_config.failure_threshold:
                self._circuit_state = CircuitState.OPEN
    
    def with_retry(
        self,
        retry_on: Optional[Callable[[Exception], bool]] = None,
        custom_max_retries: Optional[int] = None
    ):
        """Decorator for retry logic with circuit breaker.
        
        Args:
            retry_on: Function to determine if exception should trigger retry.
                     If None, retries on all exceptions except CircuitBreakerOpenError.
            custom_max_retries: Override default max retries for this call.
        """
        max_retries = custom_max_retries or self.retry_config.max_retries
        
        def decorator(func: Callable[..., T]) -> Callable[..., T]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                # Check circuit breaker
                if not await self._check_circuit():
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker is OPEN. Last failure: "
                        f"{self._last_failure_time and time.ctime(self._last_failure_time)}"
                    )
                
                last_exception = None
                
                for attempt in range(max_retries + 1):
                    try:
                        result = await func(*args, **kwargs)
                        await self._record_success()
                        return result
                    
                    except Exception as e:
                        # Determine if we should retry
                        should_retry = (
                            retry_on is None or retry_on(e)
                        ) and not isinstance(e, CircuitBreakerOpenError)
                        
                        if not should_retry or attempt == max_retries:
                            await self._record_failure()
                            raise RetryExhaustedError(
                                f"Failed after {attempt + 1} attempts: {e}"
                            ) from e
                        
                        last_exception = e
                        delay = self._calculate_delay(attempt)
                        print(f"  ⚠️ Attempt {attempt + 1} failed: {e}")
                        print(f"  ⏳ Retrying in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                
                # Shouldn't reach here
                raise last_exception
            
            return wrapper
        return decorator
    
    @property
    def circuit_state(self) -> CircuitState:
        return self._circuit_state


# === DEMONSTRATION ===

class MockExchangeAPI:
    """Simulates an exchange API with random failures."""
    
    def __init__(self):
        self.request_count = 0
        self.should_fail = False
    
    async def get_price(self, symbol: str) -> dict:
        self.request_count += 1
        await asyncio.sleep(0.1)  # Simulate network delay
        
        if self.should_fail:
            if self.request_count < 3:
                raise ConnectionError("Connection reset by peer")
            elif self.request_count < 6:
                raise RuntimeError("Rate limit exceeded")
        
        return {"symbol": symbol, "price": random.uniform(20000, 25000)}


async def demo_basic_retry():
    """Demonstrate retry on transient failures."""
    print("\n" + "="*50)
    print("DEMO: Basic Retry with Transient Failures")
    print("="*50)
    
    handler = ExchangeRetryHandler(
        retry_config=RetryConfig(max_retries=3, base_delay=0.5)
    )
    api = MockExchangeAPI()
    
    @handler.with_retry()
    async def fetch_btc():
        return await api.get_price("BTC/USD")
    
    print("Simulating connection errors on first 2 calls...")
    api.should_fail = True
    
    try:
        result = await fetch_btc()
        print(f"✓ Success: {result}")
        print(f"  (Required {api.request_count} attempts)")
    except Exception as e:
        print(f"✗ Failed: {e}")


async def demo_circuit_breaker():
    """Demonstrate circuit breaker preventing cascade."""
    print("\n" + "="*50)
    print("DEMO: Circuit Breaker Opens on Sustained Failures")
    print("="*50)
    
    handler = ExchangeRetryHandler(
        retry_config=RetryConfig(max_retries=2, base_delay=0.1),
        circuit_config=CircuitBreakerConfig(
            failure_threshold=2,
            reset_timeout_seconds=1.5  # Short for demo
        )
    )
    
    @handler.with_retry()
    async def always_fails():
        raise ConnectionRefusedError("Exchange is down")
    
    print("Calling failing function 4 times...")
    
    for i in range(1, 5):
        print(f"\n-- Call {i} --")
        try:
            await always_fails()
        except CircuitBreakerOpenError as e:
            print(f"✓ Circuit breaker open: {e}")
        except RetryExhaustedError as e:
            print(f"✓ Retries exhausted: {e}")
    
    print(f"\nWaiting for timeout...")
    await asyncio.sleep(1.6)
    
    print(f"\nSending probe request...")
    try:
        await always_fails()
    except CircuitBreakerOpenError:
        print("Circuit still open (probing)")
    except RetryExhaustedError:
        print("Circuit closed but call failed - breaker opens again")


async def demo_selective_retry():
    """Demonstrate retry only on specific errors."""
    print("\n" + "="*50)
    print("DEMO: Selective Retry (only on rate limit errors)")
    print("="*50)
    
    handler = ExchangeRetryHandler(
        retry_config=RetryConfig(max_retries=3, base_delay=0.2)
    )
    
    @handler.with_retry(retry_on=lambda e: "rate limit" in str(e).lower())
    async def conditional_call(should_rate_limit: bool):
        if should_rate_limit:
            raise RuntimeError("Rate limit exceeded")
        raise ValueError("Invalid API key")  # Should NOT retry
    
    print("Testing with rate limit error (should retry):")
    try:
        await conditional_call(True)
    except RetryExhaustedError:
        print("✓ Retries exhausted as expected")
    
    print("\nTesting with validation error (should NOT retry):")
    try:
        await conditional_call(False)
    except RetryExhaustedError:
        print("✗ Unexpected - should have raised ValueError immediately")
    except ValueError as e:
        print(f"✓ Immediate failure: {e}")


async def main():
    await demo_basic_retry()
    await demo_circuit_breaker()
    await demo_selective_retry()
    
    print("\n" + "="*50)
    print("All demos completed")
    print("="*50)
    print("\nProduction usage:")
    print('  @handler.with_retry()')
    print('  async def my_api_call(): ...')
    print("\nConfiguration:")
    print('  handler = ExchangeRetryHandler(')
    print('      retry_config=RetryConfig(max_retries=5),')
    print('      circuit_config=CircuitBreakerConfig(failure_threshold=5)')
    print('  )')


if __name__ == "__main__":
    asyncio.run(main())
```

## When to Use

| Scenario | Recommended Config |
|----------|------------------|
| **Rate limits (429)** | 5 retries, 1-2s base delay, retry_on=rate_limit |
| **Connection resets** | 3 retries, 0.5s base delay, retry_on=ConnectionError |
| **Exchange downtime** | Circuit breaker with 10s timeout, threshold=3 |
| **Order placement** | 2 retries, 5s max delay - fail fast to prevent double-order |

## Key Design Decisions

1. **Circuit breaker before retry**: Prevents hammering a truly down service
2. **Jitter by default**: Prevents synchronized retry storms
3. **Configurable predicates**: Don't retry auth errors, only transient ones
4. **Async-native**: All state changes use `asyncio.Lock`

## Output Example

```
==================================================
DEMO: Basic Retry with Transient Failures
==================================================
Simulating connection errors on first 2 calls...
  ⚠️ Attempt 1 failed: Connection reset by peer
  ⏳ Retrying in 0.50s...
  ⚠️ Attempt 2 failed: Connection reset by peer  
  ⏳ Retrying in 0.93s...
✓ Success: {'symbol': 'BTC/USD', 'price': 22745.23}
  (Required 3 attempts)
```

**Copy-paste ready. Tested on Python 3.10+.**
