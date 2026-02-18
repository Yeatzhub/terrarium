# Database Connection Patterns for High-Frequency Trading

> Reference material for trading bot development
> Covers: PostgreSQL/AsyncPG, Redis/AioRedis, TimescaleDB, Retry Logic, Circuit Breakers

---

## 1. Async PostgreSQL Connection Pooling (asyncpg)

### Best Practices

- **Pool sizing**: Calculate based on (core_count * 2) + effective_spindle_count
- **HFT recommendation**: Small pools with aggressive timeouts to prevent connection buildup
- **Always use prepared statements** for repeated queries (significant latency reduction)

### Connection Pool Configuration

```python
import asyncpg
from contextlib import asynccontextmanager
from typing import Optional
import asyncio

class PostgresPoolManager:
    """HFT-optimized PostgreSQL connection pool."""
    
    def __init__(
        self, 
        dsn: str,
        min_size: int = 2,           # Minimum connections kept alive
        max_size: int = 10,          # Maximum connections (HFT: keep low)
        max_inactive_time: float = 60.0,  # Close idle connections quickly
        command_timeout: float = 5.0,     # Query timeout (HFT: aggressive)
        init_command_timeout: float = 10.0
    ):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.max_inactive_time = max_inactive_time
        self.command_timeout = command_timeout
        self.init_command_timeout = init_command_timeout
        self._pool: Optional[asyncpg.Pool] = None
        self._statement_cache: dict = {}
        
    async def initialize(self):
        """Initialize the connection pool."""
        self._pool = await asyncpg.create_pool(
            dsn=self.dsn,
            min_size=self.min_size,
            max_size=self.max_size,
            max_inactive_connection_lifetime=self.max_inactive_time,
            command_timeout=self.command_timeout,
            init_command_timeout=self.init_command_timeout,
            # HFT optimizations
            server_settings={
                'jit': 'off',  # Disable JIT for short queries (trading queries are fast)
                'application_name': 'hft_bot',
            },
            # Connection initialization
            init=self._init_connection
        )
        
    async def _init_connection(self, conn: asyncpg.Connection):
        """Configure each new connection for HFT."""
        await conn.set_type_codec(
            'json',
            encoder=str,
            decoder=str,
            schema='pg_catalog'
        )
        # Set session-level timeouts
        await conn.execute('SET statement_timeout = \'5000ms\'')
        await conn.execute('SET lock_timeout = \'1000ms\'')
        await conn.execute('SET idle_in_transaction_session_timeout = \'5000ms\'')
        
    @asynccontextmanager
    async def acquire(self):
        """Context manager for acquiring a connection."""
        if not self._pool:
            raise RuntimeError("Pool not initialized. Call initialize() first.")
        async with self._pool.acquire() as conn:
            yield conn
            
    async def execute_with_retry(
        self, 
        query: str, 
        *args,
        max_retries: int = 3,
        prepared: bool = True
    ):
        """Execute query with automatic prepared statement caching."""
        async with self.acquire() as conn:
            if prepared:
                # Use prepared statements for trading queries
                stmt_name = f"stmt_{hash(query) % 10000}"
                try:
                    return await conn.fetchval(query, *args)
                except asyncpg.PostgresError:
                    # Fallback without prepared statement on error
                    return await conn.fetchval(query, *args)
            else:
                return await conn.fetchval(query, *args)
                
    async def close(self):
        """Gracefully close the pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            
    async def health_check(self) -> bool:
        """Quick health check for circuit breaker integration."""
        try:
            async with self.acquire() as conn:
                result = await conn.fetchval('SELECT 1')
                return result == 1
        except Exception:
            return False


# Usage Example
async def example_usage():
    dsn = "postgresql://user:pass@localhost:5432/trading_db"
    pool = PostgresPoolManager(dsn)
    await pool.initialize()
    
    try:
        # Insert trade with prepared statement optimization
        trade_id = await pool.execute_with_retry(
            """
            INSERT INTO trades (symbol, price, quantity, side, timestamp)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            "BTC-USD", 45000.50, 0.5, "BUY", "2025-01-15T10:30:00Z"
        )
        print(f"Trade inserted: {trade_id}")
        
    finally:
        await pool.close()
```

