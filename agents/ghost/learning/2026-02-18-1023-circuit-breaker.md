# Python Pattern: Circuit Breaker for Trading/API Resilience

**Date:** 2026-02-18 | **Time:** 10:23 AM | **Duration:** ~15 min

## The Pattern: Fail Fast, Recover Gracefully

When an external service (exchange API, data feed) is failing, **stop calling it** for a cooldown period. Prevents:
- Cascading failures
- Rate limit exhaustion  
- Wasted compute on doomed requests
- Account locks from repeated bad auth

## Three States

```
CLOSED  →  (failures exceed threshold)  →  OPEN
  ↑                                          |
  └──────── (cooldown expires) ←─────────────┘
                 ↓
              HALF-OPEN (test request)
```

## The Code

```python
"""
Circuit Breaker Pattern for Trading/API Resilience
Fail fast when services are down, auto-recover when healthy.
"""
import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Optional, Any
from functools import wraps
import logging


class CircuitState(Enum):
    CLOSED = auto()      # Normal operation
    OPEN = auto()        # Failing fast
    HALF_OPEN = auto()   # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior."""
    failure_threshold: int = 5          # Failures before opening
    recovery_timeout: float = 30.0      # Seconds before half-open
    half_open_max_calls: int = 3        # Test calls in half-open
    success_threshold: int = 2          # Successes to close circuit


@dataclass
class CircuitBreakerStats:
    """Runtime statistics."""
    failures: int = 0
    successes: int = 0
    last_failure_time: Optional[float] = None
    state_changes: int = 0
    rejected_calls: int = 0


class CircuitOpenError(Exception):
    """Raised when circuit is open (fast fail)."""
    def __init__(self, message: str, cooldown_remaining: float):
        super().__init__(message)
        self.cooldown_remaining = cooldown_remaining


class CircuitBreaker:
    """
    Circuit breaker for resilient API calls.
    
    Usage:
        breaker = CircuitBreaker(name="BinanceAPI")
        
        @breaker.protect
        async def fetch_order_book(symbol: str):
            return await exchange.fetch_order_book(symbol)
        
        # Normal call - protected by circuit breaker
        try:
            data = await fetch_order_book("BTC/USDT")
        except CircuitOpenError:
            # Circuit is open - service likely down
            use_cached_data()
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None,
        on_state_change: Optional[Callable[[CircuitState, CircuitState], None]] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.on_state_change = on_state_change
        
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._half_open_calls = 0
        self._consecutive_successes = 0
        self._lock = asyncio.Lock()
    
    @property
    def state(self) -> CircuitState:
        return self._state
    
    @property
    def stats(self) -> CircuitBreakerStats:
        return self._stats
    
    def _transition_to(self, new_state: CircuitState):
        """Transition to new state with optional callback."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._stats.state_changes += 1
            
            logging.warning(
                f"Circuit '{self.name}': {old_state.name} → {new_state.name}"
            )
            
            if self.on_state_change:
                try:
                    self.on_state_change(old_state, new_state)
                except Exception:
                    pass
            
            # Reset counters on transition
            if new_state == CircuitState.CLOSED:
                self._stats.failures = 0
                self._consecutive_successes = 0
                self._half_open_calls = 0
            elif new_state == CircuitState.OPEN:
                self._half_open_calls = 0
                self._consecutive_successes = 0
            elif new_state == CircuitState.HALF_OPEN:
                self._half_open_calls = 0
                self._consecutive_successes = 0
    
    async def _can_execute(self) -> bool:
        """Check if call should proceed based on current state."""
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self._stats.last_failure_time:
                    elapsed = time.monotonic() - self._stats.last_failure_time
                    if elapsed >= self.config.recovery_timeout:
                        self._transition_to(CircuitState.HALF_OPEN)
                        return True
                    
                    # Still in cooldown
                    self._stats.rejected_calls += 1
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is OPEN. "
                        f"Cooldown: {self.config.recovery_timeout - elapsed:.1f}s remaining",
                        cooldown_remaining=self.config.recovery_timeout - elapsed
                    )
            
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                else:
                    # Max test calls reached, reject until we get results
                    self._stats.rejected_calls += 1
                    raise CircuitOpenError(
                        f"Circuit '{self.name}' is HALF-OPEN (max test calls reached)",
                        cooldown_remaining=0
                    )
            
            return True
    
    async def _record_success(self):
        """Record successful call."""
        async with self._lock:
            self._stats.successes += 1
            
            if self._state == CircuitState.HALF_OPEN:
                self._consecutive_successes += 1
                if self._consecutive_successes >= self.config.success_threshold:
                    self._transition_to(CircuitState.CLOSED)
    
    async def _record_failure(self):
        """Record failed call."""
        async with self._lock:
            self._stats.failures += 1
            self._stats.last_failure_time = time.monotonic()
            
            if self._state == CircuitState.HALF_OPEN:
                # Failed during test - go back to open
                self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._stats.failures >= self.config.failure_threshold:
                    self._transition_to(CircuitState.OPEN)
    
    async def call(self, operation: Callable[..., Any], *args, **kwargs) -> Any:
        """
        Execute operation with circuit breaker protection.
        
        Raises:
            CircuitOpenError: If circuit is open
            Exception: Whatever the operation raises (after recording)
        """
        await self._can_execute()
        
        try:
            if asyncio.iscoroutinefunction(operation):
                result = await operation(*args, **kwargs)
            else:
                result = operation(*args, **kwargs)
            
            await self._record_success()
            return result
            
        except CircuitOpenError:
            raise
        except Exception as e:
            await self._record_failure()
            raise
    
    def protect(self, func: Callable) -> Callable:
        """Decorator to protect a function with this circuit breaker."""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await self.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(self.call(func, *args, **kwargs))
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    def force_open(self):
        """Manually open the circuit (emergency stop)."""
        self._transition_to(CircuitState.OPEN)
        self._stats.last_failure_time = time.monotonic()
    
    def force_close(self):
        """Manually close the circuit (reset)."""
        self._transition_to(CircuitState.CLOSED)


# === TRADING-SPECIFIC EXTENSIONS ===

class TradingCircuitBreakers:
    """
    Pre-configured circuit breakers for trading operations.
    Different operations need different sensitivity.
    """
    
    @staticmethod
    def order_placement() -> CircuitBreaker:
        """For placing orders - very sensitive (fast fail)."""
        return CircuitBreaker(
            name="OrderPlacement",
            config=CircuitBreakerConfig(
                failure_threshold=2,      # Open after 2 failures
                recovery_timeout=10.0,    # 10s cooldown
                half_open_max_calls=1,
                success_threshold=1
            )
        )
    
    @staticmethod
    def market_data() -> CircuitBreaker:
        """For market data - tolerant (can use stale data)."""
        return CircuitBreaker(
            name="MarketData",
            config=CircuitBreakerConfig(
                failure_threshold=10,     # Open after 10 failures
                recovery_timeout=5.0,     # 5s cooldown (data recovers fast)
                half_open_max_calls=3,
                success_threshold=2
            )
        )
    
    @staticmethod
    def balance_fetch() -> CircuitBreaker:
        """For balance/account info - medium sensitivity."""
        return CircuitBreaker(
            name="BalanceFetch",
            config=CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=15.0,
                half_open_max_calls=2,
                success_threshold=2
            )
        )


# === USAGE EXAMPLES ===

async def example_basic_usage():
    """Basic circuit breaker usage."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Circuit Breaker")
    print("="*70)
    
    breaker = CircuitBreaker(name="TestAPI")
    
    # Simulate flaky API
    call_count = 0
    
    async def flaky_api():
        nonlocal call_count
        call_count += 1
        if call_count <= 7:  # Fail first 7 calls
            raise ConnectionError("API is down")
        return {"status": "ok", "data": "result"}
    
    # Try calls - circuit will open after 5 failures
    for i in range(10):
        try:
            result = await breaker.call(flaky_api)
            print(f"Call {i+1}: SUCCESS - {result}")
        except CircuitOpenError as e:
            print(f"Call {i+1}: CIRCUIT OPEN - {e.cooldown_remaining:.1f}s cooldown")
        except ConnectionError as e:
            print(f"Call {i+1}: FAILED - {e}")
        
        await asyncio.sleep(0.1)  # Small delay between calls
    
    print(f"\nFinal state: {breaker.state.name}")
    print(f"Stats: {breaker.stats}")


async def example_decorator():
    """Using decorator pattern."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Decorator Pattern")
    print("="*70)
    
    breaker = TradingCircuitBreakers.market_data()
    
    @breaker.protect
    async def fetch_ticker(symbol: str) -> dict:
        # Simulate occasional failure
        if hash(symbol) % 5 == 0:  # 20% failure rate
            raise TimeoutError("Market data timeout")
        return {"symbol": symbol, "price": 50000.0}
    
    # Make multiple calls
    symbols = ["BTC", "ETH", "SOL", "ADA", "DOT", "LINK", "UNI"]
    
    for symbol in symbols:
        try:
            data = await fetch_ticker(symbol)
            print(f"✓ {symbol}: ${data['price']:,.2f}")
        except CircuitOpenError:
            print(f"✗ {symbol}: Circuit open - using cached data")
        except TimeoutError:
            print(f"✗ {symbol}: Timeout (recorded by breaker)")
    
    print(f"\nCircuit state: {breaker.state.name}")


async def example_trading_scenario():
    """Realistic trading scenario with multiple breakers."""
    print("\n" + "="*70)
    print("EXAMPLE 3: Trading Bot with Circuit Breakers")
    print("="*70)
    
    # Different breakers for different operations
    order_breaker = TradingCircuitBreakers.order_placement()
    data_breaker = TradingCircuitBreakers.market_data()
    
    # Track if we should trade
    can_trade = True
    
    def on_order_state_change(old, new):
        nonlocal can_trade
        if new == CircuitState.OPEN:
            can_trade = False
            print("🚨 ORDER CIRCUIT OPEN - Trading halted!")
        elif new == CircuitState.CLOSED:
            can_trade = True
            print("✅ ORDER CIRCUIT CLOSED - Trading resumed")
    
    order_breaker.on_state_change = on_order_state_change
    
    @data_breaker.protect
    async def get_market_data():
        # Simulate market data fetch
        await asyncio.sleep(0.01)
        return {"bid": 49900, "ask": 50100}
    
    @order_breaker.protect
    async def place_order(side: str, amount: float):
        # Simulate order placement
        await asyncio.sleep(0.01)
        if not can_trade:
            raise RuntimeError("Trading halted")
        return {"order_id": "12345", "status": "filled"}
    
    # Simulate trading loop
    print("\n--- Trading Loop ---")
    
    for i in range(5):
        print(f"\nIteration {i+1}:")
        
        # Always try to get market data (tolerant)
        try:
            market = await get_market_data()
            print(f"  Market: Bid ${market['bid']}, Ask ${market['ask']}")
        except CircuitOpenError:
            print("  Market: Using stale data")
        
        # Only trade if circuits allow
        if can_trade:
            try:
                # Simulate occasional order failure
                if i == 2:
                    raise ConnectionError("Exchange API error")
                
                order = await place_order("buy", 0.1)
                print(f"  Order: Placed #{order['order_id']}")
            except CircuitOpenError:
                print("  Order: BLOCKED - Circuit open")
            except ConnectionError as e:
                print(f"  Order: Failed - {e}")
        else:
            print("  Order: SKIPPED - Trading halted")
    
    print(f"\nFinal states:")
    print(f"  Data: {data_breaker.state.name}")
    print(f"  Order: {order_breaker.state.name}")


async def main():
    """Run all examples."""
    await example_basic_usage()
    await example_decorator()
    await example_trading_scenario()
    
    print("\n" + "="*70)
    print("KEY TAKEAWAYS")
    print("="*70)
    print("""
1. CLOSED state  → Normal operation, failures counted
2. OPEN state    → Fast fail, no calls allowed (cooldown)
3. HALF-OPEN     → Testing recovery with limited calls

Benefits:
- Prevents cascading failures
- Reduces load on struggling services
- Provides clear signals for fallback logic
- Auto-recovery when service heals

Trading-specific configs:
- Order placement: Sensitive (2 failures, 10s cooldown)
- Market data: Tolerant (10 failures, 5s cooldown)
- Balance fetch: Medium (5 failures, 15s cooldown)
    """)


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Features

| Feature | Purpose |
|---------|---------|
| **Three states** | CLOSED → OPEN → HALF-OPEN → CLOSED |
| **Configurable thresholds** | Tune sensitivity per operation |
| **Auto-recovery** | Tests service after cooldown |
| **Decorator support** | `@breaker.protect` for easy wrapping |
| **Trading presets** | Pre-configured for orders/data/balance |
| **State callbacks** | Hook into state changes (alerts, logging) |

## When to Use

- **Exchange APIs** (rate limits, maintenance windows)
- **External data feeds** (intermittent failures)
- **Payment processors** (temporary unavailability)
- **Any external dependency** that can fail

## Quick Rules

1. **Different breakers for different ops** - Orders are critical, market data can stale
2. **Always handle CircuitOpenError** - Have fallback (cached data, skip iteration)
3. **Log state changes** - Important for debugging and monitoring
4. **Tune thresholds** - Start conservative, adjust based on observed failure patterns

---
*End of 15-min learning session*
