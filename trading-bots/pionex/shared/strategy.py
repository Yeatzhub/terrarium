"""
XRP COIN-M PERP Strategy
Optimized for XRP's volatility and COIN-M (inverse) contract mechanics
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class Signal(Enum):
    HOLD = 0
    LONG = 1
    SHORT = 2

@dataclass
class StrategyConfig:
    # Risk parameters (adjusted for XRP volatility)
    max_position_size: float = 100.0  # XRP contracts
    risk_per_trade: float = 0.02  # 2% of margin
    
    # XRP-specific breakout thresholds (XRP is more volatile than BTC)
    breakout_threshold: float = 0.005  # 0.5% (was 0.3% for BTC)
    volatility_threshold: float = 0.008  # 0.8% minimum volatility
    
    # Leverage (COIN-M allows higher leverage, but be careful)
    leverage: int = 20
    
    # Stop/Target (XRP needs wider stops due to volatility)
    stop_loss_pct: float = 0.015  # 1.5% stop (was 0.5%)
    take_profit_ratio: float = 2.0  # 2:1 reward/risk
    
    # Cooldown
    cooldown_minutes: int = 3  # 3 min between trades
    
    # Technical
    ema_fast: int = 8
    ema_slow: int = 21
    rsi_period: int = 14
    rsi_overbought: float = 70
    rsi_oversold: float = 30

class XRPStrategy:
    """
    Momentum breakout strategy optimized for XRP COIN-M PERP
    
    Key differences from BTC strategy:
    - Wider breakout thresholds (XRP more volatile)
    - Wider stops (avoid shakeouts)
    - Higher leverage typical for XRP (but manageable)
    - COIN-M = inverse contracts (P&L in XRP, not USDT)
    """
    
    def __init__(self, config: Optional[StrategyConfig] = None):
        self.config = config or StrategyConfig()
        self.price_history: List[float] = []
        self.volume_history: List[float] = []
        self.last_signal_time = 0
        self.consecutive_losses = 0
        self.total_risked = 0.0
        
    def update(self, price: float, volume: float = 0):
        """Update price history"""
        self.price_history.append(price)
        self.volume_history.append(volume)
        
        # Keep last 100 data points
        if len(self.price_history) > 100:
            self.price_history.pop(0)
            self.volume_history.pop(0)
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        prices_arr = np.array(prices[-period:])
        weights = np.exp(np.linspace(-1., 0., period))
        weights /= weights.sum()
        return np.convolve(prices_arr, weights, mode='valid')[0]
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI"""
        if len(prices) < period + 1:
            return 50
        
        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100 if avg_gain > 0 else 50
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def calculate_atr(self, prices: List[float], period: int = 14) -> float:
        """Calculate Average True Range for dynamic stops"""
        if len(prices) < period + 1:
            return prices[-1] * 0.01 if prices else 0
        
        # Simplified ATR using high-low (we only have close prices)
        highs = np.array(prices[-period:])
        lows = np.array(prices[-period-1:-1])
        
        tr = np.maximum(highs - lows, np.abs(np.diff(prices[-period-1:])))
        return np.mean(tr[-period:])
    
    def detect_regime(self) -> str:
        """Detect market regime for XRP"""
        if len(self.price_history) < 21:
            return "unknown"
        
        ema_fast = self.calculate_ema(self.price_history, self.config.ema_fast)
        ema_slow = self.calculate_ema(self.price_history, self.config.ema_slow)
        rsi = self.calculate_rsi(self.price_history, self.config.rsi_period)
        
        # Trend detection
        if ema_fast > ema_slow * 1.001:  # 0.1% buffer
            trend = "uptrend"
        elif ema_fast < ema_slow * 0.999:
            trend = "downtrend"
        else:
            trend = "ranging"
        
        # Volatility
        volatility = self.calculate_volatility()
        if volatility > 0.02:  # 2% volatility
            vol_regime = "high_volatility"
        elif volatility < 0.005:
            vol_regime = "low_volatility"
        else:
            vol_regime = "normal"
        
        return f"{trend}_{vol_regime}"
    
    def calculate_volatility(self, period: int = 20) -> float:
        """Calculate price volatility (standard deviation / mean)"""
        if len(self.price_history) < period:
            return 0
        
        recent_prices = self.price_history[-period:]
        returns = np.diff(recent_prices) / np.array(recent_prices[:-1])
        return np.std(returns)
    
    def generate_signal(self, current_price: float) -> Tuple[Signal, Dict]:
        """Generate trading signal for XRP COIN-M PERP"""
        
        # Check cooldown
        import time
        current_time = time.time()
        if current_time - self.last_signal_time < self.config.cooldown_minutes * 60:
            return Signal.HOLD, {'reason': 'cooldown'}
        
        # Circuit breaker
        if self.consecutive_losses >= 3:
            return Signal.HOLD, {'reason': 'circuit_breaker', 'losses': self.consecutive_losses}
        
        # Need enough price history
        if len(self.price_history) < 30:
            return Signal.HOLD, {'reason': f'insufficient_history ({len(self.price_history)}/30)'}
        
        # Calculate indicators
        ema_fast = self.calculate_ema(self.price_history, self.config.ema_fast)
        ema_slow = self.calculate_ema(self.price_history, self.config.ema_slow)
        rsi = self.calculate_rsi(self.price_history, self.config.rsi_period)
        atr = self.calculate_atr(self.price_history, 14)
        volatility = self.calculate_volatility(20)
        
        # Detect market regime
        regime = self.detect_regime()
        
        # Get support/resistance levels
        recent_lows = [min(self.price_history[max(0, i-5):i+1]) 
                      for i in range(len(self.price_history)-20, len(self.price_history))]
        recent_highs = [max(self.price_history[max(0, i-5):i+1]) 
                       for i in range(len(self.price_history)-20, len(self.price_history))]
        
        support = np.percentile(recent_lows, 20)  # 20th percentile
        resistance = np.percentile(recent_highs, 80)  # 80th percentile
        
        # Check breakout conditions
        breakout_up = current_price > resistance * (1 + self.config.breakout_threshold)
        breakout_down = current_price < support * (1 - self.config.breakout_threshold)
        
        # Volatility filter
        if volatility < self.config.volatility_threshold:
            return Signal.HOLD, {
                'reason': 'low_volatility',
                'volatility': f'{volatility:.4f}',
                'threshold': self.config.volatility_threshold
            }
        
        # Trend alignment
        trend_up = ema_fast > ema_slow
        trend_down = ema_fast < ema_slow
        
        signal_data = {
            'price': current_price,
            'ema_fast': ema_fast,
            'ema_slow': ema_slow,
            'rsi': rsi,
            'atr': atr,
            'volatility': volatility,
            'regime': regime,
            'support': support,
            'resistance': resistance,
            'breakout_up': breakout_up,
            'breakout_down': breakout_down
        }
        
        # Generate signals
        if breakout_up and trend_up and rsi < self.config.rsi_overbought:
            # Calculate position size based on risk
            stop_price = max(
                current_price * (1 - self.config.stop_loss_pct),
                support * 0.995
            )
            
            # COIN-M: Position size in XRP contracts
            risk_amount = 10.0  # 10 XRP risk per trade (paper)
            position_size = risk_amount / (current_price - stop_price) * current_price
            
            # Cap position size
            position_size = min(position_size, self.config.max_position_size)
            
            signal_data.update({
                'side': 'BUY',
                'entry': current_price,
                'stop': stop_price,
                'target': current_price + (current_price - stop_price) * self.config.take_profit_ratio,
                'size': position_size,
                'risk_xrp': risk_amount
            })
            
            self.last_signal_time = current_time
            return Signal.LONG, signal_data
            
        elif breakout_down and trend_down and rsi > self.config.rsi_oversold:
            # SHORT signal
            stop_price = min(
                current_price * (1 + self.config.stop_loss_pct),
                resistance * 1.005
            )
            
            risk_amount = 10.0
            position_size = risk_amount / (stop_price - current_price) * current_price
            position_size = min(position_size, self.config.max_position_size)
            
            signal_data.update({
                'side': 'SELL',
                'entry': current_price,
                'stop': stop_price,
                'target': current_price - (stop_price - current_price) * self.config.take_profit_ratio,
                'size': position_size,
                'risk_xrp': risk_amount
            })
            
            self.last_signal_time = current_time
            return Signal.SHORT, signal_data
        
        return Signal.HOLD, signal_data
    
    def record_trade(self, pnl: float):
        """Record trade result for circuit breaker"""
        if pnl < 0:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
    
    def reset_circuit_breaker(self):
        """Reset after review"""
        self.consecutive_losses = 0

# Example usage
if __name__ == '__main__':
    strategy = XRPStrategy()
    
    # Simulate price updates
    import random
    base_price = 2.50
    for i in range(50):
        price = base_price + random.gauss(0, 0.02)
        strategy.update(price, volume=1000)
    
    # Generate signal
    current_price = strategy.price_history[-1]
    signal, data = strategy.generate_signal(current_price)
    
    print(f"Signal: {signal.name}")
    print(f"Data: {data}")
