#!/usr/bin/env python3
"""
Pionex BTC COIN-M Perp Trading Bot
Migrating Toobit strategy to Pionex
"""

import asyncio
import logging
import os
import signal
import sys
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/pionex_btc_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import Pionex client from shared
sys.path.insert(0, str(Path(__file__).parent.parent / 'shared'))
from client import PionexClient, PionexCredentials
from oracle_aggressive import AggressiveStrategy, Signal

class PionexBTCBot:
    """BTC COIN-M Perp bot for Pionex"""
    
    def __init__(self):
        self.paper_mode = os.getenv('PIONEX_BTC_PAPER', 'true').lower() == 'true'
        self.symbol = 'BTC_USDT'  # Pionex USDT-M format
        self.initial_balance = float(os.getenv('PIONEX_BTC_CAPITAL', '0.01'))  # 0.01 BTC (~$1000 at $100k BTC)
        self.balance = self.initial_balance
        
        # State file
        self.state_file = Path(__file__).parent / 'state.json'
        self.state = self._load_state()
        
        # Trading components
        self.client = None
        self.strategy = AggressiveStrategy()
        self.price_history = []
        self.max_history = 100
        self.last_signal = None
        self.last_signal_time = 0
        self.cooldown_seconds = 300  # 5 min between trades
        
        logger.info(f"BTC Bot initialized: {self.symbol}")
        logger.info(f"Paper mode: {self.paper_mode}")
        logger.info(f"Balance: {self.balance} BTC")
        
    def _init_client(self):
        """Initialize API client"""
        api_key = os.getenv('PIONEX_API_KEY', '')
        api_secret = os.getenv('PIONEX_API_SECRET', '')
        
        if not api_key or not api_secret:
            logger.warning("No API credentials - pure paper mode")
            self.client = None
        else:
            self.client = PionexClient(
                PionexCredentials(api_key, api_secret),
                paper=self.paper_mode
            )
            
    def _load_state(self) -> Dict:
        """Load or initialize state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.balance = state.get('balance', self.initial_balance)
                    logger.info(f"Loaded state: {self.balance} BTC")
                    return state
            except Exception as e:
                logger.error(f"Error loading state: {e}")
                
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
            'consecutive_losses': 0
        }
        
    def _save_state(self):
        """Save current state"""
        try:
            self.state['balance'] = self.balance
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            
    def _get_price(self) -> Optional[float]:
        """Get current BTC price with retry logic"""
        # Try CoinGecko with rate limiting
        try:
            import requests
            response = requests.get(
                'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd',
                timeout=10
            )
            if response.status_code == 200:
                return float(response.json()['bitcoin']['usd'])
        except Exception as e:
            logger.debug(f"Price fetch error: {e}")
            
        return None
        
    def _simulate_trade(self, side: str, size: float, price: float, stop: float, target: float):
        """Simulate paper trade"""
        trade = {
            'id': f"btc_{int(time.time())}",
            'symbol': self.symbol,
            'side': side,
            'size': size,
            'entry': price,
            'stop': stop,
            'target': target,
            'status': 'open',
            'opened_at': datetime.now().isoformat(),
            'pnl': 0.0
        }
        
        self.state['positions'][trade['id']] = trade
        self._save_state()
        
        logger.info(f"📊 PAPER {side}: {size:.5f} BTC @ ${price:,.2f}")
        logger.info(f"   Stop: ${stop:,.2f} | Target: ${target:,.2f}")
        
    def run(self):
        """Main trading loop"""
        logger.info("🚀 Starting Pionex BTC COIN-M Bot...")
        self._init_client()
        
        try:
            while True:
                price = self._get_price()
                if not price:
                    logger.warning("No price available, retrying...")
                    time.sleep(5)
                    continue
                    
                logger.info(f"💰 BTC: ${price:,.2f} | Balance: {self.balance:.5f} BTC")
                
                # Close positions logic here
                # Strategy signal logic here
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down...")
            self._save_state()
            
if __name__ == '__main__':
    bot = PionexBTCBot()
    bot.run()
