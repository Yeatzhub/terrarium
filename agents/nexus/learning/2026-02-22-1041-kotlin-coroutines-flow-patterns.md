# Kotlin Coroutines & Flow - Production Patterns

## Overview
Practical patterns for real-world coroutine usage in Android apps.

## 1. Structured Concurrency with SupervisorJob

```kotlin
class SyncManager @Inject constructor(
    private val api: ApiService,
    private val dao: SyncDao
) {
    // Children fail independently (one crash doesn't kill siblings)
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    
    fun syncAll() {
        scope.launch {
            // These run in parallel, failure of one doesn't cancel others
            listOf(
                async { syncUsers() },
                async { syncOrders() },
                async { syncProducts() }
            ).awaitAll() // Wait for all, collect any exceptions
                .onSuccess { Log.d("Sync", "All completed") }
                .onFailure { Log.e("Sync", "Some failed", it) }
        }
    }
    
    fun cancel() = scope.cancel() // Clean shutdown
}
```

## 2. Flow Operators Cheat Sheet

```kotlin
// Transform & Filter
prices
    .map { it * 1.1 }                    // Transform each
    .filter { it > 100 }                 // Keep matching
    .filterNot { it.isNaN() }            // Exclude matching
    .distinctUntilChanged()              // Skip duplicates in sequence
    .scan(initial = 0.0) { acc, p -> acc + p } // Running accumulation
    
// Combine Multiple Flows
combine(flowA, flowB) { a, b -> a + b }  // Latest from both
merge(flowA, flowB)                      // All emissions interleaved
flowA.zip(flowB) { a, b -> Pair(a,b) }   // Pair 1st with 1st, 2nd with 2nd
flattenMerge(concurrency = 4) { flowOfFlows } // Parallel collection

// Buffering & Throttling
shareIn(scope, SharingStarted.Eagerly)  // Hot flow, multicast
buffer(capacity = 64)                     // Backpressure buffer
conflate()                                // Keep only latest
debounce(300.milliseconds)               // Wait for pause
throttleFirst(1.seconds)                 // Max 1 emission per second
sample(100.milliseconds)                  // Emit latest periodically
```

## 3. Error Recovery Patterns

```kotlin
class Repository @Inject constructor(
    private val api: ApiService,
    private val dao: CacheDao
) {
    // Pattern 1: Retry with exponential backoff
    fun fetchWithRetry(id: String): Flow<Result<Data>> = flow {
        emit(api.fetch(id))
    }
        .retry(3) { attempt, error ->
            if (error is IOException && attempt < 3) {
                delay(2.0.pow(attempt) * 1000) // 1s, 2s, 4s
                true // Retry
            } else false
        }
        .catch { emit(Result.failure(it)) }
    
    // Pattern 2: Fallback to cache
    fun observe(id: String): Flow<Data> = flow {
        emit(api.stream(id))
    }
        .catch { e ->
            Log.w("Repo", "API failed, using cache", e)
            emitAll(dao.observe(id))
        }
    
    // Pattern 3: Circuit breaker
    private val failures = AtomicInteger(0)
    
    fun protectedFetch(): Flow<Data> = flow {
        if (failures.get() >= 5) {
            throw CircuitBreakerOpen()
        }
        try {
            emit(api.fetch())
            failures.set(0)
        } catch (e: IOException) {
            if (failures.incrementAndGet() >= 5) {
                Log.w("Circuit", "Opening circuit after 5 failures")
            }
            throw e
        }
    }
}
```

## 4. ViewModel Coroutine Patterns

