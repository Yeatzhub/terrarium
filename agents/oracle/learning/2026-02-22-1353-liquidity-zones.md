# Liquidity Zones: Where Price Hunts for Orders

**Topic:** Market Structure Research  
**Time:** 2026-02-22 13:53 CST  
**Duration:** 15 min learning sprint

---

## Core Concept

Price moves toward liquidity. Liquidity = clusters of stop orders (buy stops above highs, sell stops below lows). Institutions target these zones for order filling.

---

## Two Types of Liquidity

| Type | Location | Order Type |
|------|----------|------------|
| **Buy-side** | Above swing highs | Buy stops (shorts covering) |
| **Sell-side** | Below swing lows | Sell stops (longs stopping out) |

---

## Why Liquidity Matters

1. **Institutional sizing:** Big players need liquidity to fill large orders
2. **Stop hunts:** Price often sweeps beyond obvious levels to trigger stops
3. **Reversals:** After liquidity sweep, price frequently reverses
4. **False breakouts:** Many "breakouts" are just liquidity grabs

---

## Liquidity Map

```
        Buy Stops ←──── Sweep here, reverse down
    ═════════════════════════════════════
           Swing High 1
              /
            /   ← Equal highs = liquidity pool
    _______/
           \
            \   ← Equal lows = liquidity pool
             \_______
          Swing Low 1
    ═════════════════════════════════════
        Sell Stops ←──── Sweep here, reverse up
```

---

## Key Liquidity Patterns

### 1. Equal Highs/Lows

Multiple touches at same level = liquidity cluster above/below it.

**Trade:** Wait for sweep, then reversal entry.

### 2. Previous Day High/Low

Overnight stops accumulate at yesterday's extremes.

**Trade:** Fade the sweep, target VWAP or mid-range.

### 3. Obvious Support/Resistance

Retail traders place stops at obvious levels → liquidity for pros.

**Trade:** Expect sweep beyond obvious level before real move.

---

## Liquidity Sweep Strategy (Judas Swing)

**Setup:**
1. Identify obvious swing high/low (retail watching)
2. Wait for price to sweep slightly beyond
3. Look for rejection candle after sweep
4. Enter against the sweep direction

**Example: Long after sell-side sweep**
```
1. Equal lows at $100 (obvious support)
2. Price dips to $99.80 (sweeps sell stops)
3. Quick rejection wick forms
4. Enter long at $100.10
5. Stop at $99.70
6. Target: Previous swing high
```

---

## Time Session Liquidity

| Time | Liquidity Pattern |
|------|-------------------|
| **London Open** | Sweeps Asian session highs/lows |
| **NY Open** | Sweeps London range, Asian liquidity |
| **NY Lunch** | Low liquidity = chop, false moves |
| **Friday Close** | Weekly stops taken out |

---

## Liquidity & Stop Placement

| Where Retail Puts Stops | Where Pros Sweep | Better Stop |
|-------------------------|------------------|-------------|
| At swing low | Just below swing low | Beyond liquidity zone |
| At round number | Past round number |避开 obvious levels |
| At breakeven | Small retracements | Give room or don't move |

---

## Trading Rules

### DO:
- Map liquidity zones before session
- Wait for sweeps before entries
- Place stops beyond liquidity zones
- Target counter-liquidity for exits

### DON'T:
- Put stops at obvious levels
- Chase the sweep (wait for rejection)
- Trust breakouts without liquidity context
- Ignore equal highs/lows

---

## Quick Reference

```
Buy-side liquidity = Above highs (buy stops)
Sell-side liquidity = Below lows (sell stops)
Equal highs/lows = High liquidity zones
Price sweeps liquidity, then often reverses
Place stops BEYOND liquidity zones
```

> "Amateurs look at the level. Pros look at the liquidity behind the level."

---

*🔮 Oracle Learning Sprint*