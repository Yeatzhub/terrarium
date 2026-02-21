# Bollinger Band Squeeze: The Volatility Breakout Setup

**Oracle Quick Study**  
*Topic: Indicator Use Case*  
*Date: 2026-02-21 12:25 PM CT*

---

## TL;DR

Bollinger Band Squeeze = volatility compression before expansion. When bands narrow to 6-month lows, a significant move (often 2-3x normal range) follows within 10-15 candles. The squeeze doesn't predict direction—it predicts magnitude. Trade the breakout, not the compression.

---

## The Mechanics

Bollinger Bands measure standard deviation from a moving average:
- **Upper Band:** 20 SMA + (2 × StdDev)
- **Lower Band:** 20 SMA - (2 × StdDev)
- **Bandwidth:** (Upper - Lower) / Middle × 100

**The Squeeze:** When bandwidth compresses to its lowest levels in recent history (typically 6-month or 120-period percentile), volatility has reached an extreme low. Markets alternate between low and high volatility—low periods predictably precede high periods.

---

## Squeeze Identification

### The Squeeze Formula

```python
# Bandwidth calculation
Bandwidth = ((Upper_Band - Lower_Band) / Middle_Band) × 100

# Squeeze condition
Squeeze = Bandwidth < Percentile(Bandwidth, 6, 120)
# (Bandwidth is in bottom 6% of last 120 periods = Squeeze)
```

### Squeeze Strength Levels

| Level | Bandwidth %ile | Expected Move | Setup Quality |
|-------|----------------|---------------|---------------|
| **Extreme** | < 2% | 3-5x ATR | ★★★★★ |
| **Strong** | 2-6% | 2-3x ATR | ★★★★☆ |
| **Moderate** | 6-10% | 1.5-2x ATR | ★★★☆☆ |
| **Weak** | > 10% | Unreliable | ★★☆☆☆ |

---

## The Trading Framework

### Step 1: Identify Squeeze

Multiple squeeze setups to watch:

1. **Single Stock/Forex Pair:** Bandwidth at 6-month low
2. **Multiple Assets:** 3+ assets in your watchlist squeezing simultaneously = sector/market move coming
3. **VIX Squeeze:** Market volatility itself compressing (rare but powerful)

### Step 2: Mark Key Levels

During squeeze, price often coils within a range. Mark:
- **Upper boundary:** Recent highs during compression
- **Lower boundary:** Recent lows during compression
- **Midpoint:** 20 SMA (often acts as pivot)

**The range typically:** 1.0-1.5 ATR (very narrow)

### Step 3: Wait for Breakout

**Do NOT trade inside the squeeze.** The edge comes from the *release*, not the compression.

**Entry Triggers:**

| Direction | Trigger | Stop Loss | Target |
|-----------|---------|-----------|--------|
| Long | Close above upper boundary | Below squeeze low | 2:1 minimum, 2x-3x ATR typical |
| Short | Close below lower boundary | Above squeeze high | 2:1 minimum, 2x-3x ATR typical |

### Step 4: Manage the Trade

**The Initial Move (First 1-3 candles):**
- Often the strongest impulse
- Take partial profits at 1:1 or 50% of target

**The Middle Phase (Candles 4-10):**
- Move continues or consolidates
- Move stop to breakeven after 1:1 hit

**The Exhaustion (After 10+ candles):**
- Look for reversal signals
- Full exit when price touches opposite band or momentum wanes

---

## Squeeze + Confluence

Stack these for higher probability:

### 1. Squeeze + Volume Profile
- Squeeze at Value Area High/Low
- Breakout from Value Area = strong move expected

### 2. Squeeze + Market Structure
- Squeeze at HTF support/resistance
- Breakout aligns with HTF trend direction
- Example: Squeeze at daily support in uptrend + bullish breakout

### 3. Squeeze + Order Blocks
- Squeeze forming at or near bullish/bearish OB
- OB + Squeeze = explosive combination

### 4. Squeeze + Seasonality/Timing
- Squeeze leading into known volatile events (earnings, FOMC, OPEX)
- Pre-event squeeze often resolves *into* the event

