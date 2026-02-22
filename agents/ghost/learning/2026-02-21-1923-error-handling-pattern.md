# Error Classification & Handling Pattern
*Ghost Learning | 2026-02-21*

Structured error handling for trading systems with classification, retry logic, and circuit breakers.

```python
"""
Structured Error Classification & Handling Pattern
Categorize errors by severity and apply appropriate handling strategies.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Callable, Any
import asyncio
import logging
from functools import wraps


class ErrorSeverity(Enum):
    """Error severity levels."""
    TRANSIENT = auto()      # Retry expected to succeed
    RECOVERABLE = auto()    # May succeed on retry with backoff
    CRITICAL = auto()       # Requires immediate attention
    FATAL = auto()          # System shutdown required
    IGNORE = auto()         # Log and continue


class ErrorCategory(Enum):
    """Trading-specific error categories."""
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "auth"
    INSUFFICIENT_FUNDS = "funds"
    ORDER_REJECTED = "order"
    MARKET_DATA = "market_data"
    EXCHANGE_ERROR = "exchange"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class TradingError(Exception):
    """Structured trading error with metadata."""
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    retryable: bool = False
    original_error: Optional[Exception] = None
    context: dict = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        super().__init__(self.message)


class ErrorClassifier:
    """Classify exceptions into structured trading errors."""
    
    @staticmethod
    def classify(error: Exception, context: dict = None) -> TradingError:
        """Classify any exception into trading error."""
        error_str = str(error).lower()
        
        # Network errors
        if any(kw in error_str for kw in ['connection', 'timeout', 'reset', 'refused', 'closed']):
            return TradingError(
                message=str(error),
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.TRANSIENT,
                retryable=True,
                original_error=error,
                context=context
            )
        
        # Rate limiting
        if any(kw in error_str for kw in ['rate limit', '429', 'too many requests', 'throttle']):
            return TradingError(
                message=str(error),
                category=ErrorCategory.RATE_LIMIT,
                severity=ErrorSeverity.RECOVERABLE,
                retryable=True,
                original_error=error,
                context=context
            )
        
        # Authentication
        if any(kw in error_str for kw in ['auth', 'key', 'permission', 'unauthorized', '403', '401']):
            return TradingError(
                message=str(error),
                category=ErrorCategory.AUTHENTICATION,
                severity=ErrorSeverity.FATAL,
                retryable=False,
                original_error=error,
                context=context
            )
        
        # Insufficient funds
        if any(kw in error_str for kw in ['insufficient', 'margin', 'balance', 'funds']):
            return TradingError(
                message=str(error),
                category=ErrorCategory.INSUFFICIENT_FUNDS,
                severity=ErrorSeverity.CRITICAL,
                retryable=False,
                original_error=error,
                context=context
            )
        
        # Order rejection
        if any(kw in error_str for kw in ['reject', 'invalid order', 'price', 'size']):
            return TradingError(
                message=str(error),
                category=ErrorCategory.ORDER_REJECTED,
                severity=ErrorSeverity.CRITICAL,
                retryable=False,
                original_error=error,
                context=context
            )
        
        # Exchange errors
        if any(kw in error_str for kw in ['exchange', 'api', 'server', '500', '502', '503']):
            return TradingError(
                message=str(error),
                category=ErrorCategory.EXCHANGE_ERROR,
                severity=ErrorSeverity.TRANSIENT,
                retryable=True,
                original_error=error,
                context=context
            )
        
        # Default
        return TradingError(
            message=str(error),
            category=ErrorCategory.UNKNOWN,
            severity=ErrorSeverity.RECOVERABLE,
            retryable=True,
            original_error=error,
            context=context
        )


@dataclass
class ErrorHandler:
    """Centralized error handling with strategies."""
    logger: logging.Logger = None
    alert_callback: Optional[Callable[[TradingError], None]] = None
    circuit_breaker: Any = None
    
    def __post_init__(self):
        if self.logger is None:
            self.logger = logging.getLogger("trading.errors")
    
    async def handle(self, error: TradingError, operation: str = "") -> None:
        """Handle error based on severity."""
        
        # Always log
        self._log_error(error, operation)
        
        # Severity-specific handling
        if error.severity == ErrorSeverity.IGNORE:
            return
        
        elif error.severity == ErrorSeverity.TRANSIENT:
            self.logger.debug(f"Transient error in {operation}: {error.message}")
            # Retry handled by decorator
        
        elif error.severity == ErrorSeverity.RECOVERABLE:
            self.logger.warning(f"Recoverable error in {operation}: {error.message}")
            # May retry with backoff
        
        elif error.severity == ErrorSeverity.CRITICAL:
            self.logger.error(f"CRITICAL error in {operation}: {error.message}")
            if self.alert_callback:
                await self._alert(error)
            # Don't retry, but don't stop system
        
        elif error.severity == ErrorSeverity.FATAL:
            self.logger.critical(f"FATAL error in {operation}: {error.message}")
            if self.alert_callback:
                await self._alert(error)
            # Consider graceful shutdown
            raise error
    
    def _log_error(self, error: TradingError, operation: str) -> None:
        """Structured logging."""
        self.logger.log(
            self._log_level(error.severity),
            f"[{error.category.value}] {operation}: {error.message}",
            extra={
                "severity": error.severity.name,
                "category": error.category.value,
                "retryable": error.retryable,
                "context": error.context
            }
        )
    
    def _log_level(self, severity: ErrorSeverity) -> int:
        """Map severity to log level."""
        mapping = {
            ErrorSeverity.IGNORE: logging.DEBUG,
            ErrorSeverity.TRANSIENT: logging.DEBUG,
            ErrorSeverity.RECOVERABLE: logging.WARNING,
            ErrorSeverity.CRITICAL: logging.ERROR,
            ErrorSeverity.FATAL: logging.CRITICAL
        }
        return mapping.get(severity, logging.ERROR)
    
    async def _alert(self, error: TradingError) -> None:
        """Send alert for critical errors."""
        if self.alert_callback:
            try:
                await self.alert_callback(error)
            except Exception as e:
                self.logger.error(f"Alert failed: {e}")


# === Circuit Breaker Pattern ===

class CircuitBreaker:
    """Prevent cascading failures."""
    
    def __init__(self, failure_threshold: int = 5, recovery_time: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = 0
        self.last_failure_time = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def record_success(self) -> None:
        """Reset on success."""
        self.failures = 0
        self.state = "CLOSED"
    
    def record_failure(self) -> None:
        """Increment failures."""
        self.failures += 1
        self.last_failure_time = asyncio.get_event_loop().time()
        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
    
    def can_execute(self) -> bool:
        """Check if operation should proceed."""
        if self.state == "CLOSED":
            return True
        
        if self.state == "OPEN":
            elapsed = asyncio.get_event_loop().time() - self.last_failure_time
            if elapsed >= self.recovery_time:
                self.state = "HALF_OPEN"
                return True
            return False
        
        return True  # HALF_OPEN allows one attempt


# === Decorator for auto-classification ===

def with_error_handling(
    handler: ErrorHandler,
    retry_transient: bool = True,
    max_retries: int = 3,
    circuit_breaker: Optional[CircuitBreaker] = None
):
    """Decorator for automatic error classification and handling."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 0
            
            while attempt <= max_retries:
                # Check circuit breaker
                if circuit_breaker and not circuit_breaker.can_execute():
                    raise TradingError(
                        message="Circuit breaker open",
                        category=ErrorCategory.SYSTEM,
                        severity=ErrorSeverity.CRITICAL,
                        retryable=False
                    )
                
                try:
                    result = await func(*args, **kwargs)
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    return result
                    
                except TradingError as e:
                    await handler.handle(e, func.__name__)
                    
                    if not e.retryable or attempt == max_retries:
                        if circuit_breaker:
                            circuit_breaker.record_failure()
                        raise
                    
                    # Retry with exponential backoff
                    if retry_transient and e.severity in [ErrorSeverity.TRANSIENT, ErrorSeverity.RECOVERABLE]:
                        delay = 2 ** attempt
                        await asyncio.sleep(min(delay, 60))
                        attempt += 1
                    else:
                        if circuit_breaker:
                            circuit_breaker.record_failure()
                        raise
                        
                except Exception as e:
                    # Classify unknown error
                    error = ErrorClassifier.classify(e, {"args": args, "kwargs": kwargs})
                    await handler.handle(error, func.__name__)
                    
                    if circuit_breaker:
                        circuit_breaker.record_failure()
                    
                    if not error.retryable or attempt == max_retries:
                        raise
                    
                    attempt += 1
        
        return wrapper
    return decorator


# === Usage Example ===

async def example():
    """Demonstrate error handling."""
    handler = ErrorHandler()
    circuit = CircuitBreaker(failure_threshold=3)
    
    @with_error_handling(handler, circuit_breaker=circuit)
    async def place_order(symbol: str, size: float):
        """Simulate order placement."""
        import random
        
        errors = [
            ConnectionResetError("Connection reset"),
            TimeoutError("Request timeout"),
            TradingError("Insufficient funds", ErrorCategory.INSUFFICIENT_FUNDS, ErrorSeverity.CRITICAL),
            Exception("Unknown error"),
            None  # Success
        ]
        
        error = random.choice(errors)
        if error:
            raise error
        
        return {"order_id": "123", "filled": size}
    
    # Simulate calls
    for i in range(10):
        try:
            result = await place_order("BTCUSD", 0.5)
            print(f"Call {i+1}: Success - {result}")
        except Exception as e:
            print(f"Call {i+1}: Failed - {e}")
        await asyncio.sleep(0.1)


# Run: asyncio.run(example())
```

