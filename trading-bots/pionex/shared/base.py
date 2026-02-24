# Base Strategy Class
from abc import ABC, abstractmethod
from typing import Dict, Optional
import pandas as pd

class BaseStrategy(ABC):
    """Base class for trading strategies"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.name = self.__class__.__name__
    
    @abstractmethod
    def analyze(self, ohlcv_data: pd.DataFrame) -> Dict:
        """
        Analyze market data and return signal
        
        Returns: {
            'signal': 'buy' | 'sell' | 'hold',
            'strength': float (0-1),
            'metadata': dict (optional)
        }
        """
        pass
    
    def calculate_position_size(self, balance: float, price: float) -> float:
        """Calculate position size based on config"""
        percent = self.config.get('POSITION_SIZE_PERCENT', 10)
        max_position = self.config.get('MAX_POSITION_USDT', 100)
        
        size = (balance * percent / 100) / price
        max_size = max_position / price
        
        return min(size, max_size)
