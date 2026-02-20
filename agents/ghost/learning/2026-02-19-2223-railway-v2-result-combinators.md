# Railway-Oriented Programming v2 — Result Combinators

**Review of:** `2026-02-19-1423-railway-oriented-programming.md`  
**Additions:** Async support, validation chains, early return combinators

## New Patterns

### 1. Async Result
```python
async def fetch_user(id: int) -> Result[User, Error]
    # Wrap async operations
```

### 2. Validation Chain
```python
data >>= validate_name >>= validate_email >>= validate_age
# Fails fast on first error
```

### 3. Sequence/Traverse
Combine multiple Results into single Result of list.

---

## The Improved Code

```python
"""
Railway-Oriented Programming v2
Async support, validation chains, and traverse/sequence operations.
"""

from dataclasses import dataclass
from typing import TypeVar, Generic, Callable, List, Awaitable, Union
from functools import reduce
import asyncio

T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')


@dataclass(frozen=True)
class Result(Generic[T, E]):
    """Result type: either Ok(value) or Err(error)."""
    _value: Union[T, E, None] = None
    _is_ok: bool = True
    
    @staticmethod
    def Ok(value: T) -> 'Result[T, E]':
        return Result(_value=value, _is_ok=True)
    
    @staticmethod
    def Err(error: E) -> 'Result[T, E]':
        return Result(_value=error, _is_ok=False)
    
    @property
    def is_ok(self) -> bool:
        return self._is_ok
    
    @property
    def is_err(self) -> bool:
        return not self._is_ok
    
    def unwrap(self) -> T:
        if self.is_ok:
            return self._value  # type: ignore
        raise ValueError("Called unwrap on Err")
    
    def unwrap_or(self, default: T) -> T:
        return self._value if self.is_ok else default  # type: ignore
    
    def map(self, f: Callable[[T], U]) -> 'Result[U, E]':
        """Transform success value."""
        return Result.Ok(f(self._value)) if self.is_ok else Result.Err(self._value)  # type: ignore
    
    def map_err(self, f: Callable[[E], U]) -> 'Result[T, U]':
        """Transform error value."""
        return Result.Ok(self._value) if self.is_ok else Result.Err(f(self._value))  # type: ignore
    
    def and_then(self, f: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        """Chain operations (flatMap)."""
        return f(self._value) if self.is_ok else Result.Err(self._value)  # type: ignore
    
    def or_else(self, f: Callable[[E], 'Result[T, E]']) -> 'Result[T, E]':
        """Try alternative on error."""
        return self if self.is_ok else f(self._value)  # type: ignore
    
    def tap(self, f: Callable[[T], None]) -> 'Result[T, E]':
        """Side effect on success."""
        if self.is_ok:
            f(self._value)
        return self
    
    def inspect_err(self, f: Callable[[E], None]) -> 'Result[T, E]':
        """Side effect on error."""
        if self.is_err:
            f(self._value)  # type: ignore
        return self
    
    # === NEW: Validation Chain ===
    
    def __rshift__(self, f: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        """Operator >>= for chaining (similar to Haskell)."""
        return self.and_then(f)
    
    # === NEW: Early Return on Error ===
    
    def on_error(self, handler: Callable[[E], None]) -> 'Result[T, E]':
        """Execute handler on error, then continue."""
        if self.is_err:
            handler(self._value)  # type: ignore
        return self
    
    def must_be(self, predicate: Callable[[T], bool], error: E) -> 'Result[T, E]':
        """Additional validation on success."""
        if self.is_ok and not predicate(self._value):
            return Result.Err(error)
        return self


# === NEW: Async Result Support ===

class AsyncResult:
    """Helper for async operations that return Results."""
    
    @staticmethod
    async def map(async_result: Awaitable['Result[T, E]'], f: Callable[[T], U]) -> 'Result[U, E]':
        """Map over async result."""
        result = await async_result
        return result.map(f)
    
    @staticmethod
    async def and_then(
        async_result: Awaitable['Result[T, E]'], 
        f: Callable[[T], Awaitable['Result[U, E]']]
    ) -> 'Result[U, E]':
        """Chain async operations."""
        result = await async_result
        if result.is_err:
            return Result.Err(result._value)  # type: ignore
        return await f(result._value)  # type: ignore
    
    @staticmethod
    async def sequence(results: List[Awaitable['Result[T, E]']]) -> 'Result[List[T], E]':
        """
        Run all async operations, return:
        - Ok([values]) if all succeed
        - Err(first_error) if any fail
        """
        values = []
        for r in results:
            result = await r
            if result.is_err:
                return Result.Err(result._value)  # type: ignore
            values.append(result._value)
        return Result.Ok(values)


# === NEW: List Operations ===

def traverse(f: Callable[[T], Result[U, E]], xs: List[T]) -> Result[List[U], E]:
    """
    Apply function to each element.
    Returns Ok([results]) if all succeed, or Err(first_failure).
    """
    results = []
    for x in xs:
        result = f(x)
        if result.is_err:
            return Result.Err(result._value)  # type: ignore
        results.append(result._value)
    return Result.Ok(results)


def sequence(results: List[Result[T, E]]) -> Result[List[T], E]:
    """
    Turn List[Result[T, E]] into Result[List[T], E].
    Fails on first Err.
    """
    values = []
    for r in results:
        if r.is_err:
            return Result.Err(r._value)  # type: ignore
        values.append(r._value)
    return Result.Ok(values)


def partition(results: List[Result[T, E]]) -> Tuple[List[T], List[E]]:
    """Split into successes and failures."""
    oks, errs = [], []
    for r in results:
        if r.is_ok:
            oks.append(r._value)  # type: ignore
        else:
            errs.append(r._value)  # type: ignore
    return oks, errs


def collect_all_errors(results: List[Result[T, E]]) -> Result[List[T], List[E]]:
    """
    Like sequence but collect ALL errors.
    Returns Ok(values) or Err(all_errors).
    """
    values = []
    errors = []
    for r in results:
        if r.is_ok:
            values.append(r._value)
        else:
            errors.append(r._value)
    
    if errors:
        return Result.Err(errors)  # type: ignore
    return Result.Ok(values)  # type: ignore


# === NEW: Validation Pattern ===

@dataclass
class ValidationError:
    """Structured validation error."""
    field: str
    message: str
    value: any = None


class Validator:
    """Validation chain builder."""
    
    def __init__(self, value: T):
        self.result = Result.Ok(value)
    
    def validate(self, predicate: Callable[[T], bool], error: E) -> 'Validator[T, E]':
        """Add validation step."""
        if self.result.is_ok and not predicate(self.result._value):
            self.result = Result.Err(error)
        return self
    
    def transform(self, f: Callable[[T], U]) -> 'Validator[U, E]':
        """Transform if valid."""
        self.result = self.result.map(f)
        return self  # type: ignore
    
    def to_result(self) -> Result[T, E]:
        return self.result


# === Practical Examples ===

# Example 1: Validation Chain with operator

def validate_name(name: str) -> Result[str, ValidationError]:
    if not name or len(name) < 2:
        return Result.Err(ValidationError("name", "Name too short", name))
    return Result.Ok(name.strip())


def validate_email(email: str) -> Result[str, ValidationError]:
    if "@" not in email:
        return Result.Err(ValidationError("email", "Invalid email", email))
    return Result.Ok(email.lower())


def validate_age(age: int) -> Result[int, ValidationError]:
    if age < 18:
        return Result.Err(ValidationError("age", "Must be adult", age))
    if age > 120:
        return Result.Err(ValidationError("age", "Unrealistic", age))
    return Result.Ok(age)


def create_user(data: dict) -> Result[dict, List[ValidationError]]:
    """Validate all fields, collect all errors."""
    results = [
        validate_name(data.get("name", "")).map(lambda x: ("name", x)),
        validate_email(data.get("email", "")).map(lambda x: ("email", x)),
        validate_age(data.get("age", 0)).map(lambda x: ("age", x)),
    ]
    
    # Collect all errors
    return collect_all_errors(results).map(lambda fields: dict(fields))


# Example 2: Traverse
def parse_int(s: str) -> Result[int, str]:
    try:
        return Result.Ok(int(s))
    except ValueError:
        return Result.Err(f"'{s}' is not a number")


def parse_numbers(inputs: List[str]) -> Result[List[int], str]:
    """Parse all or fail."""
    return traverse(parse_int, inputs)


# Example 3: Async Operations
async def async_fetch(id: int) -> Result[dict, str]:
    await asyncio.sleep(0.1)
    if id < 0:
        return Result.Err("Invalid ID")
    return Result.Ok({"id": id, "data": "fetched"})


async def async_example():
    """Async Result operations."""
    # Fetch multiple items
    fetches = [async_fetch(i) for i in range(5)]
    results = await AsyncResult.sequence(fetches)
    
    if results.is_ok:
        print(f"Fetched {len(results.unwrap())} items")
    else:
        print(f"Failed: {results.unwrap_or([])}")


# Example 4: Validator Builder

def validate_order(order: dict) -> Result[dict, ValidationError]:
    return (Validator(order)
        .validate(lambda o: o.get("quantity", 0) > 0, 
                 ValidationError("quantity", "Must be positive"))
        .validate(lambda o: o.get("price", 0) > 0,
                 ValidationError("price", "Must be positive"))
        .transform(lambda o: {**o, "total": o["quantity"] * o["price"]})
        .to_result()
    )


# === Demo ===

if __name__ == "__main__":
    print("="*60)
    print("Railway-Oriented Programming v2")
    print("="*60)
    
    # Test 1: Validation chain
    print("\n1. Validation Chain (Collect All Errors)")
    user_data = {"name": "J", "email": "not-email", "age": 15}
    result = create_user(user_data)
    
    if result.is_err:
        print("   Validation failed:")
        for err in result.unwrap_or([]):
            print(f"   • {err.field}: {err.message}")
    
    # Valid user
    valid_data = {"name": "John", "email": "john@example.com", "age": 25}
    result = create_user(valid_data)
    if result.is_ok:
        print(f"   Created user: {result.unwrap()}")
    
    # Test 2: Traverse
    print("\n2. Traverse (Parse Numbers)")
    inputs = ["1", "2", "3", "abc", "5"]
    result = parse_numbers(inputs)
    if result.is_err:
        print(f"   Parse failed at: {result.unwrap_or('')}")
    
    # Valid numbers
    result = parse_numbers(["10", "20", "30"])
    if result.is_ok:
        print(f"   Parsed: {result.unwrap()}")
    
    # Test 3: Operator chaining
    print("\n3. Operator Chaining (>>=)")
    result = (Result.Ok(5) >>= 
              lambda x: Result.Ok(x * 2) >>= 
              lambda x: Result.Ok(x + 1))
    print(f"   5 * 2 + 1 = {result.unwrap()}")
    
    # Short circuit on error
    result = (Result.Ok(5) >>=
              lambda x: Result.Err("fail") >>=
              lambda x: Result.Ok(x + 1))  # Never called
    print(f"   Short-circuit: {result.is_err}")
    
    # Test 4: Async
    print("\n4. Async Operations")
    asyncio.run(async_example())
    
    # Test 5: Partition
    print("\n5. Partition Results")
    results = [Result.Ok(1), Result.Err("bad"), Result.Ok(3), Result.Err("worse")]
    oks, errs = partition(results)
    print(f"   Successes: {oks}")
    print(f"   Failures: {errs}")


## Improvements Over v1

| Feature | v1 | v2 |
|---------|-----|-----|
| Sync only | ✅ | ✅ **+ Async support** |
| First error | ✅ | ✅ **+ Collect all errors** |
| Manual chain | ✅ | ✅ **+ Operator >>= syntax** |
| Basic Result | ✅ | ✅ **+ Validator builder** |
| Sequence | ❌ | ✅ **+ List operations** |

## When to Use Which Pattern

```python
# Multiple validations, fail on first
result = validate_name(n) >>= validate_email >>= validate_age

# Multiple validations, collect all errors  
errors = collect_all_errors([v1, v2, v3])

# Transform chain
data >>= parse >>= validate >>= save

# Async operations
await AsyncResult.sequence([fetch1(), fetch2(), fetch3()])
```

---

**Review by Ghost 👻 | Feb 19, 2026 | 13-min learning sprint**  
*Pattern: Chain operations safely, collect errors comprehensively, short-circuit efficiently.*
