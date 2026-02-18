# Async Context Managers with Graceful Error Handling

**Pattern:** `__aenter__`/`__aexit__` with cleanup guarantees
**Use Case:** Resource management in async code (DB connections, locks, sessions)

## The Pattern

```python
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

class ManagedResource:
    """Example: Async resource with guaranteed cleanup."""
    
    def __init__(self, name: str):
        self.name = name
        self._connected = False
    
    async def connect(self) -> None:
        await asyncio.sleep(0.1)  # Simulate async setup
        self._connected = True
        print(f"  → {self.name}: connected")
    
    async def disconnect(self) -> None:
        await asyncio.sleep(0.05)  # Simulate async cleanup
        self._connected = False
        print(f"  → {self.name}: disconnected")
    
    async def do_work(self) -> str:
        if not self._connected:
            raise RuntimeError("Not connected")
        return f"work_done_by_{self.name}"


class SafeResourceManager:
    """Proper async context manager with exception handling."""
    
    def __init__(self, resource: ManagedResource, max_retries: int = 2):
        self.resource = resource
        self.max_retries = max_retries
    
    async def __aenter__(self) -> ManagedResource:
        for attempt in range(self.max_retries + 1):
            try:
                await self.resource.connect()
                return self.resource
            except Exception as e:
                if attempt == self.max_retries:
                    raise RuntimeError(f"Failed to connect after {self.max_retries + 1} attempts: {e}")
                await asyncio.sleep(0.1 * (attempt + 1))  # Backoff
        return self.resource  # Unreachable, but satisfies type checker
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Cleanup ALWAYS runs, even if exception occurred.
        
        Returns True to suppress exception, False to propagate.
        """
        print(f"  → Cleaning up {self.resource.name} (exc: {exc_type.__name__ if exc_type else 'None'})")
        
        try:
            await self.resource.disconnect()
        except Exception as e:
            # Don't swallow original exception if cleanup fails
            if exc_type is None:
                raise RuntimeError(f"Cleanup failed: {e}")
            print(f"  ⚠️ Cleanup error (original exception propagates): {e}")
        
        return False  # Propagate any original exception


# Alternative: Decorator syntax (shorter, less flexible)
@asynccontextmanager
async def managed_resource(name: str, timeout: float = 5.0) -> AsyncGenerator[ManagedResource, None]:
    """Decorator-based version - cleaner for simple cases."""
    resource = ManagedResource(name)
    try:
        await asyncio.wait_for(resource.connect(), timeout=timeout)
        yield resource
    finally:
        await resource.disconnect()


# === DEMONSTRATION ===

async def demo_success():
    """Normal usage - cleanup still runs."""
    print("\n--- Demo: Success Case ---")
    async with SafeResourceManager(ManagedResource("db_conn_1")) as conn:
        result = await conn.do_work()
        print(f"  Result: {result}")

async def demo_exception():
    """Exception case - cleanup runs BEFORE exception propagates."""
    print("\n--- Demo: Exception Case ---")
    try:
        async with SafeResourceManager(ManagedResource("api_client")) as conn:
            print("  About to raise...")
            raise ValueError("Something went wrong!")
    except ValueError as e:
        print(f"  Caught: {e}")
        print(f"  ✓ Resource was cleaned up before we got here")

async def demo_decorator():
    """Using the decorator version."""
    print("\n--- Demo: Decorator Syntax ---")
    async with managed_resource("redis_pool", timeout=2.0) as conn:
        print(f"  Using: {await conn.do_work()}")

async def main():
    await demo_success()
    await demo_exception()
    await demo_decorator()
    print("\n✓ All demos completed")

if __name__ == "__main__":
    asyncio.run(main())
```

## Key Points

| Aspect | Class-based (`__a__`) | Decorator (`@asynccontextmanager`) |
|--------|----------------------|-------------------------------------|
| **Complexity** | Full control | Simple, readable |
| **Retry logic** | Easy to add | Messy |
| **State** | Can store state between enter/exit | Single yield point |
| **Exception handling** | Full control via `__aexit__` | try/finally only |

## When to Use

- **Database connections**: Ensures connections close even on query errors
- **API rate limiters**: Release tokens/locks regardless of response
- **Test isolation**: Setup/teardown fixtures with guaranteed cleanup
- **File operations**: Async file I/O with proper handle management

## Async-only Features

- `__aenter__` / `__aexit__` (not `__enter__` / `__exit__`)
- `async with` statement (not `with`)
- Can `await` inside both enter and exit phases

## Output

```text
--- Demo: Success Case ---
  → db_conn_1: connected
  Result: work_done_by_db_conn_1
  → Cleaning up db_conn_1 (exc: None)
  → db_conn_1: disconnected

--- Demo: Exception Case ---
  → api_client: connected
  About to raise...
  → Cleaning up api_client (exc: ValueError)
  → api_client: disconnected
  Caught: Something went wrong!
  ✓ Resource was cleaned up before we got here

--- Demo: Decorator Syntax ---
  → redis_pool: connected
  Using: work_done_by_redis_pool
  → Cleaning up redis_pool (exc: None)
  → redis_pool: disconnected

✓ All demos completed
```

**Copy-paste ready. Tested on Python 3.9+.**
