# Fair Value Gaps (FVG): The Imbalance That Drives Price

**Oracle Quick Study**  
*Topic: Market Structure*  
*Date: 2026-02-21 09:25 PM CT*

---

## TL;DR

Fair Value Gaps = imbalanced price movement where aggressive buying/selling left no overlap between candle wicks. These gaps represent inefficiencies that price returns to fill 70-80% of the time before continuing. Trade the initial move, or the gap fill, but know which one you're trading.

---

## What Is a Fair Value Gap?

A Fair Value Gap (FVG) forms when price moves aggressively in one direction, creating a gap between candle wicks that wasn't traded through.

**Bullish FVG (BISI - Buy Side Imbalance):**
- Candle 1: Any candle
- Candle 2: Strong bull candle (impulse)
- Candle 3: Any candle
- **The Gap:** Low of Candle 3 is ABOVE the High of Candle 1
- This unfilled zone = bullish imbalance

**Bearish FVG (SIbi - Sell Side Imbalance):**
- Candle 1: Any candle
- Candle 2: Strong bear candle (impulse)
- Candle 3: Any candle
- **The Gap:** High of Candle 3 is BELOW the Low of Candle 1
- This unfilled zone = bearish imbalance

**Visual:**
```
Bullish FVG:
    │
    │    ╭──╮  ← Candle 3
    │    │  │
    │────╯  │  ← GAP ZONE (not traded)
    │       │
    │  ╭────╯  ← Candle 1
    │  │
    │──╯       ← Candle 2 (impulse)
    │

Bearish FVG:
    │
    │──╮       ← Candle 2 (impulse down)
    │  │
    │  ╰────╮  ← Candle 1
    │       │
    │────╮  │  ← GAP ZONE (not traded)
    │    │  │
    │    ╰──╯  ← Candle 3
    │
```

---

## Why FVGs Matter

**Market Theory:**
- Price moves via aggressive market orders (imbalance)
- When aggressive buying overwhelms selling, price jumps
- This creates "untouched" price zones (the gap)
- Later, price returns to these zones to "balance" the market
- Institutions often defend these zones (their fill prices)

**The Statistics:**
- FVGs fill 70-80% of the time on same timeframe
- Higher timeframe FVGs fill less often but are stronger when they do
- Multiple overlapping FVGs = stronger zone

---

## The Three FVG Types

### Type 1: Standard FVG
**Formation:** Clear 3-candle gap as described above
**Reliability:** High (~75% fill rate)
**Use:** Entry zones, profit targets

### Type 2: Mitigated FVG
**Formation:** Price returned and filled the FVG zone
**Status:** No longer relevant for entries; acts as standard support/resistance
**Use:** If price broke through and reclaimed = now flipped level

### Type 3: Consequent Encroachment (CE)
**Formation:** The 50% midpoint of the FVG
**Significance:** Often where price stalls during gap fill
**Use:** Partial profit target, optimal entry within FVG

---

## Trading the FVG

### Setup 1: FVG as Entry Zone (Most Common)

**Context:**
- Price in uptrend, forms bullish FVG
- Price pulls back toward FVG zone
- HTF trend intact

**Entry:**
1. Mark FVG zone (Candle 1 high to Candle 3 low)
2. Mark 50% level (Consequent Encroachment)
3. Wait for price to enter FVG zone
4. Look for reaction at CE or zone boundary
5. Enter on rejection candle close

**Stop:** Below FVG low (invalidation)
**Target:** Previous high or next major level

**Win Rate:** ~65% when aligned with HTF trend

### Setup 2: FVG as Profit Target

**Context:**
- You're in a winning trade
- Price approaching opposing FVG

**Action:**
- Scale out 50% at CE (50% of FVG)
- Scale out remaining 50% at far edge of FVG
- Trail stop on remainder if momentum continues

**Why:** Price often fills FVG then reverses. Don't give back profits.

### Setup 3: Confluence Entries (Highest Quality)

**FVG + Order Block:**
- Bullish FVG aligns with bullish Order Block
- Price returns to both simultaneously
- Entry at confluence = multiple edges

**FVG + Liquidity Sweep:**
- Price sweeps liquidity (equal lows)
- Into FVG zone
- Reversal from both = strong signal

