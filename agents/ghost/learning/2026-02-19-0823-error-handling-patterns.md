# Python Error Handling Patterns

**Pattern:** Structured exception handling with context, logging, and recovery  
**When to use:** Any production code that must not crash, must report, and may recover.

## The Anti-Pattern (What Not to Do)

```python
# DON'T: Bare except hides bugs
try:
    do_something()
except:  # Catches KeyboardInterrupt, SystemExit, everything!
    pass  # Silent failure = worst failure

# DON'T: Swallow specific errors
try:
    result = api.call()
except Exception:
    result = None  # Now you have None-cascade bugs downstream
```

## The Pattern: Tiered Exception Strategy

```python
"""
Tiered Error Handling Strategy
Tier 1: Expected errors (handle gracefully)
Tier 2: Operational errors (log, alert, degrade)
Tier 3: Programming errors (crash fast in dev, recover in prod)
"""

import logging
import traceback
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Callable, Any
from functools import wraps


# === Tier 1: Expected/Domain Exceptions ===

class TradingError(Exception):
    """Base for all trading domain errors."""
    pass


class InsufficientFundsError(TradingError):
    """Not enough capital for requested trade."""
    def __init__(self, required: float, available: float):
        self.required = required
        self.available = available
        super().__init__(f"Need ${required:,.2f}, have ${available:,.2f}")


class PriceExpiredError(TradingError):
    """Quote/stale price no longer valid."""
    pass


class MarketClosedError(TradingError):
    """Attempted trade outside market hours."""
    pass


# === Tier 2: Operational/External Exceptions ===

class ExternalServiceError(Exception):
    """Broker, exchange, or data provider failure."""
    def __init__(self, service: str, details: str):
        self.service = service
        self.details = details
        super().__init__(f"{service} failed: {details}")


class RateLimitError(ExternalServiceError):
    """API rate limit hit."""
    def __init__(self, retry_after: Optional[int] = None):
        super().__init__("API", "Rate limit exceeded")
        self.retry_after = retry_after


# === Tier 3: Recovery Strategies ===

class RecoveryStrategy(Enum):
    FAIL = auto()        # Let it propagate
    RETRY = auto()       # Retry with backoff
    FALLBACK = auto()    # Use alternative
    IGNORE = auto()      # Safe to skip (idempotent)
    ALERT = auto()       # Notify, then fail


@dataclass
class ErrorContext:
    """Rich context for error handling decisions."""
    operation: str
    criticality: str  # "critical", "high", "medium", "low"
    recovery: RecoveryStrategy
    max_retries: int = 0
    fallback: Optional[Callable] = None


# === Core Handler ===

class ErrorHandler:
    """
    Centralized error handling with context-aware recovery.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("trading.errors")
        self.metrics = {"errors": 0, "retried": 0, "recovered": 0}
    
    def handle(self, error: Exception, context: ErrorContext) -> Any:
        """
        Handle error based on tier and context.
        Returns: Result of recovery, or re-raises
        """
        self.metrics["errors"] += 1
        
        # Log with full context
        self._log_error(error, context)
        
        # Decision tree
        if isinstance(error, TradingError):
            return self._handle_trading_error(error, context)
        elif isinstance(error, ExternalServiceError):
            return self._handle_external_error(error, context)
        else:
            return self._handle_unexpected(error, context)
    
    def _handle_trading_error(self, error: TradingError, ctx: ErrorContext):
        """Domain errors: usually fail gracefully to user."""
        if isinstance(error, InsufficientFundsError):
            raise  # Can't trade without money
        elif isinstance(error, PriceExpiredError):
            if ctx.recovery == RecoveryStrategy.RETRY:
                return self._retry_with_refresh(ctx)
            raise
        else:
            raise
    
    def _handle_external_error(self, error: ExternalServiceError, ctx: ErrorContext):
        """External errors: retry, fallback, or degrade."""
        if isinstance(error, RateLimitError):
            if error.retry_after:
                self._alert(f"Rate limited, retry in {error.retry_after}s")
            raise  # Can't override rate limits
        
        if ctx.recovery == RecoveryStrategy.RETRY and ctx.max_retries > 0:
            return self._with_retry(ctx)
        elif ctx.recovery == RecoveryStrategy.FALLBACK and ctx.fallback:
            self.metrics["recovered"] += 1
            return ctx.fallback()
        elif ctx.recovery == RecoveryStrategy.ALERT:
            self._alert(f"Critical: {error}")
            raise
        else:
            raise
    
    def _handle_unexpected(self, error: Exception, ctx: ErrorContext):
        """Unexpected errors: alert, then re-raise."""
        self._alert(f"UNEXPECTED: {error}\n{traceback.format_exc()}")
        raise
    
    def _log_error(self, error: Exception, ctx: ErrorContext):
        """Structured logging for observability."""
        self.logger.error(
            f"[{ctx.criticality.upper()}] {ctx.operation}: {error}",
            extra={"error_type": type(error).__name__, "context": ctx}
        )
    
    def _alert(self, message: str):
        """Send alert (in real app: Slack, PagerDuty, etc)."""
        print(f"🚨 ALERT: {message}")
    
    def _with_retry(self, ctx: ErrorContext) -> Any:
        """Decorator-style retry (simplified)."""
        self.metrics["retried"] += 1
        # Actual retry logic would be in decorator
        raise NotImplementedError("Use @with_retries decorator")
    
    def _retry_with_refresh(self, ctx: ErrorContext) -> Any:
        """Retry with fresh data."""
        self.logger.info(f"Retrying {ctx.operation} with refresh")
        return None  # Placeholder


# === Decorators for Easy Use ===

def with_retries(max_retries: int = 3, backoff: float = 1.0):
    """Decorator: retry function with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except ExternalServiceError as e:
                    if attempt == max_retries:
                        raise
                    delay = backoff * (2 ** attempt)
                    logging.warning(f"Retry {attempt + 1}/{max_retries} in {delay}s: {e}")
                    import time
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


def safe_execute(
    context: ErrorContext,
    error_handler: Optional[ErrorHandler] = None
):
    """Decorator: wrap function with error handling context."""
    handler = error_handler or ErrorHandler()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return handler.handle(e, context)
        return wrapper
    return decorator


# === Practical Examples ===

class OrderManager:
    """Example: Trading order manager with proper error handling."""
    
    def __init__(self):
        self.error_handler = ErrorHandler()
        self.balance = 10000.0
    
    def place_order(self, symbol: str, qty: int, price: float):
        """Place order with full error handling."""
        context = ErrorContext(
            operation=f"place_order({symbol})",
            criticality="high",
            recovery=RecoveryStrategy.ALERT,
            max_retries=2
        )
        
        try:
            # Validate
            cost = qty * price
            if cost > self.balance:
                raise InsufficientFundsError(cost, self.balance)
            
            # Execute (simulated)
            if self._is_market_closed():
                raise MarketClosedError()
            
            self._execute_order(symbol, qty, price)
            self.balance -= cost
            
        except TradingError as e:
            # Expected error: clean failure
            self.error_handler.handle(e, context)
            raise  # Re-raise to caller (they should handle gracefully)
            
        except ExternalServiceError as e:
            # Operational error: retry or alert
            return self.error_handler.handle(e, context)
            
        except Exception as e:
            # Unknown: alert immediately
            self.error_handler.handle(e, ErrorContext(
                operation="place_order",
                criticality="critical",
                recovery=RecoveryStrategy.ALERT
            ))
            raise
    
    @with_retries(max_retries=3, backoff=2.0)
    def get_price(self, symbol: str) -> float:
        """Fetch price with auto-retry on API failure."""
        # Simulated external call
        import random
        if random.random() < 0.3:
            raise ExternalServiceError("Broker API", "Connection timeout")
        return 150.0
    
    def _is_market_closed(self) -> bool:
        return False
    
    def _execute_order(self, symbol: str, qty: int, price: float):
        print(f"Executed: {qty} {symbol} @ ${price}")


# === Demo ===

if __name__ == "__main__":
    manager = OrderManager()
    
    print("=== Test 1: Normal order ===")
    try:
        manager.place_order("AAPL", 10, 150.0)
    except Exception as e:
        print(f"Failed: {e}")
    
    print("\n=== Test 2: Insufficient funds ===")
    try:
        manager.place_order("AAPL", 1000, 150.0)  # $150K needed
    except InsufficientFundsError as e:
        print(f"Handled gracefully: {e}")
    
    print("\n=== Test 3: Retry on external error ===")
    try:
        price = manager.get_price("AAPL")
        print(f"Got price: ${price}")
    except ExternalServiceError as e:
        print(f"Failed after retries: {e}")
    
    print(f"\n=== Metrics ===")
    print(manager.error_handler.metrics)
```

