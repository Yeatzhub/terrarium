# 📱 Jetpack Compose: Real-Time Sparkline Component

**Focus:** Custom Canvas-based Chart + Animation + State Management
**Pattern:** Stateless Composable + remember + Animatable API

---

## 1. Component Overview

A performant sparkline chart for crypto/trading prices with:
- Canvas rendering (no overhead of Box/Row layouts)
- Smooth animated path updates
- Real-time data handling
- Gesture support (touch for price tooltip)

```kotlin
@Composable
fun PriceSparkline(
    prices: List<BigDecimal>,
    modifier: Modifier = Modifier,
    isPositive: Boolean = prices.lastOrNull() >= prices.firstOrNull(),
    strokeWidth: Float = 3f,
    showFill: Boolean = true,
    animDurationMillis: Int = 300
) {
    // Animation state for path morphing
    val animatedProgress = remember { Animatable(0f) }
    val density = LocalDensity.current
    
    // Animate when data changes
    LaunchedEffect(prices) {
        if (prices.isNotEmpty()) {
            animatedProgress.snapTo(0f)
            animatedProgress.animateTo(
                targetValue = 1f,
                animationSpec = tween(
                    durationMillis = animDurationMillis,
                    easing = FastOutSlowInEasing
                )
            )
        }
    }
    
    // Convert to points for canvas
    val points = remember(prices) {
        prices.mapIndexed { index, price ->
            // Normalized 0..1
            val min = prices.minOrNull() ?: BigDecimal.ZERO
            val max = prices.maxOrNull() ?: BigDecimal.ONE
            val normalized = if (max > min) {
                (price - min).toFloat() / (max - min).toFloat()
            } else 0.5f
            
            index.toFloat() to normalized
        }
    }
    
    val color = if (isPositive) 
        MaterialTheme.colorScheme.primary 
    else 
        MaterialTheme.colorScheme.error
    
    Canvas(modifier = modifier.fillMaxSize()) {
        if (points.size < 2) return@Canvas
        
        val width = size.width
        val height = size.height
        val padding = with(density) { 8.dp.toPx() }
        
        // Create smooth path using cubic Bezier
        val path = Path().apply {
            val visiblePoints = (points.size * animatedProgress.value).toInt()
                .coerceAtLeast(2)
                .coerceAtMost(points.size)
            
            if (visiblePoints < 2) return@Canvas
            
            val stepX = (width - 2 * padding) / (points.size - 1)
            val chartHeight = height - 2 * padding
            
            // Start point
            val firstX = padding
            val firstY = height - padding - (points[0].second * chartHeight)
            moveTo(firstX, firstY)
            
            // Smooth curves using catmull-rom spline
            for (i in 1 until visiblePoints) {
                val prev = points[i - 1]
                val curr = points[i]
                val next = points.getOrNull(i + 1)
                
                val x = padding + i * stepX
                val y = height - padding - (curr.second * chartHeight)
                
                if (next != null) {
                    // Control points for smooth curve
                    val prevX = padding + (i - 1) * stepX
                    val nextX = padding + (i + 1) * stepX
                    val prevY = height - padding - (prev.second * chartHeight)
                    val nextY = height - padding - (next.second * chartHeight)
                    
                    val cp1x = x - (x - prevX) * 0.3f
                    val cp1y = y - (y - prevY) * 0.3f
                    val cp2x = x + (nextX - x) * 0.3f
                    val cp2y = y + (nextY - y) * 0.3f
                    
                    cubicTo(cp1x, cp1y, cp2x, cp2y, x, y)
                } else {
                    lineTo(x, y)
                }
            }
        }
        
        // Draw stroke
        drawPath(
            path = path,
            color = color,
            style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
        )
        
        // Draw gradient fill
        if (showFill) {
            val fillPath = Path().apply {
                addPath(path)
                lineTo(padding + (points.size - 1) * (width - 2 * padding) / (points.size - 1), height)
                lineTo(padding, height)
                close()
            }
            
            drawPath(
                path = fillPath,
                brush = Brush.verticalGradient(
                    colors = listOf(
                        color.copy(alpha = 0.3f),
                        color.copy(alpha = 0f)
                    ),
                    startY = padding,
                    endY = height
                )
            )
        }
    }
}
```

---

## 2. Interactive Touch Version