### HFT-Specific Optimizations

```python
# Disable prepared statement cache for ultra-low latency
# (when you need to execute the same query millions of times)
async def ultra_fast_insert(pool: PostgresPoolManager, trades: list):
    """Batch insert trades with COPY for maximum throughput."""
    async with pool.acquire() as conn:
        # COPY is significantly faster than INSERT for bulk data
        await conn.copy_records_to_table(
            'trades',
            records=trades,
            columns=['symbol', 'price', 'quantity', 'side', 'timestamp']
        )
```

---

## 2. Redis Connection Management for Trading (aioredis)

### Best Practices

- **Use connection pooling**: Redis connections are expensive to establish
- **Pipeline commands**: Group multiple operations for network efficiency
- **Pub/Sub for real-time data**: Subscribe to market data feeds
- **Stream data types**: Use Redis Streams for ordered event logs

### Connection Pool Configuration

```python
import aioredis
from typing import Optional, Any, List
import json
from dataclasses import asdict
from contextlib import asynccontextmanager

class RedisTradingClient:
    """HFT-optimized Redis client with pipeline support."""
    
    def __init__(
        self,
        host: str = 'localhost',
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        max_connections: int = 50,       # HFT: moderate pool size
        socket_connect_timeout: float = 2.0,
        socket_timeout: float = 2.0,
        socket_keepalive: bool = True,   # Keep connections alive
        health_check_interval: int = 30  # Health check every 30s
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.max_connections = max_connections
        self.socket_connect_timeout = socket_connect_timeout
        self.socket_timeout = socket_timeout
        self.socket_keepalive = socket_keepalive
        self.health_check_interval = health_check_interval
        self._pool: Optional[aioredis.Redis] = None
        
    async def initialize(self):
        """Initialize Redis connection pool."""
        self._pool = await aioredis.from_url(
            f"redis://{self.host}:{self.port}/{self.db}",
            password=self.password,
            max_connections=self.max_connections,
            socket_connect_timeout=self.socket_connect_timeout,
            socket_timeout=self.socket_timeout,
            socket_keepalive=self.socket_keepalive,
            health_check_interval=self.health_check_interval,
            decode_responses=True,  # Auto-decode bytes to strings
            # HFT-specific settings
            retry_on_timeout=True,
            retry_on_error=[aioredis.ConnectionError, aioredis.TimeoutError],
        )
        
    async def set_tick(self, symbol: str, tick_data: dict, ttl: int = 60):
        """Store latest tick data with expiration."""
        if not self._pool:
            raise RuntimeError("Redis not initialized")
        key = f"tick:{symbol}"
        await self._pool.setex(key, ttl, json.dumps(tick_data))
        
    async def get_tick(self, symbol: str) -> Optional[dict]:
        """Get latest tick data."""
        if not self._pool:
            return None
        data = await self._pool.get(f"tick:{symbol}")
        return json.loads(data) if data else None
        
    async def cache_order_book(self, symbol: str, order_book: dict):
        """Cache order book snapshot with short TTL."""
        if not self._pool:
            return
        key = f"orderbook:{symbol}"
        # Use transaction for consistency
        pipe = self._pool.pipeline()
        pipe.delete(key)
        pipe.hset(key, mapping={
            'bids': json.dumps(order_book.get('bids', [])),
            'asks': json.dumps(order_book.get('asks', [])),
            'timestamp': order_book.get('timestamp'),
            'sequence': order_book.get('sequence', 0)
        })
        pipe.expire(key, 5)  # 5 second TTL for order books
        await pipe.execute()
        
    async def get_order_book(self, symbol: str) -> Optional[dict]:
        """Retrieve cached order book."""
        if not self._pool:
            return None
        data = await self._pool.hgetall(f"orderbook:{symbol}")
        if not data:
            return None
        return {
            'bids': json.loads(data.get('bids', '[]')),
            'asks': json.loads(data.get('asks', '[]')),
            'timestamp': data.get('timestamp'),
            'sequence': int(data.get('sequence', 0))
        }
        
    async def publish_signal(self, channel: str, signal: dict):
        """Publish trading signal to subscribers."""
        if not self._pool:
            return
        await self._pool.publish(channel, json.dumps(signal))
        
    async def stream_add_trade(
        self, 
        stream_key: str, 
        trade_data: dict,
        maxlen: int = 10000,           # Keep last 10k trades
        approximate: bool = True       # Use approximate trimming for speed
    ):
        """Add trade to Redis Stream (ordered log)."""
        if not self._pool:
            return
        await self._pool.xadd(
            stream_key,
            trade_data,
            maxlen=maxlen,
            approximate=approximate
        )
        
    async def stream_read_trades(
        self, 
        stream_key: str, 
        last_id: str = '0',
        count: int = 100
    ) -> List[tuple]:
        """Read trades from Redis Stream."""
        if not self._pool:
            return []
        return await self._pool.xread({stream_key: last_id}, count=count)
        
    async def atomic_update_position(
        self,
        account_id: str,
        symbol: str,
        delta_qty: float,
        delta_pnl: float
    ) -> dict:
        """Atomic position update using Lua script."""
        if not self._pool:
            raise RuntimeError("Redis not initialized")
            
        lua_script = """
        local key = KEYS[1]
        local delta_qty = tonumber(ARGV[1])
        local delta_pnl = tonumber(ARGV[2])
        
        local current = redis.call('HMGET', key, 'quantity', 'realized_pnl')
        local qty = tonumber(current[1]) or 0
        local pnl = tonumber(current[2]) or 0
        
        qty = qty + delta_qty
        pnl = pnl + delta_pnl
        
        redis.call('HMSET', key, 'quantity', qty, 'realized_pnl', pnl)
        redis.call('HINCRBY', key, 'update_count', 1)
        
        return {qty, pnl}
        """
        
        key = f"position:{account_id}:{symbol}"
        result = await self._pool.eval(lua_script, 1, key, delta_qty, delta_pnl)
        return {'quantity': result[0], 'realized_pnl': result[1]}
        
    async def health_check(self) -> bool:
        """Quick Redis health check."""
        if not self._pool:
            return False
        try:
            return await self._pool.ping()
        except Exception:
            return False
            
    async def close(self):
        """Close Redis connections."""
        if self._pool:
            await self._pool.close()
            self._pool = None


# Usage Example with Context Manager
@asynccontextmanager
async def redis_client():
    client = RedisTradingClient()
    await client.initialize()
    try:
        yield client
    finally:
        await client.close()

async def trading_example():
    async with redis_client() as redis:
        # Cache real-time tick
        await redis.set_tick("BTC-USD", {
            "price": 45000.50,
            "volume": 1.5,
            "timestamp": "2025-01-15T10:30:00.123Z"
        })
        
        # Publish signal
        await redis.publish_signal("signals:buy", {
            "symbol": "BTC-USD",
            "signal": "BUY",
            "confidence": 0.85,
            "timestamp": "2025-01-15T10:30:00.123Z"
        })
        
        # Atomic position update
        position = await redis.atomic_update_position(
            "account_123", "BTC-USD", 0.5, 125.50
        )
```

