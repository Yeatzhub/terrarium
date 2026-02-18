"""
WebSocket Order Book Manager - Production-Ready Async Implementation
Advanced asyncio patterns with automatic reconnection, rate limiting, and backpressure handling.
"""

import asyncio
import json
import logging
import time
from asyncio import Queue, QueueFull
from collections import defaultdict, deque
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Set, Any, AsyncIterator
from functools import wraps
import aiohttp
import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatusCode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger('OrderBook')


# =============================================================================
# Exceptions
# =============================================================================

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


# =============================================================================
# Data Structures
# =============================================================================

class Side(Enum):
    """Order book side"""
    BID = auto()
    ASK = auto()

@dataclass(frozen=True, order=True)
class PriceLevel:
    """Represents a price level in the order book"""
    price: Decimal
    size: Decimal
    side: Side = field(compare=False)
    
    def __post_init__(self):
        object.__setattr__(self, 'price', Decimal(str(self.price)).quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP))
        object.__setattr__(self, 'size', Decimal(str(self.size)).quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP))

@dataclass
class OrderBookLevel:
    """Mutable price level for order book management"""
    price: Decimal
    size: Decimal
    last_update: float = field(default_factory=time.time)
    update_count: int = 0
    
    def update(self, new_size: Decimal):
        """Update level size and metadata"""
        self.size = new_size
        self.last_update = time.time()
        self.update_count += 1

@dataclass
class Trade:
    """Represents a trade/market tick"""
    price: Decimal
    size: Decimal
    side: Side
    timestamp: float
    trade_id: Optional[str] = None

@dataclass  
class OrderBookSnapshot:
    """Complete order book state"""
    symbol: str
    bids: List[PriceLevel]
    asks: List[PriceLevel]
    last_update_id: int
    timestamp: float


# =============================================================================
# Circuit Breaker Pattern
# =============================================================================

