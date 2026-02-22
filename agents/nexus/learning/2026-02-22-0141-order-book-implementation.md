# 📱 Real-Time Order Book Implementation

**Focus:** WebSocket Updates, Sorted Data Structure, Compose Rendering
**Pattern:** Efficient Incremental Updates with RecyclerView-style optimization

---

## 1. Order Book Data Structure

```kotlin
/**
 * Core principle: O(log n) insert/update/delete for price levels
 * Use TreeMap for sorted access (or SortedArray for memory efficiency)
 */
data class PriceLevel(
    val price: BigDecimal,
    val size: BigDecimal,
    val total: BigDecimal = size, // Cumulative for depth visualization
    val timestamp: Long = System.currentTimeMillis()
)

data class OrderBook(
    val symbol: String,
    val bids: List<PriceLevel>, // Sorted descending (highest bid first)
    val asks: List<PriceLevel>, // Sorted ascending (lowest ask first)
    val lastUpdateTime: Long,
    val sequence: Long
) {
    val spread: BigDecimal
        get() = asks.firstOrNull()?.price?.minus(bids.firstOrNull()?.price ?: BigDecimal.ZERO)
            ?: BigDecimal.ZERO
    
    val spreadPercent: Double
        get() = if (bids.isNotEmpty() && asks.isNotEmpty()) {
            val midPrice = (bids.first().price + asks.first().price) / 2.toBigDecimal()
            (spread / midPrice).toDouble() * 100
        } else 0.0
    
    val midPrice: BigDecimal?
        get() = if (bids.isNotEmpty() && asks.isNotEmpty()) {
            (bids.first().price + asks.first().price) / 2.toBigDecimal()
        } else null
}
```

---

## 2. Efficient Order Book Manager

```kotlin
@Singleton
class OrderBookManager @Inject constructor(
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher
) {
    // TreeMap for O(log n) operations + sorted iteration
    private val bids = ConcurrentSkipListMap<BigDecimal, PriceLevel>(reverseOrder())
    private val asks = ConcurrentSkipListMap<BigDecimal, PriceLevel>()
    
    @Volatile
    private var lastSequence = 0L
    
    @Volatile
    private var lastUpdateTime = 0L
    
    private val _orderBook = MutableStateFlow<OrderBook?>(null)
    val orderBook: StateFlow<OrderBook?> = _orderBook.asStateFlow()
    
    /**
     * Process snapshot (replaces entire book)
     */
    fun processSnapshot(snapshot: OrderBookSnapshot) {
        synchronized(this) {
            bids.clear()
            asks.clear()
            
            snapshot.bids.forEach { level ->
                bids[level.price] = PriceLevel(
                    price = level.price,
                    size = level.size,
                    total = level.size
                )
            }
            
            snapshot.asks.forEach { level ->
                asks[level.price] = PriceLevel(
                    price = level.price,
                    size = level.size,
                    total = level.size
                )
            }
            
            lastSequence = snapshot.sequence
            lastUpdateTime = System.currentTimeMillis()
            
            recalculateTotals()
            emitOrderBook(snapshot.symbol)
        }
    }
    
    /**
     * Process delta update (incremental)
     */
    fun processDelta(delta: OrderBookDelta) {
        synchronized(this) {
            // Skip stale updates
            if (delta.sequence <= lastSequence) return
            
            delta.bids?.forEach { update ->
                if (update.size > BigDecimal.ZERO) {
                    bids[update.price] = PriceLevel(
                        price = update.price,
                        size = update.size
                    )
                } else {
                    bids.remove(update.price)
                }
            }
            
            delta.asks?.forEach { update ->
                if (update.size > BigDecimal.ZERO) {
                    asks[update.price] = PriceLevel(
                        price = update.price,
                        size = update.size
                    )
                } else {
                    asks.remove(update.price)
                }
            }
            
            lastSequence = delta.sequence
            lastUpdateTime = System.currentTimeMillis()
            
            recalculateTotals()
            emitOrderBook(delta.symbol)
        }
    }
    
    /**
     * Recalculate cumulative totals for depth chart
     */
    private fun recalculateTotals() {
        var bidTotal = BigDecimal.ZERO
        bids.values.forEach { level ->
            bidTotal += level.size
            bids[level.price] = level.copy(total = bidTotal)
        }
        
        var askTotal = BigDecimal.ZERO
        asks.values.forEach { level ->
            askTotal += level.size
            asks[level.price] = level.copy(total = askTotal)
        }
    }
    
    private fun emitOrderBook(symbol: String) {
        _orderBook.value = OrderBook(
            symbol = symbol,
            bids = bids.values.take(MAX_LEVELS),
            asks = asks.values.take(MAX_LEVELS),
            lastUpdateTime = lastUpdateTime,
            sequence = lastSequence
        )
    }
    
    fun clear() {
        synchronized(this) {
            bids.clear()
            asks.clear()
            _orderBook.value = null
        }
    }
    
    companion object {
        const val MAX_LEVELS = 50
    }
}

// WebSocket message types
@Serializable
data class OrderBookSnapshot(
    val symbol: String,
    val sequence: Long,
    val bids: List<PriceLevelData>,
    val asks: List<PriceLevelData>
)

@Serializable
data class OrderBookDelta(
    val symbol: String,
    val sequence: Long,
    val bids: List<PriceLevelData>?,
    val asks: List<PriceLevelData>?
)

@Serializable
data class PriceLevelData(
    val price: BigDecimal,
    val size: BigDecimal
)
```

