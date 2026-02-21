# 📱 Android Architecture Testing Guide

**Focus:** Unit Tests + Integration Tests + Compose UI Tests
**Pattern:** Repository + ViewModel + UI Layer testing strategy

---

## 1. Testing Strategy Overview

```
┌─────────────────────────────────────────────────┐
│  Unit Tests (JVM) - Fast, offline              │
│  ├── Repository (fake data sources)            │
│  ├── ViewModel (fake repositories)           │
│  └── Use Cases / Business Logic                │
├─────────────────────────────────────────────────┤
│  Integration Tests (JVM + Android)             │
│  ├── Database (Room in-memory)                 │
│  └── Repository + DAO + API                    │
├─────────────────────────────────────────────────┤
│  UI Tests (Android Emulator)                   │
│  ├── Compose Screen Tests                      │
│  └── End-to-End Flows                          │
└─────────────────────────────────────────────────┘
```

---

## 2. Testing Dependencies

```kotlin
// build.gradle.kts (Module level)
dependencies {
    // Unit testing
    testImplementation("junit:junit:4.13.2")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.7.3")
    testImplementation("io.mockk:mockk:1.13.8")
    testImplementation("com.google.truth:truth:1.1.5")
    
    // Architecture component testing
    testImplementation("androidx.arch.core:core-testing:2.2.0")
    
    // Room testing
    testImplementation("androidx.room:room-testing:2.6.1")
    
    // Hilt testing
    testImplementation("com.google.dagger:hilt-android-testing:2.48")
    kaptTest("com.google.dagger:hilt-android-compiler:2.48")
    
    // UI tests
    androidTestImplementation("androidx.compose.ui:ui-test-junit4")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
    androidTestImplementation("com.google.dagger:hilt-android-testing:2.48")
    kaptAndroidTest("com.google.dagger:hilt-android-compiler:2.48")
}
```

---

## 3. Coroutines Test Setup

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class MainDispatcherRule : TestWatcher() {
    private val testDispatcher = StandardTestDispatcher()
    
    override fun starting(description: Description) {
        Dispatchers.setMain(testDispatcher)
    }
    
    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}

// Use in tests
class MyViewModelTest {
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()
    
    @get:Rule
    val instantExecutorRule = InstantTaskExecutorRule() // For LiveData (optional)
    
    // Or use runTest for coroutines
    @Test
    fun `emits loading then success`() = runTest {
        val viewModel = createViewModel()
        
        viewModel.uiState.test {
            assertEquals(UiState.Loading, awaitItem())
            assertEquals(UiState.Success, awaitItem())
        }
    }
}
```

---

## 4. Repository Testing (with Fakes)

```kotlin
// Fake implementation for testing
class FakePriceDao : PriceDao {
    private val prices = mutableListOf<PriceEntity>()
    private val pricesFlow = MutableStateFlow<List<PriceEntity>>(emptyList())
    
    override fun getLatestPrices(symbols: List<String>): Flow<List<PriceEntity>> = 
        pricesFlow.map { list -> 
            list.filter { it.symbol in symbols }
        }
    
    override suspend fun insertPrice(price: PriceEntity) {
        prices.removeAll { it.symbol == price.symbol }
        prices.add(price)
        pricesFlow.value = prices.toList()
    }
    
    override suspend fun purgeOld(olderThan: Long) {
        prices.removeAll { it.updatedAt < olderThan }
        pricesFlow.value = prices.toList()
    }
}

class FakeTradingApi : TradingApi {
    private val flow = MutableSharedFlow<PriceUpdate>()
    
    override fun connect(symbols: List<String>): Flow<PriceUpdate> = flow.asSharedFlow()
    
    suspend fun emitUpdate(update: PriceUpdate) {
        flow.emit(update)
    }
}

// Repository test
@OptIn(ExperimentalCoroutinesApi::class)
class TradingRepositoryTest {
    private lateinit var dao: FakePriceDao
    private lateinit var api: FakeTradingApi
    private lateinit var repository: TradingRepository
    private val testDispatcher = StandardTestDispatcher()
    
    @Before
    fun setup() {
        dao = FakePriceDao()
        api = FakeTradingApi()
        repository = TradingRepository(dao, api, testDispatcher)
    }
    
    @Test
    fun `emits cached data immediately then updates from api`() = runTest(testDispatcher) {
        // Pre-populate cache
        dao.insertPrice(PriceEntity("BTC", "50000", 1.0, System.currentTimeMillis()))
        
        // Start observing
        val job = launch {
            repository.observePriceUpdates(listOf("BTC")).test {
                // First emission is cached
                val first = awaitItem()
                assertTrue(first is NetworkResult.Success)
                
                // Emit from API
                api.emitUpdate(PriceUpdate("BTC", BigDecimal("51000"), 1.5, System.currentTimeMillis()))
                
                // Should get updated value
                val second = awaitItem()
                assertEquals(BigDecimal("51000"), (second as NetworkResult.Success).data.first().price)
            }
        }
        
        job.cancel()
    }
    
