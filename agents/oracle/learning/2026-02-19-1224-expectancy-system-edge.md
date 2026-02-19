# 🔮 Oracle Learning: Expectancy & System Edge — The Profitability Formula
**Date:** 2026-02-19 12:24 PM CT  
**Topic:** Trading Concept — Expectancy & System Edge  
**Time:** 15 minutes

---

## Core Formula

**Expectancy** = (Win Rate × Avg Win) − (Loss Rate × Avg Loss)

Or normalized per dollar risked:

**Expectancy Ratio** = (Win% × Avg R) − (Loss% × Avg R Loss)

Where R = risk unit (1R = amount risked per trade)

---

## Expectancy Tiers

| Expectancy | Status | Action Required |
|------------|--------|-----------------|
| < 0 | Losing system | Stop trading, fix edge |
| 0 to 0.1 | Breakeven/slight loss | Marginal, high variance |
| 0.1 to 0.2 | Modest edge | Viable with tight risk |
| 0.2 to 0.4 | Solid edge | Good system, trade it |
| > 0.4 | Strong edge | Scale, but watch for decay |

---

## Real Examples

### Example A: High Win Rate, Low RRR
```
Win Rate: 60%
Avg Win: 1.0R
Avg Loss: 1.0R

Expectancy = (0.60 × 1.0) − (0.40 × 1.0) = 0.60 − 0.40 = +0.20R

Result: Profitable but thin. 40% losses wipe out much of the gains.
```

### Example B: Low Win Rate, High RRR
```
Win Rate: 35%
Avg Win: 3.0R
Avg Loss: 1.0R

Expectancy = (0.35 × 3.0) − (0.65 × 1.0) = 1.05 − 0.65 = +0.40R

Result: Strong edge. Fewer wins but they pay for all losses + profit.
```

### Example C: The Danger Zone (Scalpers Beware)
```
Win Rate: 55%
Avg Win: 0.8R
Avg Loss: 1.0R

Expectancy = (0.55 × 0.8) − (0.45 × 1.0) = 0.44 − 0.45 = −0.01R

Result: **Losing system** despite 55% win rate. Asymmetric losses destroy edge.
```

---

## Win Rate vs. RRR Matrix

Target: **Expectancy ≥ 0.2R**

| Win Rate | Min Avg Win (R) | Expectancy |
|----------|-----------------|------------|
| 80% | 0.5R | +0.30R |
| 70% | 0.7R | +0.19R (marginal) |
| 60% | 1.0R | +0.20R |
| 50% | 1.5R | +0.25R |
| 40% | 2.0R | +0.20R |
| 30% | 3.0R | +0.20R |
| 25% | 4.0R | +0.20R |

**Insight:** A 60% win rate with 1:1 RRR = 0.20R expectancy. A 30% win rate with 3:1 RRR = same expectancy. Both are viable; choose what fits your psychology.

---

## System Quality: SQN (System Quality Number)

**SQN** = Expectancy / Standard Deviation of R × √Number of Trades

Or simplified: **Expectancy / Standard Deviation of R**

| SQN | Quality | Position Sizing |
|-----|---------|-----------------|
| < 1.0 | Poor | Don't trade |
| 1.0–1.5 | Below average | 0.5% risk max |
| 1.5–2.0 | Average | 1% risk |
| 2.0–2.5 | Good | 1–2% risk |
| 2.5–3.0 | Excellent | 2–3% risk |
| > 3.0 | Superb | 3%+ risk (with care) |

**Why it matters:** High expectancy with high variance (unstable results) = dangerous. SQN measures consistency.

---

## Practical Application

### Step 1: Calculate Your Current System

Track last 50–100 trades:
1. Record R-multiple for each trade (profit or loss / risk amount)
2. Calculate average win, average loss, win rate
3. Compute expectancy
4. Calculate standard deviation of R
5. Derive SQN

### Step 2: Optimize

**If expectancy < 0:**
- Review entries (are you catching knives?)
- Check stops (too tight = noise)
- Verify exits (cutting winners short?)

**If expectancy > 0 but SQN < 1.5:**
- Reduce variance: tighter entry criteria
- Filter: only trade A+ setups
- Add confluence requirements

### Step 3: Position Sizing Based on SQN

```
Risk per Trade = Account × (SQN-based %)

Example ($100k account):
SQN 1.6 (Average): $100k × 1% = $1,000 risk
SQN 2.3 (Good): $100k × 1.5% = $1,500 risk  
SQN 2.8 (Excellent): $100k × 2.5% = $2,500 risk
```

---

## Common Traps

| Trap | Why It Fails | Fix |
|------|--------------|-----|
| Optimizing for win rate only | Can have 70% wins and lose money | Always check expectancy |
| Ignoring R-multiples | $100 win vs $500 loss = disaster | Track R, not dollars |
| Small sample size | 10 trades = noise | Minimum 30 trades, ideally 100+ |
| Curve-fitting | Optimized to past, fails in future | Out-of-sample testing |
| Not updating metrics | Markets change | Recalculate monthly |

---

## Quick Calculator

**Back-of-napkin expectancy check:**

```
My system: _______% win rate
Avg win: _______ R
Avg loss: _______ R (usually 1.0)

Expectancy = (Win% × Avg Win) − ((1−Win%) × Avg Loss)
           = (____ × ____) − (____ × ____)
           = __________ R

Is it ≥ 0.2R? ☐ Yes (trade it) ☐ No (fix it)
```

---

## One-Line Wisdom

> "Win rate is vanity, expectancy is sanity. A 40% win rate with 3:1 RRR beats a 60% win rate with 0.8:1 RRR every time. Math doesn't care about your ego."

---

## Related Files
- Risk/reward: `2026-02-19-0453-risk-reward-optimization.md`
- Position sizing series: `2026-02-18-*-position-sizing*.md`
- Trade management: `2026-02-19-0753-trade-management-scaling.md`
- Kelly criterion: `2026-02-18-1053-kelly-criterion-position-sizing.md`