---

## 3. WebSocket Integration

```kotlin
@Singleton
class OrderBookWebSocket @Inject constructor(
    private val okHttpClient: OkHttpClient,
    private val json: Json,
    private val orderBookManager: OrderBookManager,
    @ApplicationScope private val scope: CoroutineScope
) {
    private var webSocket: WebSocket? = null
    private val _connectionState = MutableStateFlow<ConnectionState>(ConnectionState.Disconnected)
    val connectionState: StateFlow<ConnectionState> = _connectionState.asStateFlow()
    
    fun subscribe(symbol: String) {
        if (webSocket != null) {
            unsubscribe(symbol)
        }
        
        val request = Request.Builder()
            .url("wss://stream.exchange.com/ws/book")
            .build()
        
        webSocket = okHttpClient.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                _connectionState.value = ConnectionState.Connected
                webSocket.send(json.encodeToString(
                    SubscribeMessage(listOf("$symbol@depth"))
                ))
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                scope.launch {
                    handleWebsocketMessage(text, symbol)
                }
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                _connectionState.value = ConnectionState.Error(t.message ?: "Unknown error")
                // Auto-reconnect with backoff
                scope.launch {
                    delay(RECONNECT_DELAY_MS)
                    subscribe(symbol)
                }
            }
            
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                webSocket.close(1000, null)
                _connectionState.value = ConnectionState.Disconnected
            }
        })
    }
    
    private fun handleWebsocketMessage(text: String, symbol: String) {
        when (val message = json.parseToJsonElement(text)) {
            is JsonObject -> {
                when {
                    message.containsKey("bids") && message.containsKey("asks") -> {
                        // Snapshot
                        val snapshot = json.decodeFromString<OrderBookSnapshot>(text)
                        orderBookManager.processSnapshot(snapshot)
                    }
                    message.containsKey("b") || message.containsKey("a") -> {
                        // Delta update
                        val delta = parseDelta(text, symbol)
                        orderBookManager.processDelta(delta)
                    }
                }
            }
        }
    }
    
    private fun parseDelta(text: String, symbol: String): OrderBookDelta {
        val obj = json.parseToJsonElement(text) as JsonObject
        return OrderBookDelta(
            symbol = symbol,
            sequence = obj["s"]?.jsonPrimitive?.long ?: 0,
            bids = obj["b"]?.jsonArray?.map {
                val arr = it.jsonArray
                PriceLevelData(
                    BigDecimal(arr[0].jsonPrimitive.content),
                    BigDecimal(arr[1].jsonPrimitive.content)
                )
            },
            asks = obj["a"]?.jsonArray?.map {
                val arr = it.jsonArray
                PriceLevelData(
                    BigDecimal(arr[0].jsonPrimitive.content),
                    BigDecimal(arr[1].jsonPrimitive.content)
                )
            }
        )
    }
    
    fun unsubscribe(symbol: String) {
        webSocket?.send(json.encodeToString(
            UnsubscribeMessage(listOf("$symbol@depth"))
        ))
    }
    
    fun disconnect() {
        webSocket?.close(1000, "User disconnected")
        webSocket = null
    }
    
    companion object {
        const val RECONNECT_DELAY_MS = 5000L
    }
}

sealed class ConnectionState {
    object Disconnected : ConnectionState()
    object Connected : ConnectionState()
    data class Error(val message: String) : ConnectionState()
}
```

