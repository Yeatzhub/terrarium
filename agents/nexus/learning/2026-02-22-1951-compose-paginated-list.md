# Jetpack Compose - Advanced List Component

## Overview
Production-ready paginated list with pull-to-refresh, swipe actions, and empty/error states.

## Complete Implementation

```kotlin
// Domain model
@Immutable
data class Order(
    val id: String,
    val symbol: String,
    val side: Side,
    val quantity: Double,
    val price: Double,
    val status: Status,
    val timestamp: Instant
) {
    enum class Side { BUY, SELL }
    enum class Status { PENDING, FILLED, CANCELLED }
}

// Pagination state
@Immutable
data class Page<T>(
    val items: List<T>,
    val nextKey: String?,
    val hasMore: Boolean
)

// UI State
sealed interface OrdersUiState {
    data object Loading : OrdersUiState
    data class Success(
        val orders: List<Order>,
        val hasMore: Boolean,
        val isLoadingMore: Boolean = false,
        val isRefreshing: Boolean = false
    ) : OrdersUiState
    data class Error(val message: String) : OrdersUiState
}
```

## ViewModel with Pagination

```kotlin
@HiltViewModel
class OrdersViewModel @Inject constructor(
    private val repository: OrderRepository
) : ViewModel() {
    
    private var nextPageKey: String? = null
    private var isLoadingMore = false
    
    private val _state = MutableStateFlow<OrdersUiState>(OrdersUiState.Loading)
    val state: StateFlow<OrdersUiState> = _state.asStateFlow()
    
    private val _events = MutableSharedFlow<Event>(extraBufferCapacity = 1)
    val events: SharedFlow<Event> = _events.asSharedFlow()
    
    sealed interface Event {
        data class ShowUndo(val orderId: String) : Event
        data class ShowError(val message: String) : Event
    }
    
    init {
        loadInitial()
    }
    
    fun loadInitial() {
        viewModelScope.launch {
            _state.value = OrdersUiState.Loading
            repository.getOrders(pageSize = 20)
                .onSuccess { page ->
                    nextPageKey = page.nextKey
                    _state.value = OrdersUiState.Success(
                        orders = page.items,
                        hasMore = page.hasMore
                    )
                }
                .onFailure { error ->
                    _state.value = OrdersUiState.Error(error.message ?: "Unknown error")
                }
        }
    }
    
    fun refresh() {
        viewModelScope.launch {
            val current = _state.value as? OrdersUiState.Success ?: return@launch
            _state.value = current.copy(isRefreshing = true)
            
            repository.getOrders(pageSize = 20)
                .onSuccess { page ->
                    nextPageKey = page.nextKey
                    _state.value = OrdersUiState.Success(
                        orders = page.items,
                        hasMore = page.hasMore
                    )
                }
                .onFailure { error ->
                    _state.value = current.copy(isRefreshing = false)
                    _events.emit(Event.ShowError(error.message ?: "Refresh failed"))
                }
        }
    }
    
    fun loadMore() {
        val current = _state.value as? OrdersUiState.Success ?: return
        if (!current.hasMore || isLoadingMore || nextPageKey == null) return
        
        isLoadingMore = true
        _state.value = current.copy(isLoadingMore = true)
        
        viewModelScope.launch {
            repository.getOrders(pageSize = 20, nextKey = nextPageKey)
                .onSuccess { page ->
                    nextPageKey = page.nextKey
                    _state.value = current.copy(
                        orders = current.orders + page.items,
                        hasMore = page.hasMore,
                        isLoadingMore = false
                    )
                }
                .onFailure { error ->
                    _state.value = current.copy(isLoadingMore = false)
                    _events.emit(Event.ShowError(error.message ?: "Load failed"))
                }
            isLoadingMore = false
        }
    }
    
    fun cancelOrder(orderId: String) {
        viewModelScope.launch {
            repository.cancelOrder(orderId)
                .onSuccess {
                    _events.emit(Event.ShowUndo(orderId))
                    loadInitial() // Refresh list
                }
                .onFailure { error ->
                    _events.emit(Event.ShowError(error.message ?: "Cancel failed"))
                }
        }
    }
}
```

## Pull-to-Refresh List

