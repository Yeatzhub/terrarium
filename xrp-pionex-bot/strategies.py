"""
XRP Trading Strategies
Multiple strategies for backtesting and paper trading.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from decimal import Decimal

@dataclass
class Signal:
    """Trading signal"""
    action: str  # 'buy', 'sell', 'hold'
    price: float
    confidence: float  # 0-1
    reason: str

class TechnicalIndicators:
    """Technical indicator calculations"""
    
    @staticmethod
    def sma(prices: List[float], period: int) -> List[float]:
        """Simple Moving Average"""
        if len(prices) < period:
            return []
        return [sum(prices[i:i+period]) / period for i in range(len(prices) - period + 1)]
    
    @staticmethod
    def ema(prices: List[float], period: int) -> List[float]:
        """Exponential Moving Average"""
        if len(prices) < period:
            return []
        multiplier = 2 / (period + 1)
        ema_values = [sum(prices[:period]) / period]
        for price in prices[period:]:
            ema_values.append((price - ema_values[-1]) * multiplier + ema_values[-1])
        return ema_values
    
    @staticmethod
    def rsi(prices: List[float], period: int = 14) -> List[float]:
        """Relative Strength Index"""
        if len(prices) < period + 1:
            return []
        
        deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]
        
        rsi_values = []
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        for i in range(period, len(gains)):
            if avg_loss == 0:
                rsi_values.append(100)
            else:
                rs = avg_gain / avg_loss
                rsi_values.append(100 - (100 / (1 + rs)))
            
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        return rsi_values
    
    @staticmethod
    def bollinger_bands(prices: List[float], period: int = 20, 
                        std_dev: float = 2.0) -> Tuple[List[float], List[float], List[float]]:
        """Bollinger Bands (upper, middle, lower)"""
        if len(prices) < period:
            return [], [], []
        
        sma = TechnicalIndicators.sma(prices, period)
        upper = []
        lower = []
        
        for i, avg in enumerate(sma):
            window = prices[i:i+period]
            std = np.std(window)
            upper.append(avg + std * std_dev)
            lower.append(avg - std_dev * std_dev)
        
        return upper, sma, lower
    
    @staticmethod
    def macd(prices: List[float], fast: int = 12, slow: int = 26, 
             signal: int = 9) -> Tuple[List[float], List[float], List[float]]:
        """MACD (macd line, signal line, histogram)"""
        ema_fast = TechnicalIndicators.ema(prices, fast)
        ema_slow = TechnicalIndicators.ema(prices, slow)
        
        # Align lengths
        min_len = min(len(ema_fast), len(ema_slow))
        ema_fast = ema_fast[-min_len:]
        ema_slow = ema_slow[-min_len:]
        
        macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
        signal_line = TechnicalIndicators.ema(macd_line, signal)
        
        # Align histogram
        min_len = min(len(macd_line), len(signal_line))
        histogram = [macd_line[-(min_len-i)] - signal_line[i] for i in range(min_len)]
        
        return macd_line[-min_len:], signal_line, histogram
    
    @staticmethod
    def atr(highs: List[float], lows: List[float], closes: List[float], 
            period: int = 14) -> List[float]:
        """Average True Range"""
        if len(closes) < period + 1:
            return []
        
        tr_values = []
        for i in range(1, len(closes)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            tr_values.append(max(tr1, tr2, tr3))
        
        atr_values = [sum(tr_values[:period]) / period]
        for tr in tr_values[period:]:
            atr_values.append((atr_values[-1] * (period - 1) + tr) / period)
        
        return atr_values

class MomentumStrategy:
    """
    Momentum Strategy using RSI and MACD
    Buy when RSI < 30 (oversold) and MACD crosses up
    Sell when RSI > 70 (overbought) and MACD crosses down
    """
    
    def __init__(self, rsi_period: int = 14, rsi_oversold: float = 30, 
                 rsi_overbought: float = 70):
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.name = "RSI-MACD Momentum"
        
    def generate_signal(self, candles: List[Dict], has_position: bool = False) -> Signal:
        """Generate trading signal"""
        closes = [c['close'] for c in candles]
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        
        if len(closes) < self.rsi_period + 5:
            return Signal('hold', closes[-1] if closes else 0, 0, "Insufficient data")
        
        # Calculate indicators
        rsi_values = TechnicalIndicators.rsi(closes, self.rsi_period)
        macd_line, signal_line, histogram = TechnicalIndicators.macd(closes)
        
        current_price = closes[-1]
        current_rsi = rsi_values[-1] if rsi_values else 50
        current_macd = macd_line[-1] if macd_line else 0
        current_signal = signal_line[-1] if signal_line else 0
        
        # Check for MACD crossover (need at least 2 elements in both arrays)
        if len(macd_line) >= 2 and len(signal_line) >= 2:
            prev_macd = macd_line[-2]
            prev_signal = signal_line[-2]
            macd_crossing_up = prev_macd < prev_signal and current_macd > current_signal
            macd_crossing_down = prev_macd > prev_signal and current_macd < current_signal
        else:
            macd_crossing_up = False
            macd_crossing_down = False
        
        # Generate signals
        if not has_position:
            if current_rsi < self.rsi_oversold and macd_crossing_up:
                confidence = min(1.0, (self.rsi_oversold - current_rsi) / 20 + 0.5)
                return Signal('buy', current_price, confidence, 
                            f"RSI oversold ({current_rsi:.1f}) + MACD cross up")
        else:
            if current_rsi > self.rsi_overbought and macd_crossing_down:
                confidence = min(1.0, (current_rsi - self.rsi_overbought) / 20 + 0.5)
                return Signal('sell', current_price, confidence,
                            f"RSI overbought ({current_rsi:.1f}) + MACD cross down")
        
        return Signal('hold', current_price, 0, f"RSI: {current_rsi:.1f}, MACD: {current_macd:.4f}")

class BollingerSqueezeStrategy:
    """
    Bollinger Band Squeeze Strategy
    Enter when price breaks out of squeeze, exit at opposite band
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0, 
                 squeeze_threshold: float = 0.02):
        self.period = period
        self.std_dev = std_dev
        self.squeeze_threshold = squeeze_threshold
        self.name = "Bollinger Squeeze"
        
    def generate_signal(self, candles: List[Dict], has_position: bool = False) -> Signal:
        """Generate trading signal"""
        closes = [c['close'] for c in candles]
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        
        if len(closes) < self.period + 5:
            return Signal('hold', closes[-1] if closes else 0, 0, "Insufficient data")
        
        # Calculate Bollinger Bands
        upper, middle, lower = TechnicalIndicators.bollinger_bands(
            closes, self.period, self.std_dev
        )
        
        current_price = closes[-1]
        current_upper = upper[-1]
        current_lower = lower[-1]
        current_middle = middle[-1]
        
        # Calculate bandwidth (squeeze indicator)
        bandwidth = (current_upper - current_lower) / current_middle
        
        # Check if price broke above/below bands
        prev_price = closes[-2]
        
        if not has_position:
            # Look for breakout from squeeze
            if bandwidth < self.squeeze_threshold:
                # In squeeze, wait for breakout
                if current_price > current_upper and prev_price <= upper[-2]:
                    return Signal('buy', current_price, 0.7, 
                                f"BB squeeze breakout up (bw: {bandwidth:.4f})")
                elif current_price < current_lower and prev_price >= lower[-2]:
                    return Signal('sell', current_price, 0.7,
                                f"BB squeeze breakout down (bw: {bandwidth:.4f})")
        else:
            # Exit when price hits opposite band or middle
            position = self._get_position_context()
            if position == 'long' and current_price <= current_middle:
                return Signal('sell', current_price, 0.8, "Price returned to middle band")
            elif position == 'short' and current_price >= current_middle:
                return Signal('buy', current_price, 0.8, "Price returned to middle band")
        
        return Signal('hold', current_price, 0, 
                     f"Bands: {current_lower:.2f} - {current_upper:.2f}, BW: {bandwidth:.4f}")
    
    def _get_position_context(self) -> str:
        """Return position context - override in backtester"""
        return 'long'

