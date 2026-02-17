#!/usr/bin/env python3
"""
Phase 3: Execution & Logging
Main execution loop running every 15 minutes.
"""

import time
import logging
import json
import os
import sys
from datetime import datetime
from typing import List, Optional

from market_discovery import Market, MarketDiscovery
from trader import MeanReversionTrader, Trade

# Configuration
LOG_FILE = "polymarket_paper_trader/trades.log"
RUN_INTERVAL_MINUTES = 15
RUN_INTERVAL_SECONDS = RUN_INTERVAL_MINUTES * 60


class TradeLogger:
    """Handles logging of trading activities."""
    
    def __init__(self, log_file: str = LOG_FILE):
        self.log_file = log_file
        self._setup_logger()
    
    def _setup_logger(self):
        """Setup file and console logging."""
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        self.logger = logging.getLogger('PolymarketTrader')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers = []
        
        # File handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '[%(levelname)s] %(message)s'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)
    
    def info(self, message: str):
        self.logger.info(message)
    
    def warning(self, message: str):
        self.logger.warning(message)
    
    def error(self, message: str):
        self.logger.error(message)
    
    def trade_executed(self, trade: Trade, action: str):
        """Log a trade execution."""
        msg = f"TRADE {action.upper()}: {trade.trade_id} | "
        msg += f"Market: {trade.market_id} | "
        msg += f"Direction: {trade.direction.upper()} | "
        msg += f"Entry: ${trade.entry_price:.4f}"
        if trade.exit_price:
            msg += f" | Exit: ${trade.exit_price:.4f}"
            msg += f" | P/L: ${trade.pnl:.4f}"
        self.logger.info(msg)
    
    def api_error(self, error: Exception, context: str = ""):
        """Log API errors gracefully."""
        self.logger.error(f"API Error in {context}: {str(error)}")


class TradingBot:
    """Main trading bot that runs continuously."""
    
    def __init__(self):
        self.logger = TradeLogger()
        self.discovery = MarketDiscovery()
        self.trader = MeanReversionTrader()
        self.tracked_markets: List[Market] = []
        self.running = False
    
    def discover_markets(self) -> List[Market]:
        """Discover active markets to trade."""
        self.logger.info("Discovering markets...")
        
        try:
            # Try crypto up/down markets first
            markets = self.discovery.get_crypto_up_down_markets(limit=100)
            
            # Fall back to general crypto markets
            if not markets:
                self.logger.info("No Up/Down crypto markets found, trying general crypto...")
                markets = self.discovery.get_crypto_markets(limit=100)
            
            if not markets:
                self.logger.warning("No tradable markets found")
                return []
            
            self.logger.info(f"Discovered {len(markets)} markets")
            self.tracked_markets = markets
            return markets
            
        except Exception as e:
            self.logger.api_error(e, "market discovery")
            return []
    
    def evaluate_signals(self, markets: List[Market]):
        """Evaluate buy/sell signals for tracked markets."""
        executed_trades = []
        
        for market in markets:
            try:
                # Check for sell signals first (close existing positions)
                sell_trade = self.trader.execute_sell(market)
                if sell_trade:
                    self.logger.trade_executed(sell_trade, "SELL")
                    executed_trades.append(sell_trade)
                    continue
                
                # Check for buy signals
                buy_trade = self.trader.execute_buy(market, direction="yes")
                if buy_trade:
                    self.logger.trade_executed(buy_trade, "BUY")
                    executed_trades.append(buy_trade)
                    
            except Exception as e:
                self.logger.error(f"Error evaluating {market.market_id}: {e}")
                continue
        
        return executed_trades
    
    def log_status(self):
        """Log current portfolio status."""
        status = self.trader.get_status()
        
        self.logger.info("=" * 60)
        self.logger.info("PORTFOLIO STATUS")
        self.logger.info("=" * 60)
        self.logger.info(f"Balance: ${status['balance']:.2f}")
        self.logger.info(f"Total P/L: ${status['total_pnl']:.4f}")
        self.logger.info(f"Win Rate: {status['win_rate']:.1f}%")
        self.logger.info(f"Open Positions: {status['open_positions']}")
        self.logger.info(f"Total Trades: {status['total_trades']}")
        self.logger.info(f"Consecutive Losses: {status['consecutive_losses']}")
        
        if status['circuit_breaker']:
            self.logger.warning("⚠ CIRCUIT BREAKER TRIGGERED - Trading halted")
        
        if status['open_positions'] > 0:
            self.logger.info("Open Positions:")
            for pos in status['positions']:
                self.logger.info(f"  - {pos['question'][:50]}...")
                self.logger.info(f"    Direction: {pos['direction'].upper()}, Entry: ${pos['entry_price']:.4f}")
    
    def run_cycle(self):
        """Execute one trading cycle."""
        self.logger.info("\n" + "=" * 60)
        self.logger.info(f"TRADING CYCLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("=" * 60)
        
        # Check circuit breaker
        if self.trader.portfolio.circuit_breaker_triggered:
            self.logger.warning("Circuit breaker active - skipping cycle")
            return
        
        # Discover markets
        markets = self.discover_markets()
        if not markets:
            self.logger.warning("No markets available, skipping cycle")
            return
        
        # Evaluate trading signals
        self.logger.info("Evaluating trading signals...")
        trades = self.evaluate_signals(markets)
        
        if trades:
            self.logger.info(f"Executed {len(trades)} trades this cycle")
        else:
            self.logger.info("No trades executed this cycle")
        
        # Log status
        self.log_status()
    
    def run_single(self):
        """Run a single trading cycle (for testing)."""
        try:
            self.run_cycle()
        except Exception as e:
            self.logger.error(f"Fatal error in trading cycle: {e}")
            raise
    
    def run_continuous(self):
        """Run trading bot continuously."""
        self.running = True
        self.logger.info("=" * 60)
        self.logger.info("PAPER TRADING BOT STARTED")
        self.logger.info(f"Interval: {RUN_INTERVAL_MINUTES} minutes")
        self.logger.info("=" * 60)
        
        while self.running:
            try:
                self.run_cycle()
            except Exception as e:
                self.logger.error(f"Error in cycle: {e}")
                self.logger.info("Retrying in next cycle...")
            
            # Sleep until next cycle
            self.logger.info(f"Sleeping for {RUN_INTERVAL_MINUTES} minutes...")
            time.sleep(RUN_INTERVAL_SECONDS)
    
    def stop(self):
        """Stop the trading bot."""
        self.running = False
        self.logger.info("Trading bot stopped")


def main():
    """Main entry point."""
    import signal
    
    bot = TradingBot()
    
    def signal_handler(sig, frame):
        print("\nReceived shutdown signal...")
        bot.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check for mode argument
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        print("Running single cycle...")
        bot.run_single()
    else:
        print("Running continuously (Ctrl+C to stop)...")
        bot.run_continuous()


if __name__ == "__main__":
    main()
