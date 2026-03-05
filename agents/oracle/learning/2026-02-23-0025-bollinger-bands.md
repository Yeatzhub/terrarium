# Bollinger Bands: Volatility and Mean Reversion Trading

**Topic:** Indicator Use Case  
**Time:** 2026-02-23 00:25 CST  
**Duration:** 15 min learning sprint

---

## Core Concept

Bollinger Bands (20,2) consist of:
- **Middle band:** 20-period SMA
- **Upper band:** Middle + 2 standard deviations
- **Lower band:** Middle - 2 standard deviations

**Key principle:** Price tends to return to the mean (middle band).

---

## What the Bands Show

| Band Position | Meaning |
|---------------|---------|
| **Upper band touch** | Overbought, potential reversal |
| **Lower band touch** | Oversold, potential reversal |
| **Squeeze (tight bands)** | Low volatility, breakout coming |
| **Expansion (wide bands)** | High volatility, trend active |
| **Walk the bands** | Strong trend, can extend |

---

## The Bollinger Band Squeeze

Bands contract → expansion follows.

### Identification:
- Upper and lower bands converge
- Distance between bands is at tightest in 20 periods
- Volatility is compressed

### Strategy:
1. Wait for squeeze (lowest range in at least 20 periods)
2. Mark the breakout direction (follow big money)
3. Enter when price closes outside bands
4. Target: Walk the band in direction of breakout
5. Stop: Middle band or inside band

---

## Mean Reversion: Band Touch Strategy

### Long Setup:
1. Price touches or closes below lower band
2. RSI shows oversold (optional)
3. Wait for bullish reversal candle (engulfing, doji)
4. Enter on confirmation candle close
5. Target: Middle band (first target) or upper band
6. Stop: Below swing low of touch candle

### Short Setup:
1. Price touches or closes above upper band
2. RSI shows overbought (optional)
3. Wait for bearish reversal candle
4. Enter on confirmation candle close
5. Target: Middle band or lower band
6. Stop: Above swing high of touch candle

---

## Band Walk Strategy: Trend Trading

When bands are expanding and price rides along the outer band = strong trend.

### Rules:
- Price touches band multiple times without closing outside
- Bands are expanding (widening)
- Volume confirms trend

### Entry:
- Enter on pullback to middle band
- Or enter on first touch after band expansion

### Exit:
- When price closes on opposite side of middle band
- Trail on upper/lower band

---

## Bollinger Band Width (BBW)

Custom indicator: (Upper - Lower) / Middle × 100

| BBW Value | Interpretation |
|-----------|----------------|
| < 6% | Squeeze, breakout imminent |
| 6-10% | Normal volatility |
| > 10% | High volatility, expansion |

**Usage:** Trade mean reversion when BBW > 10%, trade breakouts when BBW < 6%

---

## Bollinger %B

Shows price position within bands: 0 = lower band, 1 = upper band, 0.5 = middle

| %B Value | Signal |
|----------|--------|
| > 0.95 | Overbought |
| < 0.05 | Oversold |
| Crosses 0.5 | Momentum shift |

---

## Best Combinations

| Indicator Combo | Use |
|-----------------|-----|
| BB + RSI | Confirm overbought/oversold |
| BB + Volume | Confirm squeeze breakout |
| BB + MACD | Confirm momentum direction |
| BB + Support/Resistance | Confluence at band edges |

---

## Timeframes

| TF | Best Use |
|----|----------|
| 5m | Entry timing within squeeze |
| 15m | Standard squeeze detection |
| 1H | Primary setup identification |
| 4H | Higher context for trend |

---

## Common Mistakes

| Mistake | Correction |
|---------|------------|
| Touching band = immediate reversal | Wait for confirmation candle |
| Same squeeze length always | Varies by market, track typical |
| Ignoring trend context | Mean reversion works better in ranges |
| Walking the band in chop | Bands need to be expanding |
| Using default (20,2) blindly | Test (14,2) or (10,1.5) |

---

## Quick Reference

```
Squeeze = Low volatility, breakout coming → Trade breakout
Band touch + reversal candle = Mean reversion → Trade bounce
Band walk = Strong trend → Trade pullbacks
Expansion = Active trend → Don't fade, go with it
Always wait for confirmation, not just band touch
```

> "Squeezes foretell volatility expansions. They don't predict direction—price does."

---

*🔮 Oracle Learning Sprint*
