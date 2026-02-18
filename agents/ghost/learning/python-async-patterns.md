# Advanced Python Async Patterns for Production

A comprehensive guide to production-grade asynchronous Python patterns, demonstrated through a WebSocket order book manager implementation.

---

## Table of Contents

1. [Pattern Overview](#pattern-overview)
2. [Core Patterns](#core-patterns)
3. [Connection Management](#connection-management)
4. [Rate Limiting](#rate-limiting)
5. [Error Handling](#error-handling)
6. [Data Structures](#data-structures)
7. [Testing Strategies](#testing-strategies)
8. [Common Pitfalls](#common-pitfalls)
9. [Best Practices](#best-practices)
10. [Performance Tips](#performance-tips)

---

## Pattern Overview

This document covers advanced asyncio patterns essential for building high-performance, resilient network applications. The patterns are demonstrated in `websocket-orderbook.py`, a production-ready WebSocket order book manager for cryptocurrency trading.

### Key Features

- **Automatic reconnection** with exponential backoff
- **Circuit breaker** pattern for fault tolerance
- **Token bucket rate limiting** with backpressure
- **Thread-safe async data structures**
- **Comprehensive error handling**

---

## Core Patterns

### 1. Circuit Breaker Pattern

The circuit breaker prevents cascade failures by temporarily rejecting requests when failures exceed a threshold.

```python
from enum import Enum, auto

class CircuitBreaker:
    class State(Enum):
        CLOSED = auto()      # Normal operation
        OPEN = auto()        # Failing, reject requests
        HALF_OPEN = auto()   # Testing if service recovered
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 3
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._state = self.State.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = asyncio.Lock()
    
    async def call(self, coro_func: Callable, *args, **kwargs) -> Any:
        """Execute coroutine with circuit breaker protection"""
        async with self._lock:
            await self._update_state()
            
            if self._state == self.State.OPEN:
                raise ConnectionError("Circuit breaker is OPEN")
            
            if self._state == self.State.HALF_OPEN:
                if self._success_count >= self.half_open_max_calls:
                    raise ConnectionError("Circuit breaker HALF_OPEN limit reached")
        
        try:
            result = await coro_func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure()
            raise
```

**When to use:**
- External service calls (APIs, databases)
- Network connections that may fail
- Services with rate limits

**Benefits:**
- Prevents cascade failures
- Allows automatic recovery
- Provides clear failure signals

### 2. Token Bucket Rate Limiting

Token bucket is ideal for rate limiting with burst capacity.

```python
class TokenBucketRateLimiter:
    """Token bucket rate limiter with message and byte limits"""
    
    def __init__(
        self,
        messages_per_second: float = 100.0,
        burst_size: int = 10,
        bytes_per_second: Optional[float] = None
    ):
        self.messages_per_second = messages_per_second
        self.burst_size = burst_size
        self.bytes_per_second = bytes_per_second
        
        self._tokens = burst_size
        self._last_update = time.monotonic()
        self._bytes_tokens = bytes_per_second or float('inf')
        self._lock = asyncio.Lock()
    
    async def acquire(self, message_size: int = 0) -> float:
        """Acquire permission to proceed. Returns wait time."""
        async with self._lock:
            now = time.monotonic()
            
            # Replenish tokens
            elapsed = now - self._last_update
            self._tokens = min(
                self.burst_size,
                self._tokens + elapsed * self.messages_per_second
            )
            self._last_update = now
            
            if self._tokens >= 1:
                self._tokens -= 1
                return 0.0
            
            # Calculate wait time
            wait_time = (1 - self._tokens) / self.messages_per_second
            return wait_time
```

**Usage:**
```python
limiter = TokenBucketRateLimiter(
    messages_per_second=100,
    burst_size=10
)

# As context manager
async with limiter:
    await send_message()

# Manual acquire
wait = await limiter.acquire()
if wait > 0:
    await asyncio.sleep(wait)
```

### 3. Async Event Notification

Use `asyncio.Event` for signaling between coroutines.

```python
class AsyncOrderBook:
    def __init__(self):
        self._update_event = asyncio.Event()
        self._subscribers: Set[asyncio.Queue] = set()
    
    async def _notify_update(self):
        """Notify all subscribers of update"""
        self._update_event.set()
        self._update_event.clear()
        
        for queue in self._subscribers:
            try:
                queue.put_nowait(snapshot)
            except QueueFull:
                pass  # Backpressure handling
    
    async def wait_for_update(self, timeout: Optional[float] = None) -> bool:
        """Wait for next order book update"""
        try:
            await asyncio.wait_for(self._update_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False
```

---

## Connection Management

### Automatic Reconnection with Exponential Backoff

```python
class WebSocketOrderBookManager:
    def __init__(self):
        self._reconnect_config = {
            'initial_delay': 1.0,
            'max_delay': 60.0,
            'backoff_factor': 2.0,
            'max_attempts': None,
            'jitter': 0.1
        }
        self._reconnect_attempts = 0
        self._current_delay = self._reconnect_config['initial_delay']
    
    async def _connection_loop(self):
        """Main connection loop with reconnection logic"""
        while self._should_run:
            try:
                await self._circuit_breaker.call(self._connect_and_run)
                
                # Reset on success
                self._reconnect_attempts = 0
                self._current_delay = self._reconnect_config['initial_delay']
                
            except ConnectionError as e:
                await self._handle_reconnect()
    
    async def _handle_reconnect(self):
        """Calculate and execute reconnection delay"""
        self._reconnect_attempts += 1
        
        # Calculate delay with jitter
        jitter = self._reconnect_config['jitter'] * (
            2 * (0.5 - asyncio.get_event_loop().time() % 1)
        )
        delay = self._current_delay + jitter
        
        logger.info(f"Reconnecting in {delay:.1f}s (attempt {self._reconnect_attempts})")
        await asyncio.sleep(delay)
        
        # Exponential backoff
        self._current_delay = min(
            self._current_delay * self._reconnect_config['backoff_factor'],
            self._reconnect_config['max_delay']
        )
```

### Connection Health Monitoring

```python
async def _ping_loop(self):
    """Send periodic ping frames"""
    while self._should_run and self._ws:
        try:
            await asyncio.sleep(30)
            if self._ws and self._connected:
                pong_waiter = await self._ws.ping()
                await asyncio.wait_for(pong_waiter, timeout=5)
        except asyncio.TimeoutError:
            logger.error("Ping timeout - connection may be dead")
            await self._ws.close()
        except Exception as e:
            logger.warning(f"Ping error: {e}")
```

---

## Rate Limiting

### Backpressure Handling

```python
async def _receive_loop(self):
    """Receive messages with rate limiting and backpressure"""
    while self._should_run and self._ws:
        try:
            msg = await self._ws.recv()
            
            try:
                async with self._rate_limiter:
                    await self._message_queue.put(msg)
            except BackpressureError:
                # Drop oldest messages
                while self._message_queue.qsize() > self._backpressure_threshold:
                    self._message_queue.get_nowait()
                await self._message_queue.put(msg)
                
        except ConnectionClosed:
            break
```

### Request Throttling

```python
async def send_with_throttle(self, message: str):
    """Send message with rate limiting"""
    async with self._rate_limiter:
        await self._ws.send(message)
```

---

## Error Handling

### Structured Exception Hierarchy

```python
class OrderBookError(Exception):
    """Base exception for order book errors"""
    pass

class ConnectionError(OrderBookError):
    """Connection-related errors"""
    pass

class RateLimitError(OrderBookError):
    """Rate limit exceeded"""
    pass

class BackpressureError(OrderBookError):
    """Backpressure threshold exceeded"""
    pass
```

### Retry Decorator

```python
def retry(
    max_attempts: int = 3,
    exceptions: tuple = (Exception,),
    delay: float = 1.0,
    backoff: float = 2.0
):
    """Retry decorator for async functions"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return await func(*args, **kwargs)
                except exceptions:
                    if attempt == max_attempts:
                        raise
                    
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
        return wrapper
    return decorator

# Usage
@retry(max_attempts=3, exceptions=(ConnectionError,), delay=1.0, backoff=2.0)
async def fetch_data():
    pass
```

---

## Data Structures

### Thread-Safe Async Order Book

```python
class AsyncOrderBook:
    def __init__(self, symbol: str, max_depth: int = 100):
        self.symbol = symbol
        self.max_depth = max_depth
        
        self._bids: Dict[Decimal, OrderBookLevel] = {}
        self._asks: Dict[Decimal, OrderBookLevel] = {}
        self._lock = asyncio.RLock()
    
    async def apply_delta(
        self,
        side: Side,
        price: Decimal,
        size: Decimal,
        update_id: int
    ):
        """Apply incremental update"""
        async with self._lock:
            target = self._bids if side == Side.BID else self._asks
            
            if size <= 0:
                target.pop(price, None)
            else:
                if price in target:
                    target[price].update(size)
                else:
                    target[price] = OrderBookLevel(price, size)
            
            # Maintain sorted order
            self._update_sorted_prices()
    
    async def get_snapshot(self) -> OrderBookSnapshot:
        """Get current order book state"""
        async with self._lock:
            return OrderBookSnapshot(
                symbol=self.symbol,
                bids=[PriceLevel(p, self._bids[p].size, Side.BID) 
                      for p in sorted(self._bids.keys(), reverse=True)],
                asks=[PriceLevel(p, self._asks[p].size, Side.ASK)
                      for p in sorted(self._asks.keys())],
                last_update_id=self._last_update_id,
                timestamp=time.time()
            )
```

### Pub/Sub Pattern

```python
async def subscribe(self, maxsize: int = 10) -> asyncio.Queue:
    """Subscribe to order book updates"""
    queue = asyncio.Queue(maxsize=maxsize)
    self._subscribers.add(queue)
    
    # Send initial snapshot
    snapshot = await self.get_snapshot()
    await queue.put(snapshot)
    
    return queue

def unsubscribe(self, queue: asyncio.Queue):
    """Unsubscribe from updates"""
    self._subscribers.discard(queue)
```

---

## Testing Strategies

### Async Test Fixtures

```python
@pytest.fixture
def event_loop():
    """Create event loop for tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def order_book():
    """Create fresh order book for each test"""
    ob = AsyncOrderBook(symbol="BTCUSDT", max_depth=10)
    yield ob
```

### Testing Circuit Breaker

```python
@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Circuit breaker opens after threshold failures"""
    cb = CircuitBreaker(failure_threshold=3)
    
    async def failing_coro():
        raise ValueError("Test error")
    
    # Trigger failures
    for _ in range(3):
        with pytest.raises(ValueError):
            await cb.call(failing_coro)
    
    assert cb.state == CircuitBreaker.State.OPEN
```

### Mocking Async Functions

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_websocket_connection():
    with patch('websockets.connect', new_callable=AsyncMock) as mock_ws:
        mock_ws.return_value = AsyncMock()
        
        manager = WebSocketOrderBookManager(uri="wss://test.example.com")
        
        await manager.start()
        assert mock_ws.called
        
        await manager.stop()
```

### Concurrent Stress Tests

```python
@pytest.mark.asyncio
async def test_order_book_concurrent_updates():
    """Order book handles concurrent updates"""
    ob = AsyncOrderBook(symbol="BTCUSDT", max_depth=100)
    await ob.apply_snapshot(sample_snapshot)
    
    async def update(i):
        await ob.apply_delta(
            side=Side.BID,
            price=Decimal(f"49990.{i:02d}"),
            size=Decimal(f"{i}.0"),
            update_id=12346 + i
        )
        return i
    
    # Run updates concurrently
    tasks = [update(i) for i in range(100)]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 100
```

---

## Common Pitfalls

### 1. Forgetting to Await

**WRONG:**
```python
async def fetch():
    response = session.get(url)  # Missing await!
    return response
```

**CORRECT:**
```python
async def fetch():
    async with session.get(url) as response:
        return await response.json()
```

### 2. Creating New Event Loops

**WRONG:**
```python
asyncio.run(main())  # Creates new loop
loop = asyncio.new_event_loop()  # Wrong in most cases
```

**CORRECT:**
```python
# Use existing loop or let asyncio manage it
await main()
```

### 3. Not Handling CancelledError

**WRONG:**
```python
async def worker():
    while True:
        await asyncio.sleep(1)  # Bare except catches CancelledError
```

**CORRECT:**
```python
async def worker():
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        # Cleanup
        raise  # Re-raise to allow proper cancellation
```

### 4. Shared Mutable State Without Locks

**WRONG:**
```python
class OrderBook:
    def __init__(self):
        self._bids = {}
    
    async def update(self, price, size):
        self._bids[price] = size  # Race condition!
```

**CORRECT:**
```python
class OrderBook:
    def __init__(self):
        self._bids = {}
        self._lock = asyncio.Lock()
    
    async def update(self, price, size):
        async with self._lock:
            self._bids[price] = size
```

### 5. Infinite Retries Without Backoff

**WRONG:**
```python
while True:
    try:
        await connect()
        break
    except:
        await asyncio.sleep(1)  # Constant delay
```

**CORRECT:**
```python
delay = 1.0
while self._reconnect_attempts < max_attempts:
    try:
        await connect()
        break
    except:
        jitter = random.random() * 0.1
        await asyncio.sleep(delay + jitter)
        delay = min(delay * 2, max_delay)  # Exponential backoff
```

### 6. Blocking in Async Code

**WRONG:**
```python
async def process():
    data = blocking_api_call()  # Blocks event loop!
    return data
```

**CORRECT:**
```python
async def process():
    data = await asyncio.to_thread(blocking_api_call)
    return data
```

### 7. Memory Leaks in Subscribers

**WRONG:**
```python
class OrderBook:
    def subscribe(self):
        queue = asyncio.Queue()
        self._subscribers.add(queue)
        return queue
    # Queue never removed!
```

**CORRECT:**
```python
class OrderBook:
    def subscribe(self):
        queue = asyncio.Queue()
        self._subscribers.add(queue)
        try:
            return queue
        finally:
            # Or explicit unsubscribe
            pass
    
    def unsubscribe(self, queue):
        self._subscribers.discard(queue)
```

---

## Best Practices

### 1. Always Use Context Managers

```python
# Good: Properly closes connection
async with aiohttp.ClientSession() as session:
    async with session.get(url) as response:
        data = await response.json()

# Good: WebSocket context manager
async with websockets.connect(uri) as ws:
    await ws.send("hello")
```

### 2. Implement Graceful Shutdown

```python
async def stop(self):
    """Clean shutdown with timeout"""
    self._should_run = False
    
    # Cancel tasks with timeout
    for task in self._tasks:
        if not task.done():
            task.cancel()
            try:
                await asyncio.wait_for(task, timeout=5)
            except asyncio.TimeoutError:
                task.cancel()
```

### 3. Use Structured Concurrency

```python
async def run_concurrent_tasks(self):
    """Run tasks with proper cleanup"""
    async with asyncio.TaskGroup() as tg:
        tg.create_task(self._receive_loop())
        tg.create_task(self._ping_loop())
        tg.create_task(self._message_processor())
    # Automatically waits and cleans up on exit
```

### 4. Implement Health Checks

```python
async def is_healthy(self) -> bool:
    """Check if connection is healthy"""
    if not self.is_connected:
        return False
    
    if self._last_message_time:
        elapsed = time.time() - self._last_message_time
        if elapsed > 60:  # No message in 60 seconds
            return False
    
    return True
```

### 5. Log with Context

```python
logger = logging.getLogger('OrderBook')

# Include context in logs
logger.info(f"[{self.symbol}] Connected to {self.uri}")
logger.warning(f"[{self.symbol}] Reconnecting in {delay}s")
```

### 6. Use Dataclasses for Data Transfer

```python
@dataclass(frozen=True)
class PriceLevel:
    price: Decimal
    size: Decimal
    side: Side
    
    def __post_init__(self):
        # Validate or normalize
        object.__setattr__(
            self, 'price',
            Decimal(str(self.price)).quantize(Decimal('0.00000001'))
        )
```

### 7. Prefer `asyncio.Event` Over Polling

```python
# Avoid polling
while not self._ready:
    await asyncio.sleep(0.1)

# Use Event
await self._ready_event.wait()
```

### 8. Use `asyncio.RLock` for Reentrant Locks

```python
class AsyncOrderBook:
    def __init__(self):
        self._lock = asyncio.RLock()  # Allows nested acquire
    
    async def method_a(self):
        async with self._lock:
            await self.method_b()  # Won't deadlock
    
    async def method_b(self):
        async with self._lock:
            # Safe with RLock
            pass
```

---

## Performance Tips

### 1. Batch Operations

```python
async def apply_batch_updates(self, updates: List[OrderBookDelta]):
    """Apply multiple updates atomically"""
    async with self._lock:
        for update in updates:
            self._apply_delta_unsafe(update)
        self._update_sorted_prices()
```

### 2. Use `deque` for Bounded Queues

```python
from collections import deque

class MetricsCollector:
    def __init__(self):
        # Only keeps last 100 values
        self._latency_history = deque(maxlen=100)
```

### 3. Avoid Creating Tasks When Not Needed

```python
# Unnecessary
task = asyncio.create_task(process_message(msg))
await task

# Better
await process_message(msg)
```

### 4. Use Connection Pooling

```python
# Share session across requests
class ApiClient:
    def __init__(self):
        self._session = aiohttp.ClientSession()
    
    async def request(self, url):
        async with self._session.get(url) as resp:
            return await resp.json()
```

### 5. Profile Async Code

```python
import time

async def profiled_operation(self):
    start = time.perf_counter()
    result = await self._operation()
    elapsed = time.perf_counter() - start
    
    if elapsed > 0.1:  # Log slow operations
        logger.warning(f"Slow operation: {elapsed:.3f}s")
    
    return result
```

---

## Resource Summary

### Key Concepts

| Pattern | Use Case | Library |
|---------|----------|---------|
| Circuit Breaker | Failing services | Custom |
| Token Bucket | Rate limiting | Custom |
| Events | Notification | `asyncio.Event` |
| Locks | Shared state | `asyncio.Lock/RLock` |
| Queues | Message passing | `asyncio.Queue` |
| Task Groups | Structured concurrency | `asyncio.TaskGroup` (3.11+) |

### Dependencies

```
aiohttp>=3.8.0
websockets>=12.0
pytest-asyncio>=0.21.0
```

### Further Reading

1. [Python Asyncio Documentation](https://docs.python.org/3/library/asyncio.html)
2. [WebSockets Library Documentation](https://websockets.readthedocs.io/)
3. [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
4. [Token Bucket Algorithm](https://en.wikipedia.org/wiki/Token_bucket)

---

*Document generated for Ghost learning session - Advanced Python Async Patterns*
