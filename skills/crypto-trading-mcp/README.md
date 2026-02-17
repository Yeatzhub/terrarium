# Crypto Trading MCP

Multi-exchange cryptocurrency trading automation with paper trading simulation.

## Quick Start

```bash
# Paper trading (safe, no API keys)
python kraken_bot.py --mode paper --strategy momentum --pair XXBTZUSD

# Polymarket arbitrage scanning
python polymarket_scanner.py --top 10
```

## Supported Exchanges

- **Kraken**: Full support, complete API, paper trading ✅
- **Toobit**: Partial (API incomplete), paper trading via external data ⚠️
- **Polymarket**: Arbitrage scanning ✅

## Strategies

- **Grid**: Multiple buy/sell levels (sideways markets)
- **Momentum**: RSI + MACD + Volume (trending markets)
- **Scalping**: Quick 1-2% moves (volatile pairs)
- **Mean Reversion**: Bollinger Bands (ranging markets)

## Safety

- Paper trading by default
- Live mode requires "LIVE" confirmation
- Risk limits built-in
- State persistence for paper trades

## Files

### Scripts
- `kraken_bot.py` - Main Kraken bot
- `kraken_api.py` - Kraken API wrapper
- `kraken_paper_trader.py` - Paper trading engine
- `kraken_strategies.py` - Trading strategies
- `toobit_bot.py` - Toobit bot (limited)
- `polymarket_scanner.py` - Arbitrage scanner

### References
- `references/configuration.md` - Setup guide
- `references/strategies.md` - Strategy docs
- `references/api-reference.md` - API docs

## MCP Integration

Integrates with MCP marketplace tools:
- `web_search_exa` - Market research
- `deep_researcher_start` - Strategy analysis
- `crawling_exa` - Exchange docs

## Risk Warning

Trading involves substantial risk. Start with paper trading. Never risk more than you can afford to lose.