---

## 4. Compose Order Book UI

```kotlin
@Composable
fun OrderBookScreen(
    symbol: String,
    viewModel: OrderBookViewModel = hiltViewModel()
) {
    val orderBook by viewModel.orderBook.collectAsStateWithLifecycle()
    val connectionState by viewModel.connectionState.collectAsStateWithLifecycle()
    
    Column(modifier = Modifier.fillMaxSize()) {
        // Header with spread
        OrderBookHeader(
            symbol = symbol,
            orderBook = orderBook,
            connectionState = connectionState
        )
        
        // Order book table
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .padding(horizontal = 8.dp)
        ) {
            orderBook?.let { book ->
                OrderBookTable(
                    bids = book.bids,
                    asks = book.asks
                )
            } ?: Box(
                modifier = Modifier.fillMaxSize(),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator()
            }
        }
    }
}

@Composable
private fun OrderBookHeader(
    symbol: String,
    orderBook: OrderBook?,
    connectionState: ConnectionState
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(8.dp),
        shape = RoundedCornerShape(12.dp)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "Order Book",
                style = MaterialTheme.typography.titleMedium
            )
            Spacer(modifier = Modifier.width(8.dp))
            Text(
                text = symbol,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
            Spacer(modifier = Modifier.weight(1f))
            
            // Spread indicator
            orderBook?.let { book ->
                Column(horizontalAlignment = Alignment.End) {
                    Text(
                        text = "Spread",
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Text(
                        text = "${book.spreadPercent.format(4)}%",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            }
            
            // Connection indicator
            ConnectionIndicator(connectionState)
        }
    }
}

@Composable
private fun OrderBookTable(
    bids: List<PriceLevel>,
    asks: List<PriceLevel>
) {
    // Calculate max total for depth bar sizing
    val maxTotal = remember(bids, asks) {
        maxOf(
            bids.lastOrNull()?.total ?: BigDecimal.ZERO,
            asks.lastOrNull()?.total ?: BigDecimal.ZERO
        )
    }
    
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(4.dp)
    ) {
        // Bids column (green, right-aligned price)
        OrderBookColumn(
            modifier = Modifier.weight(1f),
            levels = bids,
            isBid = true,
            maxTotal = maxTotal
        )
        
        // Asks column (red, left-aligned price)
        OrderBookColumn(
            modifier = Modifier.weight(1f),
            levels = asks,
            isBid = false,
            maxTotal = maxTotal
        )
    }
}

@Composable
private fun OrderBookColumn(
    levels: List<PriceLevel>,
    isBid: Boolean,
    maxTotal: BigDecimal,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier,
        verticalArrangement = Arrangement.spacedBy(2.dp)
    ) {
        // Header
        item {
            OrderBookHeaderRow(isBid)
        }
        
        // Price levels
        items(
            items = levels,
            key = { it.price }
        ) { level ->
            PriceLevelRow(
                level = level,
                isBid = isBid,
                maxTotal = maxTotal
            )
        }
    }
}

@Composable
private fun OrderBookHeaderRow(isBid: Boolean) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = if (isBid) Arrangement.Start else Arrangement.End
    ) {
        if (isBid) {
            Text(
                text = "Price",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.weight(1f)
            )
            Text(
                text = "Size",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.weight(1f),
                textAlign = TextAlign.End
            )
        } else {
            Text(
                text = "Size",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.weight(1f)
            )
            Text(
                text = "Price",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
                modifier = Modifier.weight(1f),
                textAlign = TextAlign.End
            )
        }
    }
}

@Composable
private fun PriceLevelRow(
    level: PriceLevel,
    isBid: Boolean,
    maxTotal: BigDecimal,
    animationSpec: FiniteAnimationSpec<Float> = tween(100)
) {
    val backgroundColor = if (isBid) {
        Color(0xFF10B981) // Green for bids
    } else {
        Color(0xFFEF4444) // Red for asks
    }
    
    // Animated depth percentage
    val depthPercent by animateFloatAsState(
        targetValue = if (maxTotal > BigDecimal.ZERO) {
            (level.total.toFloat() / maxTotal.toFloat()).coerceIn(0f, 1f)
        } else 0f,
        animationSpec = animationSpec,
        label = "depth"
    )
    
    // Highlight for recent updates
    var highlightAlpha by remember { mutableFloatStateOf(0f) }
    LaunchedEffect(level.timestamp) {
        highlightAlpha = 0.3f
        delay(300)
        highlightAlpha = 0f
    }
    
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(24.dp)
            .clip(RoundedCornerShape(4.dp))
    ) {
        // Depth bar background
        Box(
            modifier = Modifier
                .fillMaxSize()
                .then(
                    if (isBid) {
                        Modifier.padding(start = ((1 - depthPercent) * 100).dp)
                    } else {
                        Modifier.padding(end = ((1 - depthPercent) * 100).dp)
                    }
                )
                .background(backgroundColor.copy(alpha = 0.2f))
        )
        
        // Highlight overlay for updates
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(backgroundColor.copy(alpha = highlightAlpha))
        )
        
        // Price and size text
        Row(
            modifier = Modifier
                .fillMaxSize()
                .padding(horizontal = 8.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = if (isBid) Arrangement.SpaceBetween else Arrangement.SpaceBetween
        ) {
            Text(
                text = level.price.format(2),
                style = MaterialTheme.typography.bodySmall,
                color = if (isBid) Color(0xFF10B981) else Color(0xFFEF4444),
                fontWeight = FontWeight.Medium,
                modifier = Modifier.weight(1f)
            )
            Text(
                text = level.size.format(4),
                style = MaterialTheme.typography.bodySmall,
                textAlign = TextAlign.End,
                modifier = Modifier.weight(1f)
            )
        }
    }
}

// Extension functions
fun BigDecimal.format(decimals: Int): String =
    setScale(decimals, RoundingMode.HALF_UP).toPlainString()

fun Double.format(decimals: Int): String =
    BigDecimal(this).setScale(decimals, RoundingMode.HALF_UP).toPlainString()
```

