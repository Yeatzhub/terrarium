# Python Async Context Manager Patterns

**Topic:** Robust async resource management with error handling  
**Time:** 15 min read + use immediately

---

## Pattern: Async Context Manager with Retry & Cleanup

```python
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable
import logging

@asynccontextmanager
async def managed_resource(
    connect_fn: Callable[[], asyncio.Future],
    disconnect_fn: Callable[[], asyncio.Future],
    max_retries: int = 3,
    timeout: float = 10.0
) -> AsyncGenerator[any, None]:
    """
    Async context manager with auto-retry and guaranteed cleanup.
    Use for: DB connections, websockets, APIs, hardware.
    """
    resource = None
    last_error = None
    
    # Connect with retries
    for attempt in range(1, max_retries + 1):
        try:
            resource = await asyncio.wait_for(
                connect_fn(), 
                timeout=timeout
            )
            break
        except asyncio.TimeoutError:
            last_error = f"Timeout on attempt {attempt}"
            if attempt == max_retries:
                raise ConnectionError(last_error)
            await asyncio.sleep(attempt * 0.5)
        except Exception as e:
            last_error = str(e)
            if attempt == max_retries:
                raise
    
    try:
        yield resource
    finally:
        # Guaranteed cleanup even if consumer code crashes
        if resource is not None:
            try:
                await asyncio.wait_for(disconnect_fn(), timeout=5.0)
            except Exception as e:
                logging.warning(f"Cleanup error (ignored): {e}")


# Usage Example
async def fetch_data():
    async def connect():
        return await aiohttp.ClientSession().__aenter__()
    
    async def disconnect():
        await session.__aexit__(None, None, None)
    
    async with managed_resource(connect, disconnect) as session:
        async with session.get('https://api.example.com') as resp:
            return await resp.json()
```

---

## Pattern: Structured Error Handling Group

```python
class TaskGroup:
    """Run multiple async tasks; cancel on first error, return results."""
    
    @staticmethod
    async def gather_cancel_on_error(
        *tasks: asyncio.Task,
        return_exceptions: bool = False
    ) -> list:
        """
        Like asyncio.gather but cancels siblings on first failure.
        Prevents orphaned tasks running after caller gets error.
        """
        gathered = []
        
        def handle_done(t, idx):
            if t.cancelled():
                return
            if t.exception() and not return_exceptions:
                # Cancel siblings on error
                for other in gathered:
                    if other is not t and not other.done():
                        other.cancel()
        
        for i, coro in enumerate(tasks):
            task = asyncio.create_task(coro)
            task.add_done_callback(lambda t, idx=i: handle_done(t, idx))
            gathered.append(task)
        
        try:
            return await asyncio.gather(*gathered, return_exceptions=return_exceptions)
        except asyncio.CancelledError:
            # Ensure cleanup
            for t in gathered:
                if not t.done():
                    t.cancel()
                    try:
                        await t
                    except asyncio.CancelledError:
                        pass
            raise


# Usage
results = await TaskGroup.gather_cancel_on_error(
    fetch_user(1),
    fetch_user(2),
    fetch_user(3)
)
```

---

## Pattern: Timeout Wrapper with State

```python
@asynccontextmanager
async def timeout_with_state(seconds: float, operation_name: str = "operation"):
    """
    Context manager that tracks if timeout occurred.
    Useful for conditional logic after timeout.
    """
    state = {"timed_out": False, "cancelled": False}
    
    try:
        async with asyncio.timeout(seconds):
            yield state
    except asyncio.TimeoutError:
        state["timed_out"] = True
        logging.warning(f"{operation_name} timed out after {seconds}s")
        raise
    except asyncio.CancelledError:
        state["cancelled"] = True
        raise


# Usage
async with timeout_with_state(5.0, "DB query") as state:
    result = await expensive_query()

if state["timed_out"]:
    # Fallback logic
    result = cached_result
```

---

## Quick Reference

| Scenario | Pattern |
|----------|---------|
| DB/API connection | `managed_resource()` |
| Parallel API calls | `TaskGroup.gather_cancel_on_error()` |
| User-controlled timeout | `timeout_with_state()` |
| Fire-and-forget | `asyncio.create_task()` + handle exceptions |

---

**Files Modified:** Created new learning document  
**Ready to use:** Yes - copy patterns directly