**FVG + BOS/ChoCH:**
- FVG formed during BOS (break of structure)
- FVG zone = optimal pullback entry

---

## FVG Quality Hierarchy

| Factor | +Score | Condition |
|--------|--------|-----------|
| **Impulse strength** | +3 | Candle 2 body is 3x+ average |
| **Timeframe** | +2 | Daily/H4 FVG stronger than M5 |
| **Confluence** | +2 | Aligns with OB, liquidity, session level |
| **HTF alignment** | +2 | In direction of higher timeframe trend |
| **Volume** | +1 | Spike on impulse candle |
| **Mitigation history** | -2 | Already filled once (weaker) |

**Scoring:**
- 8-10 points: Exceptional FVG, prioritize
- 5-7 points: Good FVG, standard trade
- 0-4 points: Weak FVG, skip or reduce size

---

## The FVG Trading Checklist

### Before Entry:
- [ ] Clear 3-candle gap visible
- [ ] HTF trend direction confirmed
- [ ] FVG direction aligns with trend
- [ ] Zone marked (high/low boundaries)
- [ ] CE (50% level) marked
- [ ] Entry trigger defined (rejection pattern)
- [ ] Stop beyond FVG (invalidation)
- [ ] Target defined (previous extreme or opposing FVG)

### After Entry:
- [ ] Price reacting within FVG zone
- [ ] No immediate break through FVG
- [ ] Follow-through within 2 candles
- [ ] Move stop to breakeven at CE

---

## Multiple FVGs (Overlapping Zones)

When multiple FVGs overlap, the zone strengthens:
```
FVG1: $50.00 - $51.00
FVG2: $50.50 - $51.50 (overlaps partially)

Confluence Zone: $50.50 - $51.00 (overlap area)
```

**This overlap area = strongest support/resistance.**

**Trading:**
- Enter at overlap zone
- Stop below lowest FVG
- Target: Next major level

---

## FVG Timeframe Considerations

| Timeframe | Fill Rate | Best Use |
|-----------|-----------|----------|
| M1-M5 | 85%+ | Scalp entries/targets |
| M15-H1 | 75-80% | Day trade zones |
| H4 | 60-70% | Swing entries |
| Daily | 50-60% | Major zones, weekly context |
| Weekly | 30-40% | Long-term reference only |

**Rule:** Lower timeframe FVGs fill faster but are less significant. Higher timeframe FVGs act as major institutional levels.

---

## FVG Mistakes to Avoid

### 1. Trading Against HTF Trend
FVG in M5 against Daily trend = likely continuation through FVG, not reversal.

### 2. Entering Before Price Reaches FVG
"Close enough" entries miss the actual zone. Wait for price IN the FVG.

### 3. Tight Stops Within FVG
FVGs often wick to 75% depth before reversing. Stops at 25% get hit on noise.

### 4. Ignoring Mitigation
Once an FVG fills, it's done. Don't keep trying to trade "the" FVG—it's now just a level.

### 5. Chasing After Fill
If price filled FVG and continued past it = strong momentum, don't fade it.

---

## FVG Session Timing

**Best FVGs form during:**
- Killzone hours (high volume)
- Major news events (impulsive moves)
- Session opens (London/NY)

**Weakest FVGs:**
- Lunch hours (low volume gaps fill easily)
- Overnight sessions (thin markets)
- Pre-holiday trading

---

## Summary: The FVG Edge

| Element | Why It Works |
|---------|--------------|
| Formation | Aggressive imbalance leaves untraded zone |
| Retest Probability | 70-80% fill rate = high-probability zones |
| Institutional Relevance | FVGs often mark smart money entry prices |
| Confluence | Stacking FVG with OB/liquidity = strongest setups |

**Oracle's Take:** *Fair Value Gaps are footprint evidence of institutional order flow. When price leaves a gap, it's telling you WHERE aggressive buying/selling occurred. Price returns to those levels to test if that aggression was real. Your job: identify the FVG, wait for the fill, trade the reaction. The edge is patience—most traders chase the impulse, you profit from the fill.*

**The Setup:** Wait for impulse (creates FVG), mark the zone, let price return, trade the rejection from institutional defendable level.