class MeanReversionStrategy:
    """
    Mean Reversion Strategy
    Buy when price is significantly below mean, sell when above
    """
    
    def __init__(self, lookback: int = 20, entry_z: float = 2.0, 
                 exit_z: float = 0.5):
        self.lookback = lookback
        self.entry_z = entry_z  # Z-score threshold for entry
        self.exit_z = exit_z    # Z-score threshold for exit
        self.name = "Mean Reversion"
        
    def generate_signal(self, candles: List[Dict], has_position: bool = False) -> Signal:
        """Generate trading signal"""
        closes = [c['close'] for c in candles]
        
        if len(closes) < self.lookback:
            return Signal('hold', closes[-1] if closes else 0, 0, "Insufficient data")
        
        # Calculate mean and standard deviation
        recent = closes[-self.lookback:]
        mean = np.mean(recent)
        std = np.std(recent)
        current_price = closes[-1]
        
        if std == 0:
            z_score = 0
        else:
            z_score = (current_price - mean) / std
        
        if not has_position:
            if z_score < -self.entry_z:
                confidence = min(1.0, abs(z_score) / 3)
                return Signal('buy', current_price, confidence,
                            f"Mean reversion buy (z: {z_score:.2f})")
            elif z_score > self.entry_z:
                confidence = min(1.0, z_score / 3)
                return Signal('sell', current_price, confidence,
                            f"Mean reversion sell (z: {z_score:.2f})")
        else:
            if abs(z_score) < self.exit_z:
                return Signal('sell', current_price, 0.9,
                            f"Mean reversion exit (z: {z_score:.2f})")
        
        return Signal('hold', current_price, 0, 
                     f"Mean: {mean:.2f}, Z: {z_score:.2f}")