    @Test
    fun `handles api errors gracefully`() = runTest(testDispatcher) {
        val erroringApi = object : TradingApi {
            override fun connect(symbols: List<String>): Flow<PriceUpdate> = 
                flow { throw IOException("Connection failed") }
        }
        val repo = TradingRepository(dao, erroringApi, testDispatcher)
        
        repo.observePriceUpdates(listOf("BTC")).test {
            skipItems(1) // Skip loading/cached
            val error = awaitItem()
            assertTrue(error is NetworkResult.Error)
        }
    }
}
```

---

## 5. ViewModel Testing

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class TradeViewModelTest {
    @get:Rule
    val mainDispatcherRule = MainDispatcherRule()
    
    private lateinit var repository: FakeTradingRepository
    private lateinit var viewModel: TradeViewModel
    
    @Before
    fun setup() {
        repository = FakeTradingRepository()
        viewModel = TradeViewModel(repository)
    }
    
    @Test
    fun `initial state is loading`() = runTest {
        val initialState = viewModel.uiState.value
        assertEquals(TradeUiState(isLoading = true), initialState)
    }
    
    @Test
    fun `updates state when prices change`() = runTest {
        val prices = listOf(
            PriceEntity("BTC", "50000", 1.0, System.currentTimeMillis())
        )
        
        // Emit prices
        repository.emitPrices(prices)
        
        // Advance dispatcher
        advanceUntilIdle()
        
        // Verify state
        val state = viewModel.uiState.value
        assertEquals(prices, state.prices)
        assertFalse(state.isLoading)
    }
    
    @Test
    fun `error state is shown on failure`() = runTest {
        repository.setError("Network failed")
        
        advanceUntilIdle()
        
        assertEquals("Network failed", viewModel.uiState.value.error)
    }
    
    @Test
    fun `changing symbols restarts observation`() = runTest {
        val symbols = mutableListOf("BTC")
        repository.observeSymbols(symbols)
        
        viewModel.setSymbols(listOf("BTC", "ETH"))
        
        assertEquals(listOf("BTC", "ETH"), repository.lastObservedSymbols)
    }
}

// Fake repository for ViewModel tests
class FakeTradingRepository : TradingRepository {
    private val pricesFlow = MutableStateFlow<NetworkResult<List<PriceEntity>>>(
        NetworkResult.Loading
    )
    var lastObservedSymbols: List<String> = emptyList()
    
    override fun observePriceUpdates(symbols: List<String>): Flow<NetworkResult<List<PriceEntity>>> {
        lastObservedSymbols = symbols
        return pricesFlow
    }
    
    fun emitPrices(prices: List<PriceEntity>) {
        pricesFlow.value = NetworkResult.Success(prices)
    }
    
    fun setError(message: String) {
        pricesFlow.value = NetworkResult.Error(message)
    }
}
```

---

## 6. Room Database Testing

```kotlin
@RunWith(AndroidJUnit4::class)
@HiltAndroidTest
class PriceDaoTest {
    @get:Rule
    var hiltRule = HiltAndroidRule(this)
    
    @get:Rule
    var instantTaskExecutorRule = InstantTaskExecutorRule()
    
    private lateinit var database: TradingDatabase
    private lateinit var dao: PriceDao
    
    @Before
    fun setup() {
        // Use in-memory database for testing
        database = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            TradingDatabase::class.java
        )
        .allowMainThreadQueries() // OK for tests
        .build()
        
        dao = database.priceDao()
    }
    
    @After
    fun tearDown() {
        database.close()
    }
    
    @Test
    fun insertAndRetrievePrice() = runTest {
        val price = PriceEntity("BTC", "50000", 1.0, System.currentTimeMillis())
        
        dao.insertPrice(price)
        
        val result = dao.getLatestPrices(listOf("BTC")).first()
        
        assertEquals(1, result.size)
        assertEquals("BTC", result[0].symbol)
        assertEquals("50000", result[0].price)
    }
    
    @Test
    fun observeFlowEmitsOnChange() = runTest {
        val price1 = PriceEntity("BTC", "50000", 1.0, System.currentTimeMillis())
        val price2 = PriceEntity("BTC", "51000", 1.5, System.currentTimeMillis())
        
        dao.getLatestPrices(listOf("BTC")).test {
            // Empty initially
            assertEquals(emptyList<PriceEntity>(), awaitItem())
            
            // Insert first
            dao.insertPrice(price1)
            assertEquals(listOf(price1), awaitItem())
            
            // Update (insert replaces)
            dao.insertPrice(price2)
            assertEquals(listOf(price2), awaitItem())
        }
    }
    
    @Test
    fun purgeRemovesOldPrices() = runTest {
        val oldTime = System.currentTimeMillis() - 100000
        val oldPrice = PriceEntity("BTC", "40000", 1.0, oldTime, oldTime)
        val newPrice = PriceEntity("ETH", "3000", 1.0, System.currentTimeMillis())
        
        dao.insertPrice(oldPrice)
        dao.insertPrice(newPrice)
        
        dao.purgeOld(System.currentTimeMillis() - 50000)
        
        val allBtc = dao.getLatestPrices(listOf("BTC")).first()
        val allEth = dao.getLatestPrices(listOf("ETH")).first()
        
        assertTrue(allBtc.isEmpty())
        assertTrue(allEth.isNotEmpty())
    }
}
```