## Error Severity Strategy

| Severity | Behavior | Retry | Alert |
|----------|----------|-------|-------|
| IGNORE | Log debug | No | No |
| TRANSIENT | Retry immediately | Yes (3x) | No |
| RECOVERABLE | Retry with backoff | Yes (3x with delay) | No |
| CRITICAL | Log error, alert | No | Yes |
| FATAL | Alert, may shutdown | No | Yes (urgent) |

## Error Categories

| Category | Examples | Handling |
|----------|----------|----------|
| NETWORK | Timeout, Connection reset | Retry with backoff |
| RATE_LIMIT | 429, Throttle | Wait, retry |
| AUTHENTICATION | Invalid key, 403 | Stop, alert |
| INSUFFICIENT_FUNDS | Margin call, Low balance | Skip trade, alert |
| ORDER_REJECTED | Invalid price, Too small | Log, skip |
| EXCHANGE_ERROR | 500, 503 | Retry with circuit breaker |

## Quick Integration

```python
handler = ErrorHandler(
    alert_callback=lambda e: send_telegram_alert(f"🚨 {e.category}: {e.message}"),
    circuit_breaker=CircuitBreaker(failure_threshold=5)
)

@with_error_handling(handler, retry_transient=True)
async def fetch_price(symbol: str) -> dict:
    # Auto-classifies and handles errors
    return await exchange.get_price(symbol)
```

## Benefits

- **Structured**: Every error has category, severity, retryable flag
- **Observable**: Structured logging with context
- **Resilient**: Automatic retry for transient errors
- **Safe**: Circuit breaker prevents cascading failures
- **Actionable**: Alerts only for critical/fatal issues

---
*Pattern: Structured Error Classification & Handling*