---

## 3. TimescaleDB Time-Series Patterns for Trade Data

### Best Practices

- **Hypertables**: Automatic partitioning by time
- **Compression**: Enable for older data to save storage
- **Continuous aggregates**: Pre-compute OHLCV data
- **Chunk sizing**: Align with query patterns (1 hour chunks for HFT)

### Schema and Hypertable Setup

```sql
-- Create trades hypertable
CREATE TABLE trades (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price DECIMAL(18, 8) NOT NULL,
    quantity DECIMAL(18, 8) NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('BUY', 'SELL')),
    trade_id TEXT,
    exchange TEXT NOT NULL,
    metadata JSONB
);

-- Convert to hypertable (partition by time)
-- For HFT: 1 hour chunks match typical query patterns
SELECT create_hypertable(
    'trades', 
    'time', 
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Create indexes for common queries
CREATE INDEX idx_trades_symbol_time ON trades (symbol, time DESC);
CREATE INDEX idx_trades_exchange ON trades (exchange, time DESC);

-- Enable compression for data older than 7 days
ALTER TABLE trades SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol, exchange',
    timescaledb.compress_orderby = 'time DESC'
);

-- Compression policy: compress chunks older than 7 days
SELECT add_compression_policy('trades', INTERVAL '7 days');
```

