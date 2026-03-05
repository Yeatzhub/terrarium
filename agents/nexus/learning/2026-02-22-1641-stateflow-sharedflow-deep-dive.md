# StateFlow vs SharedFlow - The Definitive Guide

## When to Use What

| Use Case | Best Choice | Why |
|----------|-------------|-----|
| UI state (screen data) | `StateFlow` | Always has value, `collectAsStateWithLifecycle()` |
| Events (show toast) | `SharedFlow` | Fire-and-forget, no replay for late subscribers |
| One-time actions (navigation) | `SharedFlow` | Don't replay to new observers |
| Form validation state | `StateFlow` | Need current value immediately |
| WebSocket messages | `SharedFlow` | Stream, no initial value needed |
| Search results | `StateFlow` | UI needs latest results |

## StateFlow - The State Holder

```kotlin
// StateFlow ALWAYS has a value - never null
private val _state = MutableStateFlow<UiState>(UiState.Loading)
val state: StateFlow<UiState> = _state.asStateFlow()

// Key characteristics:
// 1. Must have initial value
// 2. replay = 1 (new subscribers get last value)
// 3. Value-based equality (distinctUntilChanged built-in)
// 4. Thread-safe by default

// In ViewModel
@HiltViewModel
class SearchViewModel @Inject constructor(
    private val repository: SearchRepository
) : ViewModel() {
    
    private val _query = MutableStateFlow("")
    private val _state = MutableStateFlow<SearchState>(SearchState.Empty)
    
    // Expose as immutable
    val state: StateFlow<SearchState> = _state.asStateFlow()
    
    init {
        viewModelScope.launch {
            _query
                .debounce(300)
                .filter { it.length >= 2 }
                .flatMapLatest { query ->
                    repository.search(query)
                        .catch { emit(SearchState.Error(it.message)) }
                }
                .collect { _state.value = it }
        }
    }
    
    fun setQuery(query: String) {
        _query.value = query  // Always synchronous, thread-safe
    }
}

// In Compose
@Composable
fun SearchScreen(viewModel: SearchViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    // state is NEVER null, always the latest value
}
```

## SharedFlow - The Event Stream

```kotlin
// SharedFlow is CONFIGURABLE - no value required
private val _events = MutableSharedFlow<UiEvent>()
val events: SharedFlow<UiEvent> = _events.asSharedFlow()

// Key characteristics:
// 1. No initial value required
// 2. Configurable replay, buffer, onBufferOverflow
// 3. Reference-based equality (no distinctUntilChanged)
// 4. Hot flow - active regardless of collectors

// Event patterns
sealed interface UiEvent {
    data class ShowToast(val message: String) : UiEvent
    data class Navigate(val route: String) : UiEvent
    data class ShowSnackbar(val message: String, val action: String?) : UiEvent
}

@HiltViewModel
class OrderViewModel @Inject constructor(
    private val repository: OrderRepository
) : ViewModel() {
    
    // Events: fire-and-forget, no replay for new subscribers
    private val _events = MutableSharedFlow<UiEvent>(extraBufferCapacity = 1)
    val events: SharedFlow<UiEvent> = _events.asSharedFlow()
    
    // State: always current
    private val _state = MutableStateFlow<OrderState>(OrderState.Loading)
    val state: StateFlow<OrderState> = _state.asStateFlow()
    
    fun submitOrder() {
        viewModelScope.launch {
            repository.submitOrder()
                .onSuccess {
                    // Emit event - won't replay if collector wasn't ready
                    _events.emit(UiEvent.Navigate("order/confirmation"))
                }
                .onFailure {
                    _events.emit(UiEvent.ShowToast("Order failed: ${it.message}"))
                }
        }
    }
}

// In Compose - collect events ONCE in LaunchedEffect
@Composable
fun OrderScreen(viewModel: OrderViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    
    // Event collection - must use LaunchedEffect
    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is UiEvent.ShowToast -> { /* show toast */ }
                is UiEvent.Navigate -> navController.navigate(event.route)
                is UiEvent.ShowSnackbar -> { /* show snackbar */ }
            }
        }
    }
}
```