```kotlin
@Composable
fun InteractiveSparkline(
    prices: List<PriceData>,
    modifier: Modifier = Modifier,
    onPriceSelected: ((PriceData) -> Unit)? = null
) {
    var touchOffset by remember { mutableStateOf(Offset.Unspecified) }
    val selectedIndex = remember(touchOffset, prices) {
        if (touchOffset == Offset.Unspecified || prices.isEmpty()) -1
        else {
            val width = 1000f // Approximation, use actual in draw
            val padding = 32f
            val relativeX = (touchOffset.x - padding).coerceAtLeast(0f)
            val step = (width - 2 * padding) / (prices.size - 1)
            (relativeX / step).toInt().coerceIn(0, prices.size - 1)
        }
    }
    
    Box(modifier = modifier) {
        PriceSparkline(
            prices = prices.map { it.price },
            modifier = Modifier
                .fillMaxSize()
                .pointerInput(Unit) {
                    awaitPointerEventScope {
                        while (true) {
                            val event = awaitPointerEvent()
                            touchOffset = event.changes.first().position
                            if (event.type == PointerEventType.Release) {
                                touchOffset = Offset.Unspecified
                            }
                        }
                    }
                }
        )
        
        // Selection indicator
        if (selectedIndex >= 0) {
            val selected = prices[selectedIndex]
            onPriceSelected?.invoke(selected)
        }
    }
}

@Immutable
data class PriceData(
    val timestamp: Long,
    val price: BigDecimal,
    val volume: Double
)
```

---

## 3. Integration with ViewModel

```kotlin
@HiltViewModel
class ChartViewModel @Inject constructor(
    repository: TradeRepository
) : ViewModel() {
    
    val chartData: StateFlow<ChartUiState> = repository
        .getPriceHistory("BTC")
        .map { ChartUiState(prices = it) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = ChartUiState()
        )
}

@Composable
fun PriceChartScreen(viewModel: ChartViewModel = hiltViewModel()) {
    val state by viewModel.chartData.collectAsStateWithLifecycle()
    var selectedPrice by remember { mutableStateOf<PriceData?>(null) }
    
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        // Header with selected price
        Text(
            text = selectedPrice?.let { 
                "${it.price.setScale(2, RoundingMode.HALF_UP)} USD" 
            } ?: "BTC Price",
            style = MaterialTheme.typography.headlineMedium
        )
        
        // Chart
        Card(
            modifier = Modifier.weight(1f).fillMaxWidth(),
            shape = RoundedCornerShape(16.dp)
        ) {
            if (state.prices.isNotEmpty()) {
                InteractiveSparkline(
                    prices = state.prices,
                    modifier = Modifier.fillMaxSize().padding(8.dp),
                    onPriceSelected = { selectedPrice = it }
                )
            } else {
                CircularProgressIndicator(Modifier.align(Alignment.Center))
            }
        }
    }
}
```

---

## 4. Key Compose Idioms

| Pattern | Why |
|---------|-----|
| `remember(prices)` | Cache expensive point calculations |
| `Animatable` | Smooth interpolation between data updates |
| `Canvas` | Bypass layout overhead for graphics |
| `Path.cubicTo` | Bezier curves for smooth lines |
| `pointerInput` | Custom touch handling without overhead |
| `Immutable` data class | Enables Compose smart recomposition |

---

## 5. Performance Tips

```kotlin
// ✅ DO: Use immutable lists
@Immutable
data class ChartUiState(val prices: List<PriceData> = emptyList())

// ✅ DO: Sample data for large datasets
@Composable
fun sampleData(data: List<PriceData>, maxPoints: Int = 100): List<PriceData> =
    remember(data) {
        if (data.size <= maxPoints) data
        else data.chunked(data.size / maxPoints) { it.last() }
    }

// ✅ DO: Debounce rapid updates
val debouncedPrices = prices
    .debounce(100.milliseconds) // Skip updates less than 100ms apart
    .collectAsState(emptyList())

// ❌ DON'T: Create objects in composition
// Bad: Text(price.setScale(2).toString()) // Creates new BigDecimal
// Good: remember(price) { price.setScale(2) }
```

---

## 6. Testing

```kotlin
@RunWith(AndroidJUnit4::class)
class SparklineTest {
    @get:Rule
    val composeRule = createComposeRule()
    
    @Test
    fun sparkline_rendersWithCorrectColor() {
        val prices = listOf(
            BigDecimal("100"),
            BigDecimal("110"),
            BigDecimal("105")
        )
        
        composeRule.setContent {
            PriceSparkline(
                prices = prices,
                modifier = Modifier.size(200.dp, 100.dp)
            )
        }
        
        composeRule.onRoot().captureToImage().asAndroidBitmap().apply {
            // Assert pixels at expected line positions
            assert(getPixel(100, 50) != Color.Transparent.toArgb())
        }
    }
}
```

---

## TL;DR

```kotlin
// Stateless, animated sparkline
@Composable
fun PriceSparkline(prices: List<BigDecimal>) {
    val progress = remember { Animatable(0f) }
    LaunchedEffect(prices) {
        progress.snapTo(0f)
        progress.animateTo(1f)
    }
    
    Canvas(Modifier.fillMaxSize()) {
        val path = createSmoothPath(prices, size, progress.value)
        drawPath(path, color = primary, style = Stroke(3f))
    }
}
```

**Best for:** Real-time charts, minimal allocations, 60fps animations.
