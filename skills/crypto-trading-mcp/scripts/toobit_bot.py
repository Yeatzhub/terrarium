"""
Toobit Trading Bot - Main Orchestrator
Production-ready bot with paper/live modes, logging, and safety features.
"""

import os
import sys
import time
import signal
import logging
import argparse
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Import bot components
from toobit_config import BotConfig, APIConfig, get_config
from toobit_api import ToobitAPI, ToobitAPIError
from toobit_paper_trader import PaperAccount
from toobit_strategies import create_strategy, StrategySignal, BaseStrategy


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('toobit_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('ToobitBot')


class ToobitBot:
    """
    Main Toobit Trading Bot
    
    Features:
    - Paper trading simulation
    - Live trading with safety confirmations
    - Multiple strategy support
    - Real market data in both modes
    - Graceful shutdown with state preservation
    - Comprehensive logging
    """
    
    def __init__(self, mode: str = 'paper', strategy: str = 'grid', 
                 symbol: str = 'BTCUSDT', config: Optional[BotConfig] = None):
        """
        Initialize the trading bot
        
        Args:
            mode: 'paper' or 'live'
            strategy: 'grid', 'momentum', 'arbitrage', or 'multi'
            symbol: Primary trading pair
            config: BotConfig instance (optional)
        """
        self.mode = mode
        self.strategy_name = strategy
        self.symbol = symbol
        
        # Load or create config
        if config:
            self.config = config
        else:
            self.config = BotConfig(
                mode=mode,
                strategy=strategy,
                symbol=symbol
            )
        
        # Validate configuration
        try:
            self.config.validate()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            raise
        
        # Initialize components
        self.api: Optional[ToobitAPI] = None
        self.paper_account: Optional[PaperAccount] = None
        self.strategy: Optional[BaseStrategy] = None
        self.executor = None  # Points to api or paper_account
        
        # State
        self.running = False
        self.cycle_count = 0
        self.errors_count = 0
        self.start_time = None
        
        # Graceful shutdown
        self._setup_signal_handlers()
        
        logger.info(f"ToobitBot initialized: mode={mode}, strategy={strategy}, symbol={symbol}")
    
    def _setup_signal_handlers(self):
        """Setup handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def initialize(self) -> bool:
        """Initialize all components"""
        try:
            logger.info("Initializing components...")
            
            # Initialize API (for market data in both modes)
            self.api = ToobitAPI(
                api_key=self.config.api.api_key,
                api_secret=self.config.api.api_secret,
                testnet=self.config.api.testnet
            )
            
            # Test API connectivity
            if not self.api.ping():
                logger.error("Failed to connect to Toobit API")
                return False
            
            server_time = self.api.get_server_time()
            logger.info(f"Connected to Toobit API. Server time: {datetime.fromtimestamp(server_time/1000)}")
            
            # Initialize paper or live mode
            if self.config.mode == 'paper':
                self.paper_account = PaperAccount(
                    initial_balance=self.config.paper_initial_balance,
                    state_file=self.config.paper_state_file
                )
                self.executor = self.paper_account
                logger.info(f"Paper trading mode: {self.paper_account.balance:.2f} USDT")
            else:
                # Live mode - additional safety checks
                if self.config.require_live_confirmation and not self._confirm_live_trading():
                    logger.info("Live trading cancelled by user")
                    return False
                
                self.executor = self.api
                
                # Get account balance
                try:
                    balance = self.api.get_balance()
                    usdt_balance = next(
                        (b for b in balance.get('balances', []) if b['asset'] == 'USDT'),
                        None
                    )
                    if usdt_balance:
                        logger.info(f"Live trading mode: {float(usdt_balance['free']):.2f} USDT available")
                except Exception as e:
                    logger.warning(f"Could not fetch balance: {e}")
            
            # Initialize strategy
            strategy_config = self._get_strategy_config()
            self.strategy = create_strategy(self.config.strategy, strategy_config)
            logger.info(f"Strategy initialized: {self.strategy.name}")
            
            # Log startup info
            logger.info(f"Trading pairs: {self.config.symbols}")
            logger.info(f"Update interval: {self.config.update_interval}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    def _confirm_live_trading(self) -> bool:
        """Get user confirmation for live trading"""
        print("\n" + "="*70)
        print("⚠️  LIVE TRADING MODE - REAL MONEY AT RISK")
        print("="*70)
        print(f"Strategy: {self.config.strategy}")
        print(f"Trading pairs: {', '.join(self.config.symbols)}")
        print(f"Risk settings:")
        print(f"  - Max position: {self.config.risk.max_position_pct*100}% of balance")
        print(f"  - Stop loss: {self.config.risk.stop_loss_pct*100}%")
        print(f"  - Take profit: {self.config.risk.take_profit_pct*100}%")
        print("="*70)
        
        response = input("\nType 'LIVE' to confirm live trading, or anything else to cancel: ")
        return response.strip() == 'LIVE'
    
    def _get_strategy_config(self) -> Dict:
        """Get strategy-specific configuration"""
        base_config = {
            'update_interval': self.config.update_interval,
            'min_confidence': 0.6
        }
        
        if self.config.strategy == 'grid':
            grid_cfg = {
                'grid_levels': self.config.grid.grid_levels,
                'grid_spacing_pct': self.config.grid.grid_spacing_pct,
                'order_size': self.config.grid.order_size,
                'max_grids': self.config.grid.max_grids,
                'volatility_adjust': self.config.grid.volatility_adjust,
                'trend_following': self.config.grid.trend_following,
                'pyramiding': self.config.grid.pyramiding
            }
            base_config.update(grid_cfg)
        
        elif self.config.strategy == 'momentum':
            momentum_cfg = {
                'rsi_period': self.config.momentum.rsi_period,
                'rsi_overbought': self.config.momentum.rsi_overbought,
                'rsi_oversold': self.config.momentum.rsi_oversold,
                'volume_threshold': self.config.momentum.volume_threshold,
                'use_macd': self.config.momentum.use_macd,
                'use_bollinger': self.config.momentum.use_bollinger,
                'entry_confirmation': self.config.momentum.entry_confirmation
            }
            base_config.update(momentum_cfg)
        
        elif self.config.strategy == 'arbitrage':
            arb_cfg = {
                'min_profit_pct': self.config.arbitrage.min_profit_pct,
                'max_trade_size': self.config.arbitrage.max_trade_size,
                'exchanges': self.config.arbitrage.exchanges
            }
            base_config.update(arb_cfg)
        
        elif self.config.strategy == 'multi':
            base_config.update({
                'strategy_weights': {'grid': 0.4, 'momentum': 0.6},
                'grid_config': self._get_grid_config(),
                'momentum_config': self._get_momentum_config()
            })
        
        return base_config
    
    def _get_grid_config(self) -> Dict:
        """Get grid strategy config dict"""
        return {
            'grid_levels': self.config.grid.grid_levels,
            'grid_spacing_pct': self.config.grid.grid_spacing_pct,
            'order_size': self.config.grid.order_size,
            'volatility_adjust': self.config.grid.volatility_adjust
        }
    
    def _get_momentum_config(self) -> Dict:
        """Get momentum strategy config dict"""
        return {
            'rsi_period': self.config.momentum.rsi_period,
            'volume_threshold': self.config.momentum.volume_threshold,
            'use_macd': self.config.momentum.use_macd
        }
    
    def fetch_market_data(self) -> Dict[str, Dict]:
        """Fetch market data for all trading pairs"""
        market_data = {}
        
        for symbol in self.config.symbols:
            try:
                data = {}
                
                # Get ticker data
                data['ticker'] = self.api.get_ticker(symbol)
                
                # Get orderbook
                data['orderbook'] = self.api.get_orderbook(symbol, limit=5)
                
                # Get klines
                data['klines'] = self.api.get_klines(
                    symbol, 
                    self.config.timeframe, 
                    limit=100
                )
                
                market_data[symbol] = data
                
            except ToobitAPIError as e:
                logger.warning(f"Failed to fetch {symbol}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error fetching {symbol}: {e}")
        
        return market_data
    
    def run_cycle(self) -> bool:
        """Run one trading cycle"""
        try:
            # Fetch market data
            market_data = self.fetch_market_data()
            
            if not market_data:
                logger.warning("No market data available")
                return False
            
            # Run strategy analysis
            if self.strategy.should_analyze():
                signals = self.strategy.analyze(market_data)
                
                # Execute signals
                for signal in signals:
                    if signal.confidence >= self.strategy.min_confidence:
                        logger.info(f"Signal: {signal}")
                        
                        # Check risk limits
                        if not self._check_risk_limits(signal):
                            logger.warning(f"Signal blocked by risk limits: {signal}")
                            continue
                        
                        # Execute
                        success = self.strategy.execute(signal, self.executor)
                        if success:
                            logger.info(f"Executed: {signal.action} {signal.symbol}")
            
            # Log status periodically
            if self.cycle_count % 60 == 0:
                self._log_status(market_data)
            
            return True
            
        except Exception as e:
            self.errors_count += 1
            logger.error(f"Cycle error: {e}")
            if self.errors_count > 10:
                logger.error("Too many errors, stopping bot")
                return False
            return True
    
    def _check_risk_limits(self, signal: StrategySignal) -> bool:
        """Check if signal passes risk management rules"""
        # Max position size
        if signal.metadata.get('size', 0) > self.config.risk.max_position_size:
            return False
        
        # Max open positions
        if hasattr(self.executor, 'get_positions'):
            positions = self.executor.get_positions()
            if len(positions) >= self.config.risk.max_open_positions:
                return False
        
        return True
    
    def _log_status(self, market_data: Dict):
        """Log current status"""
        if self.mode == 'paper' and self.paper_account:
            pnl = self.paper_account.get_pnl()
            logger.info(f"PAPER STATUS: Balance={pnl['current_balance']:.2f}, "
                       f"PnL={pnl['total_pnl']:.2f} ({pnl['return_pct']:+.2f}%), "
                       f"Trades={pnl['total_trades']}")
        
        # Log prices
        for symbol, data in market_data.items():
            ticker = data.get('ticker', {})
            price = ticker.get('lastPrice', 'N/A')
            change = ticker.get('priceChangePercent', 'N/A')
            logger.info(f"Market: {symbol} = {price} ({change}%)")
    
    def run(self):
        """Main bot loop"""
        if not self.initialize():
            logger.error("Bot initialization failed")
            return
        
        logger.info("="*60)
        logger.info("BOT STARTED - Running main loop")
        logger.info("Press Ctrl+C to stop gracefully")
        logger.info("="*60)
        
        self.running = True
        self.start_time = time.time()
        
        try:
            while self.running:
                self.cycle_count += 1
                
                # Run trading cycle
                if not self.run_cycle():
                    break
                
                # Sleep until next cycle
                time.sleep(self.config.update_interval)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        finally:
            self.stop()
    
    def stop(self):
        """Graceful shutdown"""
        if not self.running:
            return
        
        self.running = False
        logger.info("Shutting down bot...")
        
        # Save paper account state
        if self.paper_account:
            self.paper_account._save_state()
            logger.info(self.paper_account.get_summary())
        
        # Cancel open orders in live mode
        if self.mode == 'live' and self.api:
            try:
                for symbol in self.config.symbols:
                    self.api.cancel_all_orders(symbol)
                    logger.info(f"Cancelled open orders for {symbol}")
            except Exception as e:
                logger.warning(f"Error cancelling orders: {e}")
        
        # Final stats
        runtime = time.time() - self.start_time if self.start_time else 0
        logger.info("="*60)
        logger.info("BOT STOPPED")
        logger.info(f"Runtime: {runtime/60:.1f} minutes")
        logger.info(f"Cycles: {self.cycle_count}")
        logger.info(f"Errors: {self.errors_count}")
        logger.info("="*60)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Toobit Trading Bot - Paper & Live Trading'
    )
    parser.add_argument(
        '--mode', '-m',
        choices=['paper', 'live'],
        default='paper',
        help='Trading mode (default: paper)'
    )
    parser.add_argument(
        '--strategy', '-s',
        choices=['grid', 'momentum', 'arbitrage', 'multi'],
        default='grid',
        help='Trading strategy (default: grid)'
    )
    parser.add_argument(
        '--symbol',
        default='BTCUSDT',
        help='Trading symbol (default: BTCUSDT)'
    )
    parser.add_argument(
        '--config', '-c',
        help='Predefined config name'
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Enable live trading (requires confirmation)'
    )
    
    args = parser.parse_args()
    
    # Override mode if --live flag
    mode = 'live' if args.live else args.mode
    
    # Use predefined config if specified
    if args.config:
        config = get_config(args.config)
        # Override with CLI args
        if args.live:
            config.mode = 'live'
    else:
        config = None
    
    # Create and run bot
    bot = ToobitBot(
        mode=mode,
        strategy=args.strategy,
        symbol=args.symbol,
        config=config
    )
    
    bot.run()


if __name__ == '__main__':
    main()