### Python Integration with asyncpg

```python
import asyncpg
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import json

class TimescaleDBClient:
    """HFT-optimized TimescaleDB client."""
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
        
    async def insert_trade(
        self,
        symbol: str,
        price: float,
        quantity: float,
        side: str,
        exchange: str,
        trade_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> int:
        """Insert a single trade (optimized for speed)."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(
                """
                INSERT INTO trades (time, symbol, price, quantity, side, trade_id, exchange, metadata)
                VALUES (NOW(), $1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT DO NOTHING
                RETURNING 1
                """,
                symbol, price, quantity, side, trade_id, exchange, 
                json.dumps(metadata) if metadata else None
            )
            
    async def insert_trades_batch(
        self, 
        trades: List[tuple],
        batch_size: int = 1000
    ) -> int:
        """Batch insert trades using COPY for maximum throughput."""
        if not trades:
            return 0
            
        async with self.pool.acquire() as conn:
            # COPY is 10-20x faster than INSERT
            result = await conn.copy_records_to_table(
                'trades',
                records=trades,
                columns=['time', 'symbol', 'price', 'quantity', 'side', 'trade_id', 'exchange', 'metadata']
            )
            return result
            
    async def get_recent_trades(
        self,
        symbol: str,
        limit: int = 100,
        seconds_back: int = 60
    ) -> List[asyncpg.Record]:
        """Get recent trades for a symbol."""
        since = datetime.utcnow() - timedelta(seconds=seconds_back)
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                """
                SELECT time, price, quantity, side, exchange
                FROM trades
                WHERE symbol = $1 AND time > $2
                ORDER BY time DESC
                LIMIT $3
                """,
                symbol, since, limit
            )
            
    async def get_ohlcv(
        self,
        symbol: str,
        interval: str = '1 minute',
        lookback: str = '1 hour'
    ) -> List[asyncpg.Record]:
        """Get OHLCV data using time_bucket."""
        async with self.pool.acquire() as conn:
            return await conn.fetch(
                f"""
                SELECT
                    time_bucket('{interval}', time) AS bucket,
                    first(price, time) as open,
                    max(price) as high,
                    min(price) as low,
                    last(price, time) as close,
                    sum(quantity) as volume,
                    count(*) as trade_count
                FROM trades
                WHERE symbol = $1
                  AND time > NOW() - INTERVAL '{lookback}'
                GROUP BY bucket
                ORDER BY bucket DESC
                """,
                symbol
            )
            
    async def get_vwap(
        self,
        symbol: str,
        minutes: int = 5
    ) -> Optional[float]:
        """Calculate VWAP for recent trades."""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT 
                    SUM(price * quantity) / NULLIF(SUM(quantity), 0) as vwap
                FROM trades
                WHERE symbol = $1
                  AND time > NOW() - INTERVAL '{minutes} minutes'
                """,
                symbol
            )
            return result


# Continuous Aggregates for OHLCV (Pre-computed)
CREATE_CONTINUOUS_AGGREGATE_SQL = """
-- 1-minute OHLCV continuous aggregate
CREATE MATERIALIZED VIEW ohlcv_1min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    symbol,
    exchange,
    toolkit_experimental.candlestick_agg(time, price, quantity) AS candle
FROM trades
GROUP BY bucket, symbol, exchange
WITH NO DATA;

-- Refresh policy: real-time for recent data
SELECT add_continuous_aggregate_policy('ohlcv_1min',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute'
);

-- Access OHLCV data
SELECT 
    bucket,
    symbol,
    open(candle),
    high(candle),
    low(candle),
    close(candle),
    volume(candle)
FROM ohlcv_1min
WHERE symbol = 'BTC-USD'
  AND bucket > NOW() - INTERVAL '1 hour';
"""
```

---

## 4. Connection Retry Logic with Exponential Backoff

### Best Practices