---

## 7. Compose UI Testing

```kotlin
@HiltAndroidTest
class TradeScreenTest {
    @get:Rule(order = 0)
    var hiltRule = HiltAndroidRule(this)
    
    @get:Rule(order = 1)
    val composeRule = createAndroidComposeRule<HiltTestActivity>()
    
    @Inject
    lateinit var repository: TradingRepository
    
    @Before
    fun setup() {
        hiltRule.inject()
    }
    
    @Test
    fun displaysLoadingStateInitially() {
        composeRule.setContent {
            TradingDashboard()
        }
        
        composeRule.onNodeWithTag("loading_indicator").assertExists()
    }
    
    @Test
    fun displaysPricesWhenLoaded() = runTest {
        // Pre-populate data
        val testPrices = listOf(
            PriceEntity("BTC", "50000", 1.0, System.currentTimeMillis()),
            PriceEntity("ETH", "3000", 1.0, System.currentTimeMillis())
        )
        
        // Inject test data
        (repository as? FakeTradingRepository)?.emitPrices(testPrices)
        
        composeRule.setContent {
            TradingDashboard()
        }
        
        // Wait for composition
        composeRule.waitForIdle()
        
        // Assert prices are displayed
        composeRule.onNodeWithText("$50,000.00").assertExists()
        composeRule.onNodeWithText("$3,000.00").assertExists()
    }
    
    @Test
    fun priceCardClickOpensDetail() {
        composeRule.setContent {
            TradingDashboard(onPriceClick = { symbol ->
                // Navigate or show detail
            })
        }
        
        composeRule.onNodeWithText("BTC").performClick()
        
        composeRule.onNodeWithTag("price_detail_sheet").assertExists()
    }
    
    @Test
    fun pullToRefreshTriggersReload() {
        composeRule.setContent {
            TradingDashboard()
        }
        
        composeRule.onNodeWithTag("price_list")
            .performTouchInput { swipeDown() }
        
        // Verify refresh indicator
        composeRule.onNodeWithTag("refresh_indicator").assertExists()
    }
}

// Test Activity for Hilt injection
@HiltAndroidApp
class TestApplication : Application()

@AndroidEntryPoint
class HiltTestActivity : ComponentActivity()
```

---

## 8. Test Utilities

```kotlin
// Turbine for cleaner Flow testing (alternative to .test {})
// Dependency: testImplementation("app.cash.turbine:turbine:1.0.0")

@Test
fun `emits states in order with Turbine`() = runTest {
    val viewModel = createViewModel()
    
    viewModel.uiState.test {
        assertEquals(UiState.Loading, awaitItem())
        assertEquals(UiState.Success(emptyList()), awaitItem())
        
        // Trigger update
        fakeRepository.emitPrices(listOf(testPrice))
        
        assertEquals(UiState.Success(listOf(testPrice)), awaitItem())
        cancel()
    }
}

// Custom matchers
fun hasPrice(expected: String): SemanticsMatcher =
    SemanticsMatcher.expectValue(PriceKey, expected)

// Screenshot testing (optional)
@Test
fun priceCardMatchesReference() {
    composeRule.setContent {
        PriceCard(symbol = "BTC", price = BigDecimal("50000"))
    }
    
    composeRule.onRoot().captureToImage().asAndroidBitmap().apply {
        // Compare with reference image
    }
}
```

---

## 9. Test Coverage Goals

| Layer | Coverage Target | Key Metrics |
|-------|-----------------|-------------|
| Repository | 90%+ | All error paths, caching logic |
| ViewModel | 85%+ | State transitions, user actions |
| Use Cases | 95%+ | Business logic, edge cases |
| UI | 60%+ | Critical user journeys |
| Database | 80%+ | Migrations, complex queries |

---

## 10. CI/CD Configuration

```yaml
# .github/workflows/test.yml
name: Android Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run unit tests
        run: ./gradlew testDebugUnitTest
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run instrumented tests
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 30
          script: ./gradlew connectedCheck
```

---

## TL;DR

**Unit Tests:**
- Use fakes, not mocks, for dependencies
- `MainDispatcherRule` for coroutine tests
- `runTest { }` for structured concurrency

**Integration Tests:**
- Room: `inMemoryDatabaseBuilder()`
- Repository: Test with real DAO + fake API

**UI Tests:**
- Test behavior, not implementation
- Use semantics for assertions
- `@HiltAndroidTest` for DI

**Dependencies:**
- Turbine for Flow testing
- Truth for assertions
- MockK for mocking (sparingly)
