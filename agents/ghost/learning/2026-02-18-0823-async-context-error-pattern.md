# Python Pattern: Async Context Managers with Structured Error Handling

**Date:** 2026-02-18 | **Time:** 8:23 AM | **Duration:** ~15 min

## The Pattern: Robust Async Resource Management

When working with async resources (APIs, databases, websockets), you need **three** things:
1. Async/await for non-blocking I/O
2. Context managers for guaranteed cleanup
3. Structured error handling for resilience

## Pattern Implementation

```python
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, TypeVar, Optional
import logging

T = TypeVar('T')

class ResourceError(Exception):
    """Base exception for resource operations."""
    pass

class RetryableError(ResourceError):
    """Errors that can be retried."""
    pass

class FatalError(ResourceError):
    """Errors that should not be retried."""
    pass

# Example: Async resource (DB connection, API client, etc.)
class AsyncResource:
    def __init__(self, name: str):
        self.name = name
        self.is_connected = False
    
    async def connect(self):
        await asyncio.sleep(0.01)  # Simulate connection latency
        self.is_connected = True
        print(f"Connected to {self.name}")
    
    async def disconnect(self):
        self.is_connected = False
        print(f"Disconnected from {self.name}")
    
    async def fetch(self, query: str) -> dict:
        if not self.is_connected:
            raise ResourceError("Not connected")
        # Simulate work
        await asyncio.sleep(0.01)
        return {"query": query, "data": "result"}


@asynccontextmanager
async def managed_resource(name: str) -> AsyncGenerator[AsyncResource, None]:
    """Context manager that guarantees cleanup even on errors."""
    resource = AsyncResource(name)
    try:
        await resource.connect()
        yield resource
    except Exception as e:
        logging.error(f"Error using resource: {e}")
        raise
    finally:
        # Guaranteed cleanup even if exception occurred
        await resource.disconnect()


async def with_retry(
    operation: callable,
    max_retries: int = 3,
    base_delay: float = 0.5,
    exceptions: tuple = (RetryableError,)
) -> T:
    """Execute async operation with exponential backoff retry.
    
    Args:
        operation: Async callable to execute
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds (doubles each retry)
        exceptions: Tuple of exceptions to retry on
    
    Returns:
        Result from operation
    
    Raises:
        Last exception if all retries fail
    """
    for attempt in range(max_retries + 1):
        try:
            return await operation()
        except FatalError:
            raise  # Don't retry fatal errors
        except exceptions as e:
            if attempt == max_retries:
                raise
            delay = base_delay * (2 ** attempt)
            logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            await asyncio.sleep(delay)


async def robust_fetch(resource: AsyncResource, query: str) -> dict:
    """Fetch with proper error classification."""
    try:
        data = await resource.fetch(query)
        return data
    except ConnectionError as e:
        raise RetryableError(f"Connection failed: {e}")
    except ValueError as e:
        raise FatalError(f"Invalid query: {e}")


# === USAGE EXAMPLE ===
async def main():
    """Shows complete pattern in action."""
    
    # Pattern 1: Basic context manager (guaranteed cleanup)
    async with managed_resource("Database") as db:
        result = await db.fetch("SELECT * FROM users")
        print(f"Result: {result}")
    
    # Pattern 2: With retry logic
    async with managed_resource("API") as client:
        result = await with_retry(
            operation=lambda: robust_fetch(client, "users/1"),
            max_retries=3,
            base_delay=0.5
        )
        print(f"Fetched: {result}")
    
    # Pattern 3: Multiple resources (all cleaned up properly)
    async with managed_resource("Cache") as cache, \
               managed_resource("Database") as db:
        cache_data = await cache.fetch("key")
        db_data = await db.fetch("SELECT *")
        print(f"Combined: {cache_data}, {db_data}")
    
    # Pattern 4: Cleanup still happens on error
    try:
        async with managed_resource("FlakyService") as flaky:
            raise RetryableError("Simulated failure")
    except ResourceError as e:
        print(f"Caught (cleanup still ran!): {e}")


if __name__ == "__main__":
    asyncio.run(main())
```

## Key Takeaways

| Pattern | Purpose | Benefit |
|---------|---------|---------|
| `@asynccontextmanager` | Async resource cleanup | Guaranteed cleanup, even on exceptions |
| `with_retry()` | Resilience | Automatic retry with exponential backoff |
| `RetryableError` vs `FatalError` | Error classification | Smart retry logic (retry transient, fail fast on permanent) |
| Multiple async `with` | Resource composition | Clean syntax, all resources properly managed |

## When to Use

- **API clients** (rate limits, transient failures)
- **Database connections** (pool management, connection drops)
- **WebSocket handlers** (reconnection, heartbeat)
- **File I/O** (async file operations with proper cleanup)

## Quick Copy-Paste Snippet

```python
@asynccontextmanager
async def managed_client():
    client = MyClient()
    await client.connect()
    try:
        yield client
    finally:
        await client.disconnect()

async with managed_client() as client:
    data = await client.get_data()
```

---
*End of 15-min learning session*