class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance
    States: CLOSED -> OPEN -> HALF_OPEN -> CLOSED
    """
    
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
    
    @property
    def state(self) -> 'CircuitBreaker.State':
        return self._state
    
    async def call(self, coro_func: Callable, *args, **kwargs) -> Any:
        """Execute coroutine with circuit breaker protection"""
        async with self._lock:
            await self._update_state()
            
            if self._state == self.State.OPEN:
                raise ConnectionError(f"Circuit breaker is OPEN (last failure: {self._last_failure_time})")
            
            if self._state == self.State.HALF_OPEN and self._success_count >= self.half_open_max_calls:
                raise ConnectionError("Circuit breaker HALF_OPEN limit reached")
        
        try:
            result = await coro_func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure()
            raise
    
    async def _update_state(self):
        """Update state based on time and failures"""
        if self._state == self.State.OPEN:
            if self._last_failure_time and (time.time() - self._last_failure_time) >= self.recovery_timeout:
                self._state = self.State.HALF_OPEN
                self._success_count = 0
                logger.info("Circuit breaker -> HALF_OPEN")
    
    async def record_success(self):
        """Record successful call"""
        async with self._lock:
            self._failure_count = 0
            
            if self._state == self.State.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.half_open_max_calls:
                    self._state = self.State.CLOSED
                    self._success_count = 0
                    logger.info("Circuit breaker -> CLOSED")
    
    async def record_failure(self):
        """Record failed call"""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            if self._failure_count >= self.failure_threshold:
                if self._state != self.State.OPEN:
                    logger.warning(f"Circuit breaker -> OPEN ({self._failure_count} failures)")
                self._state = self.State.OPEN


# =============================================================================
# Rate Limiter
# =============================================================================

class TokenBucketRateLimiter:
    """
    Token bucket rate limiter for WebSocket message throttling
    Supports both message rate and data volume limits
    """
    
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
        self._bytes_tokens = bytes_per_second if bytes_per_second else float('inf')
        self._bytes_last_update = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def acquire(self, message_size: int = 0) -> float:
        """
        Acquire permission to proceed. Returns wait time.
        Raises RateLimitError if backpressure is too high.
        """
        async with self._lock:
            now = time.monotonic()
            
            # Replenish message tokens
            elapsed = now - self._last_update
            self._tokens = min(
                self.burst_size,
                self._tokens + elapsed * self.messages_per_second
            )
            self._last_update = now
            
            # Replenish byte tokens
            if self.bytes_per_second:
                byte_elapsed = now - self._bytes_last_update
                self._bytes_tokens = min(
                    self.bytes_per_second,
                    self._bytes_tokens + byte_elapsed * self.bytes_per_second
                )
                self._bytes_last_update = now
            
            # Check if we can proceed
            if self._tokens >= 1 and self._bytes_tokens >= message_size:
                self._tokens -= 1
                self._bytes_tokens -= message_size
                return 0.0
            
            # Calculate wait time
            msg_wait = (1 - self._tokens) / self.messages_per_second if self._tokens < 1 else 0
            byte_wait = 0
            if self.bytes_per_second and message_size > 0:
                byte_wait = (message_size - self._bytes_tokens) / self.bytes_per_second
            
            wait_time = max(msg_wait, byte_wait)
            
            # Reject if wait is too long (backpressure)
            if wait_time > 5.0:
                raise BackpressureError(f"Rate limit backpressure: {wait_time:.2f}s wait required")
            
            return wait_time
    
    async def __aenter__(self):
        wait = await self.acquire()
        if wait > 0:
            await asyncio.sleep(wait)
        return self
    
    async def __aexit__(self, *args):
        pass


# =============================================================================
# Order Book Implementation
# =============================================================================

class AsyncOrderBook:
    """
    Thread-safe async order book with price-time priority
    Supports incremental updates and snapshot synchronization
    """
    
    def __init__(
        self,
        symbol: str,
        max_depth: int = 100,
        price_grouping: Optional[Decimal] = None
    ):
        self.symbol = symbol
        self.max_depth = max_depth
        self.price_grouping = price_grouping
        
        # Price -> OrderBookLevel
        self._bids: Dict[Decimal, OrderBookLevel] = {}
        self._asks: Dict[Decimal, OrderBookLevel] = {}
        
        # Sorted price levels (descending for bids, ascending for asks)
        self._bid_prices: List[Decimal] = []
        self._ask_prices: List[Decimal] = []
        
        # Statistics
        self._update_count = 0
        self._last_update_id = 0
        self._last_update_time = 0.0
        
        # Async synchronization
        self._lock = asyncio.RLock()
        self._update_event = asyncio.Event()
        self._subscribers: Set[asyncio.Queue] = set()
        
        # Metrics
        self._metrics = {
            'updates_per_sec': deque(maxlen=100),
            'max_spread': Decimal('0'),
            'min_spread': Decimal('inf'),
            'avg_spread': Decimal('0')
        }
    
    async def apply_snapshot(self, snapshot: OrderBookSnapshot):
        """Apply full order book snapshot"""
        async with self._lock:
            # Clear existing
            self._bids.clear()
            self._asks.clear()
            
            # Apply bids
            for level in snapshot.bids[:self.max_depth]:
                self._bids[level.price] = OrderBookLevel(
                    price=level.price,
                    size=level.size
                )
            
            # Apply asks
            for level in snapshot.asks[:self.max_depth]:
                self._asks[level.price] = OrderBookLevel(
                    price=level.price,
                    size=level.size
                )
            
            self._update_sorted_prices()
            self._last_update_id = snapshot.last_update_id
            self._last_update_time = snapshot.timestamp
            
            logger.info(f"[{self.symbol}] Snapshot applied: {len(self._bids)} bids, {len(self._asks)} asks")
        
        await self._notify_update()
    
    async def apply_delta(
        self,
        side: Side,
        price: Decimal,
        size: Decimal,
        update_id: int,
        is_snapshot: bool = False
    ):
        """Apply incremental update (size=0 means delete)"""
        async with self._lock:
            if update_id <= self._last_update_id and not is_snapshot:
                logger.debug(f"Skipping outdated update {update_id} (current: {self._last_update_id})")
                return
            
            target_dict = self._bids if side == Side.BID else self._asks
            target_prices = self._bid_prices if side == Side.BID else self._ask_prices
            
            if size <= 0:
                # Remove level
                if price in target_dict:
                    del target_dict[price]
            else:
                # Update or insert
                if price in target_dict:
                    target_dict[price].update(size)
                else:
                    target_dict[price] = OrderBookLevel(price=price, size=size)
            
            # Maintain sorted order
            self._update_sorted_prices()
            
            # Trim to max depth
            if side == Side.BID:
                for p in self._bid_prices[self.max_depth:]:
                    self._bids.pop(p, None)
                self._bid_prices = self._bid_prices[:self.max_depth]
            else:
                for p in self._ask_prices[self.max_depth:]:
                    self._asks.pop(p, None)
                self._ask_prices = self._ask_prices[:self.max_depth]
            
            self._last_update_id = update_id
            self._last_update_time = time.time()
            self._update_count += 1
            
            # Update metrics
            self._update_metrics()
        
        await self._notify_update()
    
    def _update_sorted_prices(self):
        """Maintain sorted price lists"""
        self._bid_prices = sorted(self._bids.keys(), reverse=True)
        self._ask_prices = sorted(self._asks.keys())
    
    def _update_metrics(self):
        """Update spread metrics"""
        if self._bid_prices and self._ask_prices:
            spread = self._ask_prices[0] - self._bid_prices[0]
            self._metrics['max_spread'] = max(self._metrics['max_spread'], spread)
            self._metrics['min_spread'] = min(self._metrics['min_spread'], spread)
            # Running average
            alpha = Decimal('0.1')
            self._metrics['avg_spread'] = (alpha * spread + (Decimal('1') - alpha) * self._metrics['avg_spread'])
    
    async def _notify_update(self):
        """Notify all subscribers of update"""
        self._update_event.set()
        self._update_event.clear()
        
        # Queue updates for async subscribers
        snapshot = await self.get_snapshot()
        dead_queues = set()
        
        for queue in self._subscribers:
            try:
                queue.put_nowait(snapshot)
            except QueueFull:
                dead_queues.add(queue)
        
        # Remove dead subscribers
        self._subscribers -= dead_queues
    
    async def get_snapshot(self) -> OrderBookSnapshot:
        """Get current order book state"""
        async with self._lock:
            bids = [
                PriceLevel(price=p, size=self._bids[p].size, side=Side.BID)
                for p in self._bid_prices
            ]
            asks = [
                PriceLevel(price=p, size=self._asks[p].size, side=Side.ASK)
                for p in self._ask_prices
            ]
            
            return OrderBookSnapshot(
                symbol=self.symbol,
                bids=bids,
                asks=asks,
                last_update_id=self._last_update_id,
                timestamp=time.time()
            )
    
    async def get_bid_ask(self) -> Optional[tuple]:
        """Get best bid and ask"""
        async with self._lock:
            if not self._bid_prices or not self._ask_prices:
                return None
            
            best_bid = self._bids[self._bid_prices[0]]
            best_ask = self._asks[self._ask_prices[0]]
            
            return (
                PriceLevel(best_bid.price, best_bid.size, Side.BID),
                PriceLevel(best_ask.price, best_ask.size, Side.ASK)
            )
    
    async def get_spread(self) -> Optional[Decimal]:
        """Get current spread"""
        bid_ask = await self.get_bid_ask()
        if bid_ask:
            return bid_ask[1].price - bid_ask[0].price
        return None
    
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
    
    async def wait_for_update(self, timeout: Optional[float] = None) -> bool:
        """Wait for next order book update"""
        try:
            await asyncio.wait_for(self._update_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get order book metrics"""
        return {
            'symbol': self.symbol,
            'bid_levels': len(self._bids),
            'ask_levels': len(self._asks),
            'update_count': self._update_count,
            'spread_stats': {
                'current': str(self.get_spread()) if self.get_spread() else None,
                'min': str(self._metrics['min_spread']),
                'max': str(self._metrics['max_spread']),
                'avg': str(self._metrics['avg_spread'])
            }
        }


