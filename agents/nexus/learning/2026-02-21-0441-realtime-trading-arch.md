# 📱 Real-Time Trading App Architecture

**Focus:** MVVM + WebSocket Flow + Room Persistence + Hilt DI
**Pattern:** Repository Layer + Offline-First Real-Time Stream

---

## 1. Architecture Overview

```
UI (Compose)
  ↕️
ViewModel (StateFlow)
  ↕️
Repository (merge local + remote)
  ↕️                    ↕️
Room (Flow)           WebSocket (Flow)
(SofTruth)            (Real-time)
```

---

## 2. WebSocket Client (Kotlin Flow)

```kotlin
@Singleton
class TradingWebSocketClient @Inject constructor() {
    private val client = OkHttpClient()
    private val _priceUpdates = MutableSharedFlow<PriceUpdate>()
    val priceUpdates: SharedFlow<PriceUpdate> = _priceUpdates.asSharedFlow()
    private var webSocket: WebSocket? = null
    
    fun connect(symbols: List<String>): Flow<PriceUpdate> = callbackFlow {
        val request = Request.Builder()
            .url("wss://stream.exchange.com/ws")
            .build()
            
        webSocket = client.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(ws: WebSocket, text: String) {
                val update = json.decodeFromString<PriceUpdate>(text)
                trySend(update).isSuccess
            }
            override fun onFailure(ws: WebSocket, t: Throwable, response: Response?) {
                close(t)
            }
        })
        subscribeToSymbols(symbols)
        awaitClose { webSocket?.close(1000, "Closing") }
    }.shareIn(scope, SharingStarted.WhileSubscribed(5000))
    
    private fun subscribeToSymbols(symbols: List<String>) {
        val message = SubscribeMessage(symbols)
        webSocket?.send(json.encodeToString(message))
    }
}

@Serializable
data class PriceUpdate(
    val symbol: String,
    val price: BigDecimal,
    val volume: Double,
    val timestamp: Long
)
```

---

## 3. Repository: Merge Local + Remote

```kotlin
@Singleton
class TradingRepository @Inject constructor(
    private val priceDao: PriceDao,
    private val api: TradingWebSocketClient,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher
) {
    // Offline-first: Emit cached immediately, update when WebSocket flows
    fun observePriceUpdates(symbols: List<String>): Flow<NetworkResult<List<PriceUpdate>>> = 
        priceDao.getLatestPrices(symbols)
            .distinctUntilChanged()
            .map { cached -> NetworkResult.Success(cached) }
            .onStart { emit(NetworkResult.Loading) }
            .flatMapLatest { cachedResult ->
                // Merge with real-time stream
                api.priceUpdates
                    .filter { it.symbol in symbols }
                    .onEach { priceDao.insertPrice(it.toEntity()) } // Persist
                    .scan(cachedResult) { _, update ->
                        NetworkResult.Success(
                            (result as? NetworkResult.Success)?.data
                                ?.map { if (it.symbol == update.symbol) update else it }
                                ?: emptyList()
                        )
                    }
                    .onCompletion { emit(NetworkResult.Error("Stream closed")) }
                    .catch { emit(NetworkResult.Error(it.message)) }
            }
            .flowOn(ioDispatcher)
}

sealed class NetworkResult<out T> {
    data class Success<T>(val data: T) : NetworkResult<T>()
    data class Error(val message: String?) : NetworkResult<Nothing>()
    object Loading : NetworkResult<Nothing>()
}
```

---

## 4. Room Setup

```kotlin
@Entity(tableName = "prices")
data class PriceEntity(
    @PrimaryKey val symbol: String,
    val price: String,         // Store BigDecimal as String
    val volume: Double,
    val timestamp: Long,
    val updatedAt: Long = System.currentTimeMillis()
)

@Dao
interface PriceDao {
    @Query("SELECT * FROM prices WHERE symbol IN (:symbols)")
    fun getLatestPrices(symbols: List<String>): Flow<List<PriceEntity>>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertPrice(price: PriceEntity)
    
    @Query("DELETE FROM prices WHERE updatedAt < :olderThan")
    suspend fun purgeOld(olderThan: Long = System.currentTimeMillis() - 86400000) // 24h
}
```

