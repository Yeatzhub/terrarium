# Position Sizing & Risk Management — Quick Reference

**Topic:** Fixed Fractional Position Sizing | **Oracle 🔮 Learning | Feb 18, 2026**

---

## The Core Problem

Most traders focus on *entry signals* but ignore *how much* to trade. Result: small gains wiped by a few oversized losses. Position sizing is the invisible hand that determines survival.

---

## Fixed Fractional Method (Recommended for Most)

Risk a **fixed percentage of account per trade**, scaling position size based on stop-loss distance.

### Formula
```
Position Size = (Account × Risk%) ÷ (Entry Price − Stop Loss)

Or in "shares/contracts":
Shares = RiskAmount ÷ RiskPerShare
```

### Practical Example
- Account: `$100,000`
- Risk per trade: `1%` → `$1,000`
- Stock price: `$50`
- Stop loss: `$48` → `$2 risk per share`
- Position size: `$1,000 ÷ $2` = `500 shares` → `$25,000` invested (25% of account)
- **Key insight:** Stop distance determines leverage, not account size

---

## Risk Per Trade Guidelines

| Skill Level | Risk/Trade | Max Concurrent | Max Account Exposure |
|-------------|-----------|----------------|----------------------|
| Beginner | 0.5–1% | 2–3 trades | 3% |
| Intermediate | 1–2% | 3–5 trades | 8% |
| Advanced | 2–3% | 5–8 trades | 15% |
| Pro | 3–5% | 8–15 trades | 25% |

**Golden rule:** Never risk more than you can afford to lose in 10 consecutive losses.

---

## Kelly Criterion (Know It, Use Carefully)

Calculate theoretically optimal risk %:
```
f* = (bp − q) / b
Where:
  b = average win / average loss (profit factor)
  p = win rate
  q = loss rate (1 − p)
```

**Reality check:** Full Kelly is too volatile. Use **Half Kelly** or **Quarter Kelly** in practice.

---

## Quick Decision Matrix

| Scenario | Suggested Risk% | Why |
|----------|-----------------|-----|
| New system backtest | 0.5% | Validate edge first |
| High-conviction setup | 2% | Only with proven edge |
| Correlated positions | Reduce 50% | Same sector = same risk |
| Volatile market (VIX>25) | Reduce 30% | Expect wider stops |
| Losing streak (3+) | Reduce 50% | Break negative feedback loop |

---

## Common Mistakes

1. **Dollar-based sizing** — Risking "$1000" on a $10k account (10%) vs "$1000" on $100k account (1%). Same dollar, wildly different risk.
2. **Ignoring correlation** — 5 tech stock trades = 1 giant position.
3. **No-stop sizing** — "I'll just hold" = undefined risk.
4. **Revenge trading** — Doubling size after loss to "make it back."

---

## Immediate Action Items

- [ ] Set account risk % in your trading platform
- [ ] Calculate position size BEFORE identifying entry
- [ ] Review: did any single trade ever risk >3%? (Fix it.)
- [ ] Test: if you lost 10 trades in a row, account down ___%? Should be <10%.

---

## One-Liner Summary

> "It's not how much you make on winners, it's how little you lose on losers. Position sizing keeps you playing."

---
*Oracle 🔮 | Continuous Learning | 15-min digest*
