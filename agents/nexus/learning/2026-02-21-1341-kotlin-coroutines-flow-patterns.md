# 📱 Kotlin Coroutines & Flow Patterns

**Focus:** Hot vs Cold Flows, StateFlow, SharedFlow, Pipeline Patterns
**Pattern:** Reactive Data Streams with Proper Lifecycle Management

---

## 1. Flow Types Overview

```
Cold Flows (lazy, per-collector)
├── flow { emit(value) }
├── flowOf(1, 2, 3)
└── callbackFlow { channel.send() }

Hot Flows (eager, shared)
├── MutableStateFlow (single value, stateful)
└── MutableSharedFlow (events, configurable replay)
```

---

## 2. Cold Flow Production Patterns

### Repository with Multiple Data Sources

```kotlin
class PriceRepository @Inject constructor(
    private val api: TradingApi,
    private val dao: PriceDao
) {
    /**
     * Cold Flow: Created fresh for each collector
     * Emits: Loading → Cache → Network updates
     */
    fun observePrices(symbols: List<String>): Flow<Resource<List<Price>>> = flow {
        emit(Resource.Loading)
        
        // Emit cached data first
        val cached = dao.getPrices(symbols).first()
        if (cached.isNotEmpty()) {
            emit(Resource.Success(cached))
        }
        
        // Then fetch from network
        try {
            val response = api.getPrices(symbols)
            dao.insert(response)
            emit(Resource.Success(response))
        } catch (e: Exception) {
            if (cached.isEmpty()) {
                emit(Resource.Error(e))
            }
            // Otherwise keep showing cached data
        }
    }.flowOn(Dispatchers.IO)
    
    /**
     * Transforming Flow: Map + Filter pipeline
     */
    fun observePriceChanges(symbol: String): Flow<PriceChange> = 
        dao.getPriceHistory(symbol)
            .filter { it.size >= 2 } // Need at least 2 points
            .map { history ->
                val current = history.last()
                val previous = history.dropLast(1).last()
                PriceChange(
                    symbol = symbol,
                    current = current,
                    previous = previous,
                    percentChange = calculatePercentChange(previous, current)
                )
            }
            .distinctUntilChanged { old, new ->
                old.percentChange == new.percentChange
            }
}

sealed class Resource<out T> {
    object Loading : Resource<Nothing>()
    data class Success<T>(val data: T) : Resource<T>()
    data class Error(val throwable: Throwable) : Resource<Nothing>()
}
```

### Callback Flow (Bridging Callbacks to Flow)

```kotlin
class WebSocketPriceSource @Inject constructor() {
    /**
     * Converts callback-based WebSocket to cold Flow
     * Automatically closes when collector cancels
     */
    fun priceStream(symbols: List<String>): Flow<PriceUpdate> = callbackFlow {
        val client = OkHttpClient()
        val request = Request.Builder()
            .url("wss://stream.exchange.com/ws")
            .build()
        
        val listener = object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                // Subscribe to symbols
                webSocket.send(json.encodeToString(SubscribeMessage(symbols)))
            }
            
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val update = json.decodeFromString<PriceUpdate>(text)
                    trySend(update) // Non-blocking send to channel
                } catch (e: Exception) {
                    // Log error but don't close flow
                    println("Parse error: $e")
                }
            }
            
            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                close(t) // Close channel on fatal error
            }
            
            override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                close()
            }
        }
        
        val webSocket = client.newWebSocket(request, listener)
        
        // Cleanup when flow is cancelled
        awaitClose {
            webSocket.close(1000, "Collector cancelled")
            client.dispatcher.executorService.shutdown()
        }
    }
    
    /**
     * Retry with exponential backoff
     */
    fun resilientPriceStream(symbols: List<String>): Flow<PriceUpdate> =
        priceStream(symbols)
            .retryWhen { cause, attempt ->
                if (attempt < 5 && cause is IOException) {
                    delay(1000 * 2.0.pow(attempt.toDouble()).toLong())
                    true
                } else false
            }
            .catch { e ->
                emit(PriceUpdate.Error(e.message))
            }
}
```

---

## 3. Hot Flow Patterns

### StateFlow (Single Source of Truth)

