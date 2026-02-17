"""
Kraken Trading Bot Configuration
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class KrakenConfig:
    """Configuration for Kraken trading bot"""
    
    # API Credentials
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    
    # Trading Settings
    default_pair: str = 'XXBTZUSD'  # BTC/USD
    trading_pairs: tuple = ('XXBTZUSD', 'XETHZUSD', 'XXRPZUSD', 'XLTCZUSD')
    
    # Paper Trading
    paper_initial_balance: float = 10000.0
    paper_state_file: str = 'kraken_paper_state.json'
    
    # Risk Management
    max_position_size: float = 1000.0  # USDT per position
    max_position_pct: float = 0.2  # 20% of balance
    max_daily_loss: float = 0.05  # 5% max daily loss
    stop_loss_pct: float = 0.02  # 2%
    take_profit_pct: float = 0.04  # 4%
    
    # Strategy Defaults
    grid_levels: int = 10
    grid_spacing_pct: float = 0.005  # 0.5%
    grid_order_size: float = 100.0
    
    rsi_period: int = 14
    rsi_overbought: float = 70
    rsi_oversold: float = 30
    
    scalp_profit_target: float = 0.015  # 1.5%
    scalp_stop_loss: float = 0.008  # 0.8%
    
    # Update Intervals
    check_interval: int = 60  # seconds
    
    def __post_init__(self):
        """Load from environment variables if set"""
        self.api_key = os.getenv('KRAKEN_API_KEY', self.api_key)
        self.api_secret = os.getenv('KRAKEN_SECRET_KEY', self.api_secret)
    
    @classmethod
    def from_env(cls):
        """Create config from environment variables"""
        return cls()
    
    def is_live_ready(self) -> bool:
        """Check if configuration supports live trading"""
        return bool(self.api_key and self.api_secret)
