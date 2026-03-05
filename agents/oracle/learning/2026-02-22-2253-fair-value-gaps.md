# Fair Value Gaps: Price Imbalance Zones

**Topic:** Market Structure Research  
**Time:** 2026-02-22 22:53 CST  
**Duration:** 15 min learning sprint

---

## What Is a Fair Value Gap (FVG)?

A Fair Value Gap is an imbalance between buyers and sellers, visible as a gap between candles. It shows aggressive institutional activity.

---

## Identification

### Bullish FVG:
Three-candle pattern where:
- Candle 1: Bullish candle (high point)
- Candle 2: Large bullish candle (impulse)
- Candle 3: Continues up (low point)

**Gap location:** Between Candle 1's high and Candle 3's low

```
Candle 3 │    ╱╲
         │   ╱  
Candle 2 │  ╱   ← Large bullish impulse
         │ ╱    
Candle 1 │╱╲    
         │   ╲  ← Gap = FVG zone
         └────────
```

### Bearish FVG:
Three-candle pattern where:
- Candle 1: Bearish candle (low point)
- Candle 2: Large bearish candle (impulse)
- Candle 3: Continues down (high point)

**Gap location:** Between Candle 1's low and Candle 3's high

---

## Why FVGs Matter

1. **Price tends to return** to fill the imbalance
2. **Institutional entry zones** - where big money positioned
3. **Magnetic levels** - price gets drawn back
4. **Support/resistance** - acts as S/R when tested

---

## Quality Filters

| Factor | Strong FVG | Weak FVG |
|--------|------------|----------|
| **Impulse size** | Large (2+ average candles) | Small |
| **Volume** | High on middle candle | Low |
| **Context** | Fresh, unfilled | Already filled/masked |
| **Timeframe** | 15m, 1H, 4H | Sub-5m |
| **Alignment** | With higher TF trend | Against trend |

---

## Trading FVGs

### Strategy 1: FVG Retracement Entry

**Long Setup:**
1. Identify bullish FVG on 15m or 1H
2. Wait for price to retrace into FVG zone
3. Look for rejection candle inside the gap
4. Enter on candle close
5. Stop below FVG or recent swing low
6. Target: Next FVG or liquidity pool

**Short Setup:**
1. Identify bearish FVG on 15m or 1H
2. Wait for price to retrace into FVG zone
3. Look for rejection candle inside the gap
4. Enter on candle close
5. Stop above FVG or recent swing high
6. Target: Next FVG or liquidity pool

---

### Strategy 2: FVG Confluence

**Strongest signals combine:**
- FVG + Order Block overlap
- FVG + Support/Resistance level
- FVG + 50% retracement of impulse

```
Price moves up $100 to $120
Bullish FVG at $105-108
Order Block at $104-108
→ Confluence zone: $105-108 = High probability long entry
```

---

### Strategy 3: FVG Stacking

Multiple FVGs in same direction = strong trend

```
Price moves up: FVG1 → FVG2 → FVG3
               $105  $112  $118
               
Price pulls back → fills FVG3, FVG2... stops at FVG1
Entry at FVG1 = Highest confluence
```

**Rule:** The first FVG in a trend is usually the strongest.

---

## FVG Fill Probabilities

| Situation | Fill Probability | Action |
|-----------|------------------|--------|
| Trend continuation FVG | High (70%+) | Wait for retest |
| Late-trend FVG | Lower (50-60%) | Use with caution |
| Opposite FVG formation | Invalidates prior | Wait for new FVG |
| FVG + OB confluence | Highest (80%+) | Best entries |

---

## FVG vs Order Block

| Concept | Definition | Usage |
|---------|------------|-------|
| **FVG** | Gap between candles | Retracement target |
| **Order Block** | Candle before impulse | Entry trigger zone |
| **Confluence** | FVG + OB overlap | Highest probability |

**Typical flow:** OB triggers move → FVG created → Price returns to fill FVG → OB provides entry

---

## Common Mistakes

| Mistake | Correction |
|---------|------------|
| Marking every small gap | Focus on large impulses |
| Entering before price reaches FVG | Patience—wait for retrace |
| Ignoring fill status | Fresh FVGs work best |
| No confirmation candle | Always wait for rejection |
| Wrong timeframe | Use 15m+ for reliability |

---

## Timeframe Application

| TF | FVG Significance |
|----|------------------|
| 4H | Major liquidity, highest reliability |
| 1H | Standard entries |
| 15m | Good for precision entries |
| 5m | Use only within higher TF context |
| <5m | Too much noise, avoid |

---

## Quick Reference

```
Bullish FVG = Gap between candle 1 high and candle 3 low
Bearish FVG = Gap between candle 1 low and candle 3 high
Price tends to return to fill the gap
Entry = FVG retest + rejection candle
Confluence = FVG + Order Block = strongest signals
Fresh FVGs > Filled FVGs
```

> "FVGs show where price moved too fast. The return is inevitable."

---

*🔮 Oracle Learning Sprint*