# =============================================================================
# WebSocket Order Book Manager
# =============================================================================

class WebSocketOrderBookManager:
    """
    Production-ready WebSocket order book manager
    Features:
    - Automatic reconnection with exponential backoff
    - Circuit breaker for fault tolerance
    - Rate limiting and backpressure handling
    - Connection health monitoring
    """
    
    def __init__(
        self,
        uri: str,
        symbol: str,
        reconnect_config: Optional[Dict] = None,
        rate_limit_config: Optional[Dict] = None,
        circuit_breaker_config: Optional[Dict] = None,
        on_message: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_connect: Optional[Callable] = None,
        on_disconnect: Optional[Callable] = None
    ):
        self.uri = uri
        self.symbol = symbol
        
        # Callbacks
        self.on_message = on_message
        self.on_error = on_error
        self.on_connect = on_connect
        self.on_disconnect = on_disconnect
        
        # Configuration
        self._reconnect_config = reconnect_config or {
            'initial_delay': 1.0,
            'max_delay': 60.0,
            'backoff_factor': 2.0,
            'max_attempts': None,  # Unlimited
            'jitter': 0.1
        }
        
        self._rate_limit_config = rate_limit_config or {
            'messages_per_second': 100,
            'burst_size': 10,
            'backpressure_threshold': 1000
        }
        
        self._circuit_breaker_config = circuit_breaker_config or {
            'failure_threshold': 5,
            'recovery_timeout': 30.0,
            'half_open_max_calls': 3
        }
        
        # Components
        self._rate_limiter = TokenBucketRateLimiter(**self._rate_limit_config)
        self._circuit_breaker = CircuitBreaker(**self._circuit_breaker_config)
        self._order_book = AsyncOrderBook(symbol)
        
        # Connection state
        self._ws: Optional[websockets.WebSocketClientProtocol] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._should_run = False
        self._reconnect_attempts = 0
        self._current_delay = self._reconnect_config['initial_delay']
        
        # Tasks
        self._main_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None
        self._message_handler_task: Optional[asyncio.Task] = None
        
        # Message queue for ordered processing
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
        
        # Stats
        self._stats = {
            'messages_received': 0,
            'messages_processed': 0,
            'bytes_received': 0,
            'reconnects': 0,
            'errors': 0,
            'last_message_time': None
        }
    
    @property
    def is_connected(self) -> bool:
        return self._connected and self._ws is not None
    
    @property
    def circuit_state(self) -> CircuitBreaker.State:
        return self._circuit_breaker.state
    
    async def start(self):
        """Start the WebSocket manager"""
        if self._should_run:
            logger.warning("WebSocket manager already running")
            return
        
        self._should_run = True
        self._session = aiohttp.ClientSession()
        
        self._main_task = asyncio.create_task(self._connection_loop())
        self._message_handler_task = asyncio.create_task(self._message_processor())
        
        logger.info(f"[WebSocket-{self.symbol}] Manager started")
    
    async def stop(self):
        """Stop the WebSocket manager"""
        logger.info(f"[WebSocket-{self.symbol}] Stopping...")
        self._should_run = False
        
        # Cancel tasks
        for task in [self._main_task, self._ping_task, self._message_handler_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        # Close connection
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        if self._session:
            await self._session.close()
            self._session = None
        
        self._connected = False
        logger.info(f"[WebSocket-{self.symbol}] Stopped")
    
    async def _connection_loop(self):
        """Main connection loop with reconnection logic"""
        while self._should_run:
            try:
                await self._circuit_breaker.call(self._connect_and_run)
                
                # Reset reconnection state on successful completion
                self._reconnect_attempts = 0
                self._current_delay = self._reconnect_config['initial_delay']
                
            except ConnectionError as e:
                logger.error(f"[WebSocket-{self.symbol}] Circuit breaker open: {e}")
                await asyncio.sleep(self._reconnect_config['recovery_timeout'])
            
            except Exception as e:
                logger.error(f"[WebSocket-{self.symbol}] Connection error: {e}")
                self._stats['errors'] += 1
                
                if self.on_error:
                    try:
                        await self.on_error(e)
                    except Exception as cb_err:
                        logger.error(f"Error in error callback: {cb_err}")
            
            if not self._should_run:
                break
            
            # Reconnection logic
            self._reconnect_attempts += 1
            self._stats['reconnects'] += 1
            
            max_attempts = self._reconnect_config['max_attempts']
            if max_attempts and self._reconnect_attempts >= max_attempts:
                logger.error(f"[WebSocket-{self.symbol}] Max reconnection attempts reached")
                raise ConnectionError(f"Failed to connect after {max_attempts} attempts")
            
            # Calculate delay with jitter
            jitter = self._reconnect_config['jitter'] * (2 * (0.5 - asyncio.get_event_loop().time() % 1))
            delay = self._current_delay + jitter
            
            logger.info(f"[WebSocket-{self.symbol}] Reconnecting in {delay:.1f}s (attempt {self._reconnect_attempts})")
            await asyncio.sleep(delay)
            
            # Exponential backoff
            self._current_delay = min(
                self._current_delay * self._reconnect_config['backoff_factor'],
                self._reconnect_config['max_delay']
            )
    
    async def _connect_and_run(self):
        """Establish WebSocket connection and run main loop"""
        logger.info(f"[WebSocket-{self.symbol}] Connecting to {self.uri}")
        
        try:
            self._ws = await websockets.connect(
                self.uri,
                ping_interval=None,  # We handle ping ourselves
                close_timeout=10,
                compression=None,
                ssl=self._session._connector._ssl if self._session else None
            )
            
            self._connected = True
            logger.info(f"[WebSocket-{self.symbol}] Connected")
            
            if self.on_connect:
                try:
                    await self.on_connect(self._ws)
                except Exception as e:
                    logger.error(f"Connect callback error: {e}")
            
            # Start ping task
            self._ping_task = asyncio.create_task(self._ping_loop())
            
            # Main receive loop
            await self._receive_loop()
            
        except websockets.exceptions.InvalidStatusCode as e:
            raise ConnectionError(f"Invalid status code: {e.status_code}")
        except Exception as e:
            raise ConnectionError(f"Connection failed: {e}")
        finally:
            self._connected = False
            if self._ping_task:
                self._ping_task.cancel()
                try:
                    await self._ping_task
                except asyncio.CancelledError:
                    pass
                self._ping_task = None
            
            if self.on_disconnect:
                try:
                    await self.on_disconnect()
                except Exception as e:
                    logger.error(f"Disconnect callback error: {e}")
    
    async def _receive_loop(self):
        """Receive messages from WebSocket"""
        while self._should_run and self._ws:
            try:
                msg = await self._ws.recv()
                
                self._stats['messages_received'] += 1
                self._stats['bytes_received'] += len(msg) if isinstance(msg, bytes) else len(msg.encode())
                self._stats['last_message_time'] = time.time()
                
                # Rate limit check
                try:
                    async with self._rate_limiter:
                        # Queue for ordered processing
                        await self._message_queue.put(msg)
                except BackpressureError as e:
                    logger.warning(f"[WebSocket-{self.symbol}] Backpressure: {e}")
                    # Drop oldest messages
                    while self._message_queue.qsize() > self._rate_limit_config['backpressure_threshold']:
                        try:
                            self._message_queue.get_nowait()
                        except asyncio.QueueEmpty:
                            break
                    await self._message_queue.put(msg)
                
            except ConnectionClosed as e:
                logger.warning(f"[WebSocket-{self.symbol}] Connection closed: {e}")
                break
            except Exception as e:
                logger.error(f"[WebSocket-{self.symbol}] Receive error: {e}")
                self._stats['errors'] += 1
    
    async def _message_processor(self):
        """Process queued messages"""
        while self._should_run:
            try:
                msg = await self._message_queue.get()
                
                # Parse and process
                await self._process_message(msg)
                
                self._stats['messages_processed'] += 1
                
                # Callback
                if self.on_message:
                    try:
                        await self.on_message(msg)
                    except Exception as e:
                        logger.error(f"Message callback error: {e}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[WebSocket-{self.symbol}] Message processing error: {e}")
                self._stats['errors'] += 1
    
    async def _process_message(self, msg):
        """Override this method for specific exchange formats"""
        # Default: parse JSON and update order book if valid
        try:
            if isinstance(msg, str):
                data = json.loads(msg)
                # Subclasses should override for specific handling
                logger.debug(f"Received message: {data}")
        except json.JSONDecodeError:
            pass
    
    async def _ping_loop(self):
        """Send periodic ping frames"""
        while self._should_run and self._ws:
            try:
                await asyncio.sleep(30)  # Ping every 30 seconds
                if self._ws and self._connected:
                    await self._ws.ping()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[WebSocket-{self.symbol}] Ping error: {e}")
    
    async def send(self, message: str):
        """Send message to WebSocket"""
        if not self._ws or not self._connected:
            raise ConnectionError("Not connected")
        
        async with self._rate_limiter:
            await self._ws.send(message)
    
    def get_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            **self._stats,
            'circuit_state': self.circuit_state.name,
            'queue_size': self._message_queue.qsize(),
            'reconnect_attempts': self._reconnect_attempts,
            'connected': self._connected
        }
    
    @property
    def order_book(self) -> AsyncOrderBook:
        """Access the order book"""
        return self._order_book


