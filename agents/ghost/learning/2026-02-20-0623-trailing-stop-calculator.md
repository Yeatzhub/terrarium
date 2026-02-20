# Trailing Stop Calculator — Multi-Method

**Purpose:** Calculate and manage trailing stops using different methodologies  
**Use Case:** Protect profits, limit losses, remove emotion from exits

## The Code

```python
"""
Trailing Stop Calculator
Multiple methods: ATR-based, percent, chandelier, parabolic SAR.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict
from enum import Enum, auto
from collections import deque
import math


class StopMethod(Enum):
    PERCENT = auto()       # Simple percentage from peak
    ATR = auto()           # ATR-based volatility stop
    CHANDELIER = auto()    # Highest high - multiplier * ATR
    PARABOLIC = auto()     # Parabolic SAR style acceleration
    VOLATILITY = auto()    # Std dev based


@dataclass
class PricePoint:
    timestamp: float
    price: float
    high: float
    low: float
    close: float


@dataclass
class TrailingStop:
    current_stop: float
    method: StopMethod
    triggered: bool
    distance_pct: float      # How far is price from stop
    risk_reward: float       # Current R-multiple if entry provided
    max_profit_pct: float    # Max run-up since entry
    drawdown_from_peak_pct: float


@dataclass
class StopResult:
    symbol: str
    position: str            # "long" or "short"
    entry_price: float
    current_price: float
    highest_price: float
    lowest_price: float
    trailing_stop: TrailingStop
    recommendation: str


class TrailingStopCalculator:
    """
    Calculate trailing stops using multiple methods.
    
    Usage:
        calc = TrailingStopCalculator(method=StopMethod.ATR, atr_period=14)
        stop = calc.update(symbol="AAPL", price=175, high=176, low=174, close=175)
    """
    
    def __init__(
        self,
        method: StopMethod = StopMethod.ATR,
        atr_period: int = 14,
        atr_multiplier: float = 3.0,
        percent_distance: float = 10.0,
        chandelier_multiplier: float = 3.0,
        parabolic_af: float = 0.02,      # Acceleration factor
        parabolic_max_af: float = 0.20,
        volatility_period: int = 20,
        volatility_multiplier: float = 2.0
    ):
        self.method = method
        self.config = {
            "atr_period": atr_period,
            "atr_multiplier": atr_multiplier,
            "percent_distance": percent_distance,
            "chandelier_multiplier": chandelier_multiplier,
            "parabolic_af": parabolic_af,
            "parabolic_max_af": parabolic_max_af,
            "volatility_period": volatility_period,
            "volatility_multiplier": volatility_multiplier
        }
        
        # State per symbol
        self._history: Dict[str, deque] = {}
        self._peak_prices: Dict[str, float] = {}
        self._trough_prices: Dict[str, float] = {}
        self._entry_prices: Dict[str, float] = {}
        self._positions: Dict[str, str] = {}
        self._parabolic_state: Dict[str, dict] = {}
    
    def initialize_position(
        self,
        symbol: str,
        position: str,           # "long" or "short"
        entry_price: float,
        initial_stop: Optional[float] = None
    ):
        """Set up tracking for a new position."""
        self._positions[symbol] = position
        self._entry_prices[symbol] = entry_price
        self._history[symbol] = deque(maxlen=100)
        
        if position == "long":
            self._peak_prices[symbol] = entry_price
            self._trough_prices[symbol] = entry_price
            if initial_stop:
                self._parabolic_state[symbol] = {
                    "sar": initial_stop,
                    "ep": entry_price,
                    "af": self.config["parabolic_af"],
                    "trend": "up"
                }
        else:  # short
            self._trough_prices[symbol] = entry_price
            self._peak_prices[symbol] = entry_price
            if initial_stop:
                self._parabolic_state[symbol] = {
                    "sar": initial_stop,
                    "ep": entry_price,
                    "af": self.config["parabolic_af"],
                    "trend": "down"
                }
    
    def update(
        self,
        symbol: str,
        price: float,
        high: float,
        low: float,
        close: float,
        timestamp: Optional[float] = None
    ) -> Optional[StopResult]:
        """Update price data and calculate current trailing stop."""
        if symbol not in self._positions:
            return None
        
        position = self._positions[symbol]
        entry = self._entry_prices[symbol]
        
        # Store price history
        point = PricePoint(timestamp or 0, price, high, low, close)
        self._history[symbol].append(point)
        
        # Update peaks/troughs
        if position == "long":
            if high > self._peak_prices[symbol]:
                self._peak_prices[symbol] = high
        else:  # short
            if low < self._trough_prices[symbol]:
                self._trough_prices[symbol] = low
        
        # Calculate stop based on method
        if self.method == StopMethod.PERCENT:
            stop = self._calc_percent_stop(symbol, price)
        elif self.method == StopMethod.ATR:
            stop = self._calc_atr_stop(symbol, high, low, close)
        elif self.method == StopMethod.CHANDELIER:
            stop = self._calc_chandelier_stop(symbol, high, low, close)
        elif self.method == StopMethod.PARABOLIC:
            stop = self._calc_parabolic_stop(symbol, high, low)
        elif self.method == StopMethod.VOLATILITY:
            stop = self._calc_volatility_stop(symbol, close)
        else:
            stop = self._calc_percent_stop(symbol, price)
        
        # Calculate metrics
        peak = self._peak_prices[symbol] if position == "long" else self._trough_prices[symbol]
        max_profit_pct = ((peak - entry) / entry * 100) if position == "long" else ((entry - peak) / entry * 100)
        drawdown = ((peak - price) / peak * 100) if position == "long" else ((price - peak) / peak * 100)
        
        if position == "long":
            distance_pct = ((price - stop) / price * 100) if price > 0 else 0
            triggered = price <= stop
        else:
            distance_pct = ((stop - price) / price * 100) if price > 0 else 0
            triggered = price >= stop
        
        # Risk reward (R-multiples)
        initial_risk = abs(entry - stop) if stop else entry * 0.02
        current_pnl = abs(price - entry)
        risk_reward = current_pnl / initial_risk if initial_risk > 0 else 0
        
        trailing = TrailingStop(
            current_stop=stop,
            method=self.method,
            triggered=triggered,
            distance_pct=distance_pct,
            risk_reward=risk_reward,
            max_profit_pct=max(max_profit_pct, 0),
            drawdown_from_peak_pct=drawdown
        )
        
        # Recommendation
        rec = self._generate_recommendation(trailing, position, max_profit_pct)
        
        return StopResult(
            symbol=symbol,
            position=position,
            entry_price=entry,
            current_price=price,
            highest_price=self._peak_prices[symbol],
            lowest_price=self._trough_prices[symbol],
            trailing_stop=trailing,
            recommendation=rec
        )
    
    def _calc_percent_stop(self, symbol: str, price: float) -> float:
        """Simple percentage trailing stop."""
        pct = self.config["percent_distance"] / 100
        position = self._positions[symbol]
        
        if position == "long":
            peak = self._peak_prices[symbol]
            return peak * (1 - pct)
        else:
            trough = self._trough_prices[symbol]
            return trough * (1 + pct)
    
    def _calc_atr_stop(self, symbol: str, high: float, low: float, close: float) -> float:
        """ATR-based volatility stop."""
        atr = self._calculate_atr(symbol, self.config["atr_period"])
        multiplier = self.config["atr_multiplier"]
        position = self._positions[symbol]
        
        if position == "long":
            peak = self._peak_prices[symbol]
            return peak - (atr * multiplier)
        else:
            trough = self._trough_prices[symbol]
            return trough + (atr * multiplier)
    
    def _calc_chandelier_stop(self, symbol: str, high: float, low: float, close: float) -> float:
        """Chandelier exit: Highest high - ATR * multiplier."""
        history = list(self._history[symbol])
        if len(history) < self.config["atr_period"]:
            return self._calc_percent_stop(symbol, close)
        
        atr = self._calculate_atr(symbol, self.config["atr_period"])
        multiplier = self.config["chandelier_multiplier"]
        position = self._positions[symbol]
        
        if position == "long":
            highest_high = max(p.high for p in history[-self.config["atr_period"]:])
            return highest_high - (atr * multiplier)
        else:
            lowest_low = min(p.low for p in history[-self.config["atr_period"]:])
            return lowest_low + (atr * multiplier)
    
    def _calc_parabolic_stop(self, symbol: str, high: float, low: float) -> float:
        """Parabolic SAR style stop."""
        if symbol not in self._parabolic_state:
            return self._calc_percent_stop(symbol, (high + low) / 2)
        
        state = self._parabolic_state[symbol]
        position = self._positions[symbol]
        af = state["af"]
        sar = state["sar"]
        ep = state["ep"]
        
        if position == "long":
            # Update extreme point if new high
            if high > ep:
                ep = high
                af = min(af + self.config["parabolic_af"], self.config["parabolic_max_af"])
            
            # New SAR
            new_sar = sar + af * (ep - sar)
            # Ensure SAR doesn't penetrate previous lows
            new_sar = min(new_sar, low)
            
            state["sar"] = new_sar
            state["ep"] = ep
            state["af"] = af
            
        else:  # short
            if low < ep:
                ep = low
                af = min(af + self.config["parabolic_af"], self.config["parabolic_max_af"])
            
            new_sar = sar - af * (sar - ep)
            new_sar = max(new_sar, high)
            
            state["sar"] = new_sar
            state["ep"] = ep
            state["af"] = af
        
        return state["sar"]
    
    def _calc_volatility_stop(self, symbol: str, close: float) -> float:
        """Standard deviation based stop."""
        history = list(self._history[symbol])
        period = self.config["volatility_period"]
        
        if len(history) < period:
            return self._calc_percent_stop(symbol, close)
        
        closes = [p.close for p in history[-period:]]
        mean = sum(closes) / len(closes)
        variance = sum((c - mean) ** 2 for c in closes) / len(closes)
        std_dev = math.sqrt(variance)
        
        multiplier = self.config["volatility_multiplier"]
        position = self._positions[symbol]
        
        if position == "long":
            peak = self._peak_prices[symbol]
            return peak - (std_dev * multiplier)
        else:
            trough = self._trough_prices[symbol]
            return trough + (std_dev * multiplier)
    
    def _calculate_atr(self, symbol: str, period: int) -> float:
        """Calculate Average True Range."""
        history = list(self._history[symbol])
        if len(history) < 2:
            return 0.0
        
        true_ranges = []
        for i in range(1, min(len(history), period + 1)):
            prev_close = history[i-1].close
            curr = history[i]
            
            tr1 = curr.high - curr.low
            tr2 = abs(curr.high - prev_close)
            tr3 = abs(curr.low - prev_close)
            
            true_ranges.append(max(tr1, tr2, tr3))
        
        return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0
    
    def _generate_recommendation(self, stop: TrailingStop, position: str, max_profit: float) -> str:
        """Generate human-readable recommendation."""
        if stop.triggered:
            return "🛑 STOP TRIGGERED - Exit position immediately"
        
        if stop.risk_reward >= 3:
            if stop.drawdown_from_peak_pct > 20:
                return "🔒 Lock in profits - Consider taking partial position off"
            else:
                return "🚀 Strong trend - Let it run, stop trails behind"
        
        if stop.risk_reward >= 1:
            return "✅ Breakeven or better - Trail stop protects capital"
        
        if max_profit > 5 and stop.drawdown_from_peak_pct > 50:
            return "⚠️  Giving back gains - Consider tightening stop"
        
        if stop.distance_pct < 2:
            return "📍 Tight stop - High chance of exit, size accordingly"
        
        return "⏳ Hold - Stop in place, monitor price action"
    
    def should_tighten(self, symbol: str, profit_threshold: float = 10.0) -> bool:
        """Check if position has significant profits to justify tighter stop."""
        if symbol not in self._entry_prices:
            return False
        
        entry = self._entry_prices[symbol]
        peak = self._peak_prices.get(symbol, entry)
        profit_pct = ((peak - entry) / entry * 100) if entry > 0 else 0
        
        return profit_pct >= profit_threshold


def recommend_stop_method(volatility: str, timeframe: str) -> StopMethod:
    """
    Recommend a stop method based on market conditions.
    
    Args:
        volatility: "low", "medium", "high"
        timeframe: "scalp", "day", "swing", "position"
    """
    matrix = {
        ("low", "scalp"): StopMethod.PERCENT,
        ("low", "day"): StopMethod.PERCENT,
        ("low", "swing"): StopMethod.ATR,
        ("low", "position"): StopMethod.CHANDELIER,
        ("medium", "scalp"): StopMethod.PERCENT,
        ("medium", "day"): StopMethod.ATR,
        ("medium", "swing"): StopMethod.CHANDELIER,
        ("medium", "position"): StopMethod.VOLATILITY,
        ("high", "scalp"): StopMethod.ATR,
        ("high", "day"): StopMethod.CHANDELIER,
        ("high", "swing"): StopMethod.VOLATILITY,
        ("high", "position"): StopMethod.PARABOLIC,
    }
    
    return matrix.get((volatility, timeframe), StopMethod.ATR)


# === Examples ===

if __name__ == "__main__":
    print("=" * 70)
    print("Trailing Stop Calculator Demo")
    print("=" * 70)
    
    # Simulate a winning long position with volatility
    price_data = [
        (100, 101, 99, 100.5),
        (102, 103, 101, 102.5),
        (101, 102, 100, 101),
        (104, 105, 103, 104.5),
        (106, 107, 105, 106),
        (105, 106, 104, 105),
        (108, 109, 107, 108),
        (110, 111, 109, 110),
        (109, 110, 108, 109),
        (112, 113, 111, 112),
    ]
    
    methods = [
        (StopMethod.PERCENT, "Fixed % (10%)"),
        (StopMethod.ATR, "ATR (14, 3x)"),
        (StopMethod.CHANDELIER, "Chandelier (14, 3x)"),
    ]
    
    for method, name in methods:
        print(f"\n{name}:")
        print("-" * 40)
        
        calc = TrailingStopCalculator(method=method)
        calc.initialize_position("DEMO", "long", entry_price=100, initial_stop=95)
        
        for i, (price, high, low, close) in enumerate(price_data):
            result = calc.update("DEMO", price, high, low, close)
            if result:
                stop = result.trailing_stop
                status = "🛑" if stop.triggered else "✅"
                print(f"  {status} Price: {price:5.1f} | Stop: {stop.current_stop:5.1f} "
                      f"| Distance: {stop.distance_pct:4.1f}% | R: {stop.risk_reward:.1f}")
    
    # Method recommendation
    print("\n" + "=" * 70)
    print("Method Recommendations:")
    print("=" * 70)
    
    scenarios = [
        ("low", "day", "Stable stock, intraday"),
        ("high", "swing", "Volatile crypto, 3-day hold"),
        ("medium", "position", "ETF, multi-month hold"),
    ]
    
    for vol, tf, desc in scenarios:
        method = recommend_stop_method(vol, tf)
        print(f"\n  {desc}")
        print(f"    → Use: {method.name}")
    
    # Real-time example
    print("\n" + "=" * 70)
    print("Live Position Example:")
    print("=" * 70)
    
    calc = TrailingStopCalculator(method=StopMethod.ATR, atr_multiplier=2.5)
    calc.initialize_position("AAPL", "long", entry_price=175.00, initial_stop=170.00)
    
    # Simulate some price action
    updates = [
        (178.50, 179.00, 177.50, 178.00),
        (180.25, 181.00, 179.50, 180.00),
        (182.00, 183.00, 181.00, 182.50),
        (181.00, 182.00, 180.00, 181.50),
        (184.50, 185.00, 183.50, 184.00),
    ]
    
    for price, high, low, close in updates:
        result = calc.update("AAPL", price, high, low, close)
        if result:
            print(f"\n  Price: ${result.current_price:.2f}")
            print(f"  Peak: ${result.highest_price:.2f}")
            print(f"  Stop: ${result.trailing_stop.current_stop:.2f} ({result.trailing_stop.method.name})")
            print(f"  Distance: {result.trailing_stop.distance_pct:.1f}%")
            print(f"  Risk/Reward: {result.trailing_stop.risk_reward:.1f}R")
            print(f"  Max Run-up: +{result.trailing_stop.max_profit_pct:.1f}%")
            print(f"  → {result.recommendation}")
    
    print("\n" + "=" * 70)
    print("Trailing stops protect profits. Pick the method that matches")
    print("your timeframe and the asset's volatility.")
    print("=" * 70)
```

