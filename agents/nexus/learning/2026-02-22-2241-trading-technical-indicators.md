# Mobile Trading App - Technical Indicators Pattern

## Overview
Real-time technical analysis with RSI, MACD, and moving averages in a trading app.

## Indicator Calculations (Domain Layer)

```kotlin
// Common types
@JvmInline
value class Price(val value: Double)
@JvmInline
value class Timestamp(val value: Long)

@Immutable
data class Candle(
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double,
    val volume: Double,
    val timestamp: Long
)

// RSI Calculator
object RSI {
    fun calculate(prices: List<Double>, period: Int = 14): Double? {
        if (prices.size < period + 1) return null
        
        var gains = 0.0
        var losses = 0.0
        
        // Initial average
        for (i in 1..period) {
            val change = prices[i] - prices[i - 1]
            if (change >= 0) gains += change else losses -= change
        }
        
        var avgGain = gains / period
        var avgLoss = losses / period
        
        // Smooth using Wilder's method
        for (i in (period + 1) until prices.size) {
            val change = prices[i] - prices[i - 1]
            val currentGain = if (change >= 0) change else 0.0
            val currentLoss = if (change < 0) -change else 0.0
            
            avgGain = (avgGain * (period - 1) + currentGain) / period
            avgLoss = (avgLoss * (period - 1) + currentLoss) / period
        }
        
        if (avgLoss == 0.0) return 100.0
        val rs = avgGain / avgLoss
        return 100 - (100 / (1 + rs))
    }
}

// MACD Calculator
data class MACDResult(
    val macd: Double,
    val signal: Double,
    val histogram: Double
)

object MACD {
    fun calculate(
        prices: List<Double>,
        fastPeriod: Int = 12,
        slowPeriod: Int = 26,
        signalPeriod: Int = 9
    ): MACDResult? {
        val fastEMA = EMA.calculate(prices, fastPeriod) ?: return null
        val slowEMA = EMA.calculate(prices, slowPeriod) ?: return null
        
        val macdLine = fastEMA - slowEMA
        
        // Signal line = EMA of MACD (need history)
        val macdHistory = calculateMACDHistory(prices, fastPeriod, slowPeriod)
        val signalLine = EMA.calculate(macdHistory, signalPeriod) ?: return null
        
        return MACDResult(
            macd = macdLine,
            signal = signalLine,
            histogram = macdLine - signalLine
        )
    }
    
    private fun calculateMACDHistory(
        prices: List<Double>,
        fast: Int,
        slow: Int
    ): List<Double> {
        val fastEMAs = EMA.calculateAll(prices, fast)
        val slowEMAs = EMA.calculateAll(prices, slow)
        
        return fastEMAs.zip(slowEMAs)
            .drop(slow - fast)
            .map { (fast, slow) -> fast - slow }
    }
}

// EMA Calculator
object EMA {
    fun calculate(prices: List<Double>, period: Int): Double? {
        if (prices.size < period) return null
        
        val multiplier = 2.0 / (period + 1)
        
        // Start with SMA
        var ema = prices.take(period).average()
        
        // Apply EMA formula
        for (i in period until prices.size) {
            ema = (prices[i] - ema) * multiplier + ema
        }
        
        return ema
    }
    
    fun calculateAll(prices: List<Double>, period: Int): List<Double> {
        if (prices.size < period) return emptyList()
        
        val multiplier = 2.0 / (period + 1)
        val result = mutableListOf<Double>()
        
        var ema = prices.take(period).average()
        result.add(ema)
        
        for (i in period until prices.size) {
            ema = (prices[i] - ema) * multiplier + ema
            result.add(ema)
        }
        
        return result
    }
}

// Moving Averages
object SMA {
    fun calculate(prices: List<Double>, period: Int): Double? =
        if (prices.size >= period) prices.takeLast(period).average() else null
}

// Bollinger Bands
data class BollingerBands(
    val upper: Double,
    val middle: Double,
    val lower: Double,
    val bandwidth: Double // (upper - lower) / middle
)

object Bollinger {
    fun calculate(
        prices: List<Double>,
        period: Int = 20,
        stdDevMultiplier: Double = 2.0
    ): BollingerBands? {
        if (prices.size < period) return null
        
        val recent = prices.takeLast(period)
        val middle = recent.average()
        
        val variance = recent.map { (it - middle).pow(2) }.average()
        val stdDev = sqrt(variance)
        
        return BollingerBands(
            upper = middle + stdDevMultiplier * stdDev,
            middle = middle,
            lower = middle - stdDevMultiplier * stdDev,
            bandwidth = (2 * stdDevMultiplier * stdDev) / middle
        )
    }
}
```

