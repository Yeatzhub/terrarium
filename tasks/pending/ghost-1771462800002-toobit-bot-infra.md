---
assigned_to: ghost
task_id: 1771462800002-toobit-bot-infra
status: pending
created_at: 2026-02-19T01:05:00Z
started_at: null
completed_at: null
parent_task: synthesis-1771462800000-toobit-real-trading-bot
priority: high
---

# Task: Build Toobit Trading Bot Infrastructure

**Objective:** Create production-ready Toobit trading bot that can execute real trades with real API.

## Technical Requirements

### Toobit API Integration
- API v3 endpoints: https://api.toobit.com
- Rest API for orders (place, cancel, get status)
- WebSocket for real-time market data
- Support perpetual futures only

### Core Components Needed

1. **Config System** (`btc-trading-bot/config/toobit_real.yaml`)
   - API key/secret (env var placeholders)
   - Trading pair (BTCUSDT-PERP default)
   - Strategy parameters
   - Risk limits
   - Webhook URL for UI updates

2. **API Client** (`btc-trading-bot/toobit_client.py`)
   - Authentication (HMAC SHA256)
   - Rate limit handling
   - Retry logic with exponential backoff
   - Error handling for API failures

3. **Order Manager** (`btc-trading-bot/order_manager.py`)
   - Place market orders
   - Place limit orders with timeout
   - Place stop-market orders
   - Set TP/SL brackets
   - Cancel orders
   - Get order status
   - Track fills and partial fills

4. **Position Tracker** (`btc-trading-bot/position_tracker.py`)
   - Track open positions
   - Calculate unrealized P&L
   - Calculate margin used
   - Reconcile with exchange
   - Save state to file

5. **Market Data Handler** (`btc-trading-bot/market_data.py`)
   - WebSocket connection to Toobit
   - Order book management
   - Price tick processing
   - Reconnect on disconnect
   - Buffer last 100 ticks

6. **Main Bot** (`btc-trading-bot/toobit_live_bot.py`)
   - Async main loop
   - Load strategy module
   - Execute strategy signals
   - Log all actions
   - Webhook updates to UI
   - Graceful shutdown

### Data Flow

```
WebSocket → Market Data → Strategy → Signals → Order Manager → Toobit API
                                        ↓
                              Position Tracker ← WebSocket Updates
                                        ↓
                                  File / Webhook → UI
```

### Safety Features (MANDATORY)

- [ ] Paper trading mode toggle (default ON for testing)
- [ ] Max loss limit (pause bot after configured loss)
- [ ] Circuit breaker (stop on API errors)
- [ ] Emergency close all positions function
- [ ] Position reconciliation check
- [ ] API error handling with retry limits
- [ ] Logging: All trades, errors, signals to file

### Output Files

- `btc-trading-bot/toobit_client.py` - API client
- `btc-trading-bot/order_manager.py` - Order management
- `btc-trading-bot/position_tracker.py` - Position tracking
- `btc-trading-bot/market_data.py` - Market data WebSocket
- `btc-trading-bot/toobit_live_bot.py` - Main bot (imports strategy)
- `btc-trading-bot/config/toobit_real.yaml` - Config template
- `btc-trading-bot/.env.example` - Environment variables template

### Integration

Main bot should import strategy from `strategies/` folder:
```python
from strategies.oracle_aggressive import AggressiveStrategy

strategy = AggressiveStrategy(config)
signal = strategy.on_tick(tick_data)
```

### Testing

Test on Toobit testnet first, then with minimum $10 on mainnet before full $100.

---

*Delegated by Synthesis from: Build Real Toobit Trading Bot*