---

## 5. Hilt Modules

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object TradingModule {
    
    @Provides
    @Singleton
    fun provideWebSocketClient() = TradingWebSocketClient()
    
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext ctx: Context): TradingDatabase =
        Room.databaseBuilder(ctx, TradingDatabase::class.java, "trading.db")
            .fallbackToDestructiveMigration()
            .build()
    
    @Provides
    fun providePriceDao(db: TradingDatabase) = db.priceDao()
    
    @Provides
    @IoDispatcher
    fun provideIoDispatcher(): CoroutineDispatcher = Dispatchers.IO
}

// Qualifier for dispatchers
@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class IoDispatcher
```

---

## 6. ViewModel + Compose

```kotlin
@HiltViewModel
class TradeScreenViewModel @Inject constructor(
    private val repository: TradingRepository
) : ViewModel() {
    
    private val _ uiState = MutableStateFlow(TradeUiState())
    val uiState: StateFlow<TradeUiState> = _uiState.asStateFlow()
    
    private val watchedSymbols = MutableStateFlow(listOf("BTC", "ETH", "SOL"))
    
    init {
        observePrices()
    }
    
    private fun observePrices() {
        watchedSymbols
            .flatMapLatest { symbols -> repository.observePriceUpdates(symbols) }
            .onEach { result ->
                _uiState.update { 
                    when (result) {
                        is NetworkResult.Success -> it.copy(
                            prices = result.data,
                            isLoading = false,
                            error = null
                        )
                        is NetworkResult.Error -> it.copy(
                            isLoading = false,
                            error = result.message
                        )
                        NetworkResult.Loading -> it.copy(isLoading = true)
                    }
                }
            }
            .launchIn(viewModelScope)
    }
}

data class TradeUiState(
    val prices: List<PriceEntity> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null
)

// Compose UI
@Composable
fun TradingDashboard(viewModel: TradeScreenViewModel = hiltViewModel()) {
    val state by viewModel.uiState.collectAsStateWithLifecycle()
    val prices = state.prices
    
    LazyColumn {
        items(prices) { price ->
            PriceCard(
                symbol = price.symbol,
                price = remember(price.price) { 
                    BigDecimal(price.price).setScale(2, RoundingMode.HALF_UP)
                },
                volume = price.volume
            )
        }
    }
}

@Composable
private fun PriceCard(symbol: String, price: BigDecimal, volume: Double) {
    ElevatedCard(modifier = Modifier.padding(8.dp)) {
        Row(Modifier.padding(16.dp)) {
            Text(symbol, style = MaterialTheme.typography.headlineSmall)
            Spacer(Modifier.weight(1f))
            Text("$${price}", style = MaterialTheme.typography.titleMedium)
        }
    }
}
```

---

## 7. Key Idioms

| Pattern | Why |
|---------|-----|
| `shareIn(WhileSubscribed(5000))` | Keep WebSocket alive only when UI active |
| `distinctUntilChanged()` | Skip duplicate DB emissions |
| `flatMapLatest` | Auto-cancel old stream when symbols change |
| Room + Flow | Reactive local cache that WebSocket updates |
| BigDecimal as String | Avoid float precision loss in DB |

---

## 8. Testing

```kotlin
@Test
fun `emits cached data before WebSocket connects`() = runTest {
    val mockDao = mockk<PriceDao>()
    coEvery { mockDao.getLatestPrices(any()) } returns flowOf(listOf(fakePrice))
    
    val repo = TradingRepository(mockDao, mockApi, StandardTestDispatcher())
    
    repo.observePriceUpdates(listOf("BTC"))
        .filterIsInstance<NetworkResult.Success>()
        .first()
        .data shouldBe listOf(fakePrice)
}
```

---

**TL;DR:** Repository merges Room Flow (offline truth) with WebSocket Flow (real-time updates). UI sees cached data instantly, updates arrive via shared Flow. Use `WhileSubscribed` to control WebSocket lifecycle.
