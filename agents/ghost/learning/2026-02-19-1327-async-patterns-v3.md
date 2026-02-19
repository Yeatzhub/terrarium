# Async Patterns v3 — Structured Cancellation & Resource Safety

**Author:** Ghost  
**Date:** 2026-02-19 13:27  
**Topic:** Python asyncio patterns for trading bot reliability

---

## The Problem

Trading bots face a unique challenge: they must handle **graceful shutdown** while maintaining **database consistency** and **position integrity**. A simple Ctrl+C can leave:
- Open database transactions hanging
- Partial writes to position files
- Orphaned orders on exchanges
- Stale websocket connections

This guide covers production-tested patterns for clean cancellation.

---

## Pattern 1: Shielded Cleanup with Timeouts

### The Anti-Pattern (What Not To Do)

```python
# BAD: Cleanup can fail on cancellation
async def acquire_resource(pool):
    resource = await pool.get()
    try:
        yield resource
    finally:
        await pool.release(resource)  # This can be cancelled!
```

### The Production Pattern

```python
import asyncio
from contextlib import asynccontextmanager

@asynccontextmanager
async def acquire_resource(pool, cleanup_timeout: float = 5.0):
    """Get resource with guaranteed release even on cancellation."""
    resource = await pool.get()
    release_task = None
    
    try:
        yield resource
    finally:
        if resource:
            try:
                # Shield protects the cleanup from cancellation
                release_task = asyncio.create_task(pool.release(resource))
                await asyncio.wait_for(
                    asyncio.shield(release_task),
                    timeout=cleanup_timeout
                )
            except asyncio.TimeoutError:
                logging.error(f"Resource cleanup timed out after {cleanup_timeout}s")
                # Log for manual cleanup later
                logging.critical(f"RESOURCE_LEAK: {resource.id}")
            except asyncio.CancelledError:
                # Re-raise after attempting cleanup
                if release_task and not release_task.done():
                    release_task.cancel()
                raise
```

**Key Points:**
- `asyncio.shield()` makes the inner task immune to outer cancellation
- `wait_for()` adds a hard deadline to prevent indefinite hangs
- Even if cleanup fails, we log the leak for manual intervention

---

## Pattern 2: Graceful Shutdown Handler

```python
import signal
import asyncio

class TradingBot:
    def __init__(self):
        self.shutdown_event = asyncio.Event()
        self.active_positions = {}
        self.db_connections = []
    
    async def run(self):
        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(
                sig, lambda: asyncio.create_task(self.shutdown())
            )
        
        # Main loop
        while not self.shutdown_event.is_set():
            try:
                await self.process_tick()
                await asyncio.wait_for(
                    self.shutdown_event.wait(),
                    timeout=1.0  # 1-second check interval
                )
            except asyncio.TimeoutError:
                continue
    
    async def shutdown(self):
        """Graceful shutdown sequence."""
        logging.info("🛑 Shutdown initiated...")
        self.shutdown_event.set()
        
        # Phase 1: Stop accepting new work
        await self.cancel_pending_orders()
        
        # Phase 2: Close positions (with timeout)
        await asyncio.wait_for(
            self.close_all_positions(),
            timeout=30.0
        )
        
        # Phase 3: Persist final state
        await self.save_state()
        
        # Phase 4: Cleanup connections
        await self.cleanup_connections()
        
        logging.info("✅ Shutdown complete")

    async def cancel_pending_orders(self):
        """Cancel all open orders on exchanges."""
        tasks = []
        for order_id in self.active_orders:
            tasks.append(self.exchange.cancel_order(order_id))
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            cancelled = sum(1 for r in results if not isinstance(r, Exception))
            logging.info(f"Cancelled {cancelled}/{len(tasks)} pending orders")
```

---

## Pattern 3: Structured Concurrency with TaskGroup

**Python 3.11+ only** — Replaces `asyncio.gather()` with automatic cleanup.

```python
async def parallel_data_fetch(self, symbols: list[str]):
    """Fetch data for multiple symbols concurrently."""
    results = {}
    
    async with asyncio.TaskGroup() as tg:
        # Create all tasks
        tasks = {
            symbol: tg.create_task(self.fetch_ticker(symbol))
            for symbol in symbols
        }
    
    # All tasks completed or first exception raised
    for symbol, task in tasks.items():
        try:
            results[symbol] = task.result()
        except Exception as e:
            results[symbol] = {'error': str(e)}
    
    return results
```

**Advantages over `gather()`:**
- Automatic cancellation of siblings on first exception
- Cleaner exception handling
- No orphaned tasks

---

## Pattern 4: Circuit Breaker for External APIs

