# 🔮 Oracle Learning: Smart Money Concepts — Liquidity, Order Blocks, FVG
**Date:** 2026-02-19 10:53 AM CT  
**Topic:** Market Structure — Smart Money Concepts  
**Time:** 15 minutes

---

## Core Concepts (ICT/SMC Framework)

"Smart Money" (institutions) leaves footprints. Three high-probability setups: Liquidity grabs, Order Block reactions, and Fair Value Gap fills.

---

## 1. Liquidity — Where Stops Cluster

### What is Liquidity?
Clusters of stop-loss orders above/below key levels where institutional orders can execute with minimal slippage.

**Visual Pattern:**
- **Sell-side liquidity:** Equal lows, swing lows, obvious support
- **Buy-side liquidity:** Equal highs, swing highs, obvious resistance

### Liquidity Sweep Setup

| Step | Action | Entry Trigger |
|------|--------|---------------|
| 1 | Identify liquidity pool (equal highs/lows) | — |
| 2 | Wait for sweep (break of level) | Candle close beyond level |
| 3 | Confirm displacement back | Strong reversal candle |
| 4 | Entry at breaker/OB | Market order or limit at 50% sweep |
| 5 | Stop beyond sweep | 1× ATR past sweep low/high |
| 6 | Target opposite liquidity | 2:1 minimum, 3:1 preferred |

**Example (Long):**
- $100, $100.10, $99.95 equal lows = liquidity pool below
- Price sweeps to $99.80 (stops triggered)
- Immediate reclaim above $100 with volume
- Entry: $100.20, Stop: $99.60, Target: $103 (prior resistance)

---

## 2. Order Blocks (OB) — Institutional Footprint

### What is an Order Block?
The last opposing candle before a strong directional move. Where institutional orders accumulated.

**Bullish OB:** Last bearish candle before aggressive up move  
**Bearish OB:** Last bullish candle before aggressive down move

### OB Entry Rules

**Valid OB Checklist:**
- [ ] Preceded by displacement (strong move away)
- [ ] Fresh (not yet tested)
- [ ] Aligned with higher timeframe trend
- [ ] Confluence with key level (FVG, liquidity, S/R)

**Entry Method:**
```
Aggressive: Limit order at OB 50% level
Conservative: Entry on first candle that respects OB
Stop: Beyond OB extreme (2-3 pips)
Target: Next liquidity pool or 2:1 minimum
```

### Mitigation vs. Invalidation
- **Mitigated:** Price touches OB, reacts, continues = valid for future reaction
- **Invalidated:** Price breaks through OB, closes beyond = level destroyed

---

## 3. Fair Value Gaps (FVG) — Imbalance Zones

### What is an FVG?
A gap between candles where price moved aggressively, leaving unfilled orders. Imbalances get filled.

**Identifying FVG:**
```
Bullish FVG: Current low > Previous high (gap up)
Bearish FVG: Current high < Previous low (gap down)

Visualization:
    Prev High ─────────
                      ↑ Gap = FVG
    Prev Low ─────────
         ↓
    Curr High ─────────
                      ↓
    Curr Low ─────────
```

### FVG Trading Strategy

| Condition | Action |
|-----------|--------|
| Price returns to FVG | Watch for reaction (rejection candle) |
| FVG + OB confluence | High probability entry |
| FVG fill in trend | With-trend continuation entry |
| FVG fill against trend | Counter-trend scalp only |

**Entry:**
- Conservative: Wait for price to enter FVG, then rejection candle
- Aggressive: Limit at FVG 50% level
- Stop: Beyond FVG extreme
- Target: Next FVG or liquidity pool

---

## 4. Multi-Timeframe Confluence

**Powerful Setup Stack:**
1. **Monthly/Weekly:** Draw liquidity levels
2. **Daily:** Identify Order Blocks
3. **4H:** Locate Fair Value Gaps
4. **1H:** Entry timing, sweep confirmation
5. **15m:** Precise entry, stop placement

**High Probability Criteria (3+ needed):**
- [ ] Liquidity sweep on LTF
- [ ] Reaction at HTF Order Block
- [ ] Price inside Fair Value Gap
- [ ]_aligned with HTF trend
- [ ] Volume confirmation on displacement

---

## 5. Risk Management — SMC Specific

| Concept | Risk Adjustment |
|---------|-----------------|
| Liquidity sweep entries | Tighter stops (sweep extreme) |
| OB entries | Stop beyond OB wick |
| FVG fills | Stop beyond gap extreme |
| Counter-trend SMC | Half size, quick targets |
| HTF + LTF confluence | Full size, wider targets |

**Max Risk:**
- Single SMC setup: 0.5% account
- Stacked setup (OB+FVG+liquidity): 1% account
- Counter-trend: 0.25% account

---

## Quick Reference: SMC Checklist

**Before Taking Trade:**
1. Identify liquidity pool above/below current price
2. Mark all fresh Order Blocks on chart
3. Draw Fair Value Gaps from recent displacement
4. Determine HTF trend direction (only trade aligned)
5. Wait for liquidity sweep on LTF
6. Confirm displacement back through OB/FVG
7. Set entry, stop (beyond sweep), target (next liquidity)
8. Check RRR ≥ 2:1

**Red Flags (Skip Trade):**
- OB already mitigated multiple times
- FVG already filled completely
- Sweep lacks volume/displacement
- Trading against clear HTF trend
- News event within 30 minutes

---

## One-Line Wisdom

> "Smart Money doesn't hide their footprints — they hide them in plain sight. Equal highs/lows, displacement candles, and gaps aren't accidents; they're roadmaps."

---

## Related Files
- Market regimes: `market-regimes.md`
- Market structure: `2026-02-19-0026-market-structure.md`
- Entry timing: `2026-02-19-0324-entry-timing.md`
- ATR stops: `2026-02-19-0624-atr-use-case.md`
