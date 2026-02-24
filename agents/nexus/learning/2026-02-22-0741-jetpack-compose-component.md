# Jetpack Compose - Custom Chart Component

## Overview
Building a reusable, performant line chart component for real-time price data.

## Complete Implementation

```kotlin
@Composable
fun PriceChart(
    data: List<PricePoint>,
    modifier: Modifier = Modifier,
    lineColor: Color = MaterialTheme.colorScheme.primary,
    gradientFillColor: Color = lineColor.copy(alpha = 0.2f),
    showGrid: Boolean = true,
    animateOnEntry: Boolean = true
) {
    // Validate data
    if (data.isEmpty()) {
        Box(modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            Text("No data", style = MaterialTheme.typography.bodyMedium)
        }
        return
    }
    
    // State-driven animation
    val transition = updateTransition(
        targetState = data,
        label = "chart-transition"
    )
    
    val animatedPoints by transition.animateValue(
        label = "points",
        typeConverter = ListConverter<PricePoint>(),
        transitionSpec = {
            if (animateOnEntry && initialState.isEmpty()) {
                tween(durationMillis = 800, easing = FastOutSlowInEasing)
            } else snap()
        }
    ) { points -> points }
    
    // Calculate bounds once
    val bounds = remember(data) {
        val prices = data.map { it.price }
        PriceBounds(
            min = prices.minOrNull() ?: 0f,
            max = prices.maxOrNull() ?: 1f,
            minTime = data.firstOrNull()?.timestamp ?: 0L,
            maxTime = data.lastOrNull()?.timestamp ?: 0L
        )
    }
    
    Canvas(
        modifier = modifier
            .fillMaxWidth()
            .height(200.dp)
            .semantics {
                contentDescription = "Price chart showing ${data.size} points"
            }
    ) {
        val widthPx = size.width
        val heightPx = size.height
        val padding = 16.dp.toPx()
        
        // Map functions
        val xMap: (Long) -> Float = { time ->
            padding + (time - bounds.minTime).toFloat() / 
                (bounds.maxTime - bounds.minTime).coerceAtLeast(1) * 
                (widthPx - 2 * padding)
        }
        val yMap: (Double) -> Float = { price ->
            heightPx - padding - 
                ((price - bounds.min) / (bounds.max - bounds.min).coerceAtLeast(0.01) * 
                (heightPx - 2 * padding)).toFloat()
        }
        
        // Draw grid
        if (showGrid) {
            repeat(5) { i ->
                val y = padding + i * (heightPx - 2 * padding) / 4
                drawLine(
                    color = Color.Gray.copy(alpha = 0.2f),
                    start = Offset(padding, y),
                    end = Offset(widthPx - padding, y),
                    strokeWidth = 1.dp.toPx()
                )
            }
        }
        
        // Build path
        val path = Path().apply {
            animatedPoints.forEachIndexed { i, point ->
                val x = xMap(point.timestamp)
                val y = yMap(point.price)
                if (i == 0) moveTo(x, y) else lineTo(x, y)
            }
        }
        
        // Gradient fill
        val fillPath = Path().apply {
            addPath(path)
            lineTo(xMap(bounds.maxTime), heightPx - padding)
            lineTo(xMap(bounds.minTime), heightPx - padding)
            close()
        }
        
        drawPath(
            path = fillPath,
            brush = Brush.verticalGradient(
                colors = listOf(gradientFillColor, Color.Transparent),
                startY = 0f,
                endY = heightPx
            )
        )
        
        // Draw line
        drawPath(
            path = path,
            color = lineColor,
            style = Stroke(width = 2.dp.toPx(), cap = StrokeCap.Round)
        )
    }
}

@Immutable
data class PricePoint(val timestamp: Long, val price: Double)

@Immutable
data class PriceBounds(
    val min: Double,
    val max: Double,
    val minTime: Long,
    val maxTime: Long
)
```

## Usage Example

```kotlin
@Composable
fun PriceScreen(viewModel: PriceViewModel = hiltViewModel()) {
    val priceHistory by viewModel.priceHistory.collectAsState()
    var animEntry by remember { mutableStateOf(true) }
    
    Surface(Modifier.fillMaxSize()) {
        Column(Modifier.padding(16.dp)) {
            Text("Price History", style = MaterialTheme.typography.headlineMedium)
            
            PriceChart(
                data = priceHistory,
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
                lineColor = when {
                    priceHistory.last().price > priceHistory.first().price -> 
                        Color(0xFF4CAF50)  // Green
                    else -> Color(0xFFF44336)  // Red
                },
                animateOnEntry = animEntry
            )
            
            // Controls
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    "Min: $${"%.2f".format(priceHistory.minOfOrNull { it.price } ?: 0)}",
                    color = MaterialTheme.colorScheme.error
                )
                Text(
                    "Max: $${"%.2f".format(priceHistory.maxOfOrNull { it.price } ?: 0)}",
                    color = MaterialTheme.colorScheme.primary
                )
            }
        }
    }
}
```

## Performance Patterns

| Issue | Solution |
|-------|----------|
| Re-composition on every update | Use `remember(data)` for calculations |
| Jerky animation | `updateTransition` + `animateValue` |
| Memory churn | `@Immutable` data classes |
| Blocking main thread | Pre-calculate bounds in `remember` |

## Interactive Variant with Touch

```kotlin
@Composable
fun InteractivePriceChart(
    data: List<PricePoint>,
    modifier: Modifier = Modifier,
    onPriceSelected: (PricePoint) -> Unit = {}
) {
    var selectedPoint by remember { mutableStateOf<PricePoint?>(null) }
    
    Box(modifier) {
        PriceChart(data = data)
        
        Canvas(
            Modifier
                .fillMaxSize()
                .pointerInput(data) {
                    detectTapGestures { offset ->
                        // Find nearest point
                        selectedPoint = findNearestPoint(offset, data)
                        selectedPoint?.let(onPriceSelected)
                    }
                }
        ) {
            selectedPoint?.let { point ->
                // Draw selection indicator
                drawCircle(
                    color = Color.White,
                    radius = 8.dp.toPx(),
                    center = Offset(
                        xMap(point.timestamp),
                        yMap(point.price)
                    )
                )
            }
        }
        
        // Tooltip
        AnimatedVisibility(
            selectedPoint != null,
            enter = fadeIn() + slideInVertically(),
            exit = fadeOut() + slideOutVertically()
        ) {
            PriceTooltip(selectedPoint!!)
        }
    }
}
```

## Preview Support

```kotlin
@Preview(showBackground = true)
@Composable
fun PriceChartPreview() {
    val sampleData = remember {
        (0..20).map { i ->
            PricePoint(
                timestamp = System.currentTimeMillis() + i * 60000,
                price = 50000 + (random() - 0.5) * 2000
            )
        }
    }
    
    MaterialTheme {
        PriceChart(
            data = sampleData,
            lineColor = Color(0xFF6200EE),
            showGrid = true,
            animateOnEntry = false
        )
    }
}
```

## Key Takeaways

1. **Canvas over custom layouts** for charts - more performant
2. **`remember` for expensive calculations** - avoid re-computation
3. **`@Immutable` annotations** - help Compose skip recomposition
4. **`updateTransition`** - smooth animated state changes
5. **Semantics** - essential for accessibility (TalkBack)

---
*Learned: 2026-02-22 07:41 | Focus: Custom Canvas-based chart with animation and touch interaction*