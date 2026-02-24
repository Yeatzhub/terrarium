"""
Pionex SOL COIN-M PERP Trading Bot
Main bot orchestrating strategy, execution, and risk management
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path

# Add shared directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'shared'))

from client import PionexClient, PionexCredentials
from strategy import XRPStrategy as SolStrategy, StrategyConfig, Signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/pionex_sol_bot.log')
    ]
)
logger = logging.getLogger('pionex_sol_bot')

class PionexSolBot:
    """Pionex SOL COIN-M PERP Trading Bot"""
    
    def __init__(self):
        # Configuration from environment
        self.paper_mode = os.getenv('PIONEX_PAPER', 'true').lower() == 'true'
        self.symbol = os.getenv('PIONEX_SYMBOL', 'SOL_USDT')
        self.initial_balance = float(os.getenv('PIONEX_CAPITAL', '10'))  # SOL
        
        # State file
        self.state_file = Path(__file__).parent / 'state.json'
        
        # Load state
        self.state = self._load_state()
        
        # Initialize components
        self._init_client()
        self._init_strategy()
        
        logger.info(f"Bot initialized: {self.symbol} | Paper: {self.paper_mode} | Balance: {self.state['balance']} SOL")
    
    def _init_client(self):
        """Initialize API client"""
        api_key = os.getenv('PIONEX_API_KEY', '')
        api_secret = os.getenv('PIONEX_API_SECRET', '')
        
        if not api_key or not api_secret:
            logger.warning("No API credentials - running in pure paper mode with CoinGecko data")
            self.client = None
        else:
            self.client = PionexClient(
                PionexCredentials(api_key, api_secret),
                paper=self.paper_mode
            )
            logger.info(f"API client initialized - Paper mode: {self.paper_mode}")
    
    def _init_strategy(self):
        """Initialize trading strategy"""
        config = StrategyConfig(
            max_position_size=10.0,  # SOL contracts (smaller due to higher price)
            risk_per_trade=0.02,
            breakout_threshold=0.008,  # 0.8% (SOL more volatile)
            volatility_threshold=0.012,
            leverage=15,
            stop_loss_pct=0.02,  # 2%
            take_profit_ratio=2.0,
            cooldown_minutes=3
        )
        self.strategy = SolStrategy(config)
        logger.info("Strategy initialized with SOL-specific parameters")
    
    def _load_state(self) -> Dict:
        """Load state from file"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Default state
        return {
            'balance': self.initial_balance,
            'initial_balance': self.initial_balance,
            'realized_pnl': 0.0,
            'unrealized_pnl': 0.0,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'trades': [],
            'positions': {},
            'status': 'running',
            'consecutive_losses': 0,
            'daily_pnl': 0.0,
            'trades_today': 0,
            'timestamp': datetime.now().isoformat()
        }
    
    def _save_state(self):
        """Save state to file"""
        self.state['timestamp'] = datetime.now().isoformat()
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get_price(self) -> float:
        """Get current SOL price"""
        # Try CoinGecko as primary (free, reliable)
        try:
            import requests
            resp = requests.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd',
                timeout=5
            )
            if resp.status_code == 200:
                return resp.json().get('solana', {}).get('usd', 0)
        except Exception as e:
            logger.debug(f"CoinGecko price fetch failed: {e}")
        
        # Fallback to Pionex API if client available
        if self.client:
            try:
                ticker = self.client.get_ticker('SOL_USDT')
                return float(ticker.get('price', 0))
            except Exception as e:
                logger.debug(f"Pionex price fetch failed: {e}")
        
        return 0.0
    
    def run(self):
        """Main bot loop"""
        logger.info(f"Starting SOL bot loop...")
        
        while True:
            try:
                price = self.get_price()
                if price <= 0:
                    logger.warning("Invalid price, skipping tick")
                    time.sleep(10)
                    continue
                
                # Get current position
                position = self.state['positions'].get(self.symbol)
                
                # Build tick data
                tick_data = {
                    'price': price,
                    'symbol': self.symbol,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Get signal from strategy
                raw_signal, signal_data = self.strategy.generate_signal(price)
                signal = {
                    'signal': raw_signal,
                    'reason': signal_data.get('reason', ''),
                    'size': signal_data.get('size', 1.0),
                    'stop_loss': signal_data.get('stop_loss'),
                    'take_profit': signal_data.get('take_profit')
                }
                
                logger.info(f"Price: ${price:.2f} | Signal: {signal.get('signal')} | Reason: {signal.get('reason', 'N/A')}")
                
                # Execute signal
                self._execute_signal(signal, price)
                
                # Save state
                self._save_state()
                
                # Sleep
                time.sleep(10)
                
            except KeyboardInterrupt:
                logger.info("Bot stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in bot loop: {e}", exc_info=True)
                time.sleep(30)
                break
            except Exception as e:
                logger.error(f"Error in bot loop: {e}")
                time.sleep(30)
    
    def _execute_signal(self, signal: Dict, price: float):
        """Execute trading signal"""
        action = signal.get('signal')
        
        if action == Signal.LONG:
            self._open_position('LONG', signal.get('size', 1.0), price, signal.get('stop_loss'), signal.get('take_profit'))
        elif action == Signal.SHORT:
            self._open_position('SHORT', signal.get('size', 1.0), price, signal.get('stop_loss'), signal.get('take_profit'))
        elif action == Signal.EXIT:
            self._close_position(price)
    
    def _open_position(self, side: str, size: float, price: float, stop_loss: float = None, take_profit: float = None):
        """Open a new position"""
        if self.state['positions'].get(self.symbol):
            logger.info(f"Position already exists, skipping open")
            return
        
        self.state['positions'][self.symbol] = {
            'side': side,
            'size': size,
            'entry_price': price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'opened_at': datetime.now().isoformat()
        }
        
        logger.info(f"📈 OPENED {side} {size} SOL @ ${price:.2f} | SL: ${stop_loss:.2f} | TP: ${take_profit:.2f}")
    
    def _close_position(self, price: float):
        """Close current position"""
        position = self.state['positions'].get(self.symbol)
        if not position:
            return
        
        entry = position['entry_price']
        size = position['size']
        side = position['side']
        
        # Calculate P&L
        if side == 'LONG':
            pnl = (price - entry) * size
        else:
            pnl = (entry - price) * size
        
        # Update state
        self.state['balance'] += pnl
        self.state['realized_pnl'] += pnl
        self.state['total_trades'] += 1
        
        if pnl > 0:
            self.state['winning_trades'] += 1
            self.state['consecutive_losses'] = 0
        else:
            self.state['losing_trades'] += 1
            self.state['consecutive_losses'] += 1
        
        # Record trade
        self.state['trades'].append({
            'symbol': self.symbol,
            'side': side,
            'size': size,
            'entry_price': entry,
            'exit_price': price,
            'pnl': pnl,
            'exit_reason': 'signal',
            'closed_at': datetime.now().isoformat()
        })
        
        # Clear position
        del self.state['positions'][self.symbol]
        
        logger.info(f"📉 CLOSED {side} {size} SOL @ ${price:.2f} | P&L: ${pnl:.4f}")
    
    def stop(self):
        """Stop the bot gracefully"""
        self.state['status'] = 'stopped'
        self._save_state()
        logger.info("Bot stopped")

if __name__ == '__main__':
    bot = PionexSolBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        bot.stop()