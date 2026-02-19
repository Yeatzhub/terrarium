# 🔮 Oracle Learning: Risk/Reward Ratio Optimization
**Date:** 2026-02-19 04:53 AM CT  
**Topic:** Trading Concept — Risk/Reward Ratio (RRR)  
**Time:** 15 minutes

---

## Core Concept

Risk/Reward Ratio (RRR) = Potential Reward : Risk Taken

**Formula:** RRR = (Target Price − Entry Price) / (Entry Price − Stop Loss)

---

## The 3:1 Myth vs. Reality

| RRR | Win Rate Needed (Breakeven) | Reality |
|-----|----------------------------|---------|
| 1:1 | 50% | High stress, no edge |
| 2:1 | 33% | Minimum viable target |
| 3:1 | 25% | Industry standard, but rigid |
| 5:1 | 17% | Requires wider stops, lower win rate |

**Key Insight:** Higher RRR ≠ Better. A 5:1 setup with 10% win rate loses money. A 2:1 with 45% win rate profits.

---

## Practical Framework

### Step 1: Let the Market Set Your RRR
Don't force 3:1. Calculate RRR based on:
- Technical structure (support/resistance levels)
- Volatility (ATR-based targets)
- Market regime (trending vs. ranging)

### Step 2: Minimum RRR by Strategy Type
```
Scalping:        1:1 to 1.5:1  (high frequency, tight stops)
Day Trading:     2:1 minimum   (intraday volatility)
Swing Trading:   3:1 to 5:1    (overnight risk compensation)
Position:        5:1+          (fundamental thesis, wide stops)
```

### Step 3: The RRR × Win Rate Formula
Expected Value = (Win Rate × Avg Win) − (Loss Rate × Avg Loss)

**Example:**
- Win Rate: 40%
- Avg Win: $300 (3:1 RRR)
- Avg Loss: $100
- EV = (0.40 × 300) − (0.60 × 100) = $120 − $60 = **+$60 per trade**

---

## Dynamic RRR Adjustment

| Condition | Action | RRR Adjustment |
|-----------|--------|----------------|
| High volatility (>2x ATR) | Widen stops, extend targets | 4:1 to 5:1 |
| Low volatility (<0.5x ATR) | Tighten stops, reduce targets | 2:1 to 2.5:1 |
| Strong trend | Trail stops, let winners run | Start 2:1, scale to 5:1+ |
| Choppy/range | Fixed targets at range bounds | 2:1 strict |
| Pre-news/event | Reduce position, widen stops | 4:1+ required |

---

## Quick Implementation Checklist

- [ ] Calculate RRR **before** entering (never after)
- [ ] RRR < 2:1 → Skip trade (unless scalping with 60%+ win rate)
- [ ] Adjust position size if RRR demands wider stop
- [ ] Book partial profits at 1:1, 2:1, 3:1 (scale out)
- [ ] Review monthly: actual RRR achieved vs. planned

---

## Common Pitfalls

1. **Moving target to justify entry** → RRR must be set by technicals, not desire
2. **Ignoring win rate impact** → A 2:1 strategy with 45% wins beats 4:1 with 15% wins
3. **Static RRR across regimes** → Trending markets tolerate wider RRR; chop needs tighter
4. **Not accounting for slippage** → Subtract 0.1-0.2R for realistic execution

---

## One-Line Wisdom

> "Set your stop where you're wrong, set your target where you're right — the ratio between them is the market's gift, not your demand."

---

## Related Files
- Position sizing series: `2026-02-18-*-position-sizing*.md`
- Entry timing: `2026-02-19-0324-entry-timing.md`
- Market structure: `2026-02-19-0026-market-structure.md`
- Market regimes: `market-regimes.md`