## SharedFlow Configuration Deep Dive

```kotlin
// replay: how many past values to emit to new collectors
MutableSharedFlow<Int>(
    replay = 0,    // Default: no replay (events)
    // replay = 1,  // Like StateFlow but without initial value
    // replay = 3,  // Last 3 values to new collectors
)

// extraBufferCapacity: suspend vs drop
MutableSharedFlow<Int>(
    replay = 1,
    extraBufferCapacity = 0,  // emit() suspends if no collector is ready
    // extraBufferCapacity = 64,  // Buffer 64 items before suspending
)

// onBufferOverflow: what to do when buffer is full
MutableSharedFlow<Int>(
    replay = 1,
    extraBufferCapacity = 64,
    onBufferOverflow = BufferOverflow.SUSPEND,  // Default
    // onBufferOverflow = BufferOverflow.DROP_OLDEST,  // Drop old, keep new
    // onBufferOverflow = BufferOverflow.DROP_LATEST,  // Drop new
)

// Common configurations:

// 1. Events (navigation, toasts) - fire-and-forget
MutableSharedFlow<Event>(replay = 0, extraBufferCapacity = 1)

// 2. WebSocket stream - hot, buffered
MutableSharedFlow<Message>(
    replay = 1,
    extraBufferCapacity = 64,
    onBufferOverflow = BufferOverflow.DROP_OLDEST
)

// 3. Ticker/heartbeat - always latest
MutableSharedFlow<Tick>(
    replay = 1,
    extraBufferCapacity = 0,
    onBufferOverflow = BufferOverflow.DROP_OLDEST
)
```

## The Channel Alternative for Events

```kotlin
// For guaranteed delivery (navigation events on config change)
private val _navigation = Channel<NavigationEvent>()
val navigation: ReceiveChannel<NavigationEvent> = _navigation

// In ViewModel
fun onOrderComplete() {
    viewModelScope.launch {
        _navigation.send(NavigationEvent.ToConfirmation(orderId))
    }
}

// In Compose - Channel is bufferable and survives config change
LaunchedEffect(Unit) {
    for (event in viewModel.navigation) {
        navController.navigate(event.route)
    }
}

// Channel vs SharedFlow for events:
// Channel: Guaranteed delivery, FIFO, survives rotation
// SharedFlow: May miss if no collector, supports multiple collectors
```

## Converting Between Types

```kotlin
// Flow → StateFlow
val stateFlow: StateFlow<User> = repository.observeUser()
    .stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = User.Empty
    )

// Flow → SharedFlow
val sharedFlow: SharedFlow<Event> = repository.events()
    .shareIn(
        scope = viewModelScope,
        started = SharingStarted.Eagerly,  // Start immediately
        replay = 0  // No replay
    )

// StateFlow → Flow (for transformations)
val derivedState = stateFlow
    .map { it.toUiModel() }
    .stateIn(viewModelScope, SharingStarted.Lazily, UiModel.Empty)
```

## shareIn vs stateIn Decision Tree

```
Need initial value available immediately?
├─ YES → stateIn()
│   └─ SharingStarted.WhileSubscribed(5_000)  // Lifecycle-aware
│   └─ SharingStarted.Lazily                   // Start on first subscriber
│   └─ SharingStarted.Eagerly                  // Always on
│
└─ NO → Need multiple collectors to share same stream?
    ├─ YES → shareIn()
    │   └─ replay = 0 (events) or 1 (latest value)
    │
    └─ NO → Just use cold Flow
```

## Common Mistakes