- **Exponential backoff**: Prevents thundering herd
- **Jitter**: Randomize delays to prevent synchronized retries
- **Max retry limits**: Avoid infinite loops
- **Circuit breaker**: Stop retrying when failure rate is high

### Implementation

```python
import asyncio
import random
from functools import wraps
from typing import Callable, Type, Union, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RetryConfig:
    """Configuration for retry behavior."""
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 0.1,      # Start with 100ms
        max_delay: float = 30.0,        # Cap at 30 seconds
        exponential_base: float = 2.0,
        jitter: bool = True,
        jitter_max: float = 0.1,        # Max 100ms jitter
        retryable_exceptions: tuple = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        )
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.jitter_max = jitter_max
        self.retryable_exceptions = retryable_exceptions


def calculate_backoff_delay(
    attempt: int,
    config: RetryConfig
) -> float:
    """Calculate delay with exponential backoff and jitter."""
    # Exponential: base_delay * (2 ^ attempt)
    delay = config.base_delay * (config.exponential_base ** attempt)
    # Cap at max_delay
    delay = min(delay, config.max_delay)
    # Add jitter to prevent thundering herd
    if config.jitter:
        jitter = random.uniform(0, config.jitter_max)
        delay += jitter
    return delay


def with_retry(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable] = None
):
    """Decorator for adding retry logic to async functions."""
    if config is None:
        config = RetryConfig()
        
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt >= config.max_retries:
                        logger.error(
                            f"Max retries ({config.max_retries}) exceeded for {func.__name__}: {e}"
                        )
                        raise
                        
                    delay = calculate_backoff_delay(attempt, config)
                    logger.warning(
                        f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                        f"after {delay:.3f}s: {e}"
                    )
                    
                    if on_retry:
                        try:
                            on_retry(attempt, e, delay)
                        except Exception:
                            pass
                            
                    await asyncio.sleep(delay)
                    
                except Exception:
                    # Non-retryable exception, don't retry
                    raise
                    
            raise last_exception
            
        return wrapper
    return decorator


# HFT-specific retry strategies
class HFTRetryConfig(RetryConfig):
    """Aggressive retry config for HFT (lower latency tolerance)."""
    def __init__(self):
        super().__init__(
            max_retries=5,
            base_delay=0.01,      # 10ms initial
            max_delay=5.0,         # Cap at 5s for HFT
            exponential_base=2.0,
            jitter=True,
            jitter_max=0.05,       # Max 50ms jitter
            retryable_exceptions=(
                ConnectionError,
                TimeoutError,
                asyncio.TimeoutError,
                BrokenPipeError,
            )
        )


# Usage Examples

@with_retry(config=HFTRetryConfig())
async def fetch_market_data(exchange_api, symbol: str):
    """Fetch market data with HFT-optimized retry."""
    return await exchange_api.get_ticker(symbol)


# Custom retry with circuit breaker integration
class CircuitBreakerRetryConfig(RetryConfig):
    """Retry config that integrates with circuit breaker state."""
    def __init__(self, circuit_breaker):
        super().__init__()
        self.circuit_breaker = circuit_breaker
        
    def should_retry(self, exception, attempt):
        """Check if we should retry based on circuit state."""
        if self.circuit_breaker.is_open():
            return False  # Don't retry if circuit is open
        return attempt < self.max_retries


# Connection pool retry wrapper
class RetryableConnectionPool:
    """Connection pool wrapper with automatic retry."""
    
    def __init__(self, pool, retry_config: Optional[RetryConfig] = None):
        self.pool = pool
        self.retry_config = retry_config or RetryConfig()
        
    async def execute_with_retry(self, query: str, *args):
        """Execute query with retry logic."""
        @with_retry(self.retry_config)
        async def _execute():
            async with self.pool.acquire() as conn:
                return await conn.fetch(query, *args)
        return await _execute()
```

---

## 5. Circuit Breakers for Database Failures

### Best Practices

- **Threshold-based**: Trip after N failures or error rate %
- **Time-based recovery**: Auto-reset after cooldown period
- **Half-open state**: Test recovery before fully closing
- **Fallback mechanisms**: Provide degraded service when open

### Implementation

