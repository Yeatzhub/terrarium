# Bitcoin Trading Bot

A momentum-based trading bot using RSI + SMA crossover strategy.

## Features
- RSI overbought/oversold detection
- SMA crossover for trend confirmation
- Paper trading (no real money)
- 90-day backtesting
- Performance metrics

## Installation
```bash
pip install -r requirements.txt
```

## Usage
```bash
python btc_trading_bot.py
```

## Strategy
- **Buy**: RSI < 30 AND short SMA > long SMA
- **Sell**: RSI > 70 OR short SMA < long SMA

## Output
- `backtest_equity.csv` — Daily portfolio value
- `backtest_trades.csv` — Trade history
- `trading_bot.log` — Execution log

## Configuration
Edit parameters in `btc_trading_bot.py`:
- `rsi_period`: RSI calculation window
- `sma_fast/sma_slow`: Moving average periods
- `initial_balance`: Starting capital