```kotlin
@OptIn(ExperimentalMaterialApi::class)
@Composable
fun OrdersScreen(
    viewModel: OrdersViewModel = hiltViewModel()
) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    val snackbarHostState = remember { SnackbarHostState() }
    
    // Event handling
    LaunchedEffect(Unit) {
        viewModel.events.collect { event ->
            when (event) {
                is OrdersViewModel.Event.ShowUndo -> {
                    snackbarHostState.showSnackbar(
                        message = "Order cancelled",
                        actionLabel = "Undo",
                        duration = SnackbarDuration.Short
                    )
                }
                is OrdersViewModel.Event.ShowError -> {
                    snackbarHostState.showSnackbar(event.message)
                }
            }
        }
    }
    
    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(title = { Text("Orders") })
        }
    ) { padding ->
        when (state) {
            is OrdersUiState.Loading -> {
                Box(
                    Modifier
                        .fillMaxSize()
                        .padding(padding),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator()
                }
            }
            is OrdersUiState.Error -> {
                ErrorState(
                    message = (state as OrdersUiState.Error).message,
                    onRetry = { viewModel.loadInitial() }
                )
            }
            is OrdersUiState.Success -> {
                OrdersList(
                    state = state as OrdersUiState.Success,
                    onLoadMore = { viewModel.loadMore() },
                    onRefresh = { viewModel.refresh() },
                    onCancelOrder = { viewModel.cancelOrder(it) },
                    modifier = Modifier.padding(padding)
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterialApi::class)
@Composable
fun OrdersList(
    state: OrdersUiState.Success,
    onLoadMore: () -> Unit,
    onRefresh: () -> Unit,
    onCancelOrder: (String) -> Unit,
    modifier: Modifier = Modifier
) {
    val refreshState = rememberPullRefreshState(
        refreshing = state.isRefreshing,
        onRefresh = onRefresh
    )
    
    Box(modifier.pullRefresh(refreshState)) {
        if (state.orders.isEmpty()) {
            EmptyOrdersState(
                Modifier
                    .fillMaxSize()
                    .align(Alignment.Center)
            )
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                contentPadding = PaddingValues(16.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(
                    items = state.orders,
                    key = { it.id }
                ) { order ->
                    OrderItem(
                        order = order,
                        onCancel = { onCancelOrder(order.id) }
                    )
                }
                
                // Load more trigger
                if (state.hasMore) {
                    item {
                        LaunchedEffect(Unit) { onLoadMore() }
                        Box(
                            Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            if (state.isLoadingMore) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(24.dp),
                                    strokeWidth = 2.dp
                                )
                            }
                        }
                    }
                }
            }
        }
        
        PullRefreshIndicator(
            refreshing = state.isRefreshing,
            state = refreshState,
            modifier = Modifier.align(Alignment.TopCenter)
        )
    }
}
```

## Swipe-to-Dismiss Item

```kotlin
@OptIn(ExperimentalMaterialApi::class)
@Composable
fun OrderItem(
    order: Order,
    onCancel: () -> Unit,
    modifier: Modifier = Modifier
) {
    val dismissState = rememberDismissState(
        confirmValueChange = { value ->
            if (value == DismissValue.DismissedToStart) {
                onCancel()
                true
            } else {
                false
            }
        }
    )
    
    SwipeToDismiss(
        state = dismissState,
        modifier = modifier,
        background = {
            // Red delete background
            Box(
                Modifier
                    .fillMaxSize()
                    .background(Color.Red.copy(alpha = 0.8f))
                    .padding(horizontal = 20.dp),
                contentAlignment = Alignment.CenterEnd
            ) {
                Icon(
                    Icons.Default.Delete,
                    contentDescription = "Delete",
                    tint = Color.White,
                    modifier = Modifier.size(24.dp)
                )
            }
        },
        dismissContent = {
            OrderCard(order)
        },
        directions = setOf(DismissDirection.EndToStart)
    )
}

@Composable
fun OrderCard(order: Order) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Side indicator
            Box(
                Modifier
                    .width(4.dp)
                    .height(48.dp)
                    .background(
                        when (order.side) {
                            Order.Side.BUY -> Color(0xFF4CAF50) // Green
                            Order.Side.SELL -> Color(0xFFF44336) // Red
                        }
                    )
            )
            
            Column(
                Modifier
                    .weight(1f)
                    .padding(start = 12.dp)
            ) {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        order.symbol,
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold
                    )
                    Text(
                        "$${String.format("%.2f", order.price)}",
                        style = MaterialTheme.typography.titleMedium
                    )
                }
                
                Spacer(Modifier.height(4.dp))
                
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    Text(
                        "${order.quantity} units",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    SuggestionChip(
                        onClick = {},
                        label = { Text(order.status.name) },
                        colors = SuggestionChipDefaults.suggestionChipColors(
                            containerColor = when (order.status) {
                                Order.Status.PENDING -> Color(0xFFFFC107)
                                Order.Status.FILLED -> Color(0xFF4CAF50)
                                Order.Status.CANCELLED -> Color(0xFF9E9E9E)
                            }.copy(alpha = 0.2f)
                        )
                    )
                }
            }
        }
    }
}
```

