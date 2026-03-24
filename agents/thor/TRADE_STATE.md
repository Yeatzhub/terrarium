# Thor - Current Trade State

## Position
**None** (flat)

---

## Balance
- **Account:** 114.80 USDT (paper)
- **Last trade:** 2026-03-23 SHORT @ $1.3717, stopped at $1.4112

---

## Daily Stats (2026-03-23)
- **Trades:** 2
- **Win rate:** 50%
- **P&L:** -26.83 USDT (-19.26%)
- **Consecutive losses:** 1

---

## Circuit Breakers
| Breaker | Status | Current |
|---------|--------|---------|
| Daily Loss | ⚠️ Warning | -0.88 USDT (within 5% limit) |
| Max Drawdown | ✅ OK | -19.26% from starting |
| Consecutive Losses | ✅ OK | 1 (limit 5) |
| API Errors | ✅ OK | <10% |

---

## Risk Parameters
```json
{
  "stop_loss_pct": 0.02,
  "take_profit_pct": 0.04,
  "trailing_stop_pct": 0.015,
  "trailing_activate_pct": 0.02,
  "max_position_pct": 0.2,
  "daily_loss_limit_pct": 0.05,
  "max_consecutive_losses": 5
}
```

---

*Last updated: 2026-03-24 03:50 UTC*