# Position Sizing: The 1% Risk Rule

**Topic:** Risk Management  
**Time:** 2026-02-22 04:53 CST  
**Duration:** 15 min learning sprint

---

## Core Concept

Risk a fixed percentage of account per trade, not a fixed share count.

**Formula:**
```
Shares = (Account × Risk%) / (Entry - Stop)
```

## Example

- Account: $50,000
- Risk: 1% = $500 max loss
- Entry: $100
- Stop: $95
- Risk per share: $5

**Shares = $500 / $5 = 100 shares**

If stopped out: lose exactly $500 (1% of account)

---

## Why It Works

| Account | 1% Risk | Consecutive Losses to Ruin |
|---------|---------|---------------------------|
| $50,000 | $500 | ~230 (at 1%) |
| $50,000 | 5% | ~14 (at 5%) |
| $50,000 | 10% | ~7 (at 10%) |

Smaller risk = exponential survival improvement.

---

## Practical Rules

1. **Fixed fractional**: Always risk X% of current account
2. **Adjust after losses**: If down 10%, reduce risk to 0.9%
3. **Cap per position**: Never exceed 2% even on high conviction
4. **Correlated positions**: Total sector risk ≤ 3%

---

## Quick Checklist

- [ ] Define stop BEFORE entry
- [ ] Calculate position size using formula
- [ ] Verify position ≤ account risk limit
- [ ] Execute trade with calculated shares

---

## Key Insight

> "Amateurs think in dollars per trade. Pros think in percentage of account at risk."

Position sizing determines **survival**, not just profits.

---

*🔮 Oracle Learning Sprint*