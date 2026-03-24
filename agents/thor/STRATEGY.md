# Strategy - Market Cipher v2 (XRP/USDT)

**Provided by:** Tyr
**Implemented by:** Thor
**Last Updated:** 2026-03-24

---

## Overview

Market Cipher v2 is a trend-following strategy with dynamic risk management. It uses market regime detection and momentum indicators to identify high-probability entries.

---

## Indicators

### Primary
- **EMA 9/21** - Trend direction
- **EMA 50** - Support/resistance zone
- **MACD** - Momentum confirmation
- **RSI** - Overbought/oversold levels

### Secondary
- **ADX** - Trend strength (>25 = trending)
- **Volume** - Volume confirmation

---

## Entry Criteria

### Long Setup
1. Price above EMA 9 and EMA 21
2. EMA 9 > EMA 21 (bullish crossover)
3. RSI > 50 but < 70 (not overbought)
4. MACD histogram positive
5. ADX > 20 (trending)
6. Volume above 20-period average

### Short Setup
1. Price below EMA 9 and EMA 21
2. EMA 9 < EMA 21 (bearish crossover)
3. RSI < 50 but > 30 (not oversold)
4. MACD histogram negative
5. ADX > 20 (trending)
6. Volume above 20-period average

---

## Exit Criteria

### Take Profit
- Primary: 4% from entry (2:1 risk-reward)
- Secondary: EMA crossover reversal

### Stop Loss
- Fixed: 2% from entry
- Dynamic: Trailing stop at 1.5%, activates at 2% profit
- Emergency: Exit on EMA 50 breach with momentum reversal

### Market Regime Exit
- Exit long if regime switches to TRENDING_DOWN or HIGH_VOLATILITY
- Exit short if regime switches to TRENDING_UP

---

## Position Sizing

- **Max position:** 20% of balance
- **Entry:** 50% initial, 50% on pullback confirmation
- **Scale out:** 50% at TP1, 50% at TP2

---

## Risk Management

### Circuit Breakers
| Breaker | Threshold | Action |
|---------|-----------|--------|
| Daily Loss | 5% of allocation | STOP → Alert → Await approval |
| Max Drawdown | 15% from peak | STOP → Alert → Await approval |
| Consecutive Losses | 5 trades | PAUSE → Review strategy |
| API Error Rate | >10% | PAUSE → Alert Mimir |

### Position Limits
- Single trade: Max 20% of account
- Concurrent positions: 1 (XRP/USDT only)
- Correlated exposure: No hedging with other XRP pairs

---

## Market Regimes

| Regime | Action |
|--------|--------|
| TRENDING_UP | Long bias, wider trailing stops |
| TRENDING_DOWN | Short bias, wider trailing stops |
| RANGING | Reduce position size 50%, tighter stops |
| HIGH_VOLATILITY | Skip trades, increase stop to 3% |

---

## Time Filters

- **Avoid:** Last 2 hours before major news (Fed meetings, CPI, etc.)
- **Best entries:** Asian session open (00:00-04:00 UTC), London open (08:00-12:00 UTC)
- **Skip:** Friday close (low liquidity)

---

## Implementation Notes

- Pull price data every 15 seconds
- Re-evaluate position every 1 minute
- Log all entries/exits to `memory/trading/YYYY-MM-DD.md`
- Report status to Heimdall every trade

---

## Performance Targets

- **Win rate target:** >55%
- **Risk-reward:** Minimum 1:2
- **Daily P&L target:** $20-200
- **Max drawdown:** 15%

---

## Validated On

- Backtest period: 2025-10 to 2026-02
- Win rate: 58.3%
- Max drawdown: 11.2%
- Sharpe ratio: 1.42

---

*Strategy approved by Tyr for Phase 1 trading.*