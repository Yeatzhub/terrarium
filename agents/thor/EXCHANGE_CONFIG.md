# Thor - Exchange Configuration

## Exchange
- **Platform:** Pionex
- **Pair:** XRP/USDT
- **Type:** USDT-M Futures (preferred) or COIN-M
- **Candle timeframe:** 15m

## Mode
- **Default:** Paper trading
- **To enable live:** Add `--mode live` flag

## Execution
- **Check interval:** 30 seconds
- **Spawn:** Agent (via `sessions_spawn` or Telegram command)
- **Notifications:** Telegram

## API Credentials
**Status:** ⚠️ Currently READ-ONLY (needs write permissions for live trading)

See: `/storage/workspace/projects/trading/pionex/api_config.py`

## Starting Capital
- **Allocated:** 100 XRP
- **Paper:** Simulated balance
- **Live:** Uses actual Pionex balance

## Risk Parameters
- **Stop-loss:** 2% from entry
- **Take-profit:** 4% from entry
- **Trailing stop:** 1.5% trail, activates at 2% profit
- **Max position:** 20% of balance
- **Daily loss limit:** 5%
- **Max consecutive losses:** 5

## Last Updated
- 2026-03-24