# =============================================================================
# Exchange-Specific Implementations
# =============================================================================

class BinanceOrderBookManager(WebSocketOrderBookManager):
    """Binance-specific order book implementation"""
    
    def __init__(
        self,
        symbol: str,
        stream_type: str = 'depth@100ms',
        testnet: bool = False,
        **kwargs
    ):
        self.stream_type = stream_type
        self.testnet = testnet
        
        # Get WebSocket URL
        base_url = (
            'wss://testnet.binance.vision/ws' if testnet
            else 'wss://stream.binance.com:9443/ws'
        )
        uri = f"{base_url}/{symbol.lower()}@{stream_type}"
        
        super().__init__(uri=uri, symbol=symbol, **kwargs)
        
        self._last_update_id = None
        self._buffer = []
        self._snapshot_received = False
    
    async def _connect_and_run(self):
        """Override to fetch snapshot before streaming"""
        # Fetch snapshot via REST API
        await self._fetch_snapshot()
        await super()._connect_and_run()
    
    async def _fetch_snapshot(self):
        """Fetch order book snapshot from REST API"""
        if not self._session:
            self._session = aiohttp.ClientSession()
        
        base_url = (
            'https://testnet.binance.vision/api' if self.testnet
            else 'https://api.binance.com/api/v3'
        )
        url = f"{base_url}/depth?symbol={self.symbol.upper()}&limit=100"
        
        logger.info(f"[Binance-{self.symbol}] Fetching snapshot...")
        
        async with self._session.get(url) as resp:
            if resp.status != 200:
                raise ConnectionError(f"Failed to fetch snapshot: {resp.status}")
            
            data = await resp.json()
            
            snapshot = OrderBookSnapshot(
                symbol=self.symbol,
                bids=[
                    PriceLevel(price=Decimal(p[0]), size=Decimal(p[1]), side=Side.BID)
                    for p in data['bids']
                ],
                asks=[
                    PriceLevel(price=Decimal(p[0]), size=Decimal(p[1]), side=Side.ASK)
                    for p in data['asks']
                ],
                last_update_id=data['lastUpdateId'],
                timestamp=time.time()
            )
            
            self._last_update_id = data['lastUpdateId']
            await self._order_book.apply_snapshot(snapshot)
            self._snapshot_received = True
            
            logger.info(f"[Binance-{self.symbol}] Snapshot received (lastUpdateId={self._last_update_id})")
    
    async def _process_message(self, msg):
        """Process Binance depth update"""
        try:
            data = json.loads(msg) if isinstance(msg, str) else msg
            
            if 'e' in data:
                event_type = data['e']
                
                if event_type == 'depthUpdate':
                    # Process bid updates
                    for bid in data.get('b', []):
                        await self._order_book.apply_delta(
                            side=Side.BID,
                            price=Decimal(bid[0]),
                            size=Decimal(bid[1]),
                            update_id=data['u']
                        )
                    
                    # Process ask updates
                    for ask in data.get('a', []):
                        await self._order_book.apply_delta(
                            side=Side.ASK,
                            price=Decimal(ask[0]),
                            size=Decimal(ask[1]),
                            update_id=data['u']
                        )
                
                elif event_type == 'trade':
                    trade = Trade(
                        price=Decimal(data['p']),
                        size=Decimal(data['q']),
                        side=Side.BUY if data['m'] else Side.SELL,
                        timestamp=data['T'] / 1000,
                        trade_id=str(data['t'])
                    )
                    logger.debug(f"Trade: {trade}")
            
        except Exception as e:
            logger.error(f"Error processing Binance message: {e}")