### 5. Squeeze + Momentum Divergence
- Price making higher lows in squeeze (bullish)
- RSI/StochRSI showing accumulation during compression
- Breakout more likely upward

---

## Breakout Failure Patterns

Not all squeezes explode. Watch for:

**False Breakout (30% of squeezes):**
- Price breaks boundary then immediately reverses
- Close back inside squeeze range within 2-3 candles
- **Action:** Stop out, wait for retest of opposite boundary

**Failed Breakout (15% of squeezes):**
- Price breaks out, advances 0.5-1x ATR, then collapses
- Momentum absent despite breakout
- **Action:** Trail stops tight after entry; don't let winners reverse

**The "Walk" (10% of squeezes):**
- Price breaks out slowly with no conviction
- Drifts instead of impulses
- **Action:** Exit early; momentum missing

---

## Bollinger Band Squeeze Variations

### The TTM Squeeze (John Carter)

Custom indicator combining:
- Bollinger Bands (20,2)
- Keltner Channels (20,1.5 ATR)
- Momentum histogram

**Squeeze Condition:** BB inside KC (extreme low volatility)
**Signal:** Momentum histogram crosses zero after squeeze
**Advantage:** Built-in momentum confirmation

### The Squeeze Momentum (LazzyBear)

Combines squeeze with momentum oscillator:
- Squeeze dots on zero line when compressed
- Momentum line above/below zero shows directional bias
- **Long:** Squeeze release + momentum line rising
- **Short:** Squeeze release + momentum line falling

### Multi-Timeframe Squeeze

- HTF squeeze + LTF breakout = strongest signals
- Example: Daily BB squeeze + H1 breakout entry
- Wait for HTF squeeze; execute on LTF confirmation

---

## Position Sizing for Squeeze Plays

Squeeze breakouts have higher volatility. Size accordingly:

**Standard:** 1-2% risk
**Squeeze breakout:** 0.75-1.5% risk (wider stops needed)

**Why:** The initial breakout can have 2x normal volatility before settling. Your stop needs breathing room or you'll get whipped out on noise.

**Stop Placement:**
- Aggressive: Below/above squeeze boundary (1x ATR beyond)
- Conservative: Below/above entire squeeze range (2-3x ATR)
- Hybrid: Half position at each

---

## The Squeeze Checklist

Before taking squeeze trade, confirm:

- [ ] Bandwidth at 6-month low (extreme compression)
- [ ] Clear boundaries marked (highs/lows of squeeze)
- [ ] HTF context checked (direction aligned with trend?)
- [ ] Volume analysis (diminished during squeeze, spike on breakout)
- [ ] News/event calendar checked (avoid squeeze through earnings unless intended)
- [ ] Stop placement calculated (wider than normal due to volatility)
- [ ] Target defined (2-3x ATR or next major level)

---

## Common Mistakes

1. **Trading inside the squeeze** — There's no edge in the compression phase. Wait for the release.

2. **Predicting direction** — Squeeze is direction-neutral until breakout confirms. Don't front-run.

3. **Tight stops** — Squeeze breakouts need room. A 0.5 ATR stop will get hit on normal post-squeeze noise.

4. **Ignoring HTF** — A squeeze against HTF trend can still work but has lower probability. Know your context.

5. **Holding through exhaustion** — Squeeze moves are explosive but finite. Take profits systematically.

---

## Summary: The Squeeze Edge

| Element | Why It Works |
|---------|--------------|
| Compression | Volatility mean-reverts; extreme low predicts high |
| Energy Storage | Lack of movement builds pent-up order flow |
| Directional Release | When compression breaks, pressure releases directionally |
| Predictable Magnitude | Typically 2-3x normal ATR move |

**Oracle's Note:** *The Bollinger Band Squeeze is one of the few setups with a genuine statistical edge. Volatility compression reliably precedes expansion. Your job: identify the squeeze, mark the boundaries, wait for the breakout, and manage the inevitable volatility expansion with appropriate sizing and stops.*
