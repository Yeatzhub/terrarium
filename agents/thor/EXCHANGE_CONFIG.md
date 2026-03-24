# Thor - Exchange Configuration

## Exchange
- **Platform:** Pionex
- **Pair:** XRP/USDT
- **Type:** Spot (can be COIN-M futures)

## Mode
- **Default:** Paper trading
- **To enable live:** Add `--mode live` flag

## API Credentials
See: `/storage/workspace/projects/trading/pionex/api_config.py`

## Starting Capital
- **Paper:** $142.19 (simulated)
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