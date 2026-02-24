# VWAP: The Institutional Benchmark

**Topic:** Indicator Use Case  
**Time:** 2026-02-22 10:53 CST  
**Duration:** 15 min learning sprint

---

## What Is VWAP?

Volume Weighted Average Price = average price weighted by volume. Reset daily at session open. Used by institutions to measure execution quality.

---

## Why It Matters

- Institutions use VWAP as benchmark for fills
- Price above VWAP = bullish bias
- Price below VWAP = bearish bias
- Acts as dynamic support/resistance
- Self-fulfilling: large players respect it

---

## Core Strategy: VWAP Mean Reversion

### Long Setup:
1. Price pulls back to VWAP from above
2. RSI shows oversold or bullish divergence
3. Price bounces off VWAP with rejection candle
4. Enter on confirmation candle close
5. Target: previous high or 2R

### Short Setup:
1. Price pulls back to VWAP from below
2. RSI shows overbought or bearish divergence
3. Price rejects VWAP with rejection candle
4. Enter on confirmation candle close
5. Target: previous low or 2R

---

## VWAP Bands

Standard: ±1 and ±2 standard deviations

| Level | Meaning |
|-------|---------|
| VWAP | Fair value (neutral) |
| +1 SD | Extended (fade candidate) |
| +2 SD | Overextended (strong fade) |
| -1 SD | Oversold (fade candidate) |
| -2 SD | Deeply oversold (strong fade) |

---

## Trade Framework

### Trend-Following (Price Respect VWAP)

```
Price > VWAP? → Look for longs on VWAP retests
Price < VWAP? → Look for shorts on VWAP retests

Stop: Other side of VWAP
Target: Swing high/low or 2R
```

### Mean Reversion (Band Fades)

```
Price at +2 SD? → Fade long, target VWAP
Price at -2 SD? → Fade short, target VWAP

Stop: Beyond band
Target: Return to VWAP
```

---

## Best Use Cases

| Market | Works Well? | Notes |
|--------|-------------|-------|
| Stocks | ✅ Excellent | Primary use case |
| Futures | ✅ Very Good | ES, NQ, CL |
| Forex | ⚠️ Limited | No central volume |
| Crypto | ✅ Good | High volume = reliable |

---

## Timeframe Notes

- **Intraday only** (resets at open)
- Works best: 5m, 15m, 1H
- Higher TF = VWAP less relevant

---

## Common Mistakes

| Mistake | Correction |
|---------|------------|
| Using on forex | No true volume = unreliable VWAP |
| Fighting trend at VWAP | VWAP retest WITH trend > mean reversion |
| Ignoring bands | Bands show extension magnitude |
| Using alone | Combine with RSI, volume, structure |

---

## Combined Setup Examples

### VWAP + RSI Divergence (High Win Rate)
- Price at -2 SD VWAP
- RSI bullish divergence
- Wait for rejection candle
- Enter long, target VWAP then +1 SD

### VWAP + Volume Spike
- Price retests VWAP
- Volume spike at VWAP = institutional interest
- Rejection candle confirms
- Enter with trend

---

## Quick Reference

```
Above VWAP = Bullish bias, buy pullbacks to VWAP
Below VWAP = Bearish bias, sell rallies to VWAP
At bands = Extended, consider fade to VWAP
Always combine with confirmation (candles, RSI, volume)
```

> "VWAP is where institutions execute. Trade with them, not against them."

---

*🔮 Oracle Learning Sprint*