```kotlin
@HiltViewModel
class OrdersViewModel @Inject constructor(
    private val repository: OrderRepository
) : ViewModel() {
    
    // Pattern 1: One-shot action with loading state
    private val _uiState = MutableStateFlow<UiState>(UiState.Idle)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()
    
    fun loadOrders(userId: String) {
        viewModelScope.launch {
            _uiState.value = UiState.Loading
            repository.getOrders(userId)
                .onSuccess { _uiState.value = UiState.Success(it) }
                .onFailure { _uiState.value = UiState.Error(it.message) }
        }
    }
    
    // Pattern 2: Continuous stream with lifecycle awareness
    val liveOrders: StateFlow<List<Order>> = repository
        .observeOrders()
        .map { it.sortedByDescending(Order::timestamp) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = emptyList()
        )
    
    // Pattern 3: Parallel loading with Combine
    private val userId = MutableStateFlow<String?>(null)
    
    val dashboard: StateFlow<Dashboard> = userId
        .filterNotNull()
        .flatMapLatest { uid ->
            combine(
                repository.observeOrders(uid),
                repository.observeBalance(uid),
                repository.observeAlerts(uid)
            ) { orders, balance, alerts ->
                Dashboard(orders, balance, alerts)
            }
        }
        .stateIn(viewModelScope, SharingStarted.Lazily, Dashboard.Empty)
    
    // Pattern 4: Processing queue
    private val actionQueue = Channel<UserAction>(capacity = Channel.UNLIMITED)
    
    init {
        viewModelScope.launch {
            actionQueue
                .receiveAsFlow()
                .throttleFirst(500.milliseconds) // Rate limit
                .collect { action -> processAction(action) }
        }
    }
    
    fun submit(action: UserAction) {
        actionQueue.trySend(action)
    }
}
```

## 5. Testing Coroutines

```kotlin
@Test
fun `observeOrders combines multiple sources`() = runTest {
    // Given
    val orders = MutableStateFlow(listOf(Order("1")))
    val balance = MutableStateFlow(Balance(100.0))
    
    val repository = mock<OrderRepository> {
        on { observeOrders(any()) } doReturn orders
        on { observeBalance(any()) } doReturn balance
    }
    
    // When
    val viewModel = OrdersViewModel(repository)
    advanceUntilIdle()
    
    // Then
    val state = viewModel.dashboard.value
    assertEquals(1, state.orders.size)
    assertEquals(100.0, state.balance.amount)
}

@Test
fun `retry with backoff succeeds on third attempt`() = runTest {
    val api = mock<ApiService>()
    var attempts = 0
    
    whenever(api.fetch(any())).thenAnswer {
        if (++attempts < 3) throw IOException("Network error")
        Result.success(Data())
    }
    
    val repo = Repository(api, mock())
    val results = repo.fetchWithRetry("123").toList()
    
    assertEquals(3, attempts)
    assertTrue(results.first().isSuccess)
}
```

## 6. Dispatchers Best Practice

```kotlin
// Injectable dispatchers for testing
class Repository @Inject constructor(
    private val api: ApiService,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher
) {
    fun loadData(): Flow<Data> = flow {
        emit(api.fetch())
    }.flowOn(ioDispatcher)
}

// Dagger module
@Module
@InstallIn(SingletonComponent::class)
object CoroutinesModule {
    @Provides @IoDispatcher
    fun provideIoDispatcher(): CoroutineDispatcher = Dispatchers.IO
    
    @Provides @DefaultDispatcher
    fun provideDefaultDispatcher(): CoroutineDispatcher = Dispatchers.Default
}

// Test dispatcher
@Test
fun test() = runTest {
    val testDispatcher = StandardTestDispatcher(testScheduler)
    val repo = Repository(mock(), testDispatcher)
    // Predictable, controllable execution
}
```

## Quick Reference Table

| Need | Solution |
|------|----------|
| Parallel execution | `async { }` + `awaitAll()` |
| Sequential execution | `launch { }` blocks (in order) |
| Cancel dependent jobs | `withContext(NonCancellable)` |
| Hot flow, multi-subscriber | `shareIn(...)` |
| Latest value on subscribe | `stateIn(..., replay=1)` |
| Rate limit user input | `debounce()` |
| Limit API calls | `throttleFirst()` |
| Retry on failure | `.retry(n) { condition }` |
| Fallback on error | `.catch { emit(fallback) }` |
| Parallel Flow merge | `flattenMerge(concurrency=n)` |

## Anti-Patterns to Avoid

```kotlin
// ❌ GlobalScope - leaks, no lifecycle awareness
GlobalScope.launch { api.fetch() }

// ❌ launch in flow builder - unstructured
flow { launch { emit(api.fetch()) } }  // Wrong!

// ✅ Use flowOn instead
flow { emit(api.fetch()) }.flowOn(Dispatchers.IO)

// ❌ Blocking in coroutine
viewModelScope.launch {
    Thread.sleep(1000)  // Blocks thread!
}

// ✅ Use delay
viewModelScope.launch {
    delay(1000)  // Suspends, doesn't block
}
```

---
*Learned: 2026-02-22 10:41 | Focus: Structured concurrency, Flow operators, error recovery, testing patterns*