```kotlin
// ❌ Wrong: Using StateFlow for navigation events
private val _navEvent = MutableStateFlow<NavEvent?>(null)
val navEvent = _navEvent.asStateFlow()

// Problem: New subscriber gets last navigation event!
// Solution: Use SharedFlow or Channel

// ✅ Correct:
private val _navEvent = MutableSharedFlow<NavEvent>(extraBufferCapacity = 1)
val navEvent = _navEvent.asSharedFlow()


// ❌ Wrong: collectIn Compose without lifecycle
LaunchedEffect(events) {
    viewModel.events.collect { ... }  // Collects even in background!
}

// ✅ Correct:
viewModel.events.collectAsStateWithLifecycle()  // Lifecycle-aware


// ❌ Wrong: Trying to emit synchronously to SharedFlow with no buffer
private val _events = MutableSharedFlow<Event>()  // buffer = 0

fun sendEvent() {
    _events.tryEmit(Event())  // May fail silently!
}

// ✅ Correct:
private val _events = MutableSharedFlow<Event>(extraBufferCapacity = 1)

// Or use emit() in coroutine scope:
fun sendEvent() = viewModelScope.launch {
    _events.emit(Event())  // Suspends until collected
}
```

## Practical ViewModel Template

```kotlin
@HiltViewModel
class ProductsViewModel @Inject constructor(
    private val repository: ProductRepository
) : ViewModel() {
    
    // === STATE (always has value, survives rotation) ===
    private val _state = MutableStateFlow<UiState>(UiState.Loading)
    val state: StateFlow<UiState> = _state.asStateFlow()
    
    // === EVENTS (one-time, fire-and-forget) ===
    private val _events = MutableSharedFlow<Event>(extraBufferCapacity = 1)
    val events: SharedFlow<Event> = _events.asSharedFlow()
    
    // === NAVIGATION (guaranteed delivery) ===
    private val _navigation = Channel<NavigationEvent>()
    val navigation: ReceiveChannel<NavigationEvent> = _navigation
    
    init {
        loadProducts()
    }
    
    private fun loadProducts() {
        viewModelScope.launch {
            _state.value = UiState.Loading
            
            repository.getProducts()
                .onSuccess { products ->
                    _state.value = UiState.Success(products)
                    _events.emit(Event.ShowToast("Loaded ${products.size} products"))
                }
                .onFailure { error ->
                    _state.value = UiState.Error(error.message)
                    _events.emit(Event.ShowRetrySnackbar(error.message))
                }
        }
    }
    
    fun onProductClick(id: String) {
        viewModelScope.launch {
            _navigation.send(NavigationEvent.ToDetails(id))
        }
    }
    
    fun onRetry() {
        loadProducts()
    }
    
    // Sealed interfaces for type safety
    sealed interface UiState {
        data object Loading : UiState
        data class Success(val products: List<Product>) : UiState
        data class Error(val message: String?) : UiState
    }
    
    sealed interface Event {
        data class ShowToast(val message: String) : Event
        data class ShowRetrySnackbar(val message: String?) : Event
    }
    
    sealed interface NavigationEvent {
        data class ToDetails(val id: String) : NavigationEvent
    }
}
```

## Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│  StateFlow                    │  SharedFlow                  │
├─────────────────────────────────────────────────────────────┤
│  - Always has value           │  - No initial value needed   │
│  - replay = 1 fixed           │  - Configurable replay       │
│  - Value equality             │  - Reference equality        │
│  - UI state, form data        │  - Events, navigation        │
│  - collectAsStateWith...()    │  - LaunchedEffect.collect{}  │
│  - stateIn() to convert       │  - shareIn() to convert      │
├─────────────────────────────────────────────────────────────┤
│  When in doubt:                                             │
│  - Need current value NOW? → StateFlow                     │
│  - Need to notify once?     → SharedFlow (replay=0)        │
│  - Need guaranteed delivery? → Channel                     │
└─────────────────────────────────────────────────────────────┘
```

---
*Learned: 2026-02-22 16:41 | Focus: StateFlow vs SharedFlow decision guide, event patterns, configuration deep dive*