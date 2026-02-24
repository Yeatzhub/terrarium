# Mobile Trading App Pattern - Real-Time Architecture

## Overview
Production-ready pattern for real-time price streaming with clean architecture.

## Layer Structure

```
data/
  ├── remote/WebSocketService.kt
  ├── local/PriceDao.kt
  └── repository/PriceRepositoryImpl.kt
domain/
  ├── model/Price.kt
  └── repository/PriceRepository.kt
presentation/
  └── PriceViewModel.kt
```

## 1. WebSocket Service (Kotlin Flow)

```kotlin
@Singleton
class WebSocketService @Inject constructor() {
    private val webSocket = okhttp3.OkHttpClient.Builder()
        .pingInterval(20, TimeUnit.SECONDS)
        .build()
        .newWebSocket(
            Request.Builder().url("wss://api.exchange.com/stream").build(),
            object : WebSocketListener() {
                private val _prices = MutableSharedFlow<Price>(replay = 1)
                val prices: SharedFlow<Price> = _prices
                
                override fun onMessage(webSocket: WebSocket, text: String) {
                    runCatching { Json.decodeFromString<Price>(text) }
                        .onSuccess { _prices.tryEmit(it) }
                }
            }
        )
}
```

## 2. Room Database (Offline Cache)

```kotlin
@Entity(tableName = "prices")
data class PriceEntity(
    @PrimaryKey val symbol: String,
    val price: Double,
    val timestamp: Long
)

@Dao
interface PriceDao {
    @Query("SELECT * FROM prices WHERE symbol = :symbol")
    fun observe(symbol: String): Flow<PriceEntity?>
    
    @Upsert
    suspend fun upsert(price: PriceEntity)
}
```

## 3. Repository (Merge Sources)

```kotlin
class PriceRepositoryImpl @Inject constructor(
    private val webSocket: WebSocketService,
    private val dao: PriceDao
) : PriceRepository {
    override fun observePrice(symbol: String): Flow<Result<Price>> = channelFlow {
        // WebSocket source
        launch {
            webSocket.prices
                .filter { it.symbol == symbol }
                .collect { price ->
                    dao.upsert(price.toEntity())
                    send(Result.success(price))
                }
        }
        
        // Cached fallback
        launch {
            dao.observe(symbol)
                .filterNotNull()
                .collect { send(Result.success(it.toDomain())) }
        }
    }
        .catch { emit(Result.failure(it)) }
}
```

## 4. ViewModel (MVVM + StateFlow)

```kotlin
@HiltViewModel
class PriceViewModel @Inject constructor(
    private val repository: PriceRepository
) : ViewModel() {
    
    private val _symbol = MutableStateFlow("BTC-USD")
    val uiState: StateFlow<PriceUiState> = _symbol
        .flatMapLatest { repository.observePrice(it) }
        .map { result ->
            result.fold(
                onSuccess = { PriceUiState.Success(it) },
                onFailure = { PriceUiState.Error(it.message) }
            )
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = PriceUiState.Loading
        )
    
    fun setSymbol(symbol: String) = _symbol.tryEmit(symbol)
}
```

## 5. Compose UI

```kotlin
@Composable
fun PriceScreen(viewModel: PriceViewModel = hiltViewModel()) {
    val state by viewModel.uiState.collectAsState()
    
    AnimatedContent(state, transitionSpec = { fadeIn() with fadeOut() }) { target ->
        when (target) {
            is PriceUiState.Loading -> CircularProgressIndicator()
            is PriceUiState.Success -> PriceCard(target.price)
            is PriceUiState.Error -> ErrorRetry(target.message) { viewModel.retry() }
        }
    }
}

@Composable
fun PriceCard(price: Price) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .padding(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = when {
                price.change >= 0 -> Color(0xFF4CAF50).copy(alpha = 0.2f)
                else -> Color(0xFFF44336).copy(alpha = 0.2f)
            }
        )
    ) {
        Column(Modifier.padding(16.dp)) {
            Text(price.symbol, style = MaterialTheme.typography.headlineMedium)
            Text(
                "$${"%,.2f".format(price.value)}",
                style = MaterialTheme.typography.displaySmall
            )
        }
    }
}
```

## Key Patterns

| Pattern | Benefit |
|---------|---------|
| `SharedFlow(replay=1)` | New subscribers get last value |
| `flatMapLatest` | Auto-cancel previous symbol stream |
| `WhileSubscribed(5s)` | Stop flow when no UI observers |
| `channelFlow` | Concurrent sources in one flow |
| Room + Flow | Auto-refresh on DB changes |

## Hilt Module

```kotlin
@Module
@InstallIn(SingletonComponent::class)
object DataModule {
    @Provides @Singleton
    fun provideDatabase(app: Application): AppDatabase =
        Room.databaseBuilder(app, AppDatabase::class.java, "trading.db")
            .fallbackToDestructiveMigration()
            .build()
    
    @Binds
    fun bindRepository(impl: PriceRepositoryImpl): PriceRepository
}
```

## Testing Tips

```kotlin
@Test
fun `observePrice emits cached then live`() = runTest {
    val dao = mock<PriceDao>()
    val ws = mock<WebSocketService>()
    
    // Given cached data exists
    whenever(dao.observe("BTC")).thenReturn(flowOf(PriceEntity("BTC", 50000.0, 0L)))
    whenever(ws.prices).thenReturn(MutableSharedFlow())
    
    // When observing
    val results = repository.observePrice("BTC").take(2).toList()
    
    // Then cached is first
    assertEquals(50000.0, results.first().getOrThrow().value)
}
```

---
*Learned: 2026-02-22 | Focus: WebSocket → Flow → Room → ViewModel → Compose pipeline*