## Real-Time Provider (Data Layer)

```kotlin
@Singleton
class TechnicalIndicatorService @Inject constructor(
    private val webSocket: PriceWebSocketService
) {
    // Circular buffer for efficient memory usage
    private val priceBuffer = CircularBuffer<Double>(500)
    
    private val _indicators = MutableStateFlow<IndicatorState>(IndicatorState.Loading)
    val indicators: StateFlow<IndicatorState> = _indicators.asStateFlow()
    
    init {
        processPrices()
    }
    
    private fun processPrices() {
        webSocket.prices
            .onEach { candle ->
                priceBuffer.add(candle.close)
                calculateIndicators()
            }
            .catch { e -> 
                _indicators.value = IndicatorState.Error(e.message)
            }
            .launchIn(CoroutineScope(Dispatchers.Default + SupervisorJob()))
    }
    
    private fun calculateIndicators() {
        val prices = priceBuffer.toList()
        if (prices.size < 50) return // Wait for enough data
        
        val rsi = RSI.calculate(prices, 14)
        val macd = MACD.calculate(prices)
        val sma20 = SMA.calculate(prices, 20)
        val sma50 = SMA.calculate(prices, 50)
        val sma200 = SMA.calculate(prices, 200)
        val bollinger = Bollinger.calculate(prices, 20, 2.0)
        
        _indicators.value = IndicatorState.Ready(
            indicators = Indicators(
                rsi = rsi,
                macd = macd,
                sma20 = sma20,
                sma50 = sma50,
                sma200 = sma200,
                bollinger = bollinger,
                trend = determineTrend(sma20, sma50, sma200),
                signal = generateSignal(rsi, macd)
            ),
            lastUpdate = System.currentTimeMillis()
        )
    }
    
    private fun determineTrend(sma20: Double?, sma50: Double?, sma200: Double?): Trend {
        if (sma20 == null || sma50 == null) return Trend.Neutral
        return when {
            sma20 > sma50 && (sma200 == null || sma50 > sma200) -> Trend.StrongBullish
            sma20 > sma50 -> Trend.Bullish
            sma20 < sma50 && (sma200 == null || sma50 < sma200) -> Trend.StrongBearish
            sma20 < sma50 -> Trend.Bearish
            else -> Trend.Neutral
        }
    }
    
    private fun generateSignal(rsi: Double?, macd: MACDResult?): Signal {
        val signals = mutableListOf<String>()
        var strength = 0
        
        // RSI signals
        rsi?.let {
            when {
                it < 30 -> { signals.add("RSI Oversold"); strength += 2 }
                it < 40 -> { signals.add("RSI Weak Oversold"); strength += 1 }
                it > 70 -> { signals.add("RSI Overbought"); strength -= 2 }
                it > 60 -> { signals.add("RSI Weak Overbought"); strength -= 1 }
            }
        }
        
        // MACD signals
        macd?.let {
            when {
                it.histogram > 0 && it.macd > it.signal -> {
                    signals.add("MACD Bullish Cross")
                    strength += 1
                }
                it.histogram < 0 && it.macd < it.signal -> {
                    signals.add("MACD Bearish Cross")
                    strength -= 1
                }
            }
        }
        
        return when {
            strength >= 2 -> Signal.StrongBuy(signals)
            strength >= 1 -> Signal.Buy(signals)
            strength <= -2 -> Signal.StrongSell(signals)
            strength <= -1 -> Signal.Sell(signals)
            else -> Signal.Neutral(signals)
        }
    }
    
    // Circular buffer for fixed-size data
    class CircularBuffer<T>(private val capacity: Int) {
        private val buffer = mutableListOf<T>()
        
        fun add(item: T) {
            if (buffer.size >= capacity) buffer.removeAt(0)
            buffer.add(item)
        }
        
        fun toList(): List<T> = buffer.toList()
    }
}

// State models
sealed interface IndicatorState {
    data object Loading : IndicatorState
    data class Ready(val indicators: Indicators, val lastUpdate: Long) : IndicatorState
    data class Error(val message: String?) : IndicatorState
}

@Immutable
data class Indicators(
    val rsi: Double?,
    val macd: MACDResult?,
    val sma20: Double?,
    val sma50: Double?,
    val sma200: Double?,
    val bollinger: BollingerBands?,
    val trend: Trend,
    val signal: Signal
)

enum class Trend { StrongBullish, Bullish, Neutral, Bearish, StrongBearish }
sealed interface Signal {
    val reasons: List<String>
    data class StrongBuy(override val reasons: List<String>) : Signal
    data class Buy(override val reasons: List<String>) : Signal
    data class Neutral(override val reasons: List<String>) : Signal
    data class Sell(override val reasons: List<String>) : Signal
    data class StrongSell(override val reasons: List<String>) : Signal
}
```

