# Market Regime Detector
*2026-02-19 01:23* - Identify market conditions to adapt strategy behavior

## Purpose
Automatically detect whether markets are trending, ranging, or volatile. Use regime classification to adjust position sizes, stop distances, and signal thresholds dynamically.

## Code

```python
"""
Market Regime Detector
Identify trending, ranging, and volatile market conditions.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
from enum import Enum, auto
import statistics
from collections import deque

class MarketRegime(Enum):
    STRONG_UPTREND = auto()
    WEAK_UPTREND = auto()
    RANGING = auto()
    WEAK_DOWNTREND = auto()
    STRONG_DOWNTREND = auto()
    VOLATILE = auto()
    LOW_VOLATILITY = auto()

@dataclass
class RegimeConfig:
    """Strategy parameters tuned for specific regimes."""
    position_size_mult: float = 1.0
    stop_distance_mult: float = 1.0
    profit_target_mult: float = 1.0
    min_signal_strength: float = 0.0
    max_concurrent_positions: int = 5
    preferred_order_types: List[str] = None
    
    def __post_init__(self):
        if self.preferred_order_types is None:
            self.preferred_order_types = ['LIMIT']

class RegimeDetector:
    """
    Detect market regime from price and volume data.
    Uses ADX for trend strength + volatility measures.
    """
    
    def __init__(
        self,
        adx_period: int = 14,
        volatility_period: int = 20,
        trend_threshold: float = 25.0,
        strong_trend_threshold: float = 40.0,
        high_volatility_threshold: float = 2.0,
        low_volatility_threshold: float = 0.5,
        lookback: int = 100
    ):
        self.adx_period = adx_period
        self.volatility_period = volatility_period
        self.trend_threshold = trend_threshold
        self.strong_trend_threshold = strong_trend_threshold
        self.high_vol_threshold = high_volatility_threshold
        self.low_vol_threshold = low_volatility_threshold
        self.lookback = lookback
        
        # Price history
        self.highs: deque = deque(maxlen=lookback)
        self.lows: deque = deque(maxlen=lookback)
        self.closes: deque = deque(maxlen=lookback)
        self.volumes: deque = deque(maxlen=lookback)
    
    def update(self, high: float, low: float, close: float, volume: float = 0) -> MarketRegime:
        """Add new bar and return detected regime."""
        self.highs.append(high)
        self.lows.append(low)
        self.closes.append(close)
        self.volumes.append(volume)
        
        return self.detect()
    
    def detect(self) -> MarketRegime:
        """Analyze current data and return regime classification."""
        if len(self.closes) < self.adx_period + 10:
            return MarketRegime.RANGING  # Not enough data
        
        # Calculate indicators
        adx = self._calculate_adx()
        volatility = self._calculate_volatility()
        direction = self._calculate_direction()
        
        # Classify
        if volatility > self.high_vol_threshold:
            return MarketRegime.VOLATILE
        
        if volatility < self.low_vol_threshold:
            return MarketRegime.LOW_VOLATILITY
        
        if adx > self.strong_trend_threshold:
            if direction > 0:
                return MarketRegime.STRONG_UPTREND
            else:
                return MarketRegime.STRONG_DOWNTREND
        
        if adx > self.trend_threshold:
            if direction > 0:
                return MarketRegime.WEAK_UPTREND
            else:
                return MarketRegime.WEAK_DOWNTREND
        
        return MarketRegime.RANGING
    
    def _calculate_adx(self) -> float:
        """Calculate Average Directional Index (simplified)."""
        highs_list = list(self.highs)
        lows_list = list(self.lows)
        closes_list = list(self.closes)
        
        if len(highs_list) < self.adx_period + 1:
            return 0.0
        
        # Calculate +DM and -DM
        plus_dm = []
        minus_dm = []
        tr = []  # True range
        
        for i in range(1, len(highs_list)):
            high_diff = highs_list[i] - highs_list[i-1]
            low_diff = lows_list[i-1] - lows_list[i]
            
            plus_dm.append(max(high_diff, 0) if high_diff > low_diff else 0)
            minus_dm.append(max(low_diff, 0) if low_diff > high_diff else 0)
            
            # True range
            tr.append(max(
                highs_list[i] - lows_list[i],
                abs(highs_list[i] - closes_list[i-1]),
                abs(lows_list[i] - closes_list[i-1])
            ))
        
        # Smooth with EMA-like approach (Wilder's smoothing)
        period = self.adx_period
        atr = sum(tr[:period]) / period
        plus_di = sum(plus_dm[:period]) / period / atr * 100 if atr > 0 else 0
        minus_di = sum(minus_dm[:period]) / period / atr * 100 if atr > 0 else 0
        
        dx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100 if (plus_di + minus_di) > 0 else 0
        return dx  # Simplified ADX approximation
    
    def _calculate_volatility(self) -> float:
        """Calculate normalized volatility (ATR / price)."""
        if len(self.closes) < self.volatility_period:
            return 0.0
        
        closes_list = list(self.closes)
        highs_list = list(self.highs)
        lows_list = list(self.lows)
        
        # True ranges
        trs = []
        for i in range(1, len(closes_list)):
            trs.append(max(
                highs_list[i] - lows_list[i],
                abs(highs_list[i] - closes_list[i-1]),
                abs(lows_list[i] - closes_list[i-1])
            ))
        
        if len(trs) < self.volatility_period:
            return 0.0
        
        atr = statistics.mean(trs[-self.volatility_period:])
        current_price = closes_list[-1]
        
        return (atr / current_price) * 100 if current_price > 0 else 0
    
    def _calculate_direction(self) -> float:
        """Calculate directional bias (-1 to 1)."""
        if len(self.closes) < 20:
            return 0.0
        
        closes_list = list(self.closes)
        
        # Compare short EMA vs longer EMA
        short_ema = statistics.mean(closes_list[-10:])
        long_ema = statistics.mean(closes_list[-30:]) if len(closes_list) >= 30 else statistics.mean(closes_list)
        
        diff_pct = (short_ema - long_ema) / long_ema if long_ema > 0 else 0
        return max(-1, min(1, diff_pct * 10))  # Scale to -1, 1 range
    
    def get_config(self, regime: Optional[MarketRegime] = None) -> RegimeConfig:
        """Get strategy parameters optimized for current or specified regime."""
        r = regime or self.detect()
        
        configs = {
            MarketRegime.STRONG_UPTREND: RegimeConfig(
                position_size_mult=1.2,
                stop_distance_mult=1.5,
                profit_target_mult=2.0,
                min_signal_strength=0.6,
                preferred_order_types=['MARKET', 'LIMIT']
            ),
            MarketRegime.WEAK_UPTREND: RegimeConfig(
                position_size_mult=0.8,
                stop_distance_mult=1.0,
                profit_target_mult=1.5,
                min_signal_strength=0.7,
                preferred_order_types=['LIMIT']
            ),
            MarketRegime.RANGING: RegimeConfig(
                position_size_mult=0.6,
                stop_distance_mult=0.8,
                profit_target_mult=1.0,
                min_signal_strength=0.8,
                preferred_order_types=['LIMIT'],
                max_concurrent_positions=3
            ),
            MarketRegime.WEAK_DOWNTREND: RegimeConfig(
                position_size_mult=0.8,
                stop_distance_mult=1.0,
                profit_target_mult=1.5,
                min_signal_strength=0.7,
                preferred_order_types=['LIMIT']
            ),
            MarketRegime.STRONG_DOWNTREND: RegimeConfig(
                position_size_mult=1.2,
                stop_distance_mult=1.5,
                profit_target_mult=2.0,
                min_signal_strength=0.6,
                preferred_order_types=['MARKET', 'LIMIT']
            ),
            MarketRegime.VOLATILE: RegimeConfig(
                position_size_mult=0.5,
                stop_distance_mult=2.0,
                profit_target_mult=1.5,
                min_signal_strength=0.9,
                max_concurrent_positions=2,
                preferred_order_types=['LIMIT']
            ),
            MarketRegime.LOW_VOLATILITY: RegimeConfig(
                position_size_mult=1.0,
                stop_distance_mult=0.7,
                profit_target_mult=0.8,
                min_signal_strength=0.5,
                preferred_order_types=['LIMIT']
            ),
        }
        
        return configs.get(r, RegimeConfig())
    
    def should_trade(self, side: str, signal_strength: float = 0.5) -> Tuple[bool, str]:
        """Check if trading is advisable given current regime."""
        regime = self.detect()
        config = self.get_config(regime)
        
        if signal_strength < config.min_signal_strength:
            return False, f"Signal strength {signal_strength} below threshold {config.min_signal_strength}"
        
        # Regime-direction alignment
        if regime == MarketRegime.STRONG_UPTREND and side == "SELL":
            return False, "Counter-trend short in strong uptrend"
        
        if regime == MarketRegime.STRONG_DOWNTREND and side == "BUY":
            return False, "Counter-trend long in strong downtrend"
        
        if regime == MarketRegime.VOLATILE:
            return False, "High volatility - reduced position size recommended"
        
        return True, "OK"


# === USAGE EXAMPLES ===

def example_basic_detection():
    """Basic regime detection from price bars."""
    detector = RegimeDetector()
    
    # Simulate trending data
    price = 100.0
    for i in range(50):
        price += 0.5  # Uptrend
        detector.update(high=price+1, low=price-1, close=price)
    
    regime = detector.detect()
    print(f"Detected regime: {regime.name}")
    
    config = detector.get_config()
    print(f"Position size multiplier: {config.position_size_mult}")

def example_strategy_adaptation():
    """Adapt strategy parameters based on regime."""
    
    class AdaptiveStrategy:
        def __init__(self, base_position_size: float, base_stop_pct: float):
            self.detector = RegimeDetector()
            self.base_position_size = base_position_size
            self.base_stop_pct = base_stop_pct
        
        def on_bar(self, high, low, close, volume=0):
            self.detector.update(high, low, close, volume)
        
        def calculate_position(self, signal_side: str, signal_strength: float) -> Optional[dict]:
            # Check if we should trade
            should_trade, reason = self.detector.should_trade(signal_side, signal_strength)
            if not should_trade:
                print(f"Trade rejected: {reason}")
                return None
            
            # Get regime-specific config
            config = self.detector.get_config()
            
            # Adjust parameters
            position_size = self.base_position_size * config.position_size_mult
            stop_distance = self.base_stop_pct * config.stop_distance_mult
            profit_target = stop_distance * config.profit_target_mult
            
            return {
                'size': position_size,
                'stop_pct': stop_distance,
                'target_pct': profit_target,
                'order_types': config.preferred_order_types,
                'regime': self.detector.detect().name
            }
    
    # Usage
    strategy = AdaptiveStrategy(base_position_size=1.0, base_stop_pct=0.02)
    
    # Feed some data
    for i in range(30):
        strategy.on_bar(100+i, 99+i, 100+i, 1000)
    
    # Get position sizing
    result = strategy.calculate_position("BUY", signal_strength=0.7)
    if result:
        print(f"Position: {result}")

def example_multi_timeframe():
    """Check regime across multiple timeframes."""
    
    # Daily and hourly detectors
    daily = RegimeDetector(adx_period=14, lookback=100)
    hourly = RegimeDetector(adx_period=14, lookback=100)
    
    # Only trade when aligned
    def can_trade(daily_detector, hourly_detector, side):
        d_regime = daily_detector.detect()
        h_regime = hourly_detector.detect()
        
        # Avoid counter-trend on daily
        if d_regime == MarketRegime.STRONG_UPTREND and side == "SELL":
            return False
        if d_regime == MarketRegime.STRONG_DOWNTREND and side == "BUY":
            return False
        
        # Require hourly alignment or ranging
        if side == "BUY" and h_regime in (MarketRegime.WEAK_DOWNTREND, MarketRegime.STRONG_DOWNTREND):
            return False
        if side == "SELL" and h_regime in (MarketRegime.WEAK_UPTREND, MarketRegime.STRONG_UPTREND):
            return False
        
        return True


# === QUICK REFERENCE ===

"""
Regime-Based Adjustments:

STRONG_TREND:
- Increase position size (1.2x)
- Wider stops (1.5x) to avoid shakeouts
- Larger profit targets (2.0x)
- Can use market orders for entries

RANGING:
- Reduce position size (0.6x)
- Tighter stops (0.8x) - quick exits on failed breaks
- Smaller targets (1.0x) - take profits quickly
- Use limit orders only

VOLATILE:
- Drastically reduce size (0.5x)
- Wider stops (2.0x)
- Higher signal threshold (0.9)
- Limit concurrent positions

LOW_VOLATILITY:
- Normal size (1.0x)
- Tighter stops (0.7x)
- Smaller targets (0.8x)
- Lower signal threshold (0.5) - more trades

Integration Pattern:

regime_detector = RegimeDetector()

# In bar/price update handler
regime_detector.update(bar.high, bar.low, bar.close, bar.volume)

# Before generating signal
can_trade, reason = regime_detector.should_trade("BUY", signal_strength=0.75)
if not can_trade:
    return  # Skip this signal

# Adjust position sizing
config = regime_detector.get_config()
adjusted_size = base_size * config.position_size_mult
adjusted_stop = base_stop * config.stop_distance_mult
"""

if __name__ == "__main__":
    example_basic_detection()
    print()
    example_strategy_adaptation()
```