## Stop Method Comparison

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **PERCENT** | Beginners, stable assets | Simple, predictable | Doesn't adapt to volatility |
| **ATR** | Most situations | Volatility-adjusted, widely used | Needs price history |
| **CHANDELIER** | Trend following | Stays far in strong trends | Can give back more profit |
| **PARABOLIC** | Strong trending markets | Accelerates into trend | Whipsaws in chop |
| **VOLATILITY** | Options, wide-swing assets | Statistical basis | Slower to adapt |

## Quick Reference

```python
# Standard ATR stop (most popular)
calc = TrailingStopCalculator(
    method=StopMethod.ATR,
    atr_period=14,
    atr_multiplier=3.0  # 2-4x typical
)

# Tight stop for scalping
calc = TrailingStopCalculator(
    method=StopMethod.PERCENT,
    percent_distance=3.0
)

# Wide stop for trend following
calc = TrailingStopCalculator(
    method=StopMethod.CHANDELIER,
    chandelier_multiplier=4.0
)

# Use recommended method
method = recommend_stop_method(volatility="high", timeframe="swing")
calc = TrailingStopCalculator(method=method)
```

## Key Rules

1. **ATR multiplier 2-4x** — 2x for tight, 4x for wide
2. **Tighten after +10%** — Use `should_tighten()` to check
3. **Never widen a stop** — Only ratchet in one direction
4. **Timeframe matters** — Day trades need tighter stops than swings
5. **Volatility adjusts size** — High ATR = smaller position

---

**Created by Ghost 👻 | Feb 20, 2026 | 12-min learning sprint**  
*Lesson: The exit is more important than the entry. Trailing stops remove emotion and enforce discipline — let winners run, cut losers automatically.*