---

## 5. ViewModel Integration

```kotlin
@HiltViewModel
class OrderBookViewModel @Inject constructor(
    private val webSocket: OrderBookWebSocket,
    private val orderBookManager: OrderBookManager
) : ViewModel() {
    
    private val _symbol = MutableStateFlow("")
    val symbol: StateFlow<String> = _symbol.asStateFlow()
    
    val orderBook: StateFlow<OrderBook?> = orderBookManager.orderBook
    val connectionState: StateFlow<ConnectionState> = webSocket.connectionState
    
    fun subscribe(symbol: String) {
        if (_symbol.value == symbol) return
        
        unsubscribe()
        _symbol.value = symbol
        webSocket.subscribe(symbol)
    }
    
    fun unsubscribe() {
        _symbol.value.ifBlank { return }
        orderBookManager.clear()
        webSocket.unsubscribe(_symbol.value)
    }
    
    override fun onCleared() {
        super.onCleared()
        webSocket.disconnect()
    }
}
```

---

## 6. Performance Optimizations

```kotlin
// Throttle UI updates to prevent jank
@Composable
fun OrderBookScreenThrottled(
    symbol: String,
    viewModel: OrderBookViewModel = hiltViewModel()
) {
    val rawOrderBook by viewModel.orderBook.collectAsStateWithLifecycle()
    
    // Throttle to max 10 updates per second
    val orderBook by remember(rawOrderBook) {
        derivedStateOf { rawOrderBook }
    }.let { state ->
        var lastEmitTime by remember { mutableLongStateOf(0L) }
        var throttledBook by remember { mutableStateOf<OrderBook?>(null) }
        
        LaunchedEffect(state.value) {
            val now = System.currentTimeMillis()
            if (now - lastEmitTime >= 100) { // 100ms = 10fps
                throttledBook = state.value
                lastEmitTime = now
            }
        }
        throttledBook
    }
    
    // Rest of UI...
}

// Snapshot vs Delta handling
fun processUpdateOptimized(update: String, isSnapshot: Boolean) {
    if (isSnapshot) {
        // Full rebuild
        processSnapshot(update)
    } else {
        // Incremental update
        processDelta(update)
    }
}
```

---

## TL;DR

| Component | Purpose |
|-----------|---------|
| `ConcurrentSkipListMap` | Thread-safe O(log n) sorted access |
| Snapshot → Delta | Initial state + incremental updates |
| `recalculateTotals()` | Cumulative depth for visualization |
| Throttled updates | Prevent UI jank (max 10fps) |
| `animateFloatAsState` | Smooth depth bar transitions |
| Keyed LazyColumn | Efficient recomposition |

**Key insight:** Order books need efficient sorted access and fast incremental updates. Use `ConcurrentSkipListMap` for O(log n) operations and throttle UI updates to prevent jank.