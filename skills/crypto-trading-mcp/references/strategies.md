# Trading Strategies Documentation

## Grid Trading

**Concept:** Place buy and sell orders at regular intervals around current price.

**When to Use:**
- Sideways/ranging markets
- High volatility with no clear trend
- Want to accumulate small profits frequently

**How It Works:**
1. Set center price (current market price)
2. Create grid levels above and below
3. Place buy orders below center
4. Place sell orders above center
5. As price moves, grids execute and rebalance

**Example (5% grid spacing):**
```
Price: $100
Buy grids:  $95, $90, $85, $80, $75
Sell grids: $105, $110, $115, $120, $125
```

**Pros:**
- Profits in sideways markets
- Systematic, no emotion
- Scales with volatility

**Cons:**
- Loses money in strong trends
- Requires capital for multiple positions
- Fees can eat profits if grids too tight

**Best For:** BTC/USD in consolidation, altcoins with high volatility

---

## Momentum Strategy

**Concept:** Enter trades when multiple indicators confirm trend direction.

**Indicators Used:**
- RSI (Relative Strength Index) - overbought/oversold
- MACD (Moving Average Convergence Divergence) - trend strength
- Bollinger Bands - volatility and breakout
- Volume - confirm momentum

**Entry Signals:**

**BUY when:**
- RSI < 30 (oversold)
- MACD crosses above signal
- Price touches lower Bollinger Band
- Volume spike (>1.5x average)

**SELL when:**
- RSI > 70 (overbought)
- MACD crosses below signal
- Price touches upper Bollinger Band
- Volume spike

**Pros:**
- Catches major trends early
- Multiple confirmations reduce false signals
- Good for directional markets

**Cons:**
- Lagging indicators = late entry
- False breakouts in choppy markets
- Requires patience

**Best For:** Trending markets, major news events

---

## Scalping Strategy

**Concept:** Quick trades for small profits (1-2%) with tight stops.

**How It Works:**
1. Monitor for quick momentum (5-15 min timeframe)
2. Enter on breakout
3. Set tight stop loss (0.8%)
4. Take profit at 1.5%
5. Exit quickly if wrong

**Risk Management:**
- Position size: Small (5% of account)
- Stop loss: Strict 0.8%
- Profit target: 1.5%
- Max hold time: 30 minutes

**Pros:**
- Quick profits
- No overnight risk
- Many opportunities daily

**Cons:**
- High stress
- Requires constant monitoring
- Fees impact small gains
- Easy to overtrade

**Best For:** Volatile pairs (DOGE, SHIB, small caps), active traders

---

## Mean Reversion

**Concept:** Price tends to return to average over time. Buy low, sell high.

**How It Works:**
1. Calculate Bollinger Bands (20-period, 2 std dev)
2. When price hits lower band → BUY
3. When price returns to middle band → SELL
4. When price hits upper band → SELL (or short)

**Entry Criteria:**
- Price < lower Bollinger Band
- RSI confirming oversold (<40)

**Exit Criteria:**
- Price reaches middle band (moving average)
- Stop loss: 3% below entry

**Pros:**
- High probability trades
- Clear entry/exit rules
- Works well in ranging markets

**Cons:**
- Catches falling knives in trends
- Misses big breakouts
- Requires patience

**Best For:** Mature markets (BTC, ETH) in consolidation

---

## Arbitrage Strategy

**Concept:** Exploit price differences across exchanges.

**Types:**

**Cross-Exchange:**
- Buy on Exchange A where price is lower
- Sell on Exchange B where price is higher
- Profit = price difference - fees

**Triangular:**
- BTC → ETH → USD → BTC
- Exploit rate mismatches
- Requires all three pairs

**Requirements:**
- Accounts on multiple exchanges
- Fast execution (APIs)
- Sufficient capital on each exchange
- Low latency

**Pros:**
- Near risk-free
- Consistent small profits
- Market neutral

**Cons:**
- Opportunities rare and brief
- Requires large capital
- Transfer delays between exchanges
- Fees eat small spreads

**Best For:** High-frequency, well-capitalized traders

---

## Strategy Selection Guide

| Market Condition | Recommended Strategy |
|-------------------|---------------------|
| Sideways/Range | Grid, Mean Reversion |
| Strong Trend | Momentum |
| High Volatility | Scalping, Grid |
| Low Volatility | Mean Reversion |
| News/Event | Momentum, Scalping |
| Uncertain | Paper trade all, pick best |

---

## Performance Expectations

**Grid Trading:**
- Monthly return: 5-15%
- Drawdown: 10-20% (in strong trends)
- Win rate: 60-70%

**Momentum:**
- Monthly return: 10-30%
- Drawdown: 20-40%
- Win rate: 40-50%

**Scalping:**
- Daily return: 0.5-2%
- Drawdown: 5-10%
- Win rate: 55-65%
- Requires: Full-time attention

**Mean Reversion:**
- Monthly return: 3-8%
- Drawdown: 5-15%
- Win rate: 65-75%

**Arbitrage:**
- Monthly return: 2-5%
- Drawdown: <1%
- Win rate: 80-90%
- Requires: $10k+ capital

---

## Risk Warning

All strategies can lose money. Past performance ≠ future results.

**Always:**
- Start with paper trading
- Use stop losses
- Never risk >2% per trade
- Withdraw profits regularly
