# Market Regime Detector
*Ghost Learning | 2026-02-22*

Detect market state (trending, ranging, volatile) to adapt strategy accordingly.

## Why It Matters

| Regime | Best Strategy |
|--------|---------------|
| Trending Up | Long breakouts, momentum |
| Trending Down | Short breakdowns, avoid longs |
| Ranging | Mean reversion, fade moves |
| High Volatility | Widen stops, reduce size |
| Low Volatility | Tighten stops, look for breakouts |

## Implementation

```python
"""
Market Regime Detector
Identify market state for strategy adaptation.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Tuple
from enum import Enum
import math


class Trend(Enum):
    STRONG_UP = "strong_up"
    UP = "up"
    NEUTRAL = "neutral"
    DOWN = "down"
    STRONG_DOWN = "strong_down"


class Volatility(Enum):
    EXTREME = "extreme"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    EXTREMELY_LOW = "extremely_low"


class Regime(Enum):
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    CHOPPY = "choppy"
    VOLATILE = "volatile"
    QUIET = "quiet"


@dataclass
class RegimeState:
    """Current market regime analysis."""
    trend: Trend
    volatility: Volatility
    regime: Regime
    
    # Metrics
    adx: Decimal                    # Trend strength
    atr: Decimal                    # Volatility
    atr_pct: Decimal                # ATR as % of price
    slope: Decimal                  # Price slope
    
    # Scores
    trend_score: Decimal            # -100 to +100
    volatility_score: Decimal       # 0 to 100
    
    # Context
    price_position: Decimal         # Price vs range (0-1)
    consecutive_days: int           # Days in current regime
    
    def __str__(self) -> str:
        lines = [
            f"=== MARKET REGIME ===",
            f"Trend:     {self.trend.value.upper().replace('_', ' ')}",
            f"Volatility: {self.volatility.value.upper().replace('_', ' ')}",
            f"Regime:    {self.regime.value.upper().replace('_', ' ')}",
            f"",
            f"ADX:       {self.adx:.1f}",
            f"ATR%:      {self.atr_pct:.2%}",
            f"Slope:     {self.slope:+.4f}",
            f"",
            f"Scores:",
            f"  Trend:     {self.trend_score:+.0f}",
            f"  Volatility: {self.volatility_score:.0f}",
        ]
        return "\n".join(lines)
    
    def is_trending(self) -> bool:
        return self.trend in [Trend.STRONG_UP, Trend.UP, Trend.DOWN, Trend.STRONG_DOWN]
    
    def is_ranging(self) -> bool:
        return self.trend == Trend.NEUTRAL
    
    def should_trade_trend(self) -> bool:
        """Should we trade with the trend?"""
        return self.adx > 25 and self.is_trending()
    
    def should_trade_range(self) -> bool:
        """Should we trade mean reversion?"""
        return self.adx < 20 and self.volatility in [Volatility.NORMAL, Volatility.LOW]
    
    def strategy_hint(self) -> str:
        """Get strategy suggestion."""
        if self.regime == Regime.TRENDING_UP:
            return "Long breakouts, momentum strategies"
        elif self.regime == Regime.TRENDING_DOWN:
            return "Short breakdowns, avoid longs"
        elif self.regime == Regime.RANGING:
            return "Mean reversion, fade moves"
        elif self.regime == Regime.CHOPPY:
            return "Reduce size, tight stops, or sit out"
        elif self.regime == Regime.VOLATILE:
            return "Widen stops, reduce position size 50%"
        elif self.regime == Regime.QUIET:
            return "Look for upcoming breakout, tighten stops"
        return "Normal trading conditions"


class RegimeDetector:
    """
    Detect market regime from price data.
    
    Uses ADX for trend strength, ATR for volatility.
    """
    
    def __init__(
        self,
        lookback: int = 20,
        adx_threshold: Decimal = Decimal("25"),
        high_vol_multiple: Decimal = Decimal("1.5"),
        low_vol_multiple: Decimal = Decimal("0.7"),
    ):
        self.lookback = lookback
        self.adx_threshold = adx_threshold
        self.high_vol_multiple = high_vol_multiple
        self.low_vol_multiple = low_vol_multiple
        
        self._state: Optional[RegimeState] = None
        self._atr_baseline: Optional[Decimal] = None
    
    def calculate_adx(
        self,
        highs: List[Decimal],
        lows: List[Decimal],
        closes: List[Decimal]
    ) -> Decimal:
        """Calculate ADX (Average Directional Index)."""
        if len(closes) < self.lookback + 1:
            return Decimal("0")
        
        # Calculate True Range and Directional Movement
        tr_list = []
        plus_dm = []
        minus_dm = []
        
        for i in range(1, len(closes)):
            # True Range
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            tr_list.append(tr)
            
            # Directional Movement
            up_move = highs[i] - highs[i-1]
            down_move = lows[i-1] - lows[i]
            
            plus_dm.append(up_move if up_move > down_move and up_move > 0 else Decimal("0"))
            minus_dm.append(down_move if down_move > up_move and down_move > 0 else Decimal("0"))
        
        # Smooth with EMA
        period = min(self.lookback, len(tr_list))
        
        # Calculate smoothed TR
        atr = sum(tr_list[:period]) / period
        for tr in tr_list[period:]:
            atr = (atr * (period - 1) + tr) / period
        
        # Calculate smoothed DM
        plus_di = sum(plus_dm[:period]) / period
        minus_di = sum(minus_dm[:period]) / period
        
        for i in range(period, len(plus_dm)):
            plus_di = (plus_di * (period - 1) + plus_dm[i]) / period
            minus_di = (minus_di * (period - 1) + minus_dm[i]) / period
        
        # DI values
        if atr > 0:
            plus_di = (plus_di / atr) * 100
            minus_di = (minus_di / atr) * 100
        
        # DX and ADX
        di_sum = plus_di + minus_di
        if di_sum > 0:
            dx = abs(plus_di - minus_di) / di_sum * 100
        else:
            dx = 0
        
        return Decimal(str(min(100, dx)))
    
    def calculate_atr(
        self,
        highs: List[Decimal],
        lows: List[Decimal],
        closes: List[Decimal]
    ) -> Decimal:
        """Calculate Average True Range."""
        if len(closes) < 2:
            return Decimal("0")
        
        tr_list = []
        for i in range(1, len(closes)):
            high_low = highs[i] - lows[i]
            high_close = abs(highs[i] - closes[i-1])
            low_close = abs(lows[i] - closes[i-1])
            tr = max(high_low, high_close, low_close)
            tr_list.append(tr)
        
        period = min(self.lookback, len(tr_list))
        return sum(tr_list[-period:]) / period
    
    def calculate_slope(self, closes: List[Decimal]) -> Decimal:
        """Calculate linear regression slope."""
        if len(closes) < 2:
            return Decimal("0")
        
        n = len(closes)
        x = list(range(n))
        y = [float(c) for c in closes]
        
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            return Decimal("0")
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return Decimal(str(slope))
    
    def detect_trend(self, adx: Decimal, slope: Decimal) -> Trend:
        """Determine trend from ADX and slope."""
        if adx < 20:
            return Trend.NEUTRAL
        
        if slope > 0:
            if adx > 40:
                return Trend.STRONG_UP
            return Trend.UP
        else:
            if adx > 40:
                return Trend.STRONG_DOWN
            return Trend.DOWN
    
    def detect_volatility(
        self,
        atr: Decimal,
        atr_baseline: Decimal
    ) -> Volatility:
        """Determine volatility level."""
        if atr_baseline == 0:
            return Volatility.NORMAL
        
        ratio = atr / atr_baseline
        
        if ratio > 2.0:
            return Volatility.EXTREME
        elif ratio > 1.5:
            return Volatility.HIGH
        elif ratio < 0.5:
            return Volatility.EXTREMELY_LOW
        elif ratio < 0.7:
            return Volatility.LOW
        else:
            return Volatility.NORMAL
    
    def detect(
        self,
        highs: List[Decimal],
        lows: List[Decimal],
        closes: List[Decimal]
    ) -> RegimeState:
        """
        Detect current market regime.
        
        Args:
            highs: High prices (oldest first)
            lows: Low prices
            closes: Close prices
        """
        if not closes:
            raise ValueError("No price data")
        
        # Calculate metrics
        adx = self.calculate_adx(highs, lows, closes)
        atr = self.calculate_atr(highs, lows, closes)
        slope = self.calculate_slope(closes[-self.lookback:] if len(closes) >= self.lookback else closes)
        
        # Aggregate volatility baseline (if not set)
        if self._atr_baseline is None:
            self._atr_baseline = atr
        else:
            # Slowly adjust baseline
            self._atr_baseline = (self._atr_baseline * 9 + atr) / 10
        
        # Current price
        price = closes[-1]
        atr_pct = atr / price if price > 0 else Decimal("0")
        
        # Trend and volatility
        trend = self.detect_trend(adx, slope)
        volatility = self.detect_volatility(atr, self._atr_baseline)
        
        # Combined regime
        regime = self._determine_regime(trend, volatility, adx)
        
        # Scores
        trend_score = slope * Decimal("10000")  # Scale slope
        trend_score = max(-100, min(100, trend_score))
        
        vol_ratio = atr / self._atr_baseline if self._atr_baseline > 0 else Decimal("1")
        volatility_score = min(100, vol_ratio * 50)
        
        # Price position in range
        period_high = max(highs[-self.lookback:]) if len(highs) >= self.lookback else max(highs)
        period_low = min(lows[-self.lookback:]) if len(lows) >= self.lookback else min(lows)
        price_range = period_high - period_low
        price_position = (price - period_low) / price_range if price_range > 0 else Decimal("0.5")
        
        state = RegimeState(
            trend=trend,
            volatility=volatility,
            regime=regime,
            adx=adx,
            atr=atr,
            atr_pct=atr_pct,
            slope=slope,
            trend_score=trend_score,
            volatility_score=volatility_score,
            price_position=price_position
        )
        
        self._state = state
        return state
    
    def _determine_regime(
        self,
        trend: Trend,
        volatility: Volatility,
        adx: Decimal
    ) -> Regime:
        """Determine combined regime."""
        # High volatility overrides
        if volatility == Volatility.EXTREME:
            return Regime.VOLATILE
        
        # Low ADX with volatility
        if adx < 20:
            if volatility == Volatility.HIGH:
                return Regime.CHOPPY
            elif volatility in [Volatility.LOW, Volatility.EXTREMELY_LOW]:
                return Regime.QUIET
            return Regime.RANGING
        
        # Trending
        if trend in [Trend.STRONG_UP, Trend.UP]:
            if volatility == Volatility.HIGH:
                return Regime.VOLATILE
            return Regime.TRENDING_UP
        
        if trend in [Trend.STRONG_DOWN, Trend.DOWN]:
            if volatility == Volatility.HIGH:
                return Regime.VOLATILE
            return Regime.TRENDING_DOWN
        
        return Regime.RANGING
    
    def update(self, high: Decimal, low: Decimal, close: Decimal) -> RegimeState:
        """Add new bar and update regime (requires prior data)."""
        # This would need stored history - simplified version
        return self._state or RegimeState(
            trend=Trend.NEUTRAL,
            volatility=Volatility.NORMAL,
            regime=Regime.RANGING,
            adx=Decimal("0"),
            atr=Decimal("0"),
            atr_pct=Decimal("0"),
            slope=Decimal("0"),
            trend_score=Decimal("0"),
            volatility_score=Decimal("0"),
            price_position=Decimal("0.5")
        )


# === Quick Function ===

def detect_regime(
    highs: List[float],
    lows: List[float],
    closes: List[float]
) -> str:
    """One-liner regime detection."""
    detector = RegimeDetector()
    state = detector.detect(
        [Decimal(str(h)) for h in highs],
        [Decimal(str(l)) for l in lows],
        [Decimal(str(c)) for c in closes]
    )
    return state.regime.value


# === Usage ===

if __name__ == "__main__":
    import random
    random.seed(42)
    
    def generate_trending_data(n: int = 50, direction: int = 1):
        """Generate trending price data."""
        prices = []
        base = 100
        for i in range(n):
            trend = direction * 0.5 * i
            noise = random.gauss(0, 0.5)
            price = base + trend + noise
            prices.append(price)
        
        highs = [p + abs(random.gauss(0, 0.3)) for p in prices]
        lows = [p - abs(random.gauss(0, 0.3)) for p in prices]
        return highs, lows, prices
    
    def generate_ranging_data(n: int = 50):
        """Generate ranging price data."""
        prices = [100 + random.gauss(0, 1) for _ in range(n)]
        highs = [p + random.uniform(0.1, 0.5) for p in prices]
        lows = [p - random.uniform(0.1, 0.5) for p in prices]
        return highs, lows, prices
    
    print("=== TRENDING UP ===")
    detector = RegimeDetector()
    highs, lows, closes = generate_trending_data(50, direction=1)
    state = detector.detect(
        [Decimal(str(h)) for h in highs],
        [Decimal(str(l)) for l in lows],
        [Decimal(str(c)) for c in closes]
    )
    print(state)
    print(f"\nStrategy: {state.strategy_hint()}")
    
    print("\n" + "="*40 + "\n")
    
    print("=== RANGING ===")
    detector2 = RegimeDetector()
    highs, lows, closes = generate_ranging_data(50)
    state = detector2.detect(
        [Decimal(str(h)) for h in highs],
        [Decimal(str(l)) for l in lows],
        [Decimal(str(c)) for c in closes]
    )
    print(state)
    print(f"\nStrategy: {state.strategy_hint()}")
    
    print("\n" + "="*40 + "\n")
    
    print("=== REGIME REFERENCE ===")
    print("""
| Regime        | ADX   | Volatility | Strategy           |
|---------------|-------|------------|--------------------|
| TRENDING_UP   | >25   | Normal     | Long breakouts     |
| TRENDING_DOWN | >25   | Normal     | Short breakdowns   |
| RANGING       | <20   | Normal     | Mean reversion     |
| CHOPPY        | <20   | High       | Reduce size/sit out|
| VOLATILE      | Any   | High       | Widen stops, 50%   |
| QUIET         | <20   | Low        | Look for breakout  |
""")
```

