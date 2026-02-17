# Crypto Trading MCP - Configuration Guide

## Environment Variables

Set these in your shell or `.env` file:

```bash
# Kraken Exchange
export KRAKEN_API_KEY="your_kraken_api_key"
export KRAKEN_SECRET_KEY="your_kraken_api_secret"

# Toobit Exchange  
export TOOBIT_API_KEY="your_toobit_api_key"
export TOOBIT_SECRET_KEY="your_toobit_api_secret"
```

## Paper Trading

Paper trading requires **NO API keys**. It simulates trades using real market data.

```bash
# Kraken paper trading (no keys needed)
python kraken_bot.py --mode paper --strategy momentum --pair XXBTZUSD

# Toobit paper trading
python toobit_bot.py --mode paper --strategy grid
```

## Live Trading Setup

### 1. Get API Keys

**Kraken:**
1. Log in to Kraken Pro
2. Settings → API
3. Create new key with permissions: Query Funds, Query Orders, Trade
4. Copy key and secret

**Toobit:**
1. Log in to Toobit
2. Profile → API Management
3. Create API key with trading permissions
4. Whitelist your IP address

### 2. Configure Bot

```bash
# Set credentials
export KRAKEN_API_KEY="your_key"
export KRAKEN_SECRET_KEY="your_secret"

# Run with safety confirmation
python kraken_bot.py --mode live --strategy momentum
```

## Trading Pairs

### Kraken Format
- `XXBTZUSD` - Bitcoin/USD
- `XETHZUSD` - Ethereum/USD
- `XXRPZUSD` - Ripple/USD
- `XLTCZUSD` - Litecoin/USD
- `XSOLZUSD` - Solana/USD

### Toobit Format
- `BTCUSDT` - Bitcoin/USDT
- `ETHUSDT` - Ethereum/USDT
- `DOGEUSDT` - Dogecoin/USDT
- `XRPUSDT` - Ripple/USDT

## Risk Management Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `max_position_size` | $1000 | Max position value |
| `max_position_pct` | 20% | Max % of balance per trade |
| `max_daily_loss` | 5% | Stop trading after this loss |
| `stop_loss_pct` | 2% | Default stop loss |
| `take_profit_pct` | 4% | Default take profit |

## Strategy Configuration

### Grid Strategy
```python
GridStrategy(
    grid_levels=10,        # Number of grid lines
    grid_spacing_pct=0.005, # 0.5% spacing
    order_size=100.0        # $ per grid
)
```

### Momentum Strategy
```python
MomentumStrategy(
    rsi_period=14,
    rsi_overbought=70,
    rsi_oversold=30
)
```

### Scalping Strategy
```python
ScalpingStrategy(
    profit_target=0.015,  # 1.5% target
    stop_loss=0.008       # 0.8% stop
)
```

## Paper Trading State

Paper trading persists state to JSON files:
- `kraken_paper_state.json` - Kraken paper account
- `toobit_paper_state.json` - Toobit paper account

State includes: balance, positions, trades, P&L

Delete these files to reset paper trading.

## Safety Features

1. **Paper mode default** - All bots start in paper trading
2. **Live confirmation** - Must type "LIVE" explicitly
3. **API key validation** - Checks keys before live trades
4. **Position limits** - Caps max position sizes
5. **State persistence** - Saves paper trades to file

## Troubleshooting

### "Insufficient balance" in paper mode
- Check paper state file
- Reset by deleting state file
- Or adjust `paper_initial_balance`

### API errors
- Verify API key permissions
- Check IP whitelisting
- Review rate limits

### No market data
- Check exchange status
- Verify symbol format (XXBTZUSD vs BTCUSDT)
- Test API connectivity
