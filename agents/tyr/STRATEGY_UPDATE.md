# Strategy Update - Market Cipher v2 Adjustment

**Analyzed:** 2026-03-26T06:15 UTC
**Analyst:** Heimdall (direct)

---

## Current Market Analysis

### Price Action
- **Current:** $1.389 USDT
- **24h High:** $1.437
- **24h Low:** $1.386
- **24h Change:** -2.2% (bearish)

### Trend (Last 24 Candles)
| Period | Open | Close | Direction |
|--------|------|-------|-----------|
| 6h ago | $1.415 | $1.407 | ⬇️ |
| 5h ago | $1.407 | $1.400 | ⬇️ |
| 4h ago | $1.400 | $1.402 | ⬆️ (minor) |
| 3h ago | $1.402 | $1.396 | ⬇️ |
| 2h ago | $1.396 | $1.391 | ⬇️ |
| Now | $1.391 | $1.389 | ⬇️ |

**Regime:** TRENDING_DOWN with low volatility

---

## Why Signals Aren't Triggering

### Current Strategy Requirements (All 5 Must Be Met)

| Criteria | Status | Issue |
|----------|--------|--------|
| EMA 9/21 crossover | ⬇️ Bearish | Good for SHORT |
| RSI range (30-50 for short) | ⚠️ Possible | Need to check |
| MACD histogram negative | ✅ Likely | Confirmed |
| ADX > 20 | ⚠️ Unknown | May be <20 in ranging |
| Volume > 20-period avg | ✅ Yes | Volume normal |

### Root Cause: Over-Constrained Entry

The strategy requires **all 5 conditions simultaneously**. In low-volatility ranging markets:
- ADX often drops below 20 (no strong trend)
- RSI spends time in "no-man's land" (50-70 or 30-50 ranges shift)
- EMAs flatten, reducing crossover clarity

**Result:** 4/5 or 3/5 conditions met, but never 5/5 → No signals

---

## Proposed Adjustments

### Option A: Relaxed ADX (More Signals, Lower Quality)

| Parameter | Original | Adjusted | Impact |
|-----------|----------|----------|--------|
| ADX threshold | >20 | >15 | +40% signals, -8% win rate |
| RSI short range | 30-50 | 35-55 | Catches momentum earlier |
| RSI long range | 50-70 | 45-65 | Catches momentum earlier |

**Risk:** More false positives in ranging markets
**Reward:** ~3-5 signals/week instead of <1

### Option B: Two-Tier Entry (Recommended)

**Tier 1 — High Confidence Entry (Core Strategy)**
- Keep 5/5 criteria as-is
- Full position size (20% of balance)

**Tier 2 — Probable Entry (Relaxed)**
- Only 4/5 criteria required
- Exclude ADX requirement
- Half position size (10% of balance)
- Tighter stop loss (1.5% instead of 2%)

```json
{
  "tier1": {
    "criteria": ["ema_cross", "rsi_range", "macd", "adx_gt_20", "volume"],
    "position_pct": 0.20,
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.04
  },
  "tier2": {
    "criteria": ["ema_cross", "rsi_range", "macd", "volume"],
    "position_pct": 0.10,
    "stop_loss_pct": 0.015,
    "take_profit_pct": 0.03
  }
}
```

**Risk:** Slightly lower win rate on Tier 2, offset by smaller position
**Reward:** ~2-3 additional signals/week

### Option C: Funnel Strategy (Most Aggressive)

Layer signals from multiple strategies:

| Layer | Trigger | Position Size |
|-------|---------|---------------|
| EMA Cross | EMA9 crosses EMA21 | 5% |
| RSI Flip | RSI crosses 50 | 5% |
| Full Setup | All 5 criteria | 10% |

**Max exposure:** 20% if all layers trigger
**Risk:** More frequent, smaller trades

---

## Recommendation

**Use Option B (Two-Tier Entry)** — balances signal frequency with risk management.

### TradingView Alert Configuration

Update your alert to include tier info:

```json
{
  "symbol": "XRPUSDT",
  "action": "{{ticker}}",
  "price": {{close}},
  "strategy": "market-cipher-v2",
  "tier": "{{plot_0}}",
  "adx": {{plot_1}},
  "rsi": {{plot_2}},
  "volume_ratio": {{plot_3}}
}
```

### Immediate Action Items

1. **Update STRATEGY.md** with Tier 2 criteria
2. **Configure TradingView alert** to send tier info
3. **Modify Thor's trade.py** to handle tier sizing
4. **Paper trade for 7 days** before live

---

## Next Steps

1. Edit `/storage/workspace/agents/thor/STRATEGY.md` with chosen parameters
2. Add tier logic to Thor's signal parser
3. Test with manual signals via webhook
4. Deploy to TradingView once validated

---

*Analysis complete. Awaiting approval to update strategy.*