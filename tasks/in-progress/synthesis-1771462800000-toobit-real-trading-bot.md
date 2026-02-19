---
assigned_to: synthesis
task_id: 1771462800000-toobit-real-trading-bot
status: in-progress
created_at: 2026-02-19T01:00:00Z
started_at: 2026-02-18T19:05:41-06:00
completed_at: null
priority: high
type: real-trading
---

# Task: Build Real Toobit Trading Bot

**Objective:** Build a working Toobit trading bot that makes real trades with real market data. Aggressive strategy to double $100 as fast as possible.

## Background

We need a production-ready trading bot for Toobit perpetual futures exchange. This is NOT paper trading - this will use real API keys and make real trades. Goal is aggressive growth strategy to turn $100 into $200+ quickly.

## Delegation Plan

- [ ] **Oracle**: Design aggressive trading strategy
  - High-risk/high-reward approach
  - Scalping or momentum-based strategy
  - Position sizing for $100 capital
  - Risk management (stop losses mandatory)
  - Target: Double $100 in shortest time possible

- [ ] **Ghost**: Build Toobit trading bot infrastructure
  - Toobit API integration (real, not paper)
  - Order execution engine
  - Websocket real-time market data
  - Position tracking and P&L calculation
  - Error handling and circuit breakers
  - API credential management (secure)
  - Placeholder for real API keys

- [ ] **Pixel**: Build Toobit trading UI
  - New page: `/trading/bot/toobit/live`
  - Real-time position display
  - Live P&L tracking
  - Order entry interface
  - Trade history table
  - Charts (price, position, P&L over time)
  - Start/Stop bot controls
  - Match Mission Control dark theme

## Requirements

### Oracle's Strategy Requirements
- Perpetual futures on BTC, ETH, or high-volatility altcoins
- Leverage: 5-20x (aggressive but managed)
- Entry signals: Breakout momentum or scalping
- Exit signals: TP/SL or trailing stops
- Max drawdown: 20% ($20 loss max before pause)
- Position sizing: Risk 5-10% per trade
- Frequency: Multiple trades per hour

### Ghost's Technical Requirements
- Python-based (async/await)
- Toobit API v3 or latest
- Real-time order book via WebSocket
- Order types: Market, Limit, Stop-Market, TP/SL
- Automatic position reconciliation
- Logging: All trades to file + UI webhook
- Config file for API credentials (env vars)
- Paper trading toggle for testing (default OFF for this task)

### Pixel's UI Requirements
- Built with Next.js + Tailwind + shadcn/ui
- Real-time updates via API polling (2-second)
- Components:
  - Balance card with live P&L
  - Active position card (size, entry, unrealized P&L)
  - Recent trades table (last 20)
  - Performance chart ( equity curve)
  - Controls: Start Bot, Stop Bot, Emergency Close All
  - Configuration panel (pair, leverage, strategy params)

## Testing Protocol

1. **Phase 1**: Ghost builds bot, Oracle provides strategy, Pixel builds UI - all using testnet/simulation
2. **Phase 2**: Run on testnet with $100 test funds
3. **Phase 3**: Run on mainnet for 24 hours
4. **Phase 4**: Iterate based on results - adjust strategy, fix bugs, optimize

Repeat phases 2-4 until bot achieves consistent profitability.

## Success Criteria

- Bot makes real trades on Toobit
- Tracks P&L accurately
- UI shows live data
- Strategy executes as designed
- Can start/stop/pause via UI
- Eventually doubles the $100

## Output Files

- `btc-trading-bot/toobit_live_bot.py` - Main bot (Ghost)
- `btc-trading-bot/strategies/oracle_aggressive.py` - Strategy (Oracle)
- `mission-control/src/app/trading/bot/toobit/live/page.tsx` - UI (Pixel)
- `btc-trading-bot/config/toobit_real.yaml` - Config template
- Documentation on how to add real API keys

## Risk Warning

⚠️ This bot will trade with real money. Include prominent warnings in UI.
Include emergency stop functionality. Test thoroughly on testnet first.

## Priority

HIGH - This is a top priority initiative. Coordinate agents to work in parallel where possible.

---

*Assigned by: Synthesis (Team Lead)*
*Started: 2026-02-19*
*Target: Working bot within 48 hours*