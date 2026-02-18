"""
Demo script showing async patterns without external dependencies
"""

import asyncio
import random
from decimal import Decimal
from websocket_orderbook import (
    CircuitBreaker,
    TokenBucketRateLimiter,
    AsyncOrderBook,
    Side,
    PriceLevel,
    OrderBookSnapshot,
    retry,
    semaphore_gather
)


async def demo_circuit_breaker():
    """Demonstrate circuit breaker functionality"""
    print("\n" + "="*60)
    print("DEMO: Circuit Breaker Pattern")
    print("="*60)
    
    cb = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=2.0,
        half_open_max_calls=2
    )
    
    # Phase 1: Normal operation
    print("\n[Phase 1] Normal operation:")
    for i in range(5):
        try:
            result = await cb.call(lambda: asyncio.sleep(0.1, "success"))
            print(f"  Call {i+1}: SUCCESS")
        except Exception as e:
            print(f"  Call {i+1}: FAILED - {e}")
    
    # Phase 2: Trigger failures
    print("\n[Phase 2] Triggering failures:")
    fail_count = 0
    async def failing_coro():
        nonlocal fail_count
        fail_count += 1
        raise ValueError(f"Simulated failure #{fail_count}")
    
    for i in range(5):
        try:
            await cb.call(failing_coro)
        except ValueError:
            print(f"  Call {i+1}: FAILED (expected), circuit state: {cb.state.name}")
        except ConnectionError as e:
            print(f"  Call {i+1}: CIRCUIT OPEN - {e}")
            break
    
    print(f"\nCurrent state: {cb.state.name}")
    print("Waiting for recovery timeout...")
    await asyncio.sleep(2.5)
    
    # Phase 3: Recovery
    print("\n[Phase 3] Recovery (HALF_OPEN):")
    try:
        async def success_coro():
            return "recovered"
        result = await cb.call(success_coro)
        print(f"  Test call: {result}")
        print(f"  Circuit state: {cb.state.name}")
    except Exception as e:
        print(f"  Recovery failed: {e}")


async def demo_rate_limiter():
    """Demonstrate rate limiting"""
    print("\n" + "="*60)
    print("DEMO: Token Bucket Rate Limiter")
    print("="*60)
    
    # Fast burst
    limiter = TokenBucketRateLimiter(
        messages_per_second=5.0,
        burst_size=3
    )
    
    print("\n[Phase 1] Burst of 3 messages (should be immediate):")
    for i in range(3):
        wait = await limiter.acquire()
        print(f"  Message {i+1}: wait={wait:.3f}s")
    
    print("\n[Phase 2] Rate limiting kicks in:")
    for i in range(5):
        wait = await limiter.acquire()
        if wait > 0:
            print(f"  Message {i+4}: wait={wait:.3f}s...")
            await asyncio.sleep(wait)
        print(f"  Message {i+4}: SENT (rate limited)")


async def demo_order_book():
    """Demonstrate order book operations"""
    print("\n" + "="*60)
    print("DEMO: Async Order Book")
    print("="*60)
    
    # Create order book
    ob = AsyncOrderBook(symbol="BTCUSDT", max_depth=5)
    
    # Apply snapshot
    snapshot = OrderBookSnapshot(
        symbol="BTCUSDT",
        bids=[
            PriceLevel(Decimal("50000"), Decimal("1.5"), Side.BID),
            PriceLevel(Decimal("49990"), Decimal("2.0"), Side.BID),
            PriceLevel(Decimal("49980"), Decimal("3.0"), Side.BID),
        ],
        asks=[
            PriceLevel(Decimal("50010"), Decimal("1.2"), Side.ASK),
            PriceLevel(Decimal("50020"), Decimal("2.5"), Side.ASK),
            PriceLevel(Decimal("50030"), Decimal("4.0"), Side.ASK),
        ],
        last_update_id=1,
        timestamp=asyncio.get_event_loop().time()
    )
    
    await ob.apply_snapshot(snapshot)
    print("\n[Order Book Snapshot Applied]")
    
    # Get bid/ask
    bid_ask = await ob.get_bid_ask()
    if bid_ask:
        best_bid, best_ask = bid_ask
        spread = await ob.get_spread()
        print(f"  Best Bid: {best_bid.price} @ {best_bid.size}")
        print(f"  Best Ask: {best_ask.price} @ {best_ask.size}")
        print(f"  Spread: {spread}")
    
    # Apply delta updates
    print("\n[Delta Updates]")
    await ob.apply_delta(Side.BID, Decimal("50000"), Decimal("0.5"), 2)
    print("  Reduced bid @ 50000 to 0.5")
    
    await ob.apply_delta(Side.BID, Decimal("50005"), Decimal("1.0"), 3)
    print("  Added new bid @ 50005 with size 1.0")
    
    await ob.apply_delta(Side.ASK, Decimal("50030"), Decimal("0"), 4)
    print("  Removed ask @ 50030 (size=0)")
    
    # Get updated state
    bid_ask = await ob.get_bid_ask()
    if bid_ask:
        best_bid, best_ask = bid_ask
        print(f"\n[Updated]")
        print(f"  Best Bid: {best_bid.price} @ {best_bid.size}")
        print(f"  Best Ask: {best_ask.price} @ {best_ask.size}")
    
    # Subscribe and receive updates
    print("\n[Pub/Sub Test]")
    queue = await ob.subscribe()
    
    # Get initial snapshot from queue
    initial = await asyncio.wait_for(queue.get(), timeout=1.0)
    print(f"  Subscriber received snapshot with {len(initial.bids)} bids, {len(initial.asks)} asks")
    
    # Cleanup
    ob.unsubscribe(queue)


async def demo_concurrency():
    """Demonstrate concurrent execution patterns"""
    print("\n" + "="*60)
    print("DEMO: Concurrent Execution with Semaphore")
    print("="*60)
    
    semaphore = asyncio.Semaphore(3)
    
    async def worker(task_id):
        print(f"  Task {task_id}: START")
        await asyncio.sleep(0.5)
        print(f"  Task {task_id}: DONE")
        return task_id
    
    tasks = [worker(i) for i in range(10)]
    print("\nRunning 10 tasks with max 3 concurrent...")
    results = await semaphore_gather(tasks, semaphore)
    print(f"Completed: {results}")


async def demo_retry():
    """Demonstrate retry decorator"""
    print("\n" + "="*60)
    print("DEMO: Retry Decorator")
    print("="*60)
    
    attempt = [0]
    max_failures = 2
    
    @retry(max_attempts=4, exceptions=(ValueError,), delay=0.1, backoff=2.0)
    async def unreliable_operation():
        attempt[0] += 1
        print(f"  Attempt {attempt[0]}...")
        if attempt[0] <= max_failures:
            raise ValueError(f"Simulated failure #{attempt[0]}")
        return "success"
    
    print("\nExecuting unreliable operation with retry...")
    result = await unreliable_operation()
    print(f"Final result: {result}")
    print(f"Total attempts: {attempt[0]}")


async def main():
    """Run all demos"""
    print("\n" + "█"*60)
    print("ADVANCED ASYNC PATTERNS DEMO")
    print("█"*60)
    
    await demo_circuit_breaker()
    await demo_rate_limiter()
    await demo_order_book()
    await demo_concurrency()
    await demo_retry()
    
    print("\n" + "█"*60)
    print("ALL DEMOS COMPLETED")
    print("█"*60)


if __name__ == "__main__":
    asyncio.run(main())
