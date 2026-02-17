"""
Kraken Trading Strategies
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate RSI from price list"""
    if len(prices) < period + 1:
        return 50.0
    
    deltas = np.diff(prices)
    gains = deltas[deltas > 0]
    losses = -deltas[deltas < 0]
    
    avg_gain = np.mean(gains) if len(gains) > 0 else 0
    avg_loss = np.mean(losses) if len(losses) > 0 else 0.001
    
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def calculate_ema(prices: List[float], period: int) -> float:
    """Calculate EMA"""
    if len(prices) < period:
        return prices[-1] if prices else 0
    
    multiplier = 2 / (period + 1)
    ema = np.mean(prices[:period])
    
    for price in prices[period:]:
        ema = (price - ema) * multiplier + ema
    
    return ema


def calculate_macd(prices: List[float]) -> Tuple[float, float, float]:
    """Calculate MACD (macd, signal, histogram)"""
    if len(prices) < 26:
        return 0, 0, 0
    
    ema12 = calculate_ema(prices, 12)
    ema26 = calculate_ema(prices, 26)
    macd = ema12 - ema26
    
    # Signal line (EMA9 of MACD) - simplified
    signal = macd * 0.9  # Approximation
    histogram = macd - signal
    
    return macd, signal, histogram


def calculate_bollinger(prices: List[float], period: int = 20, std_dev: int = 2) -> Tuple[float, float, float]:
    """Calculate Bollinger Bands (lower, middle, upper)"""
    if len(prices) < period:
        return prices[-1] * 0.95, prices[-1], prices[-1] * 1.05 if prices else (0, 0, 0)
    
    recent = prices[-period:]
    middle = np.mean(recent)
    std = np.std(recent)
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return lower, middle, upper


@dataclass
class Signal:
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    reason: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None


class GridStrategy:
    """Grid trading - multiple buy/sell levels"""
    
    def __init__(self, grid_levels: int = 10, grid_spacing_pct: float = 0.005,
                 order_size: float = 100.0, max_grids: int = 20):
        self.grid_levels = grid_levels
        self.grid_spacing = grid_spacing_pct
        self.order_size = order_size
        self.max_grids = max_grids
        self.grids = []
    
    def analyze(self, current_price: float, ohlc: List[List[float]] = None) -> Signal:
        """Generate grid placement signal"""
        if not self.grids:
            # Initial grid setup
            self.setup_grids(current_price)
            return Signal('hold', 0.5, 'Setting up initial grids')
        
        # Check if price moved significantly
        avg_grid = sum(self.grids) / len(self.grids) if self.grids else current_price
        deviation = abs(current_price - avg_grid) / avg_grid
        
        if deviation > 0.02:  # 2% deviation
            self.setup_grids(current_price)
            return Signal('hold', 0.6, f'Rebalanced grids (deviation: {deviation:.2%})')
        
        # Find nearest grid level
        nearest = min(self.grids, key=lambda x: abs(x - current_price))
        distance = abs(current_price - nearest) / current_price
        
        if distance < 0.001:  # Very close to grid
            if current_price < avg_grid:
                return Signal('buy', 0.7, f'Near buy grid @ {nearest:.2f}')
            else:
                return Signal('sell', 0.7, f'Near sell grid @ {nearest:.2f}')
        
        return Signal('hold', 0.3, 'Within grid range')
    
    def setup_grids(self, center_price: float):
        """Set up grid levels around center price"""
        self.grids = []
        for i in range(1, self.grid_levels + 1):
            # Buy grids below
            self.grids.append(center_price * (1 - self.grid_spacing * i))
            # Sell grids above
            self.grids.append(center_price * (1 + self.grid_spacing * i))
        logger.info(f"Set up {len(self.grids)} grid levels around {center_price:.2f}")


