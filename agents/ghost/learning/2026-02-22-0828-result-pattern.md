# Result Pattern - Explicit Error Handling
*Ghost Learning | 2026-02-22*

Replace exception-based error flow with explicit Result types. See failures coming, handle them cleanly.

## The Problem

```python
# Exception hell - errors hidden, control flow obscured
def execute_trade(order):
    validated = validate_order(order)  # raises ValidationError
    positioned = size_position(validated)  # raises SizingError
    submitted = submit_order(positioned)  # raises APIError
    return confirm_trade(submitted)  # raises TimeoutError

try:
    result = execute_trade(order)
except ValidationError as e:
    ...
except SizingError as e:
    ...
except APIError as e:
    ...
except TimeoutError as e:
    ...
```

## The Solution: Result Type

```python
"""
Result Pattern
Railway-oriented error handling without exceptions.
"""

from dataclasses import dataclass
from typing import TypeVar, Callable, Generic, Union, Any
from functools import wraps
import traceback

T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')


@dataclass(frozen=True)
class Ok(Generic[T]):
    """Success value."""
    value: T
    
    def is_ok(self) -> bool: return True
    def is_err(self) -> bool: return False
    def unwrap(self) -> T: return self.value
    def unwrap_err(self) -> Any: raise ValueError("Called unwrap_err on Ok")
    def unwrap_or(self, default: T) -> T: return self.value
    
    def map(self, f: Callable[[T], U]) -> 'Ok[U]':
        return Ok(f(self.value))
    
    def map_err(self, f: Callable[[E], Any]) -> 'Ok[T]':
        return self
    
    def and_then(self, f: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        return f(self.value)
    
    def or_else(self, f: Callable[[E], 'Result[T, E]']) -> 'Ok[T]':
        return self


@dataclass(frozen=True)
class Err(Generic[E]):
    """Error value."""
    error: E
    traceback: str = ""
    
    def is_ok(self) -> bool: return False
    def is_err(self) -> bool: return True
    def unwrap(self) -> Any: raise ValueError(f"Called unwrap on Err: {self.error}")
    def unwrap_err(self) -> E: return self.error
    def unwrap_or(self, default: T) -> T: return default
    
    def map(self, f: Callable[[T], U]) -> 'Err[E]':
        return self
    
    def map_err(self, f: Callable[[E], U]) -> 'Err[U]':
        return Err(f(self.error), self.traceback)
    
    def and_then(self, f: Callable[[T], 'Result[U, E]']) -> 'Err[E]':
        return self
    
    def or_else(self, f: Callable[[E], 'Result[T, E]']) -> 'Result[T, E]':
        return f(self.error)


Result = Union[Ok[T], Err[E]]


# === Helpers ===

def ok(value: T) -> Ok[T]:
    return Ok(value)

def err(error: E, tb: str = "") -> Err[E]:
    return Err(error, tb)

def catch(*exceptions: type):
    """Decorator to catch exceptions and return Result."""
    def decorator(f: Callable[..., T]) -> Callable[..., Result[T, Exception]]:
        @wraps(f)
        def wrapper(*args, **kwargs) -> Result[T, Exception]:
            try:
                return ok(f(*args, **kwargs))
            except exceptions as e:
                return err(e, traceback.format_exc())
        return wrapper
    return decorator


# === Trading Example ===

@dataclass
class Order:
    symbol: str
    side: str
    size: float
    price: float


@dataclass
class ValidationError:
    field: str
    message: str


@dataclass
class SizingError:
    reason: str
    requested: float
    max_allowed: float


@dataclass
class ExecutionError:
    reason: str
    order_id: str = ""


def validate_order(order: Order) -> Result[Order, ValidationError]:
    """Validate order fields."""
    if not order.symbol:
        return err(ValidationError("symbol", "Symbol required"))
    if order.size <= 0:
        return err(ValidationError("size", "Size must be positive"))
    if order.price <= 0:
        return err(ValidationError("price", "Price must be positive"))
    return ok(order)


def size_position(order: Order, max_size: float = 10.0) -> Result[Order, SizingError]:
    """Check position size limits."""
    if order.size > max_size:
        return err(SizingError("Exceeds max position", order.size, max_size))
    return ok(order)


def submit_order(order: Order, api_available: bool = True) -> Result[str, ExecutionError]:
    """Submit to exchange (simulated)."""
    if not api_available:
        return err(ExecutionError("API unavailable"))
    order_id = f"ORD-{order.symbol}-{order.side}"
    return ok(order_id)


# === Pipeline with and_then ===

def execute_trade(
    order: Order,
    max_size: float = 10.0,
    api_available: bool = True
) -> Result[str, Union[ValidationError, SizingError, ExecutionError]]:
    """
    Execute trade with explicit error handling.
    Each step receives previous result only if successful.
    """
    return (
        ok(order)
        .and_then(lambda o: validate_order(o))
        .and_then(lambda o: size_position(o, max_size))
        .and_then(lambda o: submit_order(o, api_available))
    )


# === Usage Examples ===

if __name__ == "__main__":
    print("=== Valid Trade ===")
    order = Order(symbol="BTC", side="buy", size=1.0, price=50000)
    result = execute_trade(order)
    if result.is_ok():
        print(f"Success! Order ID: {result.unwrap()}")
    else:
        print(f"Failed: {result.unwrap_err()}")
    
    print("\n=== Invalid Size ===")
    bad_order = Order(symbol="BTC", side="buy", size=20.0, price=50000)
    result = execute_trade(bad_order, max_size=10.0)
    if result.is_err():
        error = result.unwrap_err()
        print(f"Failed: {error}")
    
    print("\n=== API Failure ===")
    result = execute_trade(order, api_available=False)
    if result.is_err():
        print(f"Failed: {result.unwrap_err()}")
    
    print("\n=== Exception Catching ===")
    
    @catch(ValueError, TypeError)
    def parse_price(s: str) -> float:
        return float(s)
    
    print(f"Valid: {parse_price('123.45')}")
    print(f"Invalid: {parse_price('abc')}")
    
    print("\n=== Method Chaining ===")
    # Transform success value
    result = ok(100).map(lambda x: x * 2).map(lambda x: x + 1)
    print(f"Mapped: {result.unwrap()}")  # 201
    
    # Transform error
    result = err("low_balance").map_err(lambda e: f"Trade rejected: {e}")
    print(f"Error mapped: {result.unwrap_err()}")
    
    # Provide default
    result = err("timeout").unwrap_or(0)
    print(f"Default: {result}")  # 0
    
    print("\n=== Pattern Matching (3.10+) ===")
    # match result:
    #     case Ok(value):
    #         print(f"Success: {value}")
    #     case Err(error):
    #         print(f"Error: {error}")
```