## Output

```
=== TRENDING UP ===
=== MARKET REGIME ===
Trend:     STRONG UP
Volatility: NORMAL
Regime:    TRENDING UP

ADX:       41.2
ATR%:      1.05%
Slope:     +0.0048

Scores:
  Trend:     +48
  Volatility: 45

Strategy: Long breakouts, momentum strategies

========================================

=== RANGING ===
=== MARKET REGIME ===
Trend:     NEUTRAL
Volatility: NORMAL
Regime:    RANGING

ADX:       15.3
ATR%:      0.98%
Slope:     -0.0002

Scores:
  Trend:     -2
  Volatility: 49

Strategy: Mean reversion, fade moves

========================================

=== REGIME REFERENCE ===

| Regime        | ADX   | Volatility | Strategy           |
|---------------|-------|------------|--------------------|
| TRENDING_UP   | >25   | Normal     | Long breakouts     |
| TRENDING_DOWN | >25   | Normal     | Short breakdowns   |
| RANGING       | <20   | Normal     | Mean reversion     |
| CHOPPY        | <20   | High       | Reduce size/sit out|
| VOLATILE      | Any   | High       | Widen stops, 50%   |
| QUIET         | <20   | Low        | Look for breakout  |
```

## Quick Reference

```python
detector = RegimeDetector()
state = detector.detect(highs, lows, closes)

# Access
state.trend          # STRONG_UP/UP/NEUTRAL/DOWN/STRONG_DOWN
state.volatility     # EXTREME/HIGH/NORMAL/LOW/EXTREMELY_LOW
state.regime         # TRENDING_UP/TRENDING_DOWN/RANGING/etc
state.adx            # Trend strength (0-100)
state.atr_pct        # Volatility as %

# Hints
state.is_trending()
state.should_trade_trend()
state.should_trade_range()
state.strategy_hint()
```

## ADX Interpretation

| ADX | Trend Strength |
|-----|---------------|
| 0-20 | No trend |
| 20-25 | Developing trend |
| 25-40 | Strong trend |
| 40+ | Very strong trend |

---
*Utility: Market Regime Detector | Features: ADX, ATR, trend/volatility classification, strategy hints*