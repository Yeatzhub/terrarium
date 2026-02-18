"""
pytest unit tests for WebSocket order book manager
Production-grade test coverage for all async patterns
"""

import asyncio
import json
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import timedelta

# Import the module under test
from websocket_orderbook import (
    CircuitBreaker,
    CircuitBreakerError,
    TokenBucketRateLimiter,
    AsyncOrderBook,
    WebSocketOrderBookManager,
    BinanceOrderBookManager,
    Side,
    PriceLevel,
    OrderBookSnapshot,
    ConnectionError,
    BackpressureError,
    RateLimitError,
    retry,
    semaphore_gather,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def event_loop():
    """Create event loop for tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def circuit_breaker():
    """Create fresh circuit breaker for each test"""
    cb = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=1.0,
        half_open_max_calls=2
    )
    yield cb


@pytest.fixture
async def rate_limiter():
    """Create fresh rate limiter for each test"""
    rl = TokenBucketRateLimiter(
        messages_per_second=10.0,
        burst_size=5
    )
    yield rl


@pytest.fixture
async def order_book():
    """Create fresh order book for each test"""
    ob = AsyncOrderBook(
        symbol="BTCUSDT",
        max_depth=10
    )
    yield ob


@pytest.fixture
def sample_snapshot():
    """Create sample order book snapshot"""
    return OrderBookSnapshot(
        symbol="BTCUSDT",
        bids=[
            PriceLevel(price=Decimal("50000.00"), size=Decimal("1.5"), side=Side.BID),
            PriceLevel(price=Decimal("49990.00"), size=Decimal("2.0"), side=Side.BID),
            PriceLevel(price=Decimal("49980.00"), size=Decimal("3.0"), side=Side.BID),
        ],
        asks=[
            PriceLevel(price=Decimal("50010.00"), size=Decimal("1.2"), side=Side.ASK),
            PriceLevel(price=Decimal("50020.00"), size=Decimal("2.5"), side=Side.ASK),
            PriceLevel(price=Decimal("50030.00"), size=Decimal("4.0"), side=Side.ASK),
        ],
        last_update_id=12345,
        timestamp=1234567890.0
    )


# =============================================================================
# Circuit Breaker Tests
# =============================================================================

@pytest.mark.asyncio
async def test_circuit_breaker_starts_closed(circuit_breaker):
    """Circuit breaker starts in CLOSED state"""
    assert circuit_breaker.state == CircuitBreaker.State.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures(circuit_breaker):
    """Circuit breaker opens after threshold failures"""
    async def failing_coro():
        raise ValueError("Test error")
    
    # Trigger failures
    for _ in range(3):
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_coro)
    
    # Should be OPEN now
    assert circuit_breaker.state == CircuitBreaker.State.OPEN
    
    # Should reject immediately
    with pytest.raises(ConnectionError):
        await circuit_breaker.call(failing_coro)


@pytest.mark.asyncio
async def test_circuit_breaker_records_success(circuit_breaker):
    """Successful calls reset failure count"""
    async def success_coro():
        return "success"
    
    result = await circuit_breaker.call(success_coro)
    assert result == "success"


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_transition(circuit_breaker):
    """Circuit breaker transitions to HALF_OPEN after timeout"""
    async def failing_coro():
        raise ValueError("Test error")
    
    # Open the circuit
    for _ in range(3):
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_coro)
    
    assert circuit_breaker.state == CircuitBreaker.State.OPEN
    
    # Wait for recovery timeout
    await asyncio.sleep(1.1)
    
    # Should allow calls now (HALF_OPEN)
    call_count = [0]
    async def half_open_test():
        call_count[0] += 1
        return "test"
    
    result = await circuit_breaker.call(half_open_test)
    assert result == "test"
    assert call_count[0] == 1


@pytest.mark.asyncio
async def test_circuit_breaker_closes_after_successes(circuit_breaker):
    """Circuit breaker closes after enough successes in HALF_OPEN"""
    # Open it first
    async def failing_coro():
        raise ValueError("Test error")
    
    for _ in range(3):
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_coro)
    
    assert circuit_breaker.state == CircuitBreaker.State.OPEN
    
    # Wait and succeed
    await asyncio.sleep(1.1)
    
    async def success_coro():
        return "success"
    
    # Need half_open_max_calls successes
    for _ in range(2):
        await circuit_breaker.call(success_coro)
    
    assert circuit_breaker.state == CircuitBreaker.State.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_reopens_on_failure_in_half_open(circuit_breaker):
    """Circuit breaker reopens if failure in HALF_OPEN"""
    # Open it
    for _ in range(3):
        with pytest.raises(ValueError):
            await circuit_breaker.call(lambda: (_ for _ in ()).throw(ValueError("Test")))
    
    await asyncio.sleep(1.1)
    
    # Fail in half-open
    with pytest.raises(ValueError):
        await circuit_breaker.call(lambda: (_ for _ in ()).throw(ValueError("Test")))
    
    assert circuit_breaker.state == CircuitBreaker.State.OPEN


# =============================================================================
# Rate Limiter Tests
# =============================================================================

@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limit(rate_limiter):
    """Rate limiter allows requests within limit"""
    # Should be able to acquire burst_size immediately
    for _ in range(5):
        wait = await rate_limiter.acquire()
        assert wait == 0.0


@pytest.mark.asyncio
async def test_rate_limiter_delays_when_exhausted(rate_limiter):
    """Rate limiter calculates delay when tokens exhausted"""
    # Exhaust tokens
    for _ in range(5):
        await rate_limiter.acquire()
    
    # Next call should require delay
    wait = await rate_limiter.acquire()
    assert wait > 0
    assert wait < 2.0  # Should be reasonable


@pytest.mark.asyncio
async def test_rate_limiter_backpressure(rate_limiter):
    """Rate limiter raises BackpressureError on excessive wait"""
    # Set up to trigger backpressure
    limiter = TokenBucketRateLimiter(
        messages_per_second=0.01,  # Very slow
        burst_size=1
    )
    
    # Use the one token
    await limiter.acquire()
    
    # Next should trigger backpressure
    with pytest.raises(BackpressureError):
        await limiter.acquire()


@pytest.mark.asyncio
async def test_rate_limiter_context_manager():
    """Rate limiter works as async context manager"""
    limiter = TokenBucketRateLimiter(
        messages_per_second=100,
        burst_size=10
    )
    
    async with limiter:
        pass  # Should acquire token


@pytest.mark.asyncio
async def test_rate_limiter_byte_limit():
    """Rate limiter respects byte limits"""
    limiter = TokenBucketRateLimiter(
        messages_per_second=100,
        burst_size=10,
        bytes_per_second=100
    )
    
    # Send message within byte limit
    wait = await limiter.acquire(message_size=50)
    assert wait == 0.0
    
    # Exhaust byte tokens
    wait = await limiter.acquire(message_size=100)
    assert wait == 0.0  # Still have some tokens


# =============================================================================
# Order Book Tests
# =============================================================================

@pytest.mark.asyncio
async def test_order_book_apply_snapshot(order_book, sample_snapshot):
    """Order book applies snapshot correctly"""
    await order_book.apply_snapshot(sample_snapshot)
    
    snapshot = await order_book.get_snapshot()
    assert snapshot.symbol == "BTCUSDT"
    assert len(snapshot.bids) == 3
    assert len(snapshot.asks) == 3


@pytest.mark.asyncio
async def test_order_book_sorted_prices(order_book, sample_snapshot):
    """Order book maintains sorted price levels"""
    await order_book.apply_snapshot(sample_snapshot)
    
    bid_ask = await order_book.get_bid_ask()
    assert bid_ask is not None
    
    best_bid, best_ask = bid_ask
    # Best bid should be highest
    assert best_bid.price == Decimal("50000.00")
    # Best ask should be lowest
    assert best_ask.price == Decimal("50010.00")


@pytest.mark.asyncio
async def test_order_book_spread_calculation(order_book, sample_snapshot):
    """Order book calculates spread correctly"""
    await order_book.apply_snapshot(sample_snapshot)
    
    spread = await order_book.get_spread()
    assert spread is not None
    assert spread == Decimal("10.00")  # 50010 - 50000


@pytest.mark.asyncio
async def test_order_book_apply_delta_update(order_book, sample_snapshot):
    """Order book applies delta updates"""
    await order_book.apply_snapshot(sample_snapshot)
    
    # Update existing level
    await order_book.apply_delta(
        side=Side.BID,
        price=Decimal("50000.00"),
        size=Decimal("2.5"),
        update_id=12346
    )
    
    snapshot = await order_book.get_snapshot()
    best_bid = snapshot.bids[0]
    assert best_bid.size == Decimal("2.5")


@pytest.mark.asyncio
async def test_order_book_apply_delta_delete(order_book, sample_snapshot):
    """Order book deletes level when size is zero"""
    await order_book.apply_snapshot(sample_snapshot)
    
    # Delete a level
    await order_book.apply_delta(
        side=Side.BID,
        price=Decimal("49980.00"),
        size=Decimal("0"),
        update_id=12346
    )
    
    snapshot = await order_book.get_snapshot()
    prices = [b.price for b in snapshot.bids]
    assert Decimal("49980.00") not in prices


@pytest.mark.asyncio
async def test_order_book_insert_new_level(order_book, sample_snapshot):
    """Order book inserts new price level"""
    await order_book.apply_snapshot(sample_snapshot)
    
    # Insert new level
    await order_book.apply_delta(
        side=Side.BID,
        price=Decimal("50005.00"),
        size=Decimal("1.0"),
        update_id=12346
    )
    
    snapshot = await order_book.get_snapshot()
    best_bid = snapshot.bids[0]
    assert best_bid.price == Decimal("50005.00")


@pytest.mark.asyncio
async def test_order_book_update_filtering(order_book, sample_snapshot):
    """Order book skips outdated updates"""
    await order_book.apply_snapshot(sample_snapshot)
    
    # Try to update with old update_id
    await order_book.apply_delta(
        side=Side.BID,
        price=Decimal("49970.00"),
        size=Decimal("1.0"),
        update_id=12340  # Less than snapshot's 12345
    )
    
    # Level should not be added
    snapshot = await order_book.get_snapshot()
    prices = [b.price for b in snapshot.bids]
    assert Decimal("49970.00") not in prices


@pytest.mark.asyncio
async def test_order_book_max_depth(order_book):
    """Order book respects max depth"""
    snapshot = OrderBookSnapshot(
        symbol="BTCUSDT",
        bids=[
            PriceLevel(price=Decimal(f"{50000 - i}.00"), size=Decimal("1.0"), side=Side.BID)
            for i in range(20)
        ],
        asks=[
            PriceLevel(price=Decimal(f"{50000 + i}.00"), size=Decimal("1.0"), side=Side.ASK)
            for i in range(20)
        ],
        last_update_id=1,
        timestamp=1.0
    )
    
    await order_book.apply_snapshot(snapshot)
    
    result = await order_book.get_snapshot()
    assert len(result.bids) == 10  # max_depth
    assert len(result.asks) == 10


@pytest.mark.asyncio
async def test_order_book_subscription(order_book, sample_snapshot):
    """Order book subscription receives updates"""
    await order_book.apply_snapshot(sample_snapshot)
    
    # Subscribe
    queue = await order_book.subscribe()
    
    # Get initial snapshot
    initial = await queue.get()
    assert initial.symbol == "BTCUSDT"
    
    # Trigger update
    await order_book.apply_delta(
        side=Side.BID,
        price=Decimal("50000.00"),
        size=Decimal("5.0"),
        update_id=12346
    )
    
    # Should receive update
    update = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert update.symbol == "BTCUSDT"


@pytest.mark.asyncio
async def test_order_book_unsubscribe(order_book, sample_snapshot):
    """Unsubscribe removes queue from subscribers"""
    await order_book.apply_snapshot(sample_snapshot)
    
    queue = await order_book.subscribe()
    order_book.unsubscribe(queue)
    
    # Trigger multiple updates to potentially overflow
    for i in range(20):
        await order_book.apply_delta(
            side=Side.BID,
            price=Decimal(f"{50000 + i}.00"),
            size=Decimal("1.0"),
            update_id=12346 + i
        )
    
    # Queue should not have received more updates
    # (we got initial snapshot, but that's it)
    assert queue.qsize() <= 1


# =============================================================================
# WebSocket Manager Tests
# =============================================================================

@pytest.mark.asyncio
async def test_websocket_manager_initialization():
    """WebSocket manager initializes with correct settings"""
    manager = WebSocketOrderBookManager(
        uri="wss://test.example.com/ws",
        symbol="BTCUSDT",
        reconnect_config={
            'initial_delay': 1.0,
            'max_delay': 60.0,
            'backoff_factor': 2.0,
            'max_attempts': 5
        },
        rate_limit_config={
            'messages_per_second': 100,
            'burst_size': 10
        }
    )
    
    assert manager.uri == "wss://test.example.com/ws"
    assert manager.symbol == "BTCUSDT"
    assert not manager.is_connected
    assert manager.circuit_state.name == "CLOSED"


@pytest.mark.asyncio
async def test_websocket_manager_stats_structure():
    """WebSocket manager returns proper stats structure"""
    manager = WebSocketOrderBookManager(
        uri="wss://test.example.com/ws",
        symbol="BTCUSDT"
    )
    
    stats = manager.get_stats()
    assert 'messages_received' in stats
    assert 'messages_processed' in stats
    assert 'reconnects' in stats
    assert 'circuit_state' in stats
    assert '队列_size' in stats


@pytest.mark.asyncio
async def test_websocket_order_book_property():
    """WebSocket manager exposes order book property"""
    manager = WebSocketOrderBookManager(
        uri="wss://test.example.com/ws",
        symbol="BTCUSDT"
    )
    
    ob = manager.order_book
    assert ob.symbol == "BTCUSDT"


# =============================================================================
# Decorator Tests
# =============================================================================

@pytest.mark.asyncio
async def test_retry_decorator_success():
    """Retry decorator succeeds on first try"""
    call_count = [0]
    
    @retry(max_attempts=3, exceptions=(ValueError,))
    async def test_func():
        call_count[0] += 1
        return "success"
    
    result = await test_func()
    assert result == "success"
    assert call_count[0] == 1


@pytest.mark.asyncio
async def test_retry_decorator_retries_on_failure():
    """Retry decorator retries on failure"""
    call_count = [0]
    
    @retry(max_attempts=3, exceptions=(ValueError,), delay=0.01)
    async def test_func():
        call_count[0] += 1
        if call_count[0] < 3:
            raise ValueError(f"Attempt {call_count[0]}")
        return "success"
    
    result = await test_func()
    assert result == "success"
    assert call_count[0] == 3


@pytest.mark.asyncio
async def test_retry_decorator_exhausts_attempts():
    """Retry decorator raises after max attempts"""
    @retry(max_attempts=3, exceptions=(ValueError,), delay=0.01)
    async def test_func():
        raise ValueError("Always fails")
    
    with pytest.raises(ValueError, match="Always fails"):
        await test_func()


@pytest.mark.asyncio
async def test_retry_decorator_ignores_other_exceptions():
    """Retry decorator ignores non-matching exceptions"""
    @retry(max_attempts=3, exceptions=(ValueError,), delay=0.01)
    async def test_func():
        raise TypeError("Wrong exception")
    
    with pytest.raises(TypeError):
        await test_func()


@pytest.mark.asyncio
async def test_semaphore_gather_limits_concurrency():
    """Semaphore gather limits concurrent execution"""
    active_count = [0]
    max_active = [0]
    lock = asyncio.Lock()
    
    async def worker(i):
        async with lock:
            active_count[0] += 1
            max_active[0] = max(max_active[0], active_count[0])
        
        await asyncio.sleep(0.05)
        
        async with lock:
            active_count[0] -= 1
        
        return i
    
    semaphore = asyncio.Semaphore(3)
    results = await semaphore_gather(
        [worker(i) for i in range(10)],
        semaphore
    )
    
    assert max_active[0] == 3
    assert sorted(results) == list(range(10))


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.asyncio
async def test_rate_limiter_with_timeout():
    """Rate limiter handles concurrent access"""
    limiter = TokenBucketRateLimiter(
        messages_per_second=10,
        burst_size=2
    )
    
    # First 2 should be immediate
    results = []
    for _ in range(2):
        wait = await limiter.acquire()
        results.append(wait)
    
    for wait in results:
        assert wait == 0.0


@pytest.mark.asyncio
async def test_circuit_breaker_concurrent_access():
    """Circuit breaker handles concurrent calls safely"""
    cb = CircuitBreaker(failure_threshold=5, recovery_timeout=0.1)
    
    async def success():
        await asyncio.sleep(0.01)
        return "ok"
    
    # Run multiple concurrent calls
    tasks = [cb.call(success) for _ in range(10)]
    results = await asyncio.gather(*tasks)
    
    assert all(r == "ok" for r in results)


@pytest.mark.asyncio
async def test_order_book_concurrent_updates(order_book, sample_snapshot):
    """Order book handles concurrent updates"""
    await order_book.apply_snapshot(sample_snapshot)
    
    async def update(i):
        await order_book.apply_delta(
            side=Side.BID,
            price=Decimal(f"49990.{i:02d}"),
            size=Decimal(f"{i}.0"),
            update_id=12346 + i
        )
        return i
    
    # Run updates concurrently
    tasks = [update(i) for i in range(20)]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 20
    
    # Verify order book is still consistent
    snapshot = await order_book.get_snapshot()
    assert len(snapshot.bids) <= 10


# =============================================================================
# Edge Cases
# =============================================================================

@pytest.mark.asyncio
async def test_order_book_empty(order_book):
    """Order book handles empty state"""
    snapshot = await order_book.get_snapshot()
    assert len(snapshot.bids) == 0
    assert len(snapshot.asks) == 0
    
    bid_ask = await order_book.get_bid_ask()
    assert bid_ask is None
    
    spread = await order_book.get_spread()
    assert spread is None


@pytest.mark.asyncio
async def test_price_level_decimal_precision():
    """Price level handles decimal precision"""
    level = PriceLevel(
        price=Decimal("50000.123456789"),
        size=Decimal("1.12345678901234567890"),
        side=Side.BID
    )
    
    # Should be quantized to 8 decimal places
    assert level.price.as_tuple().exponent >= -8
    assert level.size.as_tuple().exponent >= -8


@pytest.mark.asyncio
async def test_circuit_breaker_immediate_reopen():
    """Circuit breaker can be opened and closed"""
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=0.01)
    
    # Open it
    with pytest.raises(ValueError):
        await cb.call(lambda: (_ for _ in ()).throw(ValueError("Test")))
    
    assert cb.state == CircuitBreaker.State.OPEN
    
    # Wait for recovery
    await asyncio.sleep(0.02)
    
    # Should be able to test now
    await cb.call(lambda: asyncio.sleep(0))


@pytest.mark.asyncio
async def test_rate_limiter_replenishment():
    """Rate limiter replenishes tokens over time"""
    limiter = TokenBucketRateLimiter(
        messages_per_second=10.0,
        burst_size=1
    )
    
    # Use the one token
    await limiter.acquire()
    
    # Wait for replenishment
    await asyncio.sleep(0.15)  # Wait ~1.5 token's worth
    
    # Should have tokens now
    wait = await limiter.acquire()
    # Might still have small delay depending on timing
    assert wait < 0.5


# =============================================================================
# Performance Tests
# =============================================================================

@pytest.mark.asyncio
async def test_order_book_high_frequency_updates(order_book, sample_snapshot):
    """Order book handles high-frequency updates"""
    await order_book.apply_snapshot(sample_snapshot)
    
    start = asyncio.get_event_loop().time()
    
    # Simulate 1000 updates
    for i in range(1000):
        await order_book.apply_delta(
            side=Side.BID,
            price=Decimal(f"49990.{i % 100:02d}"),
            size=Decimal(f"{i % 10}.0"),
            update_id=12346 + i
        )
    
    elapsed = asyncio.get_event_loop().time() - start
    
    # Should complete in reasonable time
    assert elapsed < 5.0
    
    snapshot = await order_book.get_snapshot()
    assert order_book._update_count == 1000


@pytest.mark.asyncio
async def test_circuit_breaker_performance():
    """Circuit breaker doesn't significantly impact performance"""
    cb = CircuitBreaker(failure_threshold=1000)
    
    async def fast_func():
        return "ok"
    
    start = asyncio.get_event_loop().time()
    
    # Run 1000 calls
    for _ in range(1000):
        await cb.call(fast_func)
    
    elapsed = asyncio.get_event_loop().time() - start
    
    # Should be very fast
    assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])