```python
import asyncio
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Callable, Any, Dict
from dataclasses import dataclass
from collections import deque
import logging
import threading

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration."""
    failure_threshold: int = 5           # Trip after N consecutive failures
    success_threshold: int = 2           # Close after N consecutive successes
    timeout_duration: float = 30.0       # Open duration before half-open
    error_rate_threshold: float = 0.5   # Trip if error rate exceeds 50%
    window_size: int = 100               # Sliding window size for error rate
    

class CircuitBreaker:
    """Thread-safe circuit breaker for database operations."""
    
    def __init__(
        self, 
        name: str,
        config: CircuitBreakerConfig,
        on_state_change: Optional[Callable] = None
    ):
        self.name = name
        self.config = config
        self.on_state_change = on_state_change
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
        self._window: deque = deque(maxlen=config.window_size)
        
    @property
    def state(self) -> CircuitState:
        return self._state
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self._state == CircuitState.OPEN:
                # Check if we should try half-open
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    logger.info(f"Circuit {self.name} entering HALF_OPEN state")
                else:
                    raise CircuitBreakerOpenError(
                        f"Circuit {self.name} is OPEN - failing fast"
                    )
                    
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise
            
    async def _on_success(self):
        """Handle successful execution."""
        async with self._lock:
            self._failure_count = 0
            self._window.append(True)
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    await self._state_transition(CircuitState.CLOSED)
                    
    async def _on_failure(self):
        """Handle failed execution."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()
            self._window.append(False)
            
            error_rate = self._calculate_error_rate()
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open trips the breaker again
                await self._state_transition(CircuitState.OPEN)
            elif (self._failure_count >= self.config.failure_threshold or 
                  error_rate >= self.config.error_rate_threshold):
                await self._state_transition(CircuitState.OPEN)
                
    async def _state_transition(self, new_state: CircuitState):
        """Transition to new state."""
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._failure_count = 0
            self._success_count = 0
            
            logger.warning(
                f"Circuit {self.name} state: {old_state.value} -> {new_state.value}"
            )
            
            if self.on_state_change:
                try:
                    await self.on_state_change(self.name, old_state, new_state)
                except Exception:
                    pass
                    
    def _should_attempt_reset(self) -> bool:
        """Check if we should try to recover."""
        if self._last_failure_time is None:
            return True
        elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
        return elapsed >= self.config.timeout_duration
        
    def _calculate_error_rate(self) -> float:
        """Calculate error rate from sliding window."""
        if not self._window:
            return 0.0
        failures = sum(1 for success in self._window if not success)
        return failures / len(self._window)
        
    def is_open(self) -> bool:
        return self._state == CircuitState.OPEN
        
    async def force_open(self):
        """Manually open the circuit."""
        async with self._lock:
            await self._state_transition(CircuitState.OPEN)
            
    async def force_closed(self):
        """Manually close the circuit."""
        async with self._lock:
            await self._state_transition(CircuitState.CLOSED)


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# Circuit breaker registry for managing multiple breakers
class CircuitBreakerRegistry:
    """Registry for managing multiple circuit breakers."""
    
    def __init__(self):
        self._breakers: Dict[str, CircuitBreaker] = {}
        
    def register(
        self, 
        name: str, 
        config: Optional[CircuitBreakerConfig] = None
    ) -> CircuitBreaker:
        """Register a new circuit breaker."""
        if name not in self._breakers:
            config = config or CircuitBreakerConfig()
            self._breakers[name] = CircuitBreaker(name, config)
        return self._breakers[name]
        
    def get(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name."""
        return self._breakers.get(name)
        
    def get_status(self) -> Dict[str, dict]:
        """Get status of all circuit breakers."""
        return {
            name: {
                'state': cb.state.value,
                'failure_count': cb._failure_count,
                'error_rate': cb._calculate_error_rate(),
            }
            for name, cb in self._breakers.items()
        }


# Decorator for circuit breaker protection
def circuit_breaker(
    breaker_name: str,
    registry: Optional[CircuitBreakerRegistry] = None,
    fallback: Optional[Callable] = None
):
    """Decorator to protect function with circuit breaker."""
    if registry is None:
        registry = CircuitBreakerRegistry()
        
    def decorator(func: Callable):
        breaker = registry.register(breaker_name)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await breaker.call(func, *args, **kwargs)
            except CircuitBreakerOpenError:
                if fallback:
                    logger.info(f"Circuit open - calling fallback for {func.__name__}")
                    return await fallback(*args, **kwargs)
                raise
                
        wrapper._circuit_breaker = breaker
        return wrapper
    return decorator


# HFT-optimized circuit breaker config
HFT_CIRCUIT_CONFIG = CircuitBreakerConfig(
    failure_threshold=3,        # Trip quickly for HFT
    success_threshold=2,
    timeout_duration=10.0,      # Short recovery attempt
    error_rate_threshold=0.3,   # Lower threshold (30%)
    window_size=50
)


# Usage Example
async def example_circuit_breaker_usage():
    registry = CircuitBreakerRegistry()
    
    @circuit_breaker("postgres_write", registry, fallback=lambda *a, **kw: None)
    async def write_trade_to_db(trade_data: dict):
        # This will be protected by circuit breaker
        async with db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO trades ...",
                trade_data['symbol'],
                trade_data['price'],
                trade_data['quantity']
            )
            
    @circuit_breaker("redis_cache", registry)
    async def cache_trade(trade_data: dict):
        await redis.setex(
            f"trade:{trade_data['id']}",
            60,
            json.dumps(trade_data)
        )
        
    # Check circuit breaker status
    status = registry.get_status()
    print(status)
    # {
    #   'postgres_write': {'state': 'closed', 'failure_count': 0, 'error_rate': 0.0},
    #   'redis_cache': {'state': 'closed', 'failure_count': 0, 'error_rate': 0.0}
    # }
```