# =============================================================================
# Helper Decorators
# =============================================================================

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
                except exceptions as e:
                    if attempt == max_attempts:
                        raise
                    
                    logger.warning(f"Attempt {attempt} failed: {e}, retrying in {current_delay}s")
                    await asyncio.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
            
        return wrapper
    return decorator


async def semaphore_gather(
    coros,
    semaphore: asyncio.Semaphore,
    return_exceptions: bool = True
):
    """Gather coroutines with semaphore-based concurrency limit"""
    async def sem_coro(coro):
        async with semaphore:
            return await coro
    
    return await asyncio.gather(
        *(sem_coro(c) for c in coros),
        return_exceptions=return_exceptions
    )


# =============================================================================
# Main Execution
# =============================================================================

async def main():
    """Example usage"""
    
    # Configure logging
    logging.getLogger('OrderBook').setLevel(logging.DEBUG)
    
    # Create manager
    manager = BinanceOrderBookManager(
        symbol='BTCUSDT',
        stream_type='depth@100ms',
        testnet=True,
        reconnect_config={
            'initial_delay': 1.0,
            'max_delay': 30.0,
            'backoff_factor': 1.5,
            'max_attempts': 10
        },
        rate_limit_config={
            'messages_per_second': 1000,
            'burst_size': 100
        },
        circuit_breaker_config={
            'failure_threshold': 5,
            'recovery_timeout': 30.0
        },
        on_message=lambda msg: print(f"Message: {msg[:100]}..."),
        on_error=lambda e: print(f"Error: {e}"),
        on_connect=lambda ws: print("Connected!"),
        on_disconnect=lambda: print("Disconnected!")
    )
    
    try:
        # Start manager
        await manager.start()
        
        # Monitor order book
        for _ in range(60):
            await asyncio.sleep(1)
            
            # Print order book summary
            snapshot = await manager.order_book.get_snapshot()
            bid_ask = await manager.order_book.get_bid_ask()
            spread = await manager.order_book.get_spread()
            
            if bid_ask:
                best_bid, best_ask = bid_ask
                print(f"\r[{manager.symbol}] Bid: {best_bid.price} @ {best_bid.size} | "
                      f"Ask: {best_ask.price} @ {best_ask.size} | "
                      f"Spread: {spread}", end='', flush=True)
        
        print("\n\nStats:", manager.get_stats())
        
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        await manager.stop()


if __name__ == '__main__':
    asyncio.run(main())
