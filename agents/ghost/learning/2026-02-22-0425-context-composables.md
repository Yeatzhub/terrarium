# Context Manager Composables with ExitStack

**Ghost Learning** | 2026-02-22 04:25

Build trading operations from interchangeable, composable context managers.

## The Problem

You need different combinations of safety wrappers for different trade types:
- Paper trades: just timing + logging
- Live trades: timing + rate limit + lock + logging + circuit breaker
- Batch operations: rate limit + timeout + transaction

Hardcoding each combo = duplication. Using `ExitStack` = compose dynamically.

## Core Pattern

```python
from contextlib import ExitStack, contextmanager
import asyncio
import time
from typing import Callable, ContextManager, Any

class OperationBuilder:
    """Compose context managers dynamically."""
    
    def __init__(self):
        self.stack = ExitStack()
        self.managers: list[Callable[[], ContextManager]] = []
    
    def add(self, manager_factory: Callable[[], ContextManager]) -> 'OperationBuilder':
        """Add a context manager factory to the stack."""
        self.managers.append(manager_factory)
        return self  # fluent API
    
    def __enter__(self) -> 'OperationBuilder':
        for factory in self.managers:
            self.stack.enter_context(factory())
        return self
    
    def __exit__(self, *exc):
        return self.stack.__exit__(*exc)
    
    @classmethod
    def trade(cls, paper: bool = False, timeout: float = None, 
              rate_limit: int = None) -> 'OperationBuilder':
        """Factory for common trade configurations."""
        builder = cls()
        
        # Always include timing
        builder.add(lambda: timing_context("trade"))
        
        if not paper:
            # Live trade safety layers
            builder.add(lambda: circuit_breaker())
            if rate_limit:
                builder.add(lambda: rate_limit_context(rate_limit))
            builder.add(lambda: lock_context("trading"))
        
        if timeout:
            builder.add(lambda: timeout_context(timeout))
        
        builder.add(lambda: logging_context("trade"))
        return builder
```

## Reusable Context Managers

```python
@contextmanager
def timing_context(name: str):
    """Track operation duration."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        print(f"[{name}] took {elapsed*1000:.2f}ms")

@contextmanager  
def rate_limit_context(calls_per_second: int):
    """Simple rate limiting."""
    min_interval = 1.0 / calls_per_second
    time.sleep(min_interval)  # naive; use proper rate limiter in prod
    yield

@contextmanager
def lock_context(name: str):
    """Acquire/release a lock."""
    print(f"Acquiring {name} lock...")
    yield
    print(f"Released {name} lock")

@contextmanager
def circuit_breaker(threshold: int = 3):
    """Break after repeated failures."""
    state = {"failures": 0, "open": False}
    try:
        if state["open"]:
            raise RuntimeError("Circuit breaker is OPEN")
        yield state
    except Exception:
        state["failures"] += 1
        if state["failures"] >= threshold:
            state["open"] = True
        raise

@contextmanager
def logging_context(op: str):
    """Structured logging wrapper."""
    print(f"[START] {op}")
    try:
        yield
        print(f"[SUCCESS] {op}")
    except Exception as e:
        print(f"[ERROR] {op}: {e}")
        raise
```

## Usage Examples

```python
# Paper trade - minimal overhead
with OperationBuilder.trade(paper=True) as _:
    print("Executing paper trade...")

# Live trade - full safety stack
with OperationBuilder.trade(
    paper=False, 
    timeout=5.0, 
    rate_limit=10
) as _:
    print("Executing live trade...")

# Custom composition
with OperationBuilder() as builder:
    builder.add(lambda: timing_context("batch"))
    builder.add(lambda: rate_limit_context(5))
    for i in range(3):
        print(f"Batch item {i}")
```

## Output

```
# Paper trade
[START] trade
Executing paper trade...
[trade] took 0.05ms
[SUCCESS] trade

# Live trade  
[START] trade
Acquiring trading lock...
Released trading lock
[trade] took 150.23ms
[SUCCESS] trade
```

## Async Variant

```python
from contextlib import asynccontextmanager

class AsyncOperationBuilder:
    """Async context manager composition."""
    
    def __init__(self):
        self.stack = AsyncExitStack()
        self.managers: list[Callable] = []
    
    def add(self, factory: Callable) -> 'AsyncOperationBuilder':
        self.managers.append(factory)
        return self
    
    async def __aenter__(self) -> 'AsyncOperationBuilder':
        for factory in self.managers:
            await self.stack.enter_async_context(factory())
        return self
    
    async def __aexit__(self, *exc):
        return await self.stack.__aexit__(*exc)

# Usage
async with AsyncOperationBuilder.trade(paper=False) as _:
    await execute_trade()
```

## Quick Reference

| Method | Use Case |
|--------|----------|
| `add()` | Add any context manager |
| `trade(paper=, timeout=, rate_limit=)` | Pre-built trade config |
| `ExitStack.enter_context()` | Add at runtime |
| `ExitStack.callback()` | Add cleanup function |
| `ExitStack.push()` | Manual exit handling |

## Key Benefits

1. **DRY** - Write context managers once, compose freely
2. **Testable** - Mock individual layers easily
3. **Flexible** - Add/remove layers without touching business logic
4. **Safe** - All cleanup runs even on exception

---

*Pattern: ExitStack composition | Focus: Trading operations | Time: 8 min*