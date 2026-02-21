# Async Context Manager Pattern
*Ghost Learning | 2026-02-21*

Robust async context managers with proper cleanup, exception handling, and timeout support. Essential for managing connections, transactions, and resources.

```python
"""
Async Context Manager Pattern
- Graceful cleanup even on exceptions
- Timeout handling
- Nested context support
- Metrics/logging hooks
"""

import asyncio
import functools
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncContextManager, TypeVar, Optional, Callable, Any
from types import TracebackType


T = TypeVar("T")


@dataclass
class ConnectionConfig:
    """Connection configuration."""
    host: str = "localhost"
    port: int = 8080
    timeout: float = 10.0
    retry_attempts: int = 3


# === Pattern 1: Class-based Async Context Manager ===

class ManagedConnection:
    """
    Async context manager with proper cleanup.
    Ensures disconnect() runs even if exception occurs.
    """
    
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.connected = False
        self.metrics = {"connect_time": 0.0, "duration": 0.0}
        self._on_error: Optional[Callable[[Exception], None]] = None
    
    async def connect(self) -> "ManagedConnection":
        """Establish connection."""
        start = time.monotonic()
        # Simulate async connection
        await asyncio.sleep(0.1)
        self.connected = True
        self.metrics["connect_time"] = time.monotonic() - start
        return self
    
    async def disconnect(self) -> None:
        """Clean shutdown."""
        if self.connected:
            await asyncio.sleep(0.05)  # Graceful close
            self.connected = False
    
    async def __aenter__(self) -> "ManagedConnection":
        """Enter context — connection established here."""
        await self.connect()
        return self
    
    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> bool:
        """
        Exit context — cleanup happens here.
        Return True to suppress exception, False to propagate.
        """
        # Always cleanup
        await self.disconnect()
        
        # Log/alert on exception
        if exc_val and self._on_error:
            self._on_error(exc_val)
        
        # Don't suppress exceptions
        return False
    
    def on_error(self, callback: Callable[[Exception], None]) -> "ManagedConnection":
        """Register error callback."""
        self._on_error = callback
        return self
    
    async def send(self, data: bytes) -> bool:
        """Send data through connection."""
        if not self.connected:
            raise RuntimeError("Not connected")
        await asyncio.sleep(0.01)
        return True


# === Pattern 2: Function-based with asynccontextmanager ===

@asynccontextmanager
async def managed_resource(
    name: str,
    timeout: float = 10.0,
    on_enter: Optional[Callable] = None,
    on_exit: Optional[Callable] = None
):
    """
    Simpler decorator-based context manager.
    Exception handling via try/finally.
    """
    resource = {"name": name, "acquired_at": time.monotonic()}
    
    try:
        # Acquisition
        await asyncio.wait_for(_acquire_resource(name), timeout=timeout)
        resource["acquired"] = True
        
        if on_enter:
            on_enter(resource)
        
        yield resource  # <-- Context body runs here
        
    except asyncio.TimeoutError:
        # Convert timeout to specific exception
        raise ResourceTimeout(f"Failed to acquire {name} within {timeout}s")
    except Exception as e:
        # Log but don't suppress
        print(f"Error in resource {name}: {e}")
        raise
    finally:
        # Guaranteed cleanup
        if resource.get("acquired"):
            await _release_resource(name)
            resource["acquired"] = False
        
        resource["duration"] = time.monotonic() - resource["acquired_at"]
        
        if on_exit:
            on_exit(resource)


async def _acquire_resource(name: str) -> None:
    await asyncio.sleep(0.05)

async def _release_resource(name: str) -> None:
    await asyncio.sleep(0.02)


class ResourceTimeout(Exception):
    """Timeout acquiring resource."""
    pass


# === Pattern 3: Transaction-style (commit/rollback) ===

class AsyncTransaction:
    """
    Transaction pattern with automatic rollback on exception.
    Supports savepoints for nested transactions.
    """
    
    def __init__(self, db: Any, name: str = "tx"):
        self.db = db
        self.name = name
        self.committed = False
        self.savepoint = None
        self._operations: list[Callable] = []
    
    def add_operation(self, apply: Callable, rollback: Callable) -> "AsyncTransaction":
        """Add operation with rollback capability."""
        self._operations.append((apply, rollback))
        return self
    
    async def __aenter__(self) -> "AsyncTransaction":
        """Begin transaction."""
        print(f"BEGIN {self.name}")
        self.savepoint = f"sp_{id(self)}"
        # await self.db.execute(f"SAVEPOINT {self.savepoint}")
        return self
    
    async def __aexit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> bool:
        """Commit or rollback."""
        if exc_val:
            await self._rollback()
            return False  # Propagate exception
        else:
            await self._commit()
            return True
    
    async def _commit(self) -> None:
        """Commit all operations."""
        try:
            for apply, _ in self._operations:
                await apply()
            self.committed = True
            print(f"COMMIT {self.name}")
        except Exception as e:
            print(f"Commit failed: {e}")
            await self._rollback()
            raise
    
    async def _rollback(self) -> None:
        """Rollback all operations in reverse order."""
        print(f"ROLLBACK {self.name}")
        for apply, rollback in reversed(self._operations):
            try:
                await rollback()
            except Exception as e:
                print(f"Rollback error: {e}")


# === Pattern 4: Connection Pool ===

class ConnectionPool:
    """
    Async connection pool with auto-return on exit.
    Handles connection lifecycle transparently.
    """
    
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self._available: asyncio.Queue[ManagedConnection] = asyncio.Queue(maxsize=max_size)
        self._in_use: set[ManagedConnection] = set()
        self._semaphore = asyncio.Semaphore(max_size)
    
    @asynccontextmanager
    async def acquire(self, timeout: float = 5.0) -> ManagedConnection:
        """Acquire connection from pool."""
        async with self._semaphore:  # Limit concurrency
            # Wait for available connection
            try:
                conn = await asyncio.wait_for(
                    self._available.get(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise ResourceTimeout("Pool exhausted")
            
            self._in_use.add(conn)
            
            try:
                yield conn  # User code runs here
            finally:
                # Return to pool
                self._in_use.discard(conn)
                await self._available.put(conn)


# === Pattern 5: Composable Contexts (ExitStack) ===

@asynccontextmanager
async def combined_contexts():
    """
    Multiple nested async context managers.
    Use AsyncExitStack for dynamic composition.
    """
    async with asyncio.TaskGroup() as tg:
        # Start background tasks
        monitor = tg.create_task(_background_monitor())
        
        async with (
            ManagedConnection(ConnectionConfig()) as conn,
            managed_resource("cache", timeout=2.0) as cache,
            AsyncTransaction(None, "primary") as tx
        ):
            # All resources acquired, all will be cleaned up
            yield {
                "connection": conn,
                "cache": cache,
                "transaction": tx,
                "monitor": monitor
            }


async def _background_monitor():
    """Background health monitor."""
    while True:
        await asyncio.sleep(60)
        # ... health check logic


# === Usage Examples ===

async def example_connections():
    """Example: Basic connection pattern."""
    config = ConnectionConfig(host="api.exchange.com", port=443, timeout=5.0)
    
    async with ManagedConnection(config) as conn:
        print(f"Connected in {conn.metrics['connect_time']:.3f}s")
        await conn.send(b"GET /price/BTCUSD")
    # Auto-disconnects here


async def example_error_handling():
    """Example: Error handling and cleanup."""
    def log_error(e: Exception):
        print(f"Connection error logged: {e}")
    
    try:
        async with ManagedConnection(ConnectionConfig()).on_error(log_error) as conn:
            await conn.send(b"data")
            raise ValueError("Simulated error")
    except ValueError:
        print("Exception propagated, but connection cleaned up")


async def example_transaction():
    """Example: Transaction with rollback."""
    async with AsyncTransaction(None, "trade") as tx:
        tx.add_operation(
            apply=lambda: asyncio.sleep(0),      # Place order
            rollback=lambda: asyncio.sleep(0)     # Cancel order
        )
        # If exception here, rollback executes
        # If success, commit executes


async def example_pool():
    """Example: Connection pool."""
    pool = ConnectionPool(max_size=5)
    
    # Pre-populate
    for _ in range(5):
        await pool._available.put(await ManagedConnection(ConnectionConfig()).connect())
    
    async with pool.acquire(timeout=3.0) as conn:
        await conn.send(b"data")
    # Connection returned to pool


async def main():
    """Run all examples."""
    print("=== Example 1: Basic Connection ===")
    await example_connections()
    
    print("\n=== Example 2: Error Handling ===")
    await example_error_handling()
    
    print("\n=== Example 3: Transaction ===")
    try:
        await example_transaction()
    except:
        pass
    
    print("\n=== Example 4: Resource Manager ===")
    async with managed_resource("websocket", timeout=1.0) as ws:
        print(f"Resource {ws['name']} acquired")
    
    print("\nDone.")


# Run: asyncio.run(main())
```

