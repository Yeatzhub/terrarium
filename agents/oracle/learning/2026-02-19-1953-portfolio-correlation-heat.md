# 🔮 Oracle Learning: Portfolio Correlation & Heat — Multi-Position Risk
**Date:** 2026-02-19 19:53 PM CT  
**Topic:** Trading Concept — Portfolio Risk Management  
**Time:** 15 minutes

---

## The Problem

You size each trade at 1% risk. You take 5 trades. Market moves against you. You lose **5%** — or do you?

**Reality:** If all 5 positions are correlated, you could lose **10–15%** in a single move.

---

## Understanding Correlation

**Correlation (ρ)** = How two assets move together (-1 to +1)

| Correlation | Meaning |
|-------------|---------|
| +1.0 | Perfect positive (move identical) |
| +0.7 to +0.9 | Strong positive (move together) |
| +0.3 to +0.6 | Moderate positive |
| 0 | No correlation |
| -0.3 to -0.6 | Moderate negative |
| -0.7 to -0.9 | Strong negative (hedge) |
| -1.0 | Perfect negative (mirror) |

### Common Correlations (Approximate)

**Strong Positive (+0.8 to +0.95):**
- SPY / QQQ / IWM (US indices)
- AAPL / MSFT / GOOGL (big tech)
- BTC / ETH (crypto majors)
- XLE / OIL (energy sector / crude)
- EUR/USD / GBP/USD (EUR pairs)

**Moderate Positive (+0.4 to +0.7):**
- SPY / GLD (stocks vs gold)
- Tech stocks / ARKK (growth correlation)
- USD/JPY / US 10Y yields

**Low/No Correlation (0 to +0.3):**
- SPY / TLT (stocks vs bonds, varies)
- GLD / BTC (flight assets, varies)
- Commodities vs individual stocks

**Negative Correlations:**
- SPY / VIX (inverse, typically -0.8)
- USD / Commodities (typically -0.6)

---

## Portfolio Heat Calculation

**Portfolio Heat** = Total correlated risk exposure

### Simple Method

```
For each position:
Risk = Position Size × Stop Distance

Group by correlation:
Group Risk = Sum of individual risks in group

Total Heat = Sum of all group risks (with correlation factor)

Correlation Factor:
Uncorrelated (ρ < 0.3): 1.0×
Moderate (ρ 0.3–0.6): 1.3×
Strong (ρ > 0.6): 1.8×
Perfect (ρ > 0.9): 2.0× (treat as single position)
```

### Example

```
Positions:
1. SPY long, 1% risk
2. QQQ long, 1% risk (ρ = 0.85 with SPY)
3. AAPL long, 1% risk (ρ = 0.70 with SPY)
4. GLD long, 1% risk (ρ = 0.20 with SPY)
5. BTC long, 1% risk (ρ = 0.40 with SPY)

Calculation:
Tech/Indices Group (SPY, QQQ, AAPL): 3% × 1.8 (strong corr) = 5.4% effective
Gold: 1% × 1.0 = 1%
BTC: 1% × 1.3 (mod corr) = 1.3%

Total Portfolio Heat: ~7.7%

If all 5 moved 2% against you:
Uncorrelated assumption: -5%
Actual correlated loss: -7.7%+
```

---

## Correlation Rules for Sizing

### Rule 1: Strong Correlation = Same Position

If ρ > 0.85, treat as one trade for sizing.

**Example:**
- SPY position: 1% risk
- Want QQQ too? Split the 1% → 0.5% SPY, 0.5% QQQ
- Or skip QQQ, find uncorrelated play

### Rule 2: Sector Max Exposure

Max 3% heat per correlated sector:
- Tech (AAPL, MSFT, NVDA): Combined ≤3%
- Financials (JPM, BAC, XLF): Combined ≤3%
- Crypto (BTC, ETH, SOL): Combined ≤3%

### Rule 3: Asset Class Limits

| Asset Class | Max Heat |
|-------------|----------|
| US Equities | 5% |
| International | 2% |
| Crypto | 3% |
| Commodities | 2% |
| Forex | 2% |
| Bonds | 1% |

---

## Practical Portfolio Management

### Pre-Trade Checklist

1. **List all open positions** with current P&L
2. **Calculate uncorrelated heat** (simple sum of individual risks)
3. **Group by correlation** (use ρ > 0.6 threshold)
4. **Calculate correlated heat** (apply factors)
5. **Check:** Total heat < 8% account?
6. **Check:** No single group > 3%?
7. If exceeded, **reduce size or skip trade**

### Correlation Monitoring

**Weekly review:**
- Check correlation heat map
- Adjust if correlations shifting (e.g., all risk assets correlation spiking in crash)
- Reduce sizes during high correlation environments (crises)

**Crisis behavior:**
- Correlations → +1.0 during panic (everything falls together)
- Diversification fails when you need it most
- **Solution:** Reduce total heat to 5% in volatile regimes

---

## Beta-Adjusted Sizing

**Beta (β)** = Sensitivity to market (SPY = 1.0)

| Asset | Beta | Adjustment |
|-------|------|------------|
| TLT (bonds) | -0.3 | Can size 1.5× |
| SPY | 1.0 | Baseline |
| QQQ | 1.2 | Size 0.8× |
| TQQQ (3×) | 3.0+ | Size 0.3× or avoid |
| BTC | 1.5+ | Size 0.6× |

**Formula:**
```
Adjusted Size = Target Risk / (Beta × Volatility Factor)
```

---

## Hedging with Correlation

**Natural Hedges:**
- Long SPY + Short VIX (partial)
- Long Tech + Short ARKK (pairs)
- Long USD + Short Gold (inverse)

**Portfolio Heat Reduction:**
- Net heat = Long heat − Hedge heat
- Example: 5% long + 2% short hedge = 3% net

**Warning:** Hedges cost money. Only hedge during high conviction or drawdown protection.

---

## Quick Correlation Cheat Sheet

### High Correlation Avoid (simultaneous positions)
- SPY + QQQ + IWM (pick one)
- AAPL + MSFT + NVDA (pick one, split size)
- BTC + ETH (split size)
- XLE + USO (pick one)
- EUR/USD + GBP/USD (pick one)

### Moderate Correlation (reduce size 30%)
- Tech stocks + BTC
- SPY + GLD (flight correlation spikes in crashes)

### Low Correlation (full size OK)
- SPY + TLT (usually)
- Individual sectors (XLK + XLF + XLU)
- Different asset classes

---

## Common Mistakes

| Mistake | Result | Fix |
|---------|--------|-----|
| 5 tech positions at 1% each | 5% becomes 9%+ heat | Sector limit 3% |
| SPY + QQQ + TQQT | Triple leverage on same move | Pick one |
| Correlation during calm only | Crash = all correlations → 1 | Reduce heat in stress |
| Ignoring forex correlation | EUR/USD + GBP/USD = same trade | Choose one |
| No portfolio heat tracking | Sudden large drawdowns | Weekly heat check |

---

## One-Line Wisdom

> "Five 1% positions in the same sector isn't diversification — it's concentration wearing a disguise. Correlation is the risk you don't see until it's too late."

---

## Related Files
- Position sizing: `2026-02-18-*-position-sizing*.md`
- Drawdown management: `2026-02-19-1525-drawdown-management.md`
- Expectancy: `2026-02-19-1224-expectancy-system-edge.md`
- Risk/reward: `2026-02-19-0453-risk-reward-optimization.md`
