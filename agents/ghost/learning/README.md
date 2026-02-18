# WebSocket Order Book Manager - Async Learning Project

A complete, production-ready implementation of a WebSocket order book manager demonstrating advanced Python asyncio patterns.

## Files

| File | Description |
|------|-------------|
| `websocket-orderbook.py` | Main implementation with 800+ lines of production code |
| `test_websocket_orderbook.py` | Comprehensive pytest suite with 30+ test cases |
| `python-async-patterns.md` | Complete documentation with patterns, pitfalls, best practices |
| `requirements.txt` | Python dependencies |
| `README.md` | This file |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest test_websocket_orderbook.py -v

# Run example (requires Binance testnet connection)
python websocket-orderbook.py
```

## Implementation Highlights

### 1. Circuit Breaker Pattern
- Prevents cascade failures
- Three states: CLOSED, OPEN, HALF_OPEN
- Automatic recovery with configurable timeouts
- Thread-safe concurrent access

### 2. Token Bucket Rate Limiter
- Message rate limiting
- Byte throughput limiting
- Backpressure handling with overflow detection
- Async context manager support

### 3. Async Order Book
- Thread-safe RLock for concurrent access
- Sorted price levels maintained efficiently
- Pub/sub pattern for real-time updates
- Incremental delta updates + full snapshots

### 4. WebSocket Manager
- Automatic reconnection with exponential backoff + jitter
- Connection health monitoring with ping/pong
- Circuit breaker integration
- Separate message queue for ordered processing
- Event callbacks (on_connect, on_message, on_error, on_disconnect)

### 5. Exchange-Specific Implementation
- Binance order book with REST snapshot + WebSocket deltas
- Proper synchronization of update IDs
- Handles out-of-sequence updates

## Key Patterns Demonstrated

1. **Circuit Breaker** - Fault tolerance
2. **Token Bucket** - Rate limiting
3. **Pub/Sub** - Event-driven architecture
4. **Exponential Backoff** - Connection resilience
5. **Structured Concurrency** - Task management
6. **RLock** - Reentrant locking
7. **Event Notification** - Async signaling
8. **Semaphore Gather** - Limited concurrency

## Testing Coverage

- Circuit breaker state transitions
- Rate limiting behavior
- Backpressure detection
- Order book consistency
- Concurrent update handling
- Retry decorator functionality
- Timeout handling
- Edge cases (empty state, precision, etc.)

## Documentation

See `python-async-patterns.md` for:
- Detailed pattern explanations
- Code examples
- Common pitfalls and solutions
- Best practices
- Performance tips

## Requirements

- Python 3.11+
- asyncio
- websockets
- aiohttp
- pytest-asyncio

## Author

**Ghost** - Code Execution Specialist

## Reference

Based on patterns from `solana-jupiter-bot/jupiter_momentum_bot.py` - adapted for async/concurrent execution.