```kotlin
@HiltViewModel
class TradingViewModel @Inject constructor(
    private val repository: PriceRepository
) : ViewModel() {
    
    // Private mutable, public immutable
    private val _uiState = MutableStateFlow(TradingUiState())
    val uiState: StateFlow<TradingUiState> = _uiState.asStateFlow()
    
    // Backing field for watched symbols (also StateFlow)
    private val _watchedSymbols = MutableStateFlow(listOf("BTC", "ETH"))
    val watchedSymbols: StateFlow<List<String>> = _watchedSymbols.asStateFlow()
    
    // Computed state: Auto-updates when dependencies change
    val portfolioValue: StateFlow<BigDecimal> = uiState
        .map { state ->
            state.prices.sumOf { price ->
                price.currentPrice * state.holdings[price.symbol].orZero()
            }
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = BigDecimal.ZERO
        )
    
    init {
        // Collect cold flow and convert to hot StateFlow
        observePrices()
    }
    
    private fun observePrices() {
        watchedSymbols
            .flatMapLatest { symbols ->  // Cancel old subscription when symbols change
                repository.observePrices(symbols)
            }
            .onEach { resource ->
                _uiState.update { current ->
                    when (resource) {
                        is Resource.Loading -> current.copy(isLoading = true)
                        is Resource.Success -> current.copy(
                            isLoading = false,
                            prices = resource.data,
                            error = null
                        )
                        is Resource.Error -> current.copy(
                            isLoading = false,
                            error = resource.throwable.message
                        )
                    }
                }
            }
            .launchIn(viewModelScope)
    }
    
    // User actions update StateFlow
    fun addSymbol(symbol: String) {
        _watchedSymbols.update { current ->
            if (symbol !in current) current + symbol else current
        }
    }
    
    fun removeSymbol(symbol: String) {
        _watchedSymbols.update { it - symbol }
    }
}

data class TradingUiState(
    val isLoading: Boolean = false,
    val prices: List<Price> = emptyList(),
    val holdings: Map<String, BigDecimal> = emptyMap(),
    val error: String? = null
)
```

### SharedFlow (One-Time Events)

```kotlin
@HiltViewModel
class TradingViewModel @Inject constructor(
    private val repository: PriceRepository
) : ViewModel() {
    
    // State (survives rotation)
    private val _uiState = MutableStateFlow(TradingUiState())
    val uiState = _uiState.asStateFlow()
    
    // Events (consumed once)
    private val _events = MutableSharedFlow<TradingEvent>()
    val events = _events.asSharedFlow()
    
    fun buy(symbol: String, amount: BigDecimal) {
        viewModelScope.launch {
            try {
                _uiState.update { it.copy(isProcessing = true) }
                
                val order = repository.placeOrder(symbol, amount, OrderType.BUY)
                
                // Emit one-time event (snackbar, navigation)
                _events.emit(
                    TradingEvent.OrderSuccess(
                        orderId = order.id,
                        message = "Bought $amount $symbol"
                    )
                )
                
                _uiState.update { current ->
                    current.copy(
                        isProcessing = false,
                        holdings = current.holdings + (symbol to 
                            (current.holdings[symbol].orZero() + amount))
                    )
                }
            } catch (e: Exception) {
                _events.emit(TradingEvent.ShowError(e.message ?: "Unknown error"))
                _uiState.update { it.copy(isProcessing = false) }
            }
        }
    }
}

// Event sealed class for one-time UI actions
sealed class TradingEvent {
    data class OrderSuccess(val orderId: String, val message: String) : TradingEvent()
    data class ShowError(val message: String) : TradingEvent()
    data class NavigateToOrderDetail(val orderId: String) : TradingEvent()
}

// Compose: Collect events properly
@Composable
fun TradingScreen(viewModel: TradingViewModel = hiltViewModel()) {
    val snackbarHost = remember { SnackbarHostState() }
    
    // Collect events (one-time)
    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is TradingEvent.OrderSuccess -> {
                    snackbarHost.showSnackbar(event.message)
                }
                is TradingEvent.ShowError -> {
                    snackbarHost.showSnackbar(event.message)
                }
                is TradingEvent.NavigateToOrderDetail -> {
                    // Navigation handled by NavController
                    navController.navigate("order/${event.orderId}")
                }
            }
        }
    }
    
    // Collect state (continuous)
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()
}
```

---

## 4. Flow Operators Cheat Sheet

