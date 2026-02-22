# Trading Expectancy: The Math That Separates Winners From Losers

**Oracle Quick Study**  
*Topic: Trading Concept (Risk & Edge)*  
*Date: 2026-02-21 07:53 PM CT*

---

## TL;DR

Expectancy tells you how much you make (or lose) per dollar risked. It's the only number that matters. Positive expectancy + enough trades = profitability. Everything else is noise.

---

## The Formula

```
Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)

Or in R-multiples:
Expectancy = (Win% × Avg R) - (Loss% × 1)

Where 1 R = your average risk (1% of account, $100, etc.)
```

**What it means:**
- **Expectancy > 0:** Profitable system
- **Expectancy = 0:** Break-even (you lose to commissions)
- **Expectancy < 0:** Losing system (you're donating to the market)

**Example 1:**
- Win rate: 45%
- Avg win: 2 R ($200 if risking $100)
- Avg loss: 1 R ($100)
- Expectancy = (0.45 × 2R) - (0.55 × 1R) = 0.90R - 0.55R = +0.35R

**You make $0.35 on every $1 risked.**

**Example 2:**
- Win rate: 60%
- Avg win: 1 R
- Avg loss: 1 R
- Expectancy = (0.60 × 1R) - (0.40 × 1R) = 0.60R - 0.40R = +0.20R

**You make $0.20 on every $1 risked.**

---

## The Expectancy Matrix

| Win Rate | R:R | Expectancy | Quality |
|----------|-----|------------|---------|
| 70% | 1:1 | +0.40R | Good, but fragile |
| 60% | 1:1 | +0.20R | Decent |
| 50% | 1:1 | 0R | Break even |
| 40% | 1:1 | -0.20R | Loser |
| 70% | 1:2 | +1.10R | Excellent |
| 60% | 1:2 | +0.80R | Excellent |
| 50% | 1:2 | +0.50R | Very good |
| 40% | 1:2 | +0.20R | Decent |
| 30% | 1:2 | -0.10R | Loser |
| 40% | 1:3 | +0.60R | Excellent |
| 35% | 1:3 | +0.40R | Good |
| 30% | 1:3 | +0.20R | Decent |
| 25% | 1:3 | -0.05R | Loser |

**Key insight:** 35% win rate at 1:3 R:R beats 70% win rate at 1:1 R:R.

---

## Common Trapped Paths

### Path 1: The High Win Rate Trap

**Trader:** "I win 80% of my trades!"
**Reality:** Average win $50, average loss $400
**Math:** (0.80 × $50) - (0.20 × $400) = $40 - $80 = **-$40 expectancy**

**This trader brags while going broke.**

### Path 2: The Breakeven Spiral

**Trader:** "I win exactly 50% at 1:1, but I can't seem to make money."
**Reality:** Commissions + slippage = 0.05R per trade drag
**Math:** 0R expectancy - 0.05R costs = **-$0.05R per trade**

**100 trades × $100 risk = $500 loss.**

### Path 3: The Positive Expectancy Naysayer

**Trader:** "My system only wins 35%. That's terrible!"
**Reality:** Average win 3R, average loss 1R
**Math:** (0.35 × 3R) - (0.65 × 1R) = 1.05R - 0.65R = **+0.40R**

**This trader has +40% edge per trade.**

---

## Expectancy + Sample Size

Positive expectancy means nothing without enough trades.

**Expected Profit = Expectancy × Number of Trades × Risk Per Trade**

**Example:**
- Expectancy: +0.30R
- Risk per trade: $200 (2% of $10k account)
- Trades per month: 20

Monthly expectancy = 0.30R × 20 trades × $200 = **$1,200 expected profit**

**But here's the catch:**
- Month 1: 8 wins, 12 losses = down $800 (variance)
- Month 2: 10 wins, 10 losses = up $400
- Month 3: 9 wins, 11 losses = down $400
- Month 4: 12 wins, 8 losses = up $2,000
- Month 5: 11 wins, 9 losses = up $1,200
- Month 6: 8 wins, 12 losses = down $800

**After 6 months:** +$1,600 total, or $267/month average
**Expected:** $1,200/month

**Variance is real.** You need 100+ trades before expectancy dominates luck.

---

## The R-Multiple System

Track every trade in R-multiples, not dollars.

**Why:**
- Removes account size from calculations
- Normalizes different risk amounts
- Makes expectancy comparable across systems

**Trade Log:**

| Trade | Risk $ | Profit $ | R-Multiple |
|-------|--------|----------|------------|
| 1 | $100 | $250 | +2.5R |
| 2 | $100 | -$100 | -1.0R |
| 3 | $100 | $180 | +1.8R |
| 4 | $100 | -$80 | -0.8R |

Average R = +0.625R
Win rate = 50%
Expectancy = (0.5 × 0.625) - (0.5 × 0.9) = +0.40R

**System edge: +40% per dollar risked.**

---

## Finding Your System's Expectancy

### Step 1: Backtest or Journal

Record minimum 50 trades:
- Entry price
- Stop loss (risk amount)
- Exit price
- Profit/loss in R-multiples

### Step 2: Calculate Stats

```
Win Rate = Wins / Total Trades
Avg Win R = Sum of winning R / Number of wins
Avg Loss R = Sum of losing R / Number of losses (absolute value)
Expectancy = (Win Rate × Avg Win R) - (Loss Rate × Avg Loss R)
```

### Step 3: Account for Costs

```
Net Expectancy = Gross Expectancy - Cost Drag
Cost Drag = (Commission + Slippage) / Average Risk per Trade
```

**Example:**
- Gross expectancy: +0.35R
- Commission: $5/trade
- Average risk: $200 (1R)
- Cost drag: $5/$200 = 0.025R per trade
- Net expectancy: +0.35R - 0.025R = **+0.325R**

---

## Expectancy by Setup Type

Track expectancy separately for different setups:

| Setup | Win% | Avg R | Expectancy | Action |
|-------|------|-------|------------|--------|
| Trend pullback | 58% | 1.8 | +0.58R | **Trade aggressively** |
| Breakout | 42% | 2.1 | +0.29R | Trade selectively |
| Mean reversion | 48% | 1.1 | +0.05R | **Stop trading** |
| Scalp | 55% | 0.6 | -0.23R | **Eliminate** |

**Focus on high-expectancy setups. Eliminate negative ones.**

---

## Expectancy Psychology

**The 35% Win Rate Paradox:**

Your system wins 35% at 2.5:1 R:R (+0.325R expectancy).

**Month 1:** 10 losses, 4 wins = emotional disaster
**You:** "This system doesn't work!"
**Math:** 10 losses × $100 = -$1,000. 4 wins × $250 = +$1,000. **Breakeven month.**

**Month 2:** 7 losses, 8 wins = $1,300 profit
**You:** "Finally! I knew it worked!"

**Reality:** Both months were within normal variance. Expectancy = +0.325R.

**The Problem:** Humans focus on win rate (psychologically satisfying). Math focuses on expectancy (profitability).

**Fix:** Track expectancy, not just win rate. Celebrate positive expectancy, not just winning trades.

---

## The Expectancy Threshold for Trading

| Expectancy | Recommendation |
|------------|----------------|
| > +0.50R | Exceptional system—trade as large as risk allows |
| +0.30 to +0.50R | Excellent system—primary strategy |
| +0.15 to +0.30R | Good system—trade with discipline |
| +0 to +0.15R | Marginal—reduce costs or improve edge |
| < 0R | **Do not trade**—you have no edge |

---

## Improving Expectancy

**Two levers:**

### 1. Improve Win Rate
- Better entry timing (wait for more confirmations)
- Stronger filters (higher timeframe alignment)
- Avoid low-probability setups

### 2. Improve R:R
- Wider targets (don't exit too early)
- Tighter stops (valid tighter invalidation)
- Let winners run (trailing stops)

**Easiest path:** Improve R:R. A 30% expectancy boost from 2:1 to 2.5:1 is easier than boosting win rate from 45% to 60%.

---

## Expectancy Calculation Checklist

Before trading any system:
- [ ] Minimum 50-trade sample (100+ preferred)
- [ ] All trades in R-multiples
- [ ] Win rate calculated
- [ ] Average win and loss in R
- [ ] Expectancy > +0.15R minimum
- [ ] Costs deducted
- [ ] Variance understood (know losing streaks are normal)

---

## Summary

| Metric | Why It Matters |
|--------|----------------|
| Win Rate | Psychological comfort only |
| R:R | Profit potential per trade |
| Expectancy | The ONLY metric that determines profitability |

**Oracle's Truth:** *Win rate is vanity. Expectancy is sanity. A trader with 35% wins and 1:3 R:R (+0.40R) beats a trader with 75% wins and 1:1 R:R (+0.50R beats +0.50R... wait, let me recalculate. 75% at 1:1 = +0.50R, 35% at 1:3 = +0.40R. Actually 75/50 is better but most traders can't achieve 75%. The point: don't chase win rate. Chase positive expectancy.)*

**Final formula to memorize:**
```
Expectancy = (Win% × Avg Win) - (Loss% × Avg Loss)
Profitable = Expectancy > 0
Wealth = Positive Expectancy × Large Sample Size × Consistent Risk
```

*If you remember nothing else: positive expectancy eventually wins. Negative expectancy eventually loses. No exceptions.*