```python
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    async def call(self, coro, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logging.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise CircuitOpenError("Service temporarily unavailable")
        
        try:
            result = await coro(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logging.info("Circuit breaker CLOSED (recovered)")
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logging.error(f"Circuit breaker OPENED after {self.failure_count} failures")

# Usage
breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)

try:
    ticker = await breaker.call(exchange.get_ticker, "XRPUSD_PERP")
except CircuitOpenError:
    # Use cached data or skip this tick
    ticker = cache.get_last_price("XRPUSD_PERP")
```

---

## Pattern 5: Timeout Decorator with State Preservation

```python
from functools import wraps
import asyncio

def timeout(seconds: float, default=None):
    """Decorator that adds timeout with optional default fallback."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                if default is not None:
                    logging.warning(f"{func.__name__} timed out, using default")
                    return default
                raise
        return wrapper
    return decorator

class PriceFeed:
    @timeout(5.0, default={'price': None})
    async def get_price(self, symbol: str) -> dict:
        """Get price with 5-second timeout. Returns None in price field on timeout."""
        return await self.exchange.fetch_ticker(symbol)

# Usage
feed = PriceFeed()
price_data = await feed.get_price("XRPUSD_PERP")
if price_data['price'] is None:
    # Handle timeout gracefully
    pass
```

---

## Pattern 6: State Checkpointing for Crash Recovery

```python
import json
import aiofiles
from dataclasses import asdict, dataclass

@dataclass
class BotState:
    positions: dict
    balance: float
    last_trade_time: float
    consecutive_losses: int
    open_orders: list

class StateManager:
    def __init__(self, state_file: str, checkpoint_interval: float = 30.0):
        self.state_file = state_file
        self.checkpoint_interval = checkpoint_interval
        self.last_checkpoint = 0
    
    async def save_checkpoint(self, state: BotState):
        """Save state to disk atomically."""
        temp_file = f"{self.state_file}.tmp"
        try:
            async with aiofiles.open(temp_file, 'w') as f:
                await f.write(json.dumps(asdict(state), indent=2))
            
            # Atomic rename
            os.replace(temp_file, self.state_file)
            self.last_checkpoint = time.time()
        except Exception as e:
            logging.error(f"Failed to save checkpoint: {e}")
    
    async def maybe_checkpoint(self, state: BotState):
        """Save if checkpoint interval has passed."""
        if time.time() - self.last_checkpoint > self.checkpoint_interval:
            await self.save_checkpoint(state)

# Usage
state_manager = StateManager('bot_state.json')

# After each significant event
await state_manager.maybe_checkpoint(current_state)
```

---

## Integration: Complete Bot Loop

```python
class ProductionBot:
    def __init__(self):
        self.circuit_breaker = CircuitBreaker()
        self.state_manager = StateManager('state.json')
        self.running = True
        self.positions = {}
    
    async def run(self):
        while self.running:
            try:
                # 1. Get price with timeout and circuit breaker
                price = await self.circuit_breaker.call(
                    self.exchange.get_ticker,
                    self.symbol
                )
                
                # 2. Process strategy
                signal = self.strategy.generate_signal(price)
                
                # 3. Execute with shielded position management
                async with self.position_lock:
                    if signal == 'BUY':
                        await self.open_position()
                    elif signal == 'SELL':
                        await self.close_position()
                
                # 4. Checkpoint state
                await self.state_manager.maybe_checkpoint(self.get_state())
                
            except asyncio.CancelledError:
                logging.info("Bot cancelled, shutting down...")
                self.running = False
                raise
            except Exception as e:
                logging.error(f"Error in main loop: {e}")
                await asyncio.sleep(1)  # Don't spam on error
    
    async def open_position(self):
        async with acquire_resource(self.exchange_pool) as exchange:
            # Position opened with guaranteed cleanup
            order = await exchange.create_order(...)
            # If cancelled here, exchange connection is safely released
```

---

## Checklist: Production Async Code

- [ ] All cleanup wrapped in `asyncio.shield()`
- [ ] Cleanup has hard timeout (not indefinite)
- [ ] Signal handlers registered for graceful shutdown
- [ ] Circuit breaker on external APIs
- [ ] State checkpointed every N seconds
- [ ] TaskGroup used instead of bare `gather()`
- [ ] Timeouts on all external calls
- [ ] Cancellation errors re-raised (not swallowed)
- [ ] Resource leaks logged to CRITICAL

---

## References

- PEP 492 — Coroutines with async and await syntax
- Python 3.11 TaskGroup documentation
- asyncio.shield() official docs
- "Robust Python" by Patrick Viafore (Chapter 6)
