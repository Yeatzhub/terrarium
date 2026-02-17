"""
Kraken Trading Bot
Main orchestrator for paper and live trading modes.
"""

import argparse
import time
import signal
import logging
import sys
from typing import Dict, List

from kraken_api import KrakenAPI
from kraken_paper_trader import PaperAccount
from kraken_strategies import GridStrategy, MomentumStrategy, ScalpingStrategy, MeanReversionStrategy


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('kraken_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('KrakenBot')


class KrakenBot:
    """Main trading bot for Kraken exchange"""
    
    STRATEGIES = {
        'grid': GridStrategy,
        'momentum': MomentumStrategy,
        'scalp': ScalpingStrategy,
        'mean': MeanReversionStrategy
    }
    
    def __init__(self, mode: str = 'paper', strategy: str = 'momentum',
                 pair: str = 'XXBTZUSD', interval: int = 60,
                 api_key: str = None, api_secret: str = None):
        self.mode = mode
        self.pair = pair
        self.interval = interval
        self.running = False
        self.cycles = 0
        
        # Initialize API (paper mode works without keys)
        self.api = KrakenAPI(api_key=api_key, api_secret=api_secret)
        
        # Initialize paper trading account
        self.paper = PaperAccount(state_file='kraken_paper_state.json')
        
        # Initialize strategy
        if strategy not in self.STRATEGIES:
            raise ValueError(f"Unknown strategy: {strategy}. Use: {list(self.STRATEGIES.keys())}")
        self.strategy = self.STRATEGIES[strategy]()
        self.strategy_name = strategy
        
        logger.info(f"KrakenBot: mode={mode}, strategy={strategy}, pair={pair}")
        
        # Safety check for live mode
        if mode == 'live':
            self._confirm_live_mode()
    
    def _confirm_live_mode(self):
        """Require explicit confirmation for live trading"""
        print("\n" + "="*60)
        print("⚠️  LIVE TRADING MODE - REAL MONEY AT RISK")
        print("="*60)
        print(f"Exchange: Kraken")
        print(f"Trading Pair: {self.pair}")
        print(f"Strategy: {self.strategy_name}")
        print("\nThis will execute REAL trades with REAL funds!")
        print("="*60)
        
        confirmation = input("\nType 'LIVE' to confirm: ")
        if confirmation.strip() != 'LIVE':
            print("❌ Live mode not confirmed. Exiting.")
            sys.exit(1)
        
        logger.warning("LIVE MODE CONFIRMED - Real trades will execute!")
    
    def fetch_market_data(self) -> Dict:
        """Fetch current market data"""
        try:
            # Get ticker
            ticker = self.api.get_ticker([self.pair])
            pair_data = ticker.get(self.pair, {})
            
            # Get OHLC data
            ohlc = self.api.get_ohlc(self.pair, interval=1)
            ohlc_data = ohlc.get(self.pair, [])
            
            current_price = float(pair_data.get('c', [0])[0]) if pair_data else 0
            
            return {
                'current_price': current_price,
                'ohlc': ohlc_data,
                'bid': float(pair_data.get('b', [0])[0]) if pair_data else current_price,
                'ask': float(pair_data.get('a', [0])[0]) if pair_data else current_price,
                'volume': float(pair_data.get('v', [0, 0])[1]) if pair_data else 0
            }
        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            return {'current_price': 0, 'ohlc': [], 'bid': 0, 'ask': 0, 'volume': 0}
    
    def execute_signal(self, signal, market_data: Dict) -> bool:
        """Execute trading signal"""
        if signal.action == 'hold':
            return False
        
        price = market_data['current_price']
        
        if self.mode == 'paper':
            # Paper trading
            if signal.action == 'buy':
                # Use fixed position size for paper trading
                position_value = 100.0  # $100 per trade
                quantity = position_value / price
                result = self.paper.place_paper_order(
                    self.pair, 'buy', 'market', quantity, current_price=price
                )
                if result['success']:
                    logger.info(f"✅ Paper BUY executed: {quantity:.6f} @ ${price:.2f}")
                    return True
                else:
                    logger.warning(f"❌ Paper BUY failed: {result.get('error')}")
            
            elif signal.action == 'sell':
                position = self.paper.get_position(self.pair)
                if position and position.size > 0:
                    result = self.paper.place_paper_order(
                        self.pair, 'sell', 'market', position.size, current_price=price
                    )
                    if result['success']:
                        logger.info(f"✅ Paper SELL executed: {result}")
                        return True
        
        else:  # live mode
            # Live trading - would execute real orders
            # Implementation would call self.api.place_order()
            logger.warning(f"LIVE {signal.action.upper()} signal: confidence={signal.confidence:.2f}")
            # TODO: Implement live order execution
            pass
        
        return False
    
    def run_cycle(self):
        """Execute one trading cycle"""
        market_data = self.fetch_market_data()
        
        if market_data['current_price'] == 0:
            logger.warning("No market data available, skipping cycle")
            return
        
        # Get signal from strategy
        signal = self.strategy.analyze(market_data['ohlc'])
        
        # Log status
        pos = self.paper.get_position(self.pair)
        pos_str = f"Pos: {pos.size:.4f}" if pos else "No position"
        logger.info(f"Price: ${market_data['current_price']:.2f} | {pos_str} | Signal: {signal.action} ({signal.confidence:.2f})")
        
        # Execute if signal is strong enough
        if signal.confidence > 0.6 and signal.action != 'hold':
            self.execute_signal(signal, market_data)
            # Print paper account summary
            if self.mode == 'paper':
                summary = self.paper.get_summary({self.pair: market_data['current_price']})
                logger.info(f"Paper P&L: ${summary['realized_pnl']:.2f} | Balance: ${summary['balance']:.2f}")
        
        self.cycles += 1
    
    def run(self):
        """Main bot loop"""
        self.running = True
        logger.info("="*60)
        logger.info("BOT STARTED - Running main loop")
        logger.info("Press Ctrl+C to stop gracefully")
        logger.info("="*60)
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        try:
            while self.running:
                self.run_cycle()
                
                # Sleep until next cycle
                for _ in range(self.interval):
                    if not self.running:
                        break
                    time.sleep(1)
        
        except Exception as e:
            logger.error(f"Bot error: {e}", exc_info=True)
        
        finally:
            self.shutdown()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def shutdown(self):
        """Graceful shutdown"""
        logger.info("="*60)
        logger.info("BOT STOPPED")
        logger.info(f"Runtime: {self.cycles} cycles")
        
        # Print final summary
        market_data = self.fetch_market_data()
        summary = self.paper.get_summary({self.pair: market_data['current_price']})
        
        logger.info("="*60)
        logger.info("FINAL PAPER ACCOUNT SUMMARY")
        logger.info(f"Balance: ${summary['balance']:.2f}")
        logger.info(f"Realized P&L: ${summary['realized_pnl']:.2f}")
        logger.info(f"Unrealized P&L: ${summary['unrealized_pnl']:.2f}")
        logger.info(f"Total Return: {summary['total_return_pct']:.2f}%")
        logger.info(f"Trades: {summary['trades_count']}")
        logger.info(f"Win Rate: {summary['win_rate']:.1f}%")
        logger.info("="*60)
        
        self.paper.save_state()
        logger.info("State saved. Goodbye!")


def main():
    parser = argparse.ArgumentParser(description='Kraken Trading Bot')
    parser.add_argument('--mode', choices=['paper', 'live'], default='paper',
                       help='Trading mode (default: paper)')
    parser.add_argument('--strategy', choices=['grid', 'momentum', 'scalp', 'mean'], 
                       default='momentum', help='Trading strategy')
    parser.add_argument('--pair', default='XXBTZUSD', help='Trading pair (e.g., XXBTZUSD)')
    parser.add_argument('--interval', type=int, default=60, help='Cycle interval in seconds')
    parser.add_argument('--api-key', help='Kraken API key (for live mode)')
    parser.add_argument('--api-secret', help='Kraken API secret (for live mode)')
    
    args = parser.parse_args()
    
    bot = KrakenBot(
        mode=args.mode,
        strategy=args.strategy,
        pair=args.pair,
        interval=args.interval,
        api_key=args.api_key,
        api_secret=args.api_secret
    )
    
    bot.run()


if __name__ == '__main__':
    main()