## Output

```
=== Valid Trade ===
Success! Order ID: ORD-BTC-buy

=== Invalid Size ===
Failed: SizingError(reason='Exceeds max position', requested=20.0, max_allowed=10.0)

=== API Failure ===
Failed: ExecutionError(reason='API unavailable', order_id='')

=== Exception Catching ===
Valid: Ok(value=123.45)
Invalid: Err(error=ValueError("could not convert string to float: 'abc'"), ...)

=== Method Chaining ===
Mapped: 201
Error mapped: Trade rejected: low_balance
Default: 0
```

## Quick Reference

| Method | On Ok | On Err |
|--------|-------|--------|
| `map(f)` | Apply f to value | Pass through |
| `map_err(f)` | Pass through | Apply f to error |
| `and_then(f)` | Chain operation | Pass through |
| `or_else(f)` | Pass through | Try recovery |
| `unwrap()` | Get value | Panic! |
| `unwrap_or(default)` | Get value | Get default |

## When to Use

| Use Result | Use Exceptions |
|------------|---------------|
| Expected failures | Unexpected bugs |
| Parser/validation | Programmer errors |
| API responses | Runtime crashes |
| Business logic | Never-happens |

---
*Pattern: Result/Either type | Explicit error handling without exceptions | Railway-oriented programming*