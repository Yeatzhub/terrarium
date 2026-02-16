#!/usr/bin/env python3
"""
Bitcoin Trading Bot with Momentum Strategy
Uses RSI + SMA Crossover with risk management
"""

import ccxt
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TradingStrategy:
    """RSI + SMA Crossover Strategy - Optimized for lower timeframe"""
    
    def __init__(
        self,
        rsi_period: int = 7,
        rsi_overbought: float = 65,
        rsi_oversold: float = 35,
        sma_fast: int = 5,
        sma_slow: int = 15
    ):
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.rma_fast = sma_fast
        self.sma_fast = sma_fast
        self.sma_slow = sma_slow
    
    def calculate_rsi(self, prices: pd.Series) -> pd.Series:
        delta = prices.diff()
        gain = delta.where(delta > 0, 0).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['rsi'] = self.calculate_rsi(df['close'])
        df['sma_fast'] = df['close'].rolling(window=self.sma_fast).mean()
        df['sma_slow'] = df['close'].rolling(window=self.sma_slow).mean()
        
        df['signal'] = 0
        
        # Buy: RSI oversold + SMA bullish
        buy = (df['rsi'] < self.rsi_oversold) & (df['sma_fast'] > df['sma_slow'])
        df.loc[buy, 'signal'] = 1
        
        # Sell: RSI overbought OR SMA bearish
        sell = (df['rsi'] > self.rsi_overbought) | (df['sma_fast'] < df['sma_slow'])
        df.loc[sell, 'signal'] = -1
        
        return df


class TradingBot:
    """BTC Trading Bot with paper trading"""
    
    def __init__(
        self,
        symbol: str = 'BTC/USDT',
        timeframe: str = '15m',
        initial_balance: float = 10000.0,
        risk_per_trade: float = 0.15
    ):
        self.symbol = symbol
        self.timeframe = timeframe
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.risk_per_trade = risk_per_trade
        self.strategy = TradingStrategy()
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []
        self.position = None
        
        # Paper trading exchange (Coinbase - US friendly, better history)
        self.exchange = ccxt.coinbase({'enableRateLimit': True})
        logger.info(f"Bot initialized: {symbol} | Balance: ${initial_balance:,.2f}")
    
    def fetch_data(self, days: int = 90) -> pd.DataFrame:
        since = self.exchange.milliseconds() - (days * 24 * 60 * 60 * 1000)
        ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, since=since)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    
    def backtest(self, days: int = 90) -> Dict:
        df = self.fetch_data(days)
        df = self.strategy.generate_signals(df)
        
        balance = self.initial_balance
        position = 0
        trades = []
        equity = [{'timestamp': df['timestamp'].iloc[0], 'equity': balance}]
        
        for i in range(len(df)):
            price = df['close'].iloc[i]
            signal = df['signal'].iloc[i]
            timestamp = df['timestamp'].iloc[i]
            
            if signal == 1 and position == 0:
                position = balance / price
                entry_price = price
                balance = 0
                logger.info(f"BUY @ ${price:.2f}")
                
            elif signal == -1 and position > 0:
                balance = position * price
                pnl = balance - self.initial_balance
                trades.append({
                    'timestamp': timestamp,
                    'action': 'SELL',
                    'price': price,
                    'pnl': pnl,
                    'return_pct': (pnl / self.initial_balance) * 100
                })
                position = 0
                logger.info(f"SELL @ ${price:.2f} | P&L: ${pnl:.2f}")
            
            current_equity = balance + (position * price)
            equity.append({'timestamp': timestamp, 'equity': current_equity})
        
        final_equity = balance + (position * price)
        total_return = ((final_equity - self.initial_balance) / self.initial_balance) * 100
        
        wins = [t for t in trades if t['pnl'] > 0]
        win_rate = (len(wins) / len(trades) * 100) if trades else 0
        
        results = {
            'total_return': f"{total_return:.2f}%",
            'win_rate': f"{win_rate:.2f}%",
            'trades': len(trades),
            'final_equity': f"${final_equity:,.2f}",
            'trades_detail': trades
        }
        
        # Save results
        pd.DataFrame(equity).to_csv('backtest_equity.csv', index=False)
        pd.DataFrame(trades).to_csv('backtest_trades.csv', index=False)
        
        return results


if __name__ == "__main__":
    bot = TradingBot()
    print("="*50)
    print("BACKTESTING BTC TRADING STRATEGY")
    print("="*50)
    results = bot.backtest(days=30)
    print(f"Total Return: {results['total_return']}")
    print(f"Win Rate: {results['win_rate']}")
    print(f"Total Trades: {results['trades']}")
    print(f"Final Equity: {results['final_equity']}")
    print("="*50)
    print("Results saved to: backtest_equity.csv, backtest_trades.csv")
