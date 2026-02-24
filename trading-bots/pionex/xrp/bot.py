"""
Pionex XRP COIN-M PERP Trading Bot
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
from strategy import XRPStrategy, StrategyConfig, Signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/pionex_xrp_bot.log')
    ]
)
logger = logging.getLogger('pionex_xrp_bot')

class PionexXRPBot:
    """Pionex XRP COIN-M PERP Trading Bot"""
    
    def __init__(self):
        # Configuration from environment
        self.paper_mode = os.getenv('PIONEX_PAPER', 'true').lower() == 'true'
        self.symbol = os.getenv('PIONEX_SYMBOL', 'XRP_USDT')  # Pionex USDT-M format
        self.initial_balance = float(os.getenv('PIONEX_CAPITAL', '100'))  # XRP
        
        # State file
        self.state_file = Path(__file__).parent / 'state.json'
        
        # Load state
        self.state = self._load_state()
        
        # Initialize components
        self._init_client()
        self._init_strategy()
        
        logger.info(f"Bot initialized: {self.symbol} | Paper: {self.paper_mode} | Balance: {self.state['balance']} XRP")
    
    def _init_client(self):
        """Initialize API client"""
        api_key = os.getenv('PIONEX_API_KEY', '')
        api_secret = os.getenv('PIONEX_API_SECRET', '')
        
        if not api_key or not api_secret:
            logger.warning("No API credentials - running in pure paper mode with CoinGecko data")
            self.client = None
        else:
            # Initialize client with API credentials
            # Even in paper mode, we use real Pionex data for prices
            self.client = PionexClient(
                PionexCredentials(api_key, api_secret),
                paper=self.paper_mode  # True = simulate trades, False = real trades
            )
            logger.info(f"API client initialized - Paper mode: {self.paper_mode} (trades simulated, market data real)")
    
    def _init_strategy(self):
        """Initialize trading strategy"""
        config = StrategyConfig(
            max_position_size=100.0,  # XRP contracts
            risk_per_trade=0.02,
            breakout_threshold=0.005,  # 0.5%
            volatility_threshold=0.008,
            leverage=20,
            stop_loss_pct=0.015,  # 1.5%
            take_profit_ratio=2.0,
            cooldown_minutes=3
        )
        self.strategy = XRPStrategy(config)
    
    def _load_state(self) -> Dict:
        """Load or initialize state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    logger.info(f"Loaded state from {self.state_file}")
                    return state
            except Exception as e:
                logger.error(f"Error loading state: {e}")
        
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
            'last_trade_date': None
        }
    
    def _save_state(self):
        """Save current state"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def _get_price(self) -> Optional[float]:
        """Get current XRP price - prefer Pionex API if available, fallback to CoinGecko"""
        
        # Try Pionex API first if credentials are available
        # This gives us real exchange price even in paper mode
        if self.client:
            try:
                ticker = self.client.get_ticker(self.symbol)
                price = float(ticker.get('price', 0))
                if price > 0:
                    logger.debug(f"Pionex XRP price: ${price:.4f}")
                    return price
            except Exception as e:
                logger.warning(f"Error fetching Pionex price: {e}")
        
        # Fallback to CoinGecko if Pionex not available
        try:
            import requests
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=ripple&vs_currencies=usd',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                price = data.get('ripple', {}).get('usd', 0)
                if price > 0:
                    logger.debug(f"CoinGecko XRP price: ${price:.4f}")
                    return float(price)
        except Exception as e:
            logger.error(f"Error fetching CoinGecko price: {e}")
        
        # Last resort: use a reasonable default
        logger.warning("Using fallback price - all market data sources unavailable")
        return 1.40  # Approximate XRP price
    
    def _execute_signal(self, signal: Signal, data: Dict):
        """Execute trading signal"""
        if signal == Signal.HOLD:
            logger.info(f"HOLD: {data.get('reason', 'no_signal')}")
            return
        
        side = data.get('side')
        size = data.get('size', 0)
        entry = data.get('entry', 0)
        stop = data.get('stop', 0)
        target = data.get('target', 0)
        
        logger.info(f"🔥 SIGNAL: {side} {size:.2f} XRP @ ${entry:.4f} | Stop: ${stop:.4f} | Target: ${target:.4f}")
        
        if self.paper_mode:
            self._simulate_trade(side, size, entry, stop, target)
        else:
            # Live trading - place real order
            self._place_live_order(side, size, entry, stop)
    
    def _simulate_trade(self, side: str, size: float, entry: float, stop: float, target: float):
        """Simulate trade execution in paper mode"""
        position_key = self.symbol
        
        # Check if we have an open position
        if position_key in self.state['positions']:
            logger.info("Already have position - skipping")
            return
        
        # Record entry
        position = {
            'symbol': self.symbol,
            'side': side,
            'size': size,
            'entry_price': entry,
            'stop_price': stop,
            'target_price': target,
            'entry_time': datetime.now().isoformat(),
            'unrealized_pnl': 0.0
        }
        
        self.state['positions'][position_key] = position
        self.state['total_trades'] += 1
        
        logger.info(f"📝 Paper position opened: {side} {size:.2f} XRP @ ${entry:.4f}")
        self._save_state()
    
    def _place_live_order(self, side: str, size: float, entry: float, stop: float):
        """Place live order via API"""
        if not self.client:
            logger.error("No client available for live trading")
            return
        
        try:
            result = self.client.place_order(
                symbol=self.symbol,
                side=side,
                size=size,
                order_type='MARKET'
            )
            logger.info(f"Live order result: {result}")
        except Exception as e:
            logger.error(f"Error placing live order: {e}")
    
    def _check_positions(self):
        """Check and update open positions"""
        current_price = self._get_price()
        if not current_price:
            return
        
        position_key = self.symbol
        if position_key not in self.state['positions']:
            return
        
        position = self.state['positions'][position_key]
        entry = position['entry_price']
        stop = position['stop_price']
        target = position['target_price']
        side = position['side']
        size = position['size']
        
        # Calculate unrealized P&L (in XRP for COIN-M)
        if side == 'BUY':  # LONG
            pnl = (current_price - entry) / entry * size
            should_exit = current_price <= stop or current_price >= target
        else:  # SHORT
            pnl = (entry - current_price) / entry * size
            should_exit = current_price >= stop or current_price <= target
        
        position['unrealized_pnl'] = pnl
        self.state['unrealized_pnl'] = pnl
        
        # Check for exit
        if should_exit:
            exit_reason = 'target' if current_price >= target else 'stop'
            self._close_position(current_price, exit_reason)
        else:
            logger.info(f"Position: {side} {size:.2f} XRP | Entry: ${entry:.4f} | Current: ${current_price:.4f} | P&L: {pnl:.4f} XRP")
    
    def _close_position(self, exit_price: float, reason: str):
        """Close position and record trade"""
        position_key = self.symbol
        if position_key not in self.state['positions']:
            return
        
        position = self.state['positions'][position_key]
        side = position['side']
        size = position['size']
        entry = position['entry_price']
        
        # Calculate realized P&L (in XRP)
        if side == 'BUY':
            pnl = (exit_price - entry) / entry * size
        else:
            pnl = (entry - exit_price) / entry * size
        
        # Deduct fees (0.05% per trade, 0.1% total)
        fees = size * 0.001
        net_pnl = pnl - fees
        
        # Record trade
        trade = {
            'symbol': self.symbol,
            'side': side,
            'size': size,
            'entry_price': entry,
            'exit_price': exit_price,
            'pnl': round(net_pnl, 6),
            'fees': round(fees, 6),
            'exit_reason': reason,
            'closed_at': datetime.now().isoformat()
        }
        
        self.state['trades'].append(trade)
        self.state['balance'] += net_pnl
        self.state['realized_pnl'] += net_pnl
        self.state['daily_pnl'] += net_pnl
        
        # Track wins/losses
        if net_pnl > 0:
            self.state['winning_trades'] += 1
            self.strategy.record_trade(1)
            logger.info(f"✅ WIN: +{net_pnl:.4f} XRP ({reason})")
        else:
            self.state['losing_trades'] += 1
            self.strategy.record_trade(-1)
            self.state['consecutive_losses'] += 1
            logger.info(f"❌ LOSS: {net_pnl:.4f} XRP ({reason})")
        
        # Remove position
        del self.state['positions'][position_key]
        self.state['unrealized_pnl'] = 0.0
        
        self._save_state()
    
    def run(self):
        """Main trading loop"""
        logger.info("🚀 Starting Pionex XRP COIN-M Bot...")
        
        try:
            while True:
                # Get price
                price = self._get_price()
                if not price:
                    logger.warning("No price available, retrying...")
                    time.sleep(5)
                    continue
                
                logger.info(f"📊 XRP Price: ${price:.4f}")
                
                # Update strategy
                self.strategy.update(price)
                
                # Check positions first
                self._check_positions()
                
                # Generate signal (only if no position)
                if self.symbol not in self.state['positions']:
                    signal, data = self.strategy.generate_signal(price)
                    self._execute_signal(signal, data)
                
                # Save state
                self._save_state()
                
                # Status report
                logger.info(f"💰 Balance: {self.state['balance']:.4f} XRP | Trades: {self.state['total_trades']} | Positions: {len(self.state['positions'])}")
                
                # Wait for next tick
                time.sleep(30)  # 30 second intervals
                
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            self._save_state()
        except Exception as e:
            logger.error(f"Bot error: {e}", exc_info=True)
            self._save_state()

if __name__ == '__main__':
    bot = PionexXRPBot()
    bot.run()
