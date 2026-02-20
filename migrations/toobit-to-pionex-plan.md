# Trading Bot Migration Plan

## Current Bots

### 1. Pionex XRP COIN-M Perp
- **Status:** ✅ Running
- **Location:** `btc-trading-bot/pionex/`
- **Action:** Keep as-is

### 2. Toobit BTC
- **Status:** Active on Toobit
- **Strategy:** Aggressive breakout/momentum
- **Action:** Migrate to Pionex BTC COIN-M Perp

### 3. DCA Reversal Bot
- **Status:** Need to build
- **Strategy:** DCA with safety trades
- **Action:** Create new bot for Pionex

## Migration Steps

### Phase 1: Create Pionex BTC Bot (Migrate Toobit Strategy)
1. Copy Toobit strategy to Pionex structure
2. Adapt for BTC COIN-M PERP
3. Test in paper mode
4. Switch over

### Phase 2: Build DCA Bot ✅ COMPLETED
1. ✅ Implement grid/DCA logic
2. ✅ Multi-level entry system  
3. ✅ Unified exit logic
4. ✅ Paper test first (enabled by default)

### Phase 3: Shutdown Toobit (PENDING)
1. Once Pionex BTC is stable
2. Stop Toobit bot
3. Archive Toobit code

## New Bots Created ✅

### Pionex BTC COIN-M Bot
- Location: `btc-trading-bot/pionex/pionex_btc_bot.py`
- Service: `pionex-btc.service`
- Strategy: Aggressive (migrated from Toobit)
- Paper mode: Enabled by default

### Pionex DCA Reversal Bot
- Location: `btc-trading-bot/pionex/dca_reversal_bot.py`
- Service: `pionex-dca.service`
- Strategy: Mean reversion with safety trades
- Levels: 3 safety levels with increasing size
- Paper mode: Enabled by default

## Exchange Consolidation Benefits
- Single API credentials
- Unified risk monitoring
- Simpler portfolio tracking
- Easier dashboard integration
- All bots on one exchange = unified risk management