class TrendFollowingStrategy:
    """
    Trend Following with EMA crossover
    Buy on golden cross (EMA9 > EMA21)
    Sell on death cross (EMA9 < EMA21)
    """
    
    def __init__(self, fast_ema: int = 9, slow_ema: int = 21):
        self.fast_ema = fast_ema
        self.slow_ema = slow_ema
        self.name = f"EMA{fast_ema}-{slow_ema} Trend"
        
    def generate_signal(self, candles: List[Dict], has_position: bool = False) -> Signal:
        """Generate trading signal"""
        closes = [c['close'] for c in candles]
        
        if len(closes) < self.slow_ema + 1:
            return Signal('hold', closes[-1] if closes else 0, 0, "Insufficient data")
        
        # Calculate EMAs
        ema_fast = TechnicalIndicators.ema(closes, self.fast_ema)
        ema_slow = TechnicalIndicators.ema(closes, self.slow_ema)
        
        # Align arrays
        min_len = min(len(ema_fast), len(ema_slow))
        ema_fast = ema_fast[-min_len:]
        ema_slow = ema_slow[-min_len:]
        
        current_price = closes[-1]
        current_fast = ema_fast[-1]
        current_slow = ema_slow[-1]
        
        if len(ema_fast) >= 2:
            prev_fast = ema_fast[-2]
            prev_slow = ema_slow[-2]
            golden_cross = prev_fast < prev_slow and current_fast > current_slow
            death_cross = prev_fast > prev_slow and current_fast < current_slow
        else:
            golden_cross = False
            death_cross = False
        
        if not has_position and golden_cross:
            return Signal('buy', current_price, 0.8, "Golden cross")
        elif has_position and death_cross:
            return Signal('sell', current_price, 0.8, "Death cross")
        
        trend = "Up" if current_fast > current_slow else "Down"
        return Signal('hold', current_price, 0, 
                     f"EMA{self.fast_ema}: {current_fast:.2f}, EMA{self.slow_ema}: {current_slow:.2f} ({trend})")

# Strategy registry
STRATEGIES = {
    'momentum': MomentumStrategy,
    'bollinger': BollingerSqueezeStrategy,
    'mean_reversion': MeanReversionStrategy,
    'trend_following': TrendFollowingStrategy
}

def get_strategy(name: str, **kwargs) -> object:
    """Get strategy by name"""
    if name in STRATEGIES:
        return STRATEGIES[name](**kwargs)
    raise ValueError(f"Unknown strategy: {name}. Available: {list(STRATEGIES.keys())}")

# Example usage
if __name__ == "__main__":
    # Create sample candles
    candles = [
        {'open': 2.0, 'high': 2.1, 'low': 1.9, 'close': 2.0, 'volume': 1000},
        {'open': 2.0, 'high': 2.2, 'low': 1.95, 'close': 2.15, 'volume': 1200},
        {'open': 2.15, 'high': 2.3, 'low': 2.1, 'close': 2.25, 'volume': 1500},
    ] * 10  # Repeat for RSI calculation
    
    momentum = MomentumStrategy()
    signal = momentum.generate_signal(candles)
    print(f"Momentum Signal: {signal.action} @ ${signal.price:.4f} ({signal.reason})")