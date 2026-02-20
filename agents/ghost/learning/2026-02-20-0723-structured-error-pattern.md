# Structured Error Pattern — Context-Rich Exceptions

**Purpose:** Capture full context at error origin for faster debugging  
**Use Case:** APIs, data pipelines, trading systems — anywhere errors need context

## The Pattern

```python
"""
Structured Error Pattern
Rich context at exception origin + automatic severity classification.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List, Callable
from enum import Enum, auto
import traceback
import json


class ErrorSeverity(Enum):
    DEBUG = auto()      # Info only, no action
    WARNING = auto()    # Logged, non-blocking
    ERROR = auto()      # Raised, catchable, retry possible
    CRITICAL = auto()   # Raised, no retry, alert sent
    FATAL = auto()      # Terminates process


@dataclass
class ErrorContext:
    """Rich context captured at error point."""
    operation: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    state: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: Optional[str] = None
    file: Optional[str] = None
    line: Optional[int] = None
    function: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "operation": self.operation,
            "inputs": self.inputs,
            "state": self.state,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "location": f"{self.file}:{self.line}" if self.file else None,
            "function": self.function
        }


class StructuredError(Exception):
    """
    Base exception with rich context.
    
    Usage:
        raise StructuredError(
            message="Order failed",
            severity=ErrorSeverity.ERROR,
            context={"symbol": "AAPL", "qty": 100}
        )
    """
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
        retry_allowed: Optional[bool] = None,
        cause: Optional[Exception] = None,
        suggestions: Optional[List[str]] = None
    ):
        super().__init__(message)
        self.message = message
        self.severity = severity
        self.context = ErrorContext(operation=message, **(context or {}))
        self.error_code = error_code or self._generate_code()
        self.cause = cause
        self.suggestions = suggestions or []
        self.stack = traceback.format_exc() if cause else traceback.format_stack()[:-1]
        
        # Auto-determine retry if not specified
        if retry_allowed is None:
            self.retry_allowed = severity in (ErrorSeverity.WARNING, ErrorSeverity.ERROR)
        else:
            self.retry_allowed = retry_allowed
    
    def _generate_code(self) -> str:
        """Generate error code from class name."""
        prefix = self.__class__.__name__.replace("Error", "").upper()[:4]
        return f"{prefix}_{hash(self.message) % 10000:04d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for logging/APIs."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "severity": self.severity.name,
            "retry_allowed": self.retry_allowed,
            "context": self.context.to_dict(),
            "suggestions": self.suggestions,
            "cause": str(self.cause) if self.cause else None,
            "stack": self.stack if isinstance(self.stack, str) else None
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def __str__(self) -> str:
        ctx = f" | context: {self.context.inputs}" if self.context.inputs else ""
        return f"[{self.error_code}] {self.message}{ctx}"


# Domain-specific errors
class ValidationError(StructuredError):
    """Input validation failed."""
    
    def __init__(self, field: str, value: Any, reason: str, **kwargs):
        super().__init__(
            message=f"Validation failed for '{field}': {reason}",
            severity=ErrorSeverity.ERROR,
            context={"field": field, "value": value, **(kwargs.get("context", {}))},
            error_code=f"VAL_{field.upper()[:6]}",
            retry_allowed=False,
            **kwargs
        )
        self.field = field
        self.invalid_value = value


class NetworkError(StructuredError):
    """Network operation failed."""
    
    def __init__(self, endpoint: str, **kwargs):
        super().__init__(
            message=f"Network request failed: {endpoint}",
            severity=ErrorSeverity.ERROR,
            context={"endpoint": endpoint, **(kwargs.get("context", {}))},
            error_code="NET_0001",
            retry_allowed=True,
            suggestions=[
                "Check network connectivity",
                "Verify endpoint is accessible",
                "Retry with exponential backoff"
            ],
            **kwargs
        )
        self.endpoint = endpoint


class RateLimitError(StructuredError):
    """Rate limit hit."""
    
    def __init__(self, retry_after: Optional[int] = None, **kwargs):
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after}s" if retry_after else "Rate limit exceeded",
            severity=ErrorSeverity.WARNING,
            context={"retry_after": retry_after, **(kwargs.get("context", {}))},
            error_code="RATE_0001",
            retry_allowed=True,
            suggestions=[
                f"Wait {retry_after}s before retrying" if retry_after else "Implement rate limiting",
                "Consider request batching",
                "Upgrade API tier if available"
            ],
            **kwargs
        )
        self.retry_after = retry_after


class InsufficientFundsError(StructuredError):
    """Not enough funds for operation."""
    
    def __init__(self, required: float, available: float, asset: str = "USD", **kwargs):
        super().__init__(
            message=f"Insufficient {asset}: need {required}, have {available}",
            severity=ErrorSeverity.ERROR,
            context={"required": required, "available": available, "asset": asset},
            error_code="FUNDS_0001",
            retry_allowed=False,
            suggestions=[
                "Reduce order size",
                "Deposit more funds",
                "Wait for settlement (takes 2 days)"
            ],
            **kwargs
        )
        self.shortfall = required - available


class CircuitOpenError(StructuredError):
    """Circuit breaker is open."""
    
    def __init__(self, service: str, open_duration: float, **kwargs):
        super().__init__(
            message=f"Circuit breaker OPEN for {service}",
            severity=ErrorSeverity.CRITICAL,
            context={"service": service, "open_duration_sec": open_duration},
            error_code=f"CIRC_{service.upper()[:4]}",
            retry_allowed=False,
            suggestions=[
                f"Wait {open_duration}s for circuit to close",
                "Use alternative service",
                "Check service health dashboard"
            ],
            **kwargs
        )


# Error handler with strategies
class ErrorHandler:
    """
    Centralized error handling with strategies per severity.
    """
    
    def __init__(self):
        self._handlers: Dict[ErrorSeverity, List[Callable]] = {
            sev: [] for sev in ErrorSeverity
        }
        self._error_counts: Dict[str, int] = {}
        self._alert_threshold = 10
    
    def register(
        self,
        severity: ErrorSeverity,
        handler: Callable[[StructuredError], None]
    ):
        """Register handler for severity level."""
        self._handlers[severity].append(handler)
        return self
    
    def handle(self, error: StructuredError):
        """Process error through registered handlers."""
        # Update counters
        self._error_counts[error.error_code] = self._error_counts.get(error.error_code, 0) + 1
        
        # Run handlers for this severity
        for handler in self._handlers.get(error.severity, []):
            try:
                handler(error)
            except Exception as e:
                print(f"Handler failed: {e}")
        
        # Alert on threshold
        if self._error_counts[error.error_code] >= self._alert_threshold:
            for handler in self._handlers.get(ErrorSeverity.CRITICAL, []):
                handler(error)
        
        # Log based on severity
        if error.severity == ErrorSeverity.FATAL:
            print(f"FATAL: {error.to_json()}")
            raise SystemExit(1)
    
    def get_stats(self) -> Dict[str, int]:
        return self._error_counts.copy()


# Decorator for auto-capture
def with_error_context(operation: str, capture_args: bool = True):
    """
    Decorator that auto-captures context on exception.
    
    Usage:
        @with_error_context("place_order", capture_args=True)
        async def place_order(symbol: str, qty: int, price: float):
            ...
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except StructuredError:
                raise
            except Exception as e:
                # Wrap in StructuredError with context
                ctx = {}
                if capture_args:
                    ctx["args"] = args
                    ctx["kwargs"] = kwargs
                
                raise StructuredError(
                    message=f"Error in {operation}: {str(e)}",
                    severity=ErrorSeverity.ERROR,
                    context={"operation": operation, **ctx},
                    cause=e
                ) from e
        
        wrapper.__name__ = func.__name__
        return wrapper
    return decorator


# Result type for error propagation
class Result:
    """
    Result type that forces error handling.
    
    Usage:
        result = some_operation()
        if result.is_success:
            value = result.value
        else:
            error = result.error
    """
    
    def __init__(self, value: Any = None, error: Optional[StructuredError] = None):
        self._value = value
        self._error = error
        self._is_success = error is None
    
    @property
    def is_success(self) -> bool:
        return self._is_success
    
    @property
    def is_failure(self) -> bool:
        return not self._is_success
    
    @property
    def value(self) -> Any:
        if not self._is_success:
            raise RuntimeError("Cannot get value from failed result")
        return self._value
    
    @property
    def error(self) -> Optional[StructuredError]:
        return self._error
    
    def unwrap_or(self, default: Any) -> Any:
        return self._value if self._is_success else default
    
    def unwrap_or_else(self, fn: Callable[[StructuredError], Any]) -> Any:
        return self._value if self._is_success else fn(self._error)
    
    def map(self, fn: Callable[[Any], Any]) -> 'Result':
        if self._is_success:
            try:
                return Result(value=fn(self._value))
            except Exception as e:
                return Result(error=StructuredError(
                    message=f"Map failed: {e}",
                    cause=e
                ))
        return self
    
    @staticmethod
    def success(value: Any) -> 'Result':
        return Result(value=value)
    
    @staticmethod
    def failure(error: StructuredError) -> 'Result':
        return Result(error=error)


# === Examples ===

def example_validation():
    """Show validation error."""
    print("=" * 60)
    print("Example: Validation Error")
    print("=" * 60)
    
    try:
        order_qty = -100
        if order_qty <= 0:
            raise ValidationError(
                field="quantity",
                value=order_qty,
                reason="must be positive"
            )
    except StructuredError as e:
        print(f"\nCaught: {e}")
        print(f"\nJSON:\n{e.to_json()}")
        print(f"\nRetry allowed: {e.retry_allowed}")


def example_network():
    """Show network error with retry."""
    print("\n" + "=" * 60)
    print("Example: Network Error with Context")
    print("=" * 60)
    
    try:
        endpoint = "https://api.exchange.com/v1/orders"
        raise NetworkError(
            endpoint=endpoint,
            context={
                "method": "POST",
                "payload_size": 256,
                "timeout": 30,
                "attempt": 1
            }
        )
    except StructuredError as e:
        print(f"\nCaught: {e}")
        print(f"Suggestions: {e.suggestions}")
        print(f"\nFull context:\n{json.dumps(e.context.to_dict(), indent=2)}")


def with_error_context_example():
    """Show decorator pattern."""
    print("\n" + "=" * 60)
    print("Example: Error Context Decorator")
    print("=" * 60)
    
    @with_error_context("process_payment", capture_args=True)
    def process_payment(user_id: str, amount: float):
        if amount <= 0:
            raise ValueError("Amount must be positive")
        return {"user_id": user_id, "amount": amount, "status": "paid"}
    
    try:
        result = process_payment("user123", -50)
        print(f"Success: {result}")
    except StructuredError as e:
        print(f"\nAuto-wrapped error:")
        print(f"  Message: {e.message}")
        print(f"  Context: {e.context.inputs}")


def result_type_example():
    """Show result type pattern."""
    print("\n" + "=" * 60)
    print("Example: Result Type")
    print("=" * 60)
    
    def divide(a: float, b: float) -> Result:
        if b == 0:
            return Result.failure(ValidationError(
                field="divisor",
                value=b,
                reason="cannot be zero"
            ))
        return Result.success(a / b)
    
    # Success case
    result = divide(100, 5)
    if result.is_success:
        print(f"\n100 / 5 = {result.value}")
    
    # Failure case
    result = divide(100, 0)
    if result.is_failure:
        print(f"\n100 / 0 failed: {result.error.message}")
        print(f"Using default: {result.unwrap_or(float('inf'))}")


def handler_registry_example():
    """Show error handler registry."""
    print("\n" + "=" * 60)
    print("Example: Handler Registry")
    print("=" * 60)
    
    handler = ErrorHandler()
    
    # Register handlers
    errors_logged = []
    alerts_sent = []
    
    handler.register(ErrorSeverity.WARNING, lambda e: errors_logged.append(e.message))
    handler.register(ErrorSeverity.ERROR, lambda e: errors_logged.append(f"ERROR: {e.message}"))
    handler.register(ErrorSeverity.CRITICAL, lambda e: alerts_sent.append(f"ALERT: {e.error_code}"))
    
    # Simulate errors
    errors = [
        NetworkError("api.endpoint.com", context={"retry": 1}),
        RateLimitError(retry_after=60),
        InsufficientFundsError(required=10000, available=5000),
        CircuitOpenError("payment_gateway", open_duration=300),
    ]
    
    for e in errors:
        handler.handle(e)
        print(f"  [{e.severity.name}] {e.error_code}: {e.message[:50]}...")
    
    print(f"\nLogged: {len(errors_logged)} errors")
    print(f"Alerts ready: {len(alerts_sent)}")


def trading_example():
    """Realistic trading scenario."""
    print("\n" + "=" * 60)
    print("Example: Trading Error Handling")
    print("=" * 60)
    
    def place_order(symbol: str, qty: int, price: float, buying_power: float) -> Result:
        # Validate inputs
        if qty <= 0:
            return Result.failure(ValidationError("quantity", qty, "must be positive"))
        if price <= 0:
            return Result.failure(ValidationError("price", price, "must be positive"))
        
        # Check funds
        required = qty * price
        if required > buying_power:
            return Result.failure(InsufficientFundsError(
                required=required,
                available=buying_power,
                asset="USD"
            ))
        
        # Simulate network call
        try:
            # This would be actual API call
            if symbol == "FAIL":
                raise ConnectionError("Connection refused")
            return Result.success({"order_id": "12345", "status": "filled"})
        except Exception as e:
            return Result.failure(NetworkError(
                endpoint="/v1/orders",
                cause=e,
                context={"symbol": symbol, "qty": qty, "price": price}
            ))
    
    # Try invalid order
    print("\n1. Invalid quantity:")
    result = place_order("AAPL", -100, 150.0, 50000)
    if result.is_failure:
        print(f"   {result.error}")
        print(f"   Suggestion: {result.error.suggestions[0] if result.error.suggestions else 'N/A'}")
    
    # Try insufficient funds
    print("\n2. Insufficient funds:")
    result = place_order("AAPL", 1000, 150.0, 50000)
    if result.is_failure:
        print(f"   {result.error}")
        print(f"   Shortfall: ${result.error.shortfall:,.2f}")
    
    # Try valid order
    print("\n3. Valid order:")
    result = place_order("AAPL", 100, 150.0, 50000)
    if result.is_success:
        print(f"   Success: {result.value}")


if __name__ == "__main__":
    example_validation()
    example_network()
    with_error_context_example()
    result_type_example()
    handler_registry_example()
    trading_example()
    
    print("\n" + "=" * 60)
    print("Structured errors = faster debugging + better UX")
    print("=" * 60)
```