```kotlin
// Transform operators
Flow<Int>
    .map { it * 2 }                    // Transform each element
    .filter { it > 5 }                 // Keep only matching
    .filterNot { it == 10 }            // Exclude matching
    .distinctUntilChanged()            // Skip consecutive duplicates
    .flatMapConcat { fetchDetails(it) } // Sequential: wait for inner
    .flatMapMerge { fetchDetails(it) }  // Concurrent: all at once (default 16)
    .flatMapLatest { fetchDetails(it) } // Cancel previous on new emission
    .transform { emit(it); emit(it * 2) } // Custom transformation
    .scan(initial) { acc, value -> acc + value } // Running fold
    .runningReduce { acc, value -> acc + value }   // Running reduce

// Combining flows
flow1.zip(flow2) { a, b -> a to b }     // Wait for both
flow1.combine(flow2) { a, b -> a + b }  // Emit when either changes
Flow<Flow<Int>>.flattenConcat()          // Sequential inner flows
Flow<Flow<Int>>.flattenMerge(16)       // Concurrent inner flows

// Lifecycle
flow
    .onEach { println(it) }            // Side effect (observation)
    .onStart { println("Started") }      // Before first emission
    .onCompletion { println("Done") }   // After completion/cancel
    .catch { e -> emit(defaultValue) }   // Error recovery
    .retry(3)                           // Retry on error
    .retryWhen { e, attempt -> attempt < 3 }

// Buffer/Conflation
flow
    .buffer(64)              // Buffer emissions (backpressure)
    .conflate()             // Drop intermediate, keep latest
    .collectLatest { }       // Cancel slow collector on new item

// Timing
flow
    .debounce(300.millis)   // Wait 300ms silence before emitting
    .sample(1000.millis)    // Emit latest every 1s
    .throttleFirst(1000).millis // Take first, ignore rest for 1s
    .timeout(5.seconds)      // Timeout if no emission
```

---

## 5. Real-World Pipeline Pattern

```kotlin
class PriceStreamManager @Inject constructor(
    private val api: TradingApi,
    private val dao: PriceDao,
    @ApplicationScope private val scope: CoroutineScope
) {
    /**
     * Complete real-time price pipeline:
     * 1. Connect to WebSocket
     * 2. Parse incoming messages
     * 3. Validate data
     * 4. Persist to database
     * 5. Emit to collectors
     */
    fun priceStream(symbols: List<String>): Flow<List<Price>> {
        return api.webSocketFlow()
            // Filter for requested symbols only
            .filter { it.symbol in symbols }
            // Remove duplicates (based on timestamp)
            .distinctUntilChangedBy { it.timestamp }
            // Validate price values
            .filter { update ->
                update.price > BigDecimal.ZERO && update.price < BigDecimal("1000000000")
            }
            // Convert to domain model
            .map { it.toDomainModel() }
            // Persist to database on background thread
            .onEach { dao.insertPrice(it.toEntity()) }
            // Sample at 100ms to reduce UI load
            .sample(100.milliseconds)
            // Convert to list for UI
            .scan(emptyList<Price>()) { acc, price ->
                (acc.filter { it.symbol != price.symbol } + price)
                    .sortedBy { it.symbol }
            }
            // Ensure main thread not blocked
            .flowOn(Dispatchers.IO)
            // Share among collectors, keep alive 5s after last
            .shareIn(
                scope = scope,
                started = SharingStarted.WhileSubscribed(5000),
                replay = 1
            )
    }
    
    /**
     * Throttled user actions
     */
    private val _searchQueries = MutableSharedFlow<String>()
    
    val searchResults: Flow<List<Symbol>> = _searchQueries
        .debounce(300.milliseconds)  // Wait for typing to stop
        .filter { it.length >= 2 }     // Min 2 chars
        .distinctUntilChanged()        // Skip duplicate queries
        .flatMapLatest { query ->       // Cancel stale searches
            api.searchSymbols(query)
                .catch { emit(emptyList()) }
        }
        .flowOn(Dispatchers.IO)
        .shareIn(scope, SharingStarted.WhileSubscribed(), replay = 1)
    
    fun search(query: String) {
        _searchQueries.tryEmit(query)
    }
}
```

---

