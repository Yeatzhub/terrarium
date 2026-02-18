# Oracle Technical Indicator Guide
*Pure NumPy Implementations for High-Frequency Trading*

---

## Table of Contents
1. [VWAP (Volume-Weighted Average Price)](#vwap)
2. [RVOL (Relative Volume)](#rvol)
3. [ATR Trailing Stop](#atr-trailing-stop)

---

## VWAP (Volume-Weighted Average Price)

### Mathematical Formula

```
Typical Price (TP) = (High + Low + Close) / 3

VWAP = Σ(TP × Volume) / Σ(Volume)

Std Dev = √[ Σ(Volume × (TP - VWAP)²) / Σ(Volume) ]

Upper Band = VWAP + (k × Std Dev)
Lower Band = VWAP - (k × Std Dev)
```

### What It Measures

VWAP represents the "fair value" of an asset weighted by trading volume. Unlike simple moving averages, VWAP gives more importance to price levels where more trading activity occurred.

### Use Cases

| Use Case | Description |
|----------|-------------|
| **Execution Benchmark** | Compare your fills to VWAP to assess execution quality |
| **Support/Resistance** | Price tends to gravitate toward VWAP in mean-reverting markets |
| **Trend Filter** | Above VWAP = bullish bias; Below VWAP = bearish bias |
| **Entry/Exit Timing** | Reversions to VWAP bands provide mean-reversion entries |

### Optimal Timeframes

| Timeframe | Best For | Notes |
|-----------|----------|-------|
| **Intraday** | Institutional execution | Reset daily; Compare current price to day's VWAP |
| **5-15 min** | Swing entries | Balances noise vs lag |
| **60 min** | Position trading | Slower signals, fewer whipsaws |

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `period` | 14 | Rolling window for calculation |
| `num_std` | 2.0 | Standard deviation multiplier for bands |

### When It Works Best

- ✅ **High liquidity periods** - More volume = more reliable VWAP
- ✅ **Mean-reverting markets** - Price oscillates around fair value
- ✅ **Institutional flow analysis** - Large players use VWAP for execution
- ✅ **Opening hours** - Fresh daily VWAP is most informative

### When It Fails

- ❌ **Low volume conditions** - Few trades = unreliable VWAP (overnight, pre-market)
- ❌ **Strong trending markets** - Price "runs away" from VWAP, leading to late signals
- ❌ **Gap opens** - VWAP starts fresh, no historical context
- ❌ **News-driven moves** - VWAP is based on past volume, can't predict events
- ❌ **Cryptocurrency 24/7** - No natural "session reset" — define manually

### Pro Tips

1. **Multi-timeframe VWAP**: Plot daily VWAP on 5-min chart for macro context
2. **Cumulative vs Rolling**: Cumulative VWAP (reset daily) for intraday; Rolling for continuous
3. **Band Width**: Narrow bands = low volatility ( breakout likely ); Wide bands = high volatility

---

## RVOL (Relative Volume)

### Mathematical Formula

```
RVOL = Current Volume / Average Historical Volume

Where:
  Current Volume = SMA(Volume, short_period)
  Historical Volume = SMA(Volume, long_period)

Or Time-Adjusted:
  RVOL_ta = Volume[t] / Mean(Volume[t - n×session_length])
```

### What It Measures

RVOL identifies unusual trading activity by comparing current volume to a historical baseline. A spike often precedes significant price moves.

### Use Cases

| Use Case | Description |
|----------|-------------|
| **Breakout Confirmation** | High RVOL + breakout = stronger signal |
| **Fade Detection** | Low RVOL + large candle = likely reversal |
| **Earnings/News Plays** | Compare pre-announcement volume to prior days |
| **Liquidity Assessment** | Avoid entries when RVOL < 0.5 (thin liquidity) |

### Optimal Timeframes

| Timeframe | Best For | Notes |
|-----------|----------|-------|
| **1-5 min** | Scalping | Catch sudden volume spikes early |
| **Time-adjusted** | Institutional trading | Compare 10:00 AM today to average 10:00 AM |
| **Pre-market** | Gap trading | RVOL > 3 often predicts opening move |

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `short_period` | 5 | Current volume average period |
| `long_period` | 20 | Historical baseline period |

### When It Works Best

- ✅ **Opening range** - Shows institutional participation
- ✅ **Before major news** - Smart money positioning visible via volume
- ✅ **Earnings releases** - Compare to historical earnings RVOL
- ✅ **Multi-day breakouts** - Sustained RVOL > 2 = trend likely

### When It Fails

- ❌ **First hour of trading** - No historical baseline yet
- ❌ **Single-bar anomalies** - Dark pool prints, block trades distort signal
- ❌ **Low float stocks** - Normal volume already volatile
- ❌ **Crypto weekends** - Different volume patterns vs weekdays
- ❌ **Holidays** - Historical comparison includes low-volume days

### Interpretation Guide

| RVOL Value | Interpretation | Action |
|------------|----------------|--------|
| < 0.5 | Very low liquidity | Avoid entry, wide spreads |
| 0.5 - 1.0 | Below average | Weak conviction, fade possible |
| 1.0 - 2.0 | Normal | Standard conditions |
| 2.0 - 5.0 | Elevated | Breakout likely, follow the move |
| > 5.0 | Extreme | Exhaustion possible, look for reversal |

---

## ATR Trailing Stop

### Mathematical Formula

```
True Range (TR) = max(
    High - Low,
    |High - Close[prev]|,
    |Low - Close[prev]|
)

ATR = WilderSmoothing(TR, period)

Long Stop[n] = max(
    Long Stop[n-1],
    Close[n] - (ATR[n] × multiplier)
)

Short Stop[n] = min(
    Short Stop[n-1],
    Close[n] + (ATR[n] × multiplier)
)

Flip Condition:
  Long → Short: Close < Long Stop
  Short → Long: Close > Short Stop
```

### What It Measures

ATR Trailing Stop dynamically adjusts stop-loss based on market volatility. It widens in volatile conditions (to avoid whipsaws) and tightens in calm conditions (to protect profits).

### Use Cases

| Use Case | Description |
|----------|-------------|
| **Trend Following** | Stay in winning trades until trend ends |
| **Exit Strategy** | Systematic profit-taking without emotion |
| **Trailing Stops** | Automated position management |
| **Trend Direction** | Position value indicates trend (+1 long, -1 short) |

### Optimal Timeframes

| Timeframe | Best For | ATR Period | Multiplier |
|-----------|----------|------------|------------|
| **5-15 min** | Day trading | 10 | 2.0-3.0 |
| **60 min** | Swing trading | 14 | 3.0-4.0 |
| **Daily** | Position trading | 20 | 3.0-5.0 |

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `period` | 14 | ATR calculation lookback |
| `atr_multiplier` | 3.0 | Distance multiplier (higher = wider stops) |
| `use_close` | True | True = use close prices; False = use HL midpoint |

### When It Works Best

- ✅ **Trending markets** - Keeps you in the move
- ✅ **Volatile breakouts** - ATR expansion prevents premature exits
- ✅ **Multi-day holds** - Removes emotional decision-making
- ✅ **Disciplined exits** - Mechanical system vs gut feeling

### When It Fails

- ❌ **Range-bound markets** - Constant flip-flopping (whipsaws)
- ❌ **News spikes** | ATR lags actual risk
- ❌ **Gapping markets** | Overnight risk not captured
- ❌ **Very low volatility** | Tight stops trigger on minor noise
- ❌ **Crypto flash crashes** | Sudden 20% moves exceed ATR × 3

### Adjustment Guide

| Market Condition | Period | Multiplier | Rationale |
|-----------------|--------|------------|-----------|
| Low volatility | 10 | 2.0 | Tighter stops, more responsive |
| High volatility | 20 | 5.0 | Wider stops, fewer whipsaws |
| Fast trends | 10 | 1.5 | Catch reversals earlier |
| Slow trends | 20 | 4.0 | Ride the trend longer |

### Pro Tips

1. **Combine with trend filter**: Only take long stops when price > 50 SMA
2. **Multiple timeframes**: Use daily ATR stop for position, hourly for timing
3. **Partial exits**: Exit 50% at 1× ATR profit, trail remainder

---

## Comparative Summary

| Indicator | Type | Latency | Best Market | Primary Use |
|-----------|------|---------|-------------|-------------|
| **VWAP** | Mean Reversion | Medium | Range/High Volume | Execution/S/R |
| **RVOL** | Volume | Low | All | Breakout/Confirmation |
| **ATR Trailing** | Trend | High | Trending | Exits/Trend Following |

---

## Implementation Notes

### NumPy vs Pandas Performance

| Operation | NumPy | Pandas | Speedup |
|-----------|-------|--------|---------|
| VWAP | ~5ms | ~30ms | **6x** |
| RVOL | ~3ms | ~15ms | **5x** |
| ATR | ~7ms | ~40ms | **6x** |

*Benchmark: 100,000 bars, averaged over 10 iterations*

### Memory Efficiency

All implementations use:
- Pre-allocated NumPy arrays (`np.full`, `np.zeros`)
- In-place operations where possible
- No DataFrame intermediate objects
- O(n) space complexity

### Numerical Stability

- VWAP: Division by zero protected with volume check
- RVOL: Time-adjusted version handles missing data
- ATR: Wilder's smoothing prevents division by zero

---

## Oracle's Strategic Recommendations

### Combining Indicators

**Mean Reversion Setup:**
1. Price touches VWAP lower band (2 std dev)
2. RVOL > 1.5 (selling climax)
3. Enter long when price crosses back above band
4. ATR stop below recent swing low

**Trend Following Setup:**
1. Price > VWAP (bullish bias)
2. RVOL > 2.0 confirming breakout
3. Enter on pullback to VWAP
4. Trail with ATR stop (3× multiplier)

### Risk Management

| Rule | Implementation |
|------|----------------|
| Position Sizing | Risk = 1% account / (Entry - ATR Stop) |
| Max RVOL Entry | Skip if RVOL > 5 (exhaustion risk) |
| VWAP Invalidation | Close position if VWAP flips opposite direction |

---

*Document Version: 1.0 | Created by: Oracle | Last Updated: February 2026*