## Empty & Error States

```kotlin
@Composable
fun EmptyOrdersState(modifier: Modifier = Modifier) {
    Column(
        modifier,
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            Icons.Outlined.Receipt,
            contentDescription = null,
            modifier = Modifier.size(80.dp),
            tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
        )
        Spacer(Modifier.height(16.dp))
        Text(
            "No orders yet",
            style = MaterialTheme.typography.titleLarge
        )
        Text(
            "Your order history will appear here",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
fun ErrorState(
    message: String,
    onRetry: () -> Unit,
    modifier: Modifier = Modifier
) {
    Column(
        modifier
            .fillMaxSize()
            .padding(32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Icon(
            Icons.Outlined.Error,
            contentDescription = null,
            modifier = Modifier.size(64.dp),
            tint = MaterialTheme.colorScheme.error
        )
        Spacer(Modifier.height(16.dp))
        Text(
            message,
            style = MaterialTheme.typography.bodyLarge,
            textAlign = TextAlign.Center
        )
        Spacer(Modifier.height(24.dp))
        FilledTonalButton(onClick = onRetry) {
            Icon(Icons.Default.Refresh, contentDescription = null)
            Spacer(Modifier.width(8.dp))
            Text("Retry")
        }
    }
}
```

## Infinite Scroll Helper

```kotlin
// Reusable pagination helper
@Composable
fun LazyListState.OnReachedEnd(
    buffer: Int = 3,
    onLoadMore: () -> Unit
) {
    val shouldLoadMore = remember {
        derivedStateOf {
            val lastVisibleItem = layoutInfo.visibleItemsInfo.lastOrNull()?.index ?: 0
            val totalItems = layoutInfo.totalItemsCount
            lastVisibleItem >= totalItems - buffer
        }
    }
    
    LaunchedEffect(shouldLoadMore.value) {
        if (shouldLoadMore.value) {
            onLoadMore()
        }
    }
}

// Usage
@Composable
fun OrdersListImproved(
    state: OrdersUiState.Success,
    onLoadMore: () -> Unit
) {
    val listState = rememberLazyListState()
    
    LazyColumn(state = listState) {
        items(state.orders, key = { it.id }) { order ->
            OrderItem(order, {})
        }
        
        if (state.isLoadingMore) {
            item {
                CircularProgressIndicator(
                    Modifier
                        .fillMaxWidth()
                        .padding(16.dp)
                        .wrapContentWidth(Alignment.CenterHorizontally)
                )
            }
        }
    }
    
    listState.OnReachedEnd(buffer = 5) {
        if (state.hasMore && !state.isLoadingMore) {
            onLoadMore()
        }
    }
}
```

## Performance Checklist

| Optimization | Implementation |
|--------------|----------------|
| Stable items | `key = { it.id }` for stable identity |
| DiffUtil | Compose handles via `items()` key |
| Lazy loading | `OnReachedEnd` helper |
| Content padding | Avoid nested scroll containers |
| Item stability | `@Immutable` data classes |
| View recycling | LazyColumn auto-handles |

---
*Learned: 2026-02-22 19:51 | Focus: Paginated list, pull-to-refresh, swipe-to-dismiss, loading states*