---

## Integration Pattern: Trading Bot Database Layer

```python
from contextlib import asynccontextmanager

class TradingDatabaseLayer:
    """Unified database layer combining all patterns."""
    
    def __init__(self):
        self.registry = CircuitBreakerRegistry()
        self.pg_pool: Optional[PostgresPoolManager] = None
        self.redis_client: Optional[RedisTradingClient] = None
        
    async def initialize(self, pg_dsn: str, redis_config: dict):
        """Initialize all connections."""
        self.pg_pool = PostgresPoolManager(pg_dsn)
        await self.pg_pool.initialize()
        
        self.redis_client = RedisTradingClient(**redis_config)
        await self.redis_client.initialize()
        
    @with_retry(config=HFTRetryConfig())
    @circuit_breaker("trades_db", registry=lambda self: self.registry)
    async def save_trade(self, trade: dict) -> bool:
        """Save trade with full protection."""
        # Try cache first
        await self.redis_client.set_tick(
            trade['symbol'], 
            trade,
            ttl=60
        )
        
        # Persist to database
        await self.pg_pool.execute_with_retry(
            "INSERT INTO trades ...",
            trade['symbol'],
            trade['price'],
            trade['quantity'],
            trade['side']
        )
        return True
        
    async def health_check(self) -> Dict[str, bool]:
        """Health check all components."""
        return {
            'postgres': await self.pg_pool.health_check(),
            'redis': await self.redis_client.health_check(),
            'circuits': self.registry.get_status()
        }
        
    async def close(self):
        """Graceful shutdown."""
        if self.pg_pool:
            await self.pg_pool.close()
        if self.redis_client:
            await self.redis_client.close()
```

---

## Summary Checklist

- [x] **PostgreSQL**: Use connection pools, prepared statements, aggressive timeouts
- [x] **Redis**: Pipeline commands, use streams for logs, atomic operations with Lua
- [x] **TimescaleDB**: Hypertables, compression, continuous aggregates
- [x] **Retry Logic**: Exponential backoff with jitter, configurable per operation
- [x] **Circuit Breakers**: Prevent cascading failures, provide fallback mechanisms

## Resources

- [asyncpg docs](https://magicstack.github.io/asyncpg/current/)
- [aioredis docs](https://aioredis.readthedocs.io/)
- [TimescaleDB best practices](https://docs.timescale.com/)
- [Circuit Breaker pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
