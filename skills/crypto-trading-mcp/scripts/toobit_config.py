"""
Toobit Trading Bot Configuration
Centralized configuration for all bot components.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class APIConfig:
    """API credentials and endpoints"""
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    base_url: str = "https://api.toobit.com"
    testnet: bool = False
    
    def __post_init__(self):
        # Override with environment variables if set
        self.api_key = os.getenv('TOOBIT_API_KEY', self.api_key)
        self.api_secret = os.getenv('TOOBIT_API_SECRET', self.api_secret)
        
        if self.testnet:
            self.base_url = "https://api-testnet.toobit.com"


@dataclass
class RiskConfig:
    """Risk management settings"""
    max_position_size: float = 1000.0  # USDT
    max_position_pct: float = 0.2  # 20% of balance per position
    max_daily_loss: float = 0.05  # 5% max daily loss
    max_open_positions: int = 5
    stop_loss_pct: float = 0.02  # 2% stop loss
    take_profit_pct: float = 0.04  # 4% take profit
    trailing_stop_pct: float = 0.015  # 1.5% trailing stop


@dataclass
class GridStrategyConfig:
    """Grid trading strategy parameters"""
    enabled: bool = True
    grid_levels: int = 10  # Number of grid levels per side
    grid_spacing_pct: float = 0.005  # 0.5% spacing between grids
    order_size: float = 100.0  # USDT per grid order
    max_grids: int = 20  # Max open grid orders
    rebalance_threshold: float = 0.02  # Rebalance when price moves 2%
    
    # Fast growth optimizations
    volatility_adjust: bool = True  # Adjust grid spacing based on volatility
    trend_following: bool = True  # Shift grids with trend
    pyramiding: bool = False  # Add to winning positions


@dataclass
class MomentumStrategyConfig:
    """Momentum/Rsi strategy parameters"""
    enabled: bool = True
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    volume_threshold: float = 1.5  # 1.5x average volume for breakout
    price_change_threshold: float = 0.02  # 2% price change for breakout
    
    # Fast growth optimizations
    use_macd: bool = True
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    use_bollinger: bool = True
    bb_period: int = 20
    bb_std: float = 2.0
    entry_confirmation: int = 2  # Candles to confirm signal


@dataclass
class ArbitrageStrategyConfig:
    """Cross-exchange arbitrage parameters"""
    enabled: bool = True
    min_profit_pct: float = 0.001  # 0.1% minimum profit after fees
    max_trade_size: float = 5000.0  # USDT
    exchanges: List[str] = field(default_factory=lambda: [
        'binance', 'bybit', 'okx', 'kraken'
    ])
    update_interval: int = 5  # seconds


@dataclass
class BotConfig:
    """Main bot configuration"""
    mode: str = 'paper'  # 'paper' or 'live'
    strategy: str = 'grid'  # 'grid', 'momentum', 'arbitrage', or 'multi'
    symbol: str = 'BTCUSDT'
    symbols: List[str] = field(default_factory=lambda: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'])
    
    # Trading parameters
    timeframe: str = '1m'  # Default timeframe for data
    update_interval: int = 10  # seconds between cycles
    
    # Paper trading settings
    paper_initial_balance: float = 10000.0  # USDT
    paper_state_file: str = 'toobit_paper_state.json'
    
    # Logging
    log_level: str = 'INFO'
    log_file: str = 'toobit_bot.log'
    log_to_console: bool = True
    
    # Safety
    require_live_confirmation: bool = True
    dry_run_first: bool = True  # Run one cycle dry before trading
    
    # Component configs
    api: APIConfig = field(default_factory=APIConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    grid: GridStrategyConfig = field(default_factory=GridStrategyConfig)
    momentum: MomentumStrategyConfig = field(default_factory=MomentumStrategyConfig)
    arbitrage: ArbitrageStrategyConfig = field(default_factory=ArbitrageStrategyConfig)
    
    def validate(self):
        """Validate configuration"""
        if self.mode not in ['paper', 'live']:
            raise ValueError(f"Invalid mode: {self.mode}. Must be 'paper' or 'live'")
        
        if self.strategy not in ['grid', 'momentum', 'arbitrage', 'multi']:
            raise ValueError(f"Invalid strategy: {self.strategy}")
        
        if self.mode == 'live' and not self.api.api_key:
            raise ValueError("API key required for live trading")
        
        if self.mode == 'live' and self.require_live_confirmation:
            print("\n" + "="*60)
            print("⚠️  LIVE TRADING MODE ACTIVATED")
            print("="*60)
            print(f"Strategy: {self.strategy}")
            print(f"Symbol(s): {self.symbols}")
            print(f"Risk: {self.risk.max_position_pct*100}% max per position")
            print("="*60 + "\n")
        
        return True


# Predefined configurations for quick setup
CONFIGS = {
    'paper_grid': BotConfig(
        mode='paper',
        strategy='grid',
        symbol='BTCUSDT',
        symbols=['BTCUSDT', 'ETHUSDT'],
        grid=GridStrategyConfig(
            grid_levels=15,
            grid_spacing_pct=0.008,
            volatility_adjust=True,
            trend_following=True
        )
    ),
    'paper_momentum': BotConfig(
        mode='paper',
        strategy='momentum',
        symbol='BTCUSDT',
        symbols=['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT'],
        momentum=MomentumStrategyConfig(
            rsi_period=14,
            use_macd=True,
            use_bollinger=True,
            entry_confirmation=2
        )
    ),
    'paper_multi': BotConfig(
        mode='paper',
        strategy='multi',
        symbols=['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'DOTUSDT'],
        update_interval=15
    ),
    'conservative_live': BotConfig(
        mode='live',
        strategy='grid',
        symbol='BTCUSDT',
        risk=RiskConfig(
            max_position_size=500.0,
            max_position_pct=0.1,
            stop_loss_pct=0.015
        ),
        grid=GridStrategyConfig(
            grid_levels=5,
            grid_spacing_pct=0.01,
            trend_following=False
        )
    ),
    'aggressive_live': BotConfig(
        mode='live',
        strategy='momentum',
        symbols=['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
        risk=RiskConfig(
            max_position_size=2000.0,
            max_position_pct=0.3,
            stop_loss_pct=0.03
        ),
        momentum=MomentumStrategyConfig(
            rsi_overbought=75,
            rsi_oversold=25,
            entry_confirmation=1
        )
    )
}


def get_config(name: str = 'paper_grid') -> BotConfig:
    """Get a predefined configuration by name"""
    if name not in CONFIGS:
        raise ValueError(f"Unknown config: {name}. Available: {list(CONFIGS.keys())}")
    return CONFIGS[name]