## 6. Flow Testing Patterns

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class FlowPatternsTest {
    private val testDispatcher = StandardTestDispatcher()
    
    @Before
    fun setup() {
        Dispatchers.setMain(testDispatcher)
    }
    
    @Test
    fun `cold flow creates new instance per collector`() = runTest {
        var counter = 0
        val flow = flow {
            counter++
            emit(counter)
        }
        
        val first = flow.first()
        val second = flow.first()
        
        assertEquals(1, first)  // First collector
        assertEquals(2, second) // New instance for second collector
    }
    
    @Test
    fun `hot flow shares among collectors`() = runTest {
        val mutableFlow = MutableSharedFlow<Int>()
        val hotFlow = mutableFlow.asSharedFlow()
        
        val values1 = mutableListOf<Int>()
        val values2 = mutableListOf<Int>()
        
        val job1 = launch { hotFlow.toList(values1) }
        val job2 = launch { hotFlow.toList(values2) }
        
        mutableFlow.emit(1)
        mutableFlow.emit(2)
        
        advanceUntilIdle()
        
        assertEquals(listOf(1, 2), values1)
        assertEquals(listOf(1, 2), values2) // Same values
        
        job1.cancel(); job2.cancel()
    }
    
    @Test
    fun `flatMapLatest cancels previous`() = runTest {
        val trigger = MutableSharedFlow<Int>()
        val flow = trigger.flatMapLatest { delay ->
            flow {
                delay(delay.toLong())
                emit(delay)
            }
        }
        
        val results = mutableListOf<Int>()
        val job = launch { flow.toList(results) }
        
        trigger.emit(100) // Will be cancelled
        trigger.emit(50)  // This one completes first
        
        advanceTimeBy(60)
        
        assertEquals(listOf(50), results) // 100 was cancelled
        job.cancel()
    }
    
    @Test
    fun `scan accumulates values`() = runTest {
        val flow = flowOf(1, 2, 3, 4, 5)
            .scan(0) { acc, value -> acc + value }
        
        val result = flow.toList()
        
        assertEquals(listOf(0, 1, 3, 6, 10, 15), result)
    }
    
    @Test
    fun `debounce drops rapid emissions`() = runTest {
        val flow = flow {
            emit(1)
            delay(50)
            emit(2)
            delay(50)
            emit(3)
            delay(400) // Wait longer than debounce
            emit(4)
        }.debounce(100.milliseconds)
        
        val result = flow.toList()
        
        assertEquals(listOf(3, 4), result) // 1,2 dropped due to rapid emission
    }
}
```

---

## 7. Common Pitfalls & Solutions

```kotlin
// ❌ PITFALL: Launch in ViewModel with GlobalScope
GlobalScope.launch { } // Survives configuration changes!

// ✅ SOLUTION: Use viewModelScope
viewModelScope.launch { } // Auto-cancelled when ViewModel cleared

// ❌ PITFALL: Using StateFlow for one-time events
_error.value = "Error" // Re-emits on rotation

// ✅ SOLUTION: Use SharedFlow for events
_events.emit("Error") // Consumed once, not replayed

// ❌ PITFALL: Multiple collectors triggering multiple requests
viewModelScope.launch { flow.collect { } }
viewModelScope.launch { flow.collect { } } // Two WebSocket connections!

// ✅ SOLUTION: Use stateIn/shareIn
val sharedFlow = flow.shareIn(viewModelScope, WhileSubscribed(5000))

// ❌ PITFALL: Blocking with flatMapConcat
items.flatMapConcat { fetch(it) } // Sequential, slow

// ✅ SOLUTION: Use flatMapMerge for parallelism
items.flatMapMerge(concurrency = 10) { fetch(it) }

// ❌ PITFALL: Collecting Flow forever in Composable
val state = flow.collectAsState() // Never changes composition

// ✅ SOLUTION: Use collectAsStateWithLifecycle
val state by flow.collectAsStateWithLifecycle()
```

---

## TL;DR

| Pattern | Use When |
|---------|----------|
| **Cold Flow** (`flow{}`) | One-shot operations, fresh data per collector |
| **StateFlow** | UI state that survives rotation |
| **SharedFlow** | One-time events (snackbar, navigation) |
| **callbackFlow** | Convert callbacks (WebSocket, sensors) |
| **flatMapLatest** | Search: cancel stale requests |
| **flatMapConcat** | Sequential dependencies |
| **shareIn** | Share expensive flow among collectors |
| **debounce** | User input throttling |
| **scan** | Running totals/aggregations |

**Remember:** Cold flows are lazy and re-executed; hot flows are eager and shared. Use `stateIn`/`shareIn` to convert cold to hot when needed.
