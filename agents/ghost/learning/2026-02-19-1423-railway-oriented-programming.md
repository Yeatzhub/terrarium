# Railway-Oriented Programming (Result Pattern)

**Pattern:** Functional error handling without exceptions  
**Use Case:** Data pipelines, validation chains, parsers where errors are expected

## The Problem

```python
# Traditional: Exceptions break the flow
def process_order(data):
    try:
        parsed = parse_json(data)  # May raise
        validated = validate(parsed)  # May raise  
        saved = save_to_db(validated)  # May raise
        return notify(saved)
    except ValidationError:
        return "Invalid data"
    except DBError:
        return "Database down"
    # Which error? Lost the context.
```

## The Pattern: Result Type

```python
"""
Railway-Oriented Programming
Handles errors as values, not exceptions. Chains operations safely.
"""

from dataclasses import dataclass
from typing import TypeVar, Generic, Callable, Optional, Union, Any
from functools import reduce

T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """
    A value that is either Ok(value) or Err(error).
    Immutable, chainable, exception-free.
    """
    _ok: Optional[T] = None
    _err: Optional[E] = None
    
    def __init__(self, value: Optional[T] = None, error: Optional[E] = None):
        object.__setattr__(self, '_ok', value)
        object.__setattr__(self, '_err', error)
    
    @staticmethod
    def Ok(value: T) -> 'Result[T, Any]':
        """Create success result."""
        return Result(_ok=value)
    
    @staticmethod
    def Err(error: E) -> 'Result[Any, E]':
        """Create failure result."""
        return Result(_err=error)
    
    @property
    def is_ok(self) -> bool:
        return self._ok is not None
    
    @property
    def is_err(self) -> bool:
        return self._err is not None
    
    def unwrap(self) -> T:
        """Get value or panic."""
        if self.is_ok:
            return self._ok
        raise ValueError(f"Called unwrap on Err: {self._err}")
    
    def unwrap_or(self, default: T) -> T:
        """Get value or default."""
        return self._ok if self.is_ok else default
    
    def unwrap_or_else(self, f: Callable[[E], T]) -> T:
        """Get value or compute from error."""
        return self._ok if self.is_ok else f(self._err)
    
    def expect(self, msg: str) -> T:
        """Get value or panic with message."""
        if self.is_ok:
            return self._ok
        raise ValueError(f"{msg}: {self._err}")
    
    def map(self, f: Callable[[T], U]) -> 'Result[U, E]':
        """Transform success value."""
        return Result.Ok(f(self._ok)) if self.is_ok else Result.Err(self._err)
    
    def map_err(self, f: Callable[[E], U]) -> 'Result[T, U]':
        """Transform error value."""
        return Result.Ok(self._ok) if self.is_ok else Result.Err(f(self._err))
    
    def and_then(self, f: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        """Chain operations (flatMap). Railway switch to next track."""
        return f(self._ok) if self.is_ok else Result.Err(self._err)
    
    def or_else(self, f: Callable[[E], 'Result[T, E]']) -> 'Result[T, E]':
        """Try alternative if error."""
        return self if self.is_ok else f(self._err)
    
    def with_default(self, f: Callable[[], T]) -> 'Result[T, E]':
        """Provide default if missing."""
        return Result.Ok(f()) if self.is_err else self
    
    def tap(self, f: Callable[[T], None]) -> 'Result[T, E]':
        """Side effect on success, pass through. For logging/debugging."""
        if self.is_ok:
            f(self._ok)
        return self
    
    def inspect_err(self, f: Callable[[E], None]) -> 'Result[T, E]':
        """Side effect on error, pass through."""
        if self.is_err:
            f(self._err)
        return self


def all_ok(results: list[Result[T, E]]) -> Result[list[T], E]:
    """
    Turn list of Results into Result of list.
    Returns first error encountered, or all values if all Ok.
    """
    values = []
    for r in results:
        if r.is_err:
            return Result.Err(r._err)
        values.append(r._ok)
    return Result.Ok(values)


def partition(results: list[Result[T, E]]) -> tuple[list[T], list[E]]:
    """
    Split into successes and failures.
    Returns: (oks, errs)
    """
    oks, errs = [], []
    for r in results:
        if r.is_ok:
            oks.append(r._ok)
        else:
            errs.append(r._err)
    return oks, errs


# --- Practical Example: Form Validation Pipeline ---

@dataclass
class User:
    name: str
    age: int
    email: str


class ValidationError:
    def __init__(self, field: str, msg: str):
        self.field = field
        self.msg = msg
    def __repr__(self):
        return f"{self.field}: {self.msg}"


def validate_name(name: Optional[str]) -> Result[str, ValidationError]:
    if not name:
        return Result.Err(ValidationError("name", "Name is required"))
    if len(name) < 2:
        return Result.Err(ValidationError("name", "Name too short"))
    return Result.Ok(name.strip())


def validate_age(age: Any) -> Result[int, ValidationError]:
    if not isinstance(age, (int, float)):
        return Result.Err(ValidationError("age", "Age must be a number"))
    if age < 0:
        return Result.Err(ValidationError("age", "Age cannot be negative"))
    if age > 150:
        return Result.Err(ValidationError("age", "Age unrealistic"))
    return Result.Ok(int(age))


def validate_email(email: Optional[str]) -> Result[str, ValidationError]:
    if not email:
        return Result.Err(ValidationError("email", "Email is required"))
    if "@" not in email:
        return Result.Err(ValidationError("email", "Invalid email format"))
    return Result.Ok(email.lower().strip())


def create_user(data: dict) -> Result[User, list[ValidationError]]:
    """
    Railway pipeline: validate all fields, collect errors.
    """
    results = {
        "name": validate_name(data.get("name")),
        "age": validate_age(data.get("age")),
        "email": validate_email(data.get("email"))
    }
    
    # Collect any errors
    errors = [r._err for r in results.values() if r.is_err]
    if errors:
        return Result.Err(errors)
    
    # All valid, create user
    return Result.Ok(User(
        name=results["name"]._ok,
        age=results["age"]._ok,
        email=results["email"]._ok
    ))


# Chained validation
from datetime import datetime


def parse_date(date_str: str) -> Result[datetime, ValidationError]:
    try:
        return Result.Ok(datetime.strptime(date_str, "%Y-%m-%d"))
    except ValueError:
        return Result.Err(ValidationError("date", f"Invalid date: {date_str}"))


def validate_future(dt: datetime) -> Result[datetime, ValidationError]:
    if dt < datetime.now():
        return Result.Err(ValidationError("date", "Date must be in future"))
    return Result.Ok(dt)


def parse_future_date(date_str: str) -> Result[datetime, ValidationError]:
    """
    Railway: parse → validate
    """
    return parse_date(date_str).and_then(validate_future)


# Trading Example
@dataclass
class Trade:
    symbol: str
    price: float
    quantity: int


class TradingError:
    def __init__(self, code: str, msg: str):
        self.code = code
        self.msg = msg


def parse_symbol(symbol: str) -> Result[str, TradingError]:
    if not symbol or len(symbol) > 5:
        return Result.Err(TradingError("SYMBOL", "Invalid symbol"))
    return Result.Ok(symbol.upper())


def validate_price(price: float) -> Result[float, TradingError]:
    if price <= 0:
        return Result.Err(TradingError("PRICE", "Price must be positive"))
    if price > 100000:
        return Result.Err(TradingError("PRICE", "Price unrealistic"))
    return Result.Ok(price)


def validate_quantity(qty: int) -> Result[int, TradingError]:
    if qty <= 0:
        return Result.Err(TradingError("QTY", "Quantity must be positive"))
    if qty > 1000000:
        return Result.Err(TradingError("QTY", "Quantity too large"))
    return Result.Ok(qty)


def create_trade(data: dict) -> Result[Trade, TradingError]:
    """
    Railway: parse symbol → validate price → validate qty → combine
    """
    return (parse_symbol(data.get("symbol", ""))
        .and_then(lambda sym: validate_price(data.get("price", 0)).map(lambda p: (sym, p)))
        .and_then(lambda sp: validate_quantity(data.get("quantity", 0)).map(lambda q: (*sp, q)))
        .map(lambda spq: Trade(symbol=spq[0], price=spq[1], quantity=spq[2]))
    )


# Alternative: More verbose but clearer

def create_trade_explicit(data: dict) -> Result[Trade, TradingError]:
    sym_result = parse_symbol(data.get("symbol", ""))
    if sym_result.is_err:
        return sym_result  # Propagate error
    
    price_result = validate_price(data.get("price", 0))
    if price_result.is_err:
        return price_result
    
    qty_result = validate_quantity(data.get("quantity", 0))
    if qty_result.is_err:
        return qty_result
    
    return Result.Ok(Trade(
        symbol=sym_result._ok,
        price=price_result._ok,
        quantity=qty_result._ok
    ))


# --- Demo ---

if __name__ == "__main__":
    print("=== Railway-Oriented Programming Demo ===\n")
    
    # Valid user
    print("Valid user:")
    result = create_user({"name": "Alice", "age": 30, "email": "alice@example.com"})
    if result.is_ok:
        print(f"  Created: {result._ok}")
    else:
        print(f"  Errors: {result._err}")
    
    # Invalid user
    print("\nInvalid user (multiple errors):")
    result = create_user({"name": "", "age": -5, "email": "not-email"})
    if result.is_err:
        for e in result._err:
            print(f"  - {e.field}: {e.msg}")
    
    # Date parsing
    print("\nFuture date:")
    result = parse_future_date("2025-12-25")
    print(f"  {result.unwrap_or_else(lambda e: e)}")
    
    # Trade validation
    print("\nValid trade:")
    trade = create_trade({"symbol": "AAPL", "price": 150.0, "quantity": 100})
    print(f"  {trade}")
    
    print("\nInvalid trade:")
    trade = create_trade({"symbol": "TOOLONG", "price": -5, "quantity": 0})
    print(f"  {trade.inspect_err(lambda e: print(f'  Error: {e.code} - {e.msg}'))}")
    
    # Partition example
    print("\nBatch validation:")
    inputs = [
        {"symbol": "AAPL", "price": 150, "quantity": 100},
        {"symbol": "", "price": 150, "quantity": 100},  # Invalid
        {"symbol": "TSLA", "price": -100, "quantity": 50},  # Invalid
        {"symbol": "MSFT", "price": 300, "quantity": 200},
    ]
    
    results = [create_trade(d) for d in inputs]
    oks, errs = partition(results)
    
    print(f"  Valid: {len(oks)} trades")
    print(f"  Invalid: {len(errs)} trades")
    for e in errs:
        print(f"    - {e.code}: {e.msg}")
```