## Compose Dashboard UI

```kotlin
@Composable
fun TechnicalDashboard(
    viewModel: TechnicalIndicatorViewModel = hiltViewModel()
) {
    val state by viewModel.indicators.collectAsStateWithLifecycle()
    
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Signal Card
        item {
            when (val indicators = (state as? IndicatorState.Ready)?.indicators) {
                null -> { /* Loading */ }
                else -> SignalCard(indicators.signal, indicators.trend)
            }
        }
        
        // RSI Card
        item {
            (state as? IndicatorState.Ready)?.indicators?.rsi?.let { rsi ->
                RsiCard(rsi)
            }
        }
        
        // MACD Card
        item {
            (state as? IndicatorState.Ready)?.indicators?.macd?.let { macd ->
                MacdCard(macd)
            }
        }
        
        // Moving Averages Card
        item {
            (state as? IndicatorState.Ready)?.indicators?.let { ind ->
                MovingAveragesCard(ind)
            }
        }
        
        // Bollinger Bands Card
        item {
            (state as? IndicatorState.Ready)?.indicators?.bollinger?.let { bands ->
                BollingerCard(bands)
            }
        }
    }
}

@Composable
fun SignalCard(signal: Signal, trend: Trend) {
    val (color, icon, text) = when (signal) {
        is Signal.StrongBuy -> Triple(Color(0xFF00C853), Icons.Default.TrendingUp, "STRONG BUY")
        is Signal.Buy -> Triple(Color(0xFF69F0AE), Icons.Default.TrendingUp, "BUY")
        is Signal.Neutral -> Triple(Color.Gray, Icons.Default.Remove, "NEUTRAL")
        is Signal.Sell -> Triple(Color(0xFFFF5252), Icons.Default.TrendingDown, "SELL")
        is Signal.StrongSell -> Triple(Color(0xFFD50000), Icons.Default.TrendingDown, "STRONG SELL")
    }
    
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = color.copy(alpha = 0.15f))
    ) {
        Row(
            Modifier
                .fillMaxWidth()
                .padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                icon,
                contentDescription = null,
                tint = color,
                modifier = Modifier.size(48.dp)
            )
            Spacer(Modifier.width(16.dp))
            Column {
                Text(
                    text,
                    style = MaterialTheme.typography.headlineMedium,
                    color = color,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    "Trend: ${trend.name}",
                    style = MaterialTheme.typography.bodyMedium
                )
                if (signal.reasons.isNotEmpty()) {
                    Text(
                        signal.reasons.joinToString(" • "),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        }
    }
}

@Composable
fun RsiCard(rsi: Double) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text("RSI (14)", style = MaterialTheme.typography.titleMedium)
            
            // RSI Gauge
            Box(
                Modifier
                    .fillMaxWidth()
                    .height(80.dp)
                    .padding(vertical = 8.dp)
            ) {
                // Background gradient
                Canvas(Modifier.fillMaxSize()) {
                    val width = size.width
                    val height = size.height
                    
                    drawRoundRect(
                        brush = Brush.horizontalGradient(
                            colors = listOf(
                                Color(0xFF4CAF50),  // Oversold - green
                                Color(0xFFFFEB3B),  // Neutral - yellow
                                Color(0xFFF44336)   // Overbought - red
                            )
                        ),
                        cornerRadius = CornerRadius(8.dp.toPx())
                    )
                    
                    // RSI indicator
                    val indicatorX = (rsi / 100f) * width
                    drawCircle(
                        color = Color.White,
                        radius = 12.dp.toPx(),
                        center = Offset(indicatorX.toFloat(), height / 2)
                    )
                }
            }
            
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text("Oversold", style = MaterialTheme.typography.bodySmall, color = Color(0xFF4CAF50))
                Text(
                    String.format("%.1f", rsi),
                    style = MaterialTheme.typography.headlineSmall,
                    fontWeight = FontWeight.Bold
                )
                Text("Overbought", style = MaterialTheme.typography.bodySmall, color = Color(0xFFF44336))
            }
        }
    }
}

@Composable
fun MacdCard(macd: MACDResult) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text("MACD (12, 26, 9)", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(8.dp))
            
            // Histogram bar
            Canvas(
                Modifier
                    .fillMaxWidth()
                    .height(40.dp)
            ) {
                val center = size.width / 2
                val barWidth = (macd.histogram.absoluteValue / 10f).coerceIn(0f, center) * 10
                val isPositive = macd.histogram > 0
                
                drawRect(
                    color = if (isPositive) Color(0xFF4CAF50) else Color(0xFFF44336),
                    topLeft = Offset(
                        if (isPositive) center else center - barWidth,
                        0f
                    ),
                    size = Size(barWidth, size.height)
                )
            }
            
            Spacer(Modifier.height(8.dp))
            
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text("MACD", style = MaterialTheme.typography.bodySmall)
                    Text(
                        String.format("%.4f", macd.macd),
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.Medium
                    )
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("Signal", style = MaterialTheme.typography.bodySmall)
                    Text(
                        String.format("%.4f", macd.signal),
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.Medium
                    )
                }
            }
        }
    }
}

@Composable
fun MovingAveragesCard(indicators: Indicators) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text("Moving Averages", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(8.dp))
            
            listOf(
                "SMA 20" to indicators.sma20,
                "SMA 50" to indicators.sma50,
                "SMA 200" to indicators.sma200,
                "EMA 20" to indicators.bollinger?.middle
            ).forEach { (label, value) ->
                value?.let {
                    Row(
                        Modifier
                            .fillMaxWidth()
                            .padding(vertical = 4.dp),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text(label, style = MaterialTheme.typography.bodyMedium)
                        Text(
                            String.format("%.2f", it),
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Medium
                        )
                    }
                }
            }
        }
    }
}

@Composable
fun BollingerCard(bands: BollingerBands) {
    Card(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp)) {
            Text("Bollinger Bands (20, 2)", style = MaterialTheme.typography.titleMedium)
            Spacer(Modifier.height(8.dp))
            
            Row(
                Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text("Upper", style = MaterialTheme.typography.bodySmall, color = Color.Red)
                    Text(
                        String.format("%.2f", bands.upper),
                        style = MaterialTheme.typography.bodyMedium
                    )
                }
                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                    Text("Middle", style = MaterialTheme.typography.bodySmall)
                    Text(
                        String.format("%.2f", bands.middle),
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.Bold
                    )
                }
                Column(horizontalAlignment = Alignment.End) {
                    Text("Lower", style = MaterialTheme.typography.bodySmall, color = Color(0xFF4CAF50))
                    Text(
                        String.format("%.2f", bands.lower),
                        style = MaterialTheme.typography.bodyMedium
                    )
                }
            }
            
            Spacer(Modifier.height(8.dp))
            
            Text(
                "Bandwidth: ${String.format("%.2f%%", bands.bandwidth * 100)}",
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
```

## Quick Indicator Reference

| Indicator | Buy Signal | Sell Signal | Best Use |
|-----------|------------|-------------|----------|
| RSI | < 30 (oversold) | > 70 (overbought) | Range-bound markets |
| MACD | Cross above signal | Cross below signal | Trend changes |
| SMA Cross | Fast > Slow | Fast < Slow | Trend direction |
| Bollinger | Price touches lower band | Price touches upper band | Volatility breakouts |

---
*Learned: 2026-02-22 22:41 | Focus: RSI, MACD, Bollinger calculation, real-time updates, Compose dashboard*