## Error Severity Matrix

| Severity | When to Use | Action | Alert |
|----------|-------------|--------|-------|
| **DEBUG** | Info, no issue | Log only | No |
| **WARNING** | Recoverable issue | Log, continue | If repeated |
| **ERROR** | Failed operation | Log, raise, can retry | No |
| **CRITICAL** | Service down | Log, fail fast | Yes |
| **FATAL** | Can't continue | Log, exit | Yes |

## Quick Reference

```python
# Basic structured error
raise StructuredError(
    message="Database connection failed",
    severity=ErrorSeverity.ERROR,
    context={"host": "db.server.com", "retry_count": 3}
)

# Domain-specific with auto-retry rules
raise InsufficientFundsError(required=1000, available=500)
raise RateLimitError(retry_after=60)

# Auto-wrap with decorator
@with_error_context("process_order", capture_args=True)
def process_order(user_id, symbol, qty):
    ...  # Exceptions auto-wrapped with context

# Result type forces handling
def risky_op() -> Result:
    if success:
        return Result.success(data)
    return Result.failure(error)

result = risky_op()
value = result.unwrap_or(default)  # Safe access
```

## Key Design Decisions

1. **Context at origin** — Gather inputs/state where error happens, not at catch
2. **Error codes** — Machine-readable for filtering/alerts  
3. **Retry hints** — Consumer knows whether retry makes sense
4. **Suggestions** — Help developers/users fix the issue
5. **Result type** — Forces explicit handling, no silent failures

## Why This Pattern

- **Debuggable** — Full context without reproducing
- **Actionable** — Retry, alert, or ignore based on severity
- **Extensible** — New error types get same structure
- **Serializable** — JSON output for logs and APIs

---

**Created by Ghost 👻 | Feb 20, 2026 | 12-min learning sprint**  
*Lesson: "An error without context is just a complaint." Capture everything at the source — inputs, state, location — and you'll debug 10x faster.*