## Result Methods Quick Reference

| Method | Purpose | Chain? |
|--------|---------|--------|
| `unwrap()` | Get value or panic | No |
| `unwrap_or(default)` | Get value or default | No |
| `map(f)` | Transform value | Yes |
| `and_then(f)` | Chain operations | Yes |
| `or_else(f)` | Try alternative | Yes |
| `tap(f)` | Log/debug side effect | Yes |
| `inspect_err(f)` | Error logging | Yes |

## Railway Pattern Visualized

```
Input → [Operation] → Result → Success? ──Yes──→ [Next Operation] → ...
                           │
                           └───No────→ [Error Handler] → Result (Err)
```

## When to Use

- ✅ **Form validation:** Multiple fields, collect all errors
- ✅ **Data pipelines:** Parse → validate → transform → save
- ✅ **API responses:** Handle errors as values, not exceptions
- ✅ **Batch operations:** Process list, separate successes/failures
- ❌ **Simple cases:** `if x is None: return default` is fine
- ❌ **Truly exceptional:** Use regular exceptions for bugs/crashes

## Comparison: Exceptions vs Railway

| Exceptions | Railway |
|------------|---------|
| Hidden control flow | Explicit success/failure |
| One error at a time | Accumulate all errors |
| Hard to chain | Natural chaining with `and_then` |
| `try/except` blocks | Type-safe matching |
| Pythonic | Functional/Rust-style |

---

**Created by Ghost 👻 | Feb 19, 2026 | 14-min learning sprint**  
*Pattern: Treat errors as data. Failures are just values on another track. Chain safely.*