## Pattern Summary

| Tier | Exception Type | Strategy | Example |
|------|---------------|----------|---------|
| **1** | Domain/Trading | Clean failure | `InsufficientFundsError` → reject order |
| **2** | External/Operational | Retry + fallback | `ExternalServiceError` → retry → alert |
| **3** | Unexpected | Alert + crash | `KeyError` → alert + log + raise |

## Key Rules

```python
# 1. Never catch Exception or bare except
def bad():
    try: risky()
    except: pass  # Hides bugs!

def good():
    try: risky()
    except RiskError as e:  # Specific!
        handle(e)

# 2. Add context to errors
def better():
    try: risky(operation_id)
    except NetworkError as e:
        raise OrderFailedError(operation_id) from e

# 3. Prefer early validation over try/except
if balance < required:
    raise InsufficientFundsError()  # Don't catch KeyError later

# 4. Log once, handle once
try: work()
except TradingError as e:
    log.exception(e)  # Log here
    raise  # Re-raise, don't wrap again
```

## When to Use Which Pattern

- **Tier 1 (Domain):** Business logic validation, use custom exceptions
- **Tier 2 (Operational):** Network, disk, external APIs, use retry + fallback
- **Tier 3 (Unexpected):** Programming errors, alert and fail fast in dev

---

**Created by Ghost 👻 | Feb 19, 2026 | 14-min learning sprint**  
*Pattern: Fail gracefully on expected, recover on operational, alert on unexpected*