class MomentumStrategy:
    """Momentum strategy using RSI + MACD"""
    
    def __init__(self, rsi_period: int = 14, rsi_overbought: float = 70,
                 rsi_oversold: float = 30, volume_threshold: float = 1.5):
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.volume_threshold = volume_threshold
    
    def analyze(self, ohlc: List[List[float]], volumes: List[float] = None) -> Signal:
        """
        Analyze OHLC data for momentum signals
        OHLC format: [[time, open, high, low, close, vwap, volume, count], ...]
        """
        if len(ohlc) < 30:
            return Signal('hold', 0, 'Insufficient data')
        
        closes = [c[4] for c in ohlc]
        volumes = [c[6] for c in ohlc] if volumes is None else volumes
        
        # Calculate indicators
        rsi = calculate_rsi(closes, self.rsi_period)
        macd, signal, hist = calculate_macd(closes)
        lower, middle, upper = calculate_bollinger(closes)
        current_price = closes[-1]
        
        # Volume analysis
        avg_volume = np.mean(volumes[-10:])
        current_volume = volumes[-1]
        volume_spike = current_volume > avg_volume * self.volume_threshold
        
        # Generate signal
        reasons = []
        confidence = 0.5
        action = 'hold'
        
        # Buy conditions
        if rsi < self.rsi_oversold:
            reasons.append(f'RSI oversold ({rsi:.1f})')
            confidence += 0.2
            if macd > signal:
                reasons.append('MACD bullish crossover')
                confidence += 0.2
                action = 'buy'
        
        # Sell conditions
        elif rsi > self.rsi_overbought:
            reasons.append(f'RSI overbought ({rsi:.1f})')
            confidence += 0.2
            if macd < signal:
                reasons.append('MACD bearish crossover')
                confidence += 0.2
                action = 'sell'
        
        # Bollinger band breakout
        if current_price > upper and volume_spike:
            reasons.append('Upper Bollinger breakout + volume')
            confidence = min(confidence + 0.15, 0.95)
            if action == 'hold':
                action = 'buy'
        elif current_price < lower and volume_spike:
            reasons.append('Lower Bollinger breakdown + volume')
            confidence = min(confidence + 0.15, 0.95)
            if action == 'hold':
                action = 'sell'
        
        # Stop loss / take profit
        stop_loss = current_price * 0.98 if action == 'buy' else current_price * 1.02 if action == 'sell' else None
        take_profit = current_price * 1.04 if action == 'buy' else current_price * 0.96 if action == 'sell' else None
        
        return Signal(
            action=action,
            confidence=min(confidence, 1.0),
            reason=' | '.join(reasons) if reasons else 'No clear signal',
            stop_loss=stop_loss,
            take_profit=take_profit
        )


class ScalpingStrategy:
    """Quick scalp for 1-2% moves"""
    
    def __init__(self, profit_target: float = 0.015, stop_loss: float = 0.008,
                 min_volume_spike: float = 1.3):
        self.profit_target = profit_target  # 1.5%
        self.stop_loss = stop_loss  # 0.8%
        self.min_volume_spike = min_volume_spike
    
    def analyze(self, ohlc: List[List[float]], entry_price: Optional[float] = None) -> Signal:
        """Quick scalp signals"""
        if len(ohlc) < 10:
            return Signal('hold', 0, 'Insufficient data')
        
        closes = [c[4] for c in ohlc]
        volumes = [c[6] for c in ohlc]
        current = closes[-1]
        
        # Price action
        short_ma = np.mean(closes[-5:])
        long_ma = np.mean(closes[-10:])
        
        # Volume
        avg_vol = np.mean(volumes[-10:])
        vol_spike = volumes[-1] > avg_vol * self.min_volume_spike
        
        # If in position, check exit
        if entry_price:
            pnl_pct = (current - entry_price) / entry_price
            if pnl_pct >= self.profit_target:
                return Signal('sell', 0.9, f'Profit target reached ({pnl_pct:.2%})')
            if pnl_pct <= -self.stop_loss:
                return Signal('sell', 0.9, f'Stop loss hit ({pnl_pct:.2%})')
        
        # Entry signals
        if short_ma > long_ma * 1.002 and vol_spike:
            return Signal(
                'buy', 0.75,
                f'Momentum + volume spike',
                stop_loss=current * (1 - self.stop_loss),
                take_profit=current * (1 + self.profit_target)
            )
        
        if short_ma < long_ma * 0.998 and vol_spike:
            return Signal(
                'sell', 0.75,
                f'Breakdown + volume spike',
                stop_loss=current * (1 + self.stop_loss),
                take_profit=current * (1 - self.profit_target)
            )
        
        return Signal('hold', 0.3, 'No scalp opportunity')


class MeanReversionStrategy:
    """Bollinger Bands mean reversion"""
    
    def __init__(self, bb_period: int = 20, bb_std: int = 2, rsi_confirm: bool = True):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.rsi_confirm = rsi_confirm
    
    def analyze(self, ohlc: List[List[float]]) -> Signal:
        """Mean reversion signals"""
        if len(ohlc) < self.bb_period + 5:
            return Signal('hold', 0, 'Insufficient data')
        
        closes = [c[4] for c in ohlc]
        current = closes[-1]
        
        lower, middle, upper = calculate_bollinger(closes, self.bb_period, self.bb_std)
        rsi = calculate_rsi(closes, 14) if self.rsi_confirm else 50
        
        # Buy: Price below lower band + RSI oversold
        if current < lower and rsi < 40:
            return Signal(
                'buy', 0.8,
                f'Below Bollinger ({current < lower:.1%}) + RSI {rsi:.0f}',
                stop_loss=current * 0.97,
                take_profit=middle
            )
        
        # Sell: Price above upper band + RSI overbought
        if current > upper and rsi > 60:
            return Signal(
                'sell', 0.8,
                f'Above Bollinger ({current > upper:.1%}) + RSI {rsi:.0f}',
                stop_loss=current * 1.03,
                take_profit=middle
            )
        
        return Signal('hold', 0.4, f'Within bands (L:{lower:.0f} M:{middle:.0f} U:{upper:.0f})')
