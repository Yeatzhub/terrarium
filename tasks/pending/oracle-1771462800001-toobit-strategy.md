---
assigned_to: oracle
task_id: 1771462800001-toobit-strategy
status: pending
created_at: 2026-02-19T01:05:00Z
started_at: null
completed_at: null
parent_task: synthesis-1771462800000-toobit-real-trading-bot
priority: high
---

# Task: Design Aggressive Toobit Trading Strategy

**Objective:** Create an aggressive trading strategy for Toobit perpetual futures that can double $100 capital quickly.

## Strategy Requirements

- **Exchange:** Toobit perpetual futures
- **Starting Capital:** $100 USD
- **Target:** Double to $200+ as fast as possible
- **Risk Level:** HIGH (aggressive but not reckless)

## Technical Specs

### Asset Selection
- Primary: BTCUSDT-PERP or ETHUSDT-PERP (high liquidity)
- Secondary: High-volatility alts (SOL, DOGE, etc. if available)

### Strategy Type Options (choose best or combine):
1. **Scalping Momentum**
   - 1-5 minute timeframe
   - Enter on breakout above/below range
   - Quick exits (30 sec - 3 min holds)
   - High frequency (10-30 trades/day)

2. **Trend Following with Leverage**
   - 15min-1hr timeframe
   - Enter on confirmed trend
   - Pyramid into winning trades
   - Let winners run with trailing stops

3. **Range Breakout**
   - Identify consolidation zones
   - Enter on breakout with momentum
   - Quick rejection if false breakout

### Position Management
- **Leverage:** 5-20x (recommend 10x for balance)
- **Position Size:** Risk 5-10% per trade ($5-10 risk)
- **Max Drawdown:** Hard stop at 20% ($20 loss = pause trading)
- **Daily Loss Limit:** Stop after 3 consecutive losses

### Entry Rules
Define clear conditions:
- [ ] Price action pattern
- [ ] Volume confirmation
- [ ] RSI/MACD or other indicator
- [ ] Minimum volatility threshold
- [ ] Time of day considerations

### Exit Rules
- **Take Profit:** 1.5R-3R (risk:reward ratio)
- **Stop Loss:** Fixed % or technical level
- **Trailing Stop:** Activate after 1R profit
- **Time Stop:** Exit if no move in X minutes

### Risk Controls (MANDATORY)
- Maximum open positions: 2-3
- No trading during high-impact news
- Circuit breaker: Pause after 20% drawdown
- Emergency close all function

## Output

Create Python file: `btc-trading-bot/strategies/oracle_aggressive.py`

Should include:
1. Strategy class with `on_tick()` or `on_candle()` method
2. Signal generation (buy/sell/hold)
3. Position sizing calculation
4. Stop loss / take profit levels
5. Risk check methods
6. Documentation/comments explaining logic
7. Backtest results on last 7 days (if possible)

## Testing

Provide backtest or paper trading results showing:
- Win rate
- Average win/loss size
- Max drawdown
- Expected time to double $100

---

*Delegated by Synthesis from: Build Real Toobit Trading Bot*