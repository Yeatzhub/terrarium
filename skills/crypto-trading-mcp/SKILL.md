---
name: crypto-trading-mcp
description: Comprehensive cryptocurrency trading automation with paper trading simulation, multi-exchange support (Kraken, Toobit), prediction market arbitrage (Polymarket), and automated strategies including grid, momentum, and scalping. Use when building or running crypto trading bots, implementing paper trading for strategy testing, analyzing arbitrage opportunities, or automating trading operations across exchanges.
---

# Crypto Trading MCP

Multi-exchange cryptocurrency trading bot suite with paper trading simulation.

## Supported Exchanges

| Exchange | Status | Paper Trading | Features |
|----------|--------|---------------|----------|
| **Kraken** | ✅ Production-ready | ✅ Full simulation | Spot trading, complete API |
| **Toobit** | ⚠️ API incomplete | ✅ Simulation layer | Limited market data endpoints |
| **Polymarket** | ✅ Arbitrage scanner | N/A | Prediction market arbitrage |

## Quick Start

### 1. Paper Trading (No API keys needed)

```bash
# Kraken paper trading
python kraken_bot.py --mode paper --strategy grid --pair XXBTZUSD

# Toobit paper trading (uses external price feeds)
python toobit_bot.py --mode paper --strategy grid
```

### 2. Live Trading (Requires API keys)

```bash
# Set credentials
export KRAKEN_API_KEY="your_key"
export KRAKEN_SECRET_KEY="your_secret"

# Run live (requires confirmation)
python kraken_bot.py --mode live --strategy momentum --pair XXBTZUSD
```

## Strategies

| Strategy | Description | Risk Level | Best For |
|----------|-------------|------------|----------|
| **Grid** | Multiple buy/sell levels | Medium | Sideways markets |
| **Momentum** | RSI + MACD + Volume | Higher | Breakouts |
| **Scalping** | Quick 1-2% moves | High | Volatile pairs |
| **Arbitrage** | Cross-exchange price gaps | Lower | Price inefficiencies |

## Bot Architecture

### Core Components

1. **Exchange API Wrapper** - `kraken_api.py`, `toobit_api.py`
   - Rate limiting, error handling, authentication
   - Unified interface across exchanges

2. **Paper Trading Engine** - `*_paper_trader.py`
   - Realistic fee simulation (0.16% maker, 0.26% taker)
   - Slippage modeling
   - P&L tracking, state persistence

3. **Strategy Module** - `*_strategies.py`
   - Signal generation (buy/sell/hold)
   - Technical indicators (RSI, MACD, Bollinger)
   - Risk management integration

4. **Bot Orchestrator** - `*_bot.py`
   - Main event loop
   - Mode switching (paper/live)
   - Safety confirmations for live trading

### Configuration

See `references/configuration.md` for:
- API key setup
- Strategy parameters
- Risk management settings
- Exchange-specific settings

## Safety Features

- **Paper mode default**: All bots start in paper trading
- **Live confirmation**: Requires typing "LIVE" explicitly
- **Risk limits**: Position sizing, stop-loss, daily loss caps
- **State persistence**: Paper trades saved to JSON
- **Graceful shutdown**: Saves state on SIGINT

## File Structure

```
scripts/
├── kraken_api.py           # Kraken REST API client
├── kraken_paper_trader.py  # Paper trading engine
├── kraken_strategies.py    # Trading strategies
├── kraken_bot.py           # Main bot orchestrator
├── kraken_config.py        # Configuration management
├── toobit_api.py           # Toobit API client
├── toobit_paper_trader.py  # Toobit paper trading
├── toobit_strategies.py    # Toobit strategies
├── toobit_bot.py           # Toobit bot orchestrator
├── toobit_config.py        # Toobit configuration
├── polymarket_scanner.py # Polymarket arbitrage
└── setup_cron.sh           # Automated scanning cron

references/
├── configuration.md        # Configuration guide
├── strategies.md          # Strategy documentation
├── api-reference.md         # API endpoint details
└── risk-management.md       # Risk guidelines

assets/
├── sample-configs/         # Example configurations
└── templates/              # Boilerplate code
```

## Usage Patterns

### Pattern 1: Strategy Testing
```bash
# Test grid strategy on Kraken (paper)
python kraken_bot.py --mode paper --strategy grid --pair XXBTZUSD --interval 60
```

### Pattern 2: Multi-Exchange Arbitrage
```bash
# Run both bots, compare prices
# See references/arbitrage.md for cross-exchange setup
```

### Pattern 3: Polymarket Monitoring
```bash
# Hourly arbitrage scanning
python polymarket_scanner.py --top 10
```

## Risk Warnings

⚠️ **IMPORTANT:**
- Start with paper trading
- Never risk more than you can afford to lose
- Withdraw profits frequently from exchanges
- Use API keys with minimal required permissions
- Monitor bot behavior closely

## MCP Integration

This skill integrates with MCP tools:
- `web_search_exa`: Research market conditions
- `get_code_context_exa`: Analyze strategy code
- `deep_researcher_start`: Deep market analysis
- `crawling_exa`: Exchange API documentation

## Support

For detailed configuration, see `references/configuration.md`.
For strategy details, see `references/strategies.md`.
For API docs, see `references/api-reference.md`.