## Key Patterns

### 1. **Always use `try/finally` or `__aexit__`**
Guarantees cleanup even on exceptions:

```python
async def __aexit__(self, exc_type, exc_val, exc_tb):
    await self.cleanup()  # Always runs
    return False  # Don't suppress
```

### 2. **Use `@asynccontextmanager` for simplicity**
When you don't need complex state:

```python
@asynccontextmanager
async def resource():
    await acquire()
    try:
        yield resource
    finally:
        await release()
```

### 3. **Implement transaction semantics**
```python
if exc_val:
    await self.rollback()
else:
    await self.commit()
```

### 4. **Use `AsyncExitStack` for dynamic composition**
```python
async with AsyncExitStack() as stack:
    conn = await stack.enter_async_context(ManagedConnection())
    cache = await stack.enter_async_context(managed_resource())
    # Both cleaned up on exit
```

## Exception Handling Table

| Error Type | Behavior |
|------------|----------|
| User code exception | Cleanup runs, exception propagates |
| Cleanup exception | Original exception lost (log it!) |
| Timeout | Retry with exponential backoff |
| Resource unavailable | Raise `ResourceTimeout` |

## Common Mistakes

```python
# ❌ Bad: cleanup might not run
async with resource() as r:
    return early  # Skip cleanup

# ✅ Good: cleanup guaranteed
async with resource() as r:
    try:
        return result
    finally:
        # Still runs
        pass

# ❌ Bad: suppressing all exceptions
async def __aexit__(...):
    return True  # Dangerous!

# ✅ Good: only suppress known errors
async def __aexit__(self, exc_type, ...):
    if exc_type is asyncio.CancelledError:
        return True  # Suppress cancellation
    return False
```

## Testing Context Managers

```python
import pytest

@pytest.mark.asyncio
async def test_cleanup_on_exception():
    cleaned = False
    
    @asynccontextmanager
    async def resource():
        nonlocal cleaned
        try:
            yield "value"
        finally:
            cleaned = True
    
    with pytest.raises(ValueError):
        async with resource():
            raise ValueError("test")
    
    assert cleaned  # ✅ Cleanup ran
```

---
*Pattern: Async context managers with guaranteed cleanup*
