# Volatility Regime Detector — Market State Classification

**Purpose:** Detect high/low volatility regimes to adjust position sizing and strategy parameters  
**Use Case:** Reduce size in high volatility, increase in low volatility; avoid trading regime transitions

## The Code

```python
"""
Volatility Regime Detector
Identify market volatility states (low, normal, high, extreme)
for dynamic position sizing and risk adjustment.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Tuple
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque
import statistics
import math


class VolatilityRegime(Enum):
    EXTREME_LOW = auto()   # < 5th percentile
    LOW = auto()           # 5th-25th percentile
    NORMAL = auto()        # 25th-75th percentile
    HIGH = auto()          # 75th-95th percentile
    EXTREME_HIGH = auto()  # > 95th percentile


class RegimeTransition(Enum):
    STABLE = auto()        # Staying in same regime
    ESCALATING = auto()    # Moving to higher volatility
    DEESCALATING = auto()  # Moving to lower volatility
    SPIKE = auto()         # Sudden jump to extreme
    COLLAPSE = auto()      # Sudden drop to low


@dataclass
class RegimeState:
    """Current volatility regime state."""
    regime: VolatilityRegime
    current_atr: float
    current_volatility: float  # Annualized
    percentile: float  # 0-100 where current vol ranks historically
    transition: RegimeTransition
    duration_bars: int  # How long in current regime
    
    # Recommendations
    position_size_multiplier: float
    stop_widening_factor: float
    trade_confidence: str  # high, medium, low


@dataclass
class VolatilityMetrics:
    """Comprehensive volatility statistics."""
    atr_14: float
    atr_20: float
    atr_50: float
    
    realized_vol_20d: float  # 20-day realized volatility
    realized_vol_50d: float
    
    historical_percentiles: Dict[str, float]  # 5th, 25th, 75th, 95th
    
    vs_average: float  # Current vs historical average (%)
    vs_median: float
    trend_direction: str  # rising, falling, stable
    trend_strength: float  # 0-1


class VolatilityRegimeDetector:
    """
    Detect market volatility regimes for dynamic risk management.
    
    Usage:
        detector = VolatilityRegimeDetector(lookback_period=252)
        
        for bar in price_data:
            regime = detector.update(bar.high, bar.low, bar.close)
            print(f"Regime: {regime.regime.name}, Size multiplier: {regime.position_size_multiplier}")
    """
    
    def __init__(
        self,
        lookback_period: int = 252,
        atr_period: int = 14,
        regime_thresholds: Optional[Dict] = None,
        volatility_method: str = "atr"  # "atr", "stddev", "parkinson"
    ):
        self.lookback = lookback_period
        self.atr_period = atr_period
        self.method = volatility_method
        
        # Default thresholds (5th, 25th, 75th, 95th percentiles)
        self.thresholds = regime_thresholds or {
            "extreme_low": 5,
            "low": 25,
            "high": 75,
            "extreme_high": 95
        }
        
        # State
        self.price_history: deque = deque(maxlen=lookback_period)
        self.high_history: deque = deque(maxlen=lookback_period)
        self.low_history: deque = deque(maxlen=lookback_period)
        self.close_history: deque = deque(maxlen=lookback_period)
        
        self.atr_history: deque = deque(maxlen=lookback_period)
        self.volatility_history: deque = deque(maxlen=lookback_period)
        
        self.current_regime: Optional[VolatilityRegime] = None
        self.regime_start_bar: int = 0
        self.bar_count: int = 0
        
        # Previous for transition detection
        self.previous_atr: Optional[float] = None
        self.previous_regime: Optional[VolatilityRegime] = None
    
    def update(
        self,
        high: float,
        low: float,
        close: float,
        timestamp: Optional[datetime] = None
    ) -> RegimeState:
        """
        Update with new price bar and return current regime.
        """
        self.bar_count += 1
        
        # Store price data
        self.high_history.append(high)
        self.low_history.append(low)
        self.close_history.append(close)
        
        # Calculate ATR
        atr = self._calculate_atr()
        if atr:
            self.atr_history.append(atr)
        
        # Calculate volatility
        vol = self._calculate_volatility()
        if vol:
            self.volatility_history.append(vol)
        
        # Determine regime
        regime = self._classify_regime(atr or 0, vol or 0)
        
        # Detect transition
        transition = self._detect_transition(regime, atr)
        
        # Track regime duration
        if regime != self.current_regime:
            self.regime_start_bar = self.bar_count
            self.previous_regime = self.current_regime
            self.current_regime = regime
        
        duration = self.bar_count - self.regime_start_bar
        
        # Calculate percentile
        percentile = self._calculate_percentile(vol or 0)
        
        # Generate recommendations
        size_mult, stop_factor, confidence = self._generate_recommendations(regime, transition)
        
        self.previous_atr = atr
        
        return RegimeState(
            regime=regime,
            current_atr=atr or 0,
            current_volatility=vol or 0,
            percentile=percentile,
            transition=transition,
            duration_bars=duration,
            position_size_multiplier=size_mult,
            stop_widening_factor=stop_factor,
            trade_confidence=confidence
        )
    
    def _calculate_atr(self) -> Optional[float]:
        """Calculate Average True Range."""
        if len(self.close_history) < 2:
            return None
        
        true_ranges = []
        for i in range(1, min(len(self.close_history), self.atr_period + 1)):
            prev_close = list(self.close_history)[-i-1] if i < len(self.close_history) else self.close_history[0]
            curr_high = list(self.high_history)[-i]
            curr_low = list(self.low_history)[-i]
            
            tr1 = curr_high - curr_low
            tr2 = abs(curr_high - prev_close)
            tr3 = abs(curr_low - prev_close)
            
            true_ranges.append(max(tr1, tr2, tr3))
        
        if not true_ranges:
            return None
        
        return sum(true_ranges) / len(true_ranges)
    
    def _calculate_volatility(self) -> Optional[float]:
        """Calculate annualized volatility."""
        if len(self.close_history) < 20:
            return None
        
        closes = list(self.close_history)[-20:]
        
        if self.method == "atr":
            # Use ATR-based volatility
            if len(self.atr_history) > 0:
                avg_atr = statistics.mean(self.atr_history)
                current_price = closes[-1]
                return (avg_atr / current_price) * math.sqrt(252) * 100 if current_price > 0 else 0
            return None
        
        elif self.method == "stddev":
            # Standard deviation of returns
            returns = [(closes[i] / closes[i-1]) - 1 for i in range(1, len(closes))]
            if len(returns) > 1:
                std = statistics.stdev(returns)
                return std * math.sqrt(252) * 100
            return None
        
        else:  # parkinson
            # Parkinson volatility (uses high-low)
            if len(self.high_history) >= 20 and len(self.low_history) >= 20:
                highs = list(self.high_history)[-20:]
                lows = list(self.low_history)[-20:]
                log_hl = [math.log(h / l) ** 2 for h, l in zip(highs, lows) if l > 0]
                if log_hl:
                    return math.sqrt(sum(log_hl) / len(log_hl) * 252 / (4 * math.log(2))) * 100
            return None
    
    def _classify_regime(self, atr: float, vol: float) -> VolatilityRegime:
        """Classify current volatility into regime."""
        if len(self.volatility_history) < 50:
            return VolatilityRegime.NORMAL
        
        vols = list(self.volatility_history)
        vols.sort()
        
        # Calculate percentiles
        p5 = vols[int(len(vols) * 0.05)]
        p25 = vols[int(len(vols) * 0.25)]
        p75 = vols[int(len(vols) * 0.75)]
        p95 = vols[int(len(vols) * 0.95)]
        
        if vol <= p5:
            return VolatilityRegime.EXTREME_LOW
        elif vol <= p25:
            return VolatilityRegime.LOW
        elif vol <= p75:
            return VolatilityRegime.NORMAL
        elif vol <= p95:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.EXTREME_HIGH
    
    def _detect_transition(
        self,
        current_regime: VolatilityRegime,
        current_atr: Optional[float]
    ) -> RegimeTransition:
        """Detect what type of transition is occurring."""
        if self.previous_regime is None or current_regime == self.previous_regime:
            return RegimeTransition.STABLE
        
        # Determine direction
        regime_order = [
            VolatilityRegime.EXTREME_LOW,
            VolatilityRegime.LOW,
            VolatilityRegime.NORMAL,
            VolatilityRegime.HIGH,
            VolatilityRegime.EXTREME_HIGH
        ]
        
        prev_idx = regime_order.index(self.previous_regime) if self.previous_regime in regime_order else 2
        curr_idx = regime_order.index(current_regime) if current_regime in regime_order else 2
        
        # Check for sudden spike/collapse (2+ regime jumps)
        if abs(curr_idx - prev_idx) >= 2:
            if curr_idx > prev_idx:
                return RegimeTransition.SPIKE
            else:
                return RegimeTransition.COLLAPSE
        
        # Gradual change
        if curr_idx > prev_idx:
            return RegimeTransition.ESCALATING
        else:
            return RegimeTransition.DEESCALATING
    
    def _calculate_percentile(self, current_vol: float) -> float:
        """Calculate percentile of current volatility vs history."""
        if len(self.volatility_history) < 20:
            return 50.0
        
        vols = list(self.volatility_history)
        below_count = sum(1 for v in vols if v < current_vol)
        
        return (below_count / len(vols)) * 100
    
    def _generate_recommendations(
        self,
        regime: VolatilityRegime,
        transition: RegimeTransition
    ) -> Tuple[float, float, str]:
        """Generate trading recommendations based on regime."""
        # Base multipliers by regime
        multipliers = {
            VolatilityRegime.EXTREME_LOW: (1.5, 0.8, "high"),
            VolatilityRegime.LOW: (1.25, 0.9, "high"),
            VolatilityRegime.NORMAL: (1.0, 1.0, "medium"),
            VolatilityRegime.HIGH: (0.6, 1.5, "low"),
            VolatilityRegime.EXTREME_HIGH: (0.3, 2.0, "low")
        }
        
        size_mult, stop_factor, confidence = multipliers.get(regime, (1.0, 1.0, "medium"))
        
        # Adjust for transitions
        if transition == RegimeTransition.SPIKE:
            size_mult *= 0.5  # Reduce further on volatility spike
            confidence = "low"
        elif transition == RegimeTransition.ESCALATING:
            size_mult *= 0.8
            confidence = "low"
        elif transition == RegimeTransition.COLLAPSE:
            # Opportunity as volatility collapses
            confidence = "high"
        
        return size_mult, stop_factor, confidence
    
    def get_metrics(self) -> VolatilityMetrics:
        """Get comprehensive volatility metrics."""
        if len(self.close_history) < 50:
            return VolatilityMetrics(0, 0, 0, 0, 0, {}, 0, 0, "unknown", 0)
        
        closes = list(self.close_history)
        
        # Calculate ATRs
        atrs = list(self.atr_history)
        atr_14 = atrs[-1] if len(atrs) >= 14 else 0
        atr_20 = statistics.mean(atrs[-20:]) if len(atrs) >= 20 else atr_14
        atr_50 = statistics.mean(atrs[-50:]) if len(atrs) >= 50 else atr_20
        
        # Calculate realized volatility
        returns = [(closes[i] / closes[i-1]) - 1 for i in range(1, len(closes))]
        
        vol_20 = statistics.stdev(returns[-20:]) * math.sqrt(252) * 100 if len(returns) >= 20 else 0
        vol_50 = statistics.stdev(returns[-50:]) * math.sqrt(252) * 100 if len(returns) >= 50 else vol_20
        
        # Historical percentiles
        vols = list(self.volatility_history)
        percentiles = {}
        if vols:
            vols_sorted = sorted(vols)
            percentiles = {
                "5th": vols_sorted[int(len(vols) * 0.05)],
                "25th": vols_sorted[int(len(vols) * 0.25)],
                "75th": vols_sorted[int(len(vols) * 0.75)],
                "95th": vols_sorted[int(len(vols) * 0.95)]
            }
        
        # Compare to average
        avg_vol = statistics.mean(vols) if vols else 0
        vs_avg = ((vols[-1] / avg_vol) - 1) * 100 if avg_vol > 0 else 0
        
        # Trend
        trend_dir, trend_str = self._calculate_trend(vols[-20:] if len(vols) >= 20 else vols)
        
        return VolatilityMetrics(
            atr_14=atr_14,
            atr_20=atr_20,
            atr_50=atr_50,
            realized_vol_20d=vol_20,
            realized_vol_50d=vol_50,
            historical_percentiles=percentiles,
            vs_average=vs_avg,
            vs_median=0,  # Simplified
            trend_direction=trend_dir,
            trend_strength=trend_str
        )
    
    def _calculate_trend(self, values: List[float]) -> Tuple[str, float]:
        """Calculate trend direction and strength."""
        if len(values) < 10:
            return "unknown", 0.0
        
        # Simple linear regression
        n = len(values)
        x = list(range(n))
        
        mean_x = sum(x) / n
        mean_y = sum(values) / n
        
        numerator = sum((x[i] - mean_x) * (values[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator > 0 else 0
        
        # Normalize strength
        avg_value = mean_y if mean_y > 0 else 1
        strength = min(1.0, abs(slope) / (avg_value / n))
        
        if slope > avg_value * 0.01 / n:
            return "rising", strength
        elif slope < -avg_value * 0.01 / n:
            return "falling", strength
        else:
            return "stable", strength


def generate_regime_report(detector: VolatilityRegimeDetector, symbol: str = "Unknown") -> str:
    """Generate formatted regime report."""
    state = detector.current_regime
    metrics = detector.get_metrics()
    
    lines = [
        f"{'=' * 60}",
        f"VOLATILITY REGIME REPORT: {symbol}",
        f"{'=' * 60}",
        "",
        f"Current Regime: {state.name if state else 'Unknown'}",
        f"Duration: {detector.bar_count - detector.regime_start_bar} bars",
        "",
        f"ATR (14): {metrics.atr_14:.4f}",
        f"Realized Vol (20d): {metrics.realized_vol_20d:.2f}%",
        f"Realized Vol (50d): {metrics.realized_vol_50d:.2f}%",
        "",
        "Historical Percentiles:",
    ]
    
    for pct, val in metrics.historical_percentiles.items():
        lines.append(f"  {pct}: {val:.2f}%")
    
    lines.extend([
        "",
        f"Vs Historical Avg: {metrics.vs_average:+.1f}%",
        f"Trend: {metrics.trend_direction.upper()} (strength: {metrics.trend_strength:.2f})",
        f"{'=' * 60}"
    ])
    
    return "\n".join(lines)


# === Examples ===

def example_regime_detection():
    """Demonstrate regime detection on sample data."""
    print("=" * 70)
    print("Volatility Regime Detection Demo")
    print("=" * 70)
    
    import random
    random.seed(42)
    
    # Generate price data with regime changes
    base_price = 100.0
    prices = []
    
    # Phase 1: Low volatility (days 0-50)
    for i in range(50):
        base_price *= (1 + random.normalvariate(0.0005, 0.005))
        prices.append({
            "open": base_price * (1 + random.uniform(-0.005, 0.005)),
            "high": base_price * (1 + random.uniform(0, 0.01)),
            "low": base_price * (1 + random.uniform(-0.01, 0)),
            "close": base_price
        })
    
    # Phase 2: Normal volatility (days 50-100)
    for i in range(50):
        base_price *= (1 + random.normalvariate(0.0005, 0.015))
        prices.append({
            "open": base_price * (1 + random.uniform(-0.01, 0.01)),
            "high": base_price * (1 + random.uniform(0, 0.02)),
            "low": base_price * (1 + random.uniform(-0.02, 0)),
            "close": base_price
        })
    
    # Phase 3: High volatility (days 100-150)
    for i in range(50):
        base_price *= (1 + random.normalvariate(0.0005, 0.03))
        prices.append({
            "open": base_price * (1 + random.uniform(-0.02, 0.02)),
            "high": base_price * (1 + random.uniform(0, 0.04)),
            "low": base_price * (1 + random.uniform(-0.04, 0)),
            "close": base_price
        })
    
    # Phase 4: Extreme volatility (days 150-200)
    for i in range(50):
        base_price *= (1 + random.normalvariate(0.0005, 0.05))
        prices.append({
            "open": base_price * (1 + random.uniform(-0.03, 0.03)),
            "high": base_price * (1 + random.uniform(0, 0.06)),
            "low": base_price * (1 + random.uniform(-0.06, 0)),
            "close": base_price
        })
    
    detector = VolatilityRegimeDetector(lookback_period=100, atr_period=14)
    
    print("\nProcessing 200 bars with increasing volatility...\n")
    print(f"{'Bar':<6} {'Price':<10} {'ATR':<8} {'Vol%':<8} {'Regime':<15} {'Size%':<8} {'Signal'}")
    print("-" * 70)
    
    for i, bar in enumerate(prices):
        state = detector.update(bar["high"], bar["low"], bar["close"])
        
        # Print key transitions
        if i % 25 == 0 or state.transition != RegimeTransition.STABLE:
            emoji = {
                VolatilityRegime.EXTREME_LOW: "🔵",
                VolatilityRegime.LOW: "🟢",
                VolatilityRegime.NORMAL: "⚪",
                VolatilityRegime.HIGH: "🟡",
                VolatilityRegime.EXTREME_HIGH: "🔴"
            }.get(state.regime, "⚪")
            
            trans_emoji = ""
            if state.transition == RegimeTransition.ESCALATING:
                trans_emoji = "📈"
            elif state.transition == RegimeTransition.DEESCALATING:
                trans_emoji = "📉"
            elif state.transition == RegimeTransition.SPIKE:
                trans_emoji = "⚡"
            
            print(f"{i:<6} {bar['close']:<10.2f} {state.current_atr:<8.4f} "
                  f"{state.current_volatility:<8.2f} {state.regime.name:<15} "
                  f"{state.position_size_multiplier*100:<7.0f}% {emoji} {trans_emoji}")
    
    # Final metrics
    print("\n" + "=" * 70)
    print("Final Metrics:")
    print("=" * 70)
    
    metrics = detector.get_metrics()
    print(f"\nATR (14): {metrics.atr_14:.4f}")
    print(f"Realized Volatility (20d): {metrics.realized_vol_20d:.2f}%")
    print(f"Realized Volatility (50d): {metrics.realized_vol_50d:.2f}%")
    print(f"Trend: {metrics.trend_direction.upper()}")
    
    if metrics.historical_percentiles:
        print(f"\nHistorical Percentiles:")
        for k, v in metrics.historical_percentiles.items():
            print(f"  {k}: {v:.2f}%")


def example_position_sizing():
    """Show how regime affects position sizing."""
    print("\n" + "=" * 70)
    print("Position Sizing by Regime")
    print("=" * 70)
    
    detector = VolatilityRegimeDetector()
    
    # Simulate different market conditions
    scenarios = [
        ("Quiet Market", 0.005, 100.0),    # Low vol
        ("Normal Market", 0.015, 105.0),   # Normal vol
        ("Volatile Market", 0.035, 110.0), # High vol
        ("Crash", 0.06, 95.0),             # Extreme vol
    ]
    
    base_price = 100.0
    bar_num = 0
    
    for scenario_name, vol, target_price in scenarios:
        # Generate bars for this regime
        import random
        random.seed(hash(scenario_name) % 1000)
        
        for _ in range(30):  # 30 bars per regime
            bar_num += 1
            base_price *= (1 + random.normalvariate(0.0005, vol))
            
            high = base_price * (1 + abs(random.normalvariate(0, vol)))
            low = base_price * (1 - abs(random.normalvariate(0, vol)))
            
            state = detector.update(high, low, base_price)
        
        # Show recommendation
        account = 100000
        base_risk = 2000  # 2% of account
        
        adjusted_risk = base_risk * state.position_size_multiplier
        shares = int(adjusted_risk / (state.current_atr * 2)) if state.current_atr > 0 else 0
        
        print(f"\n{scenario_name}:")
        print(f"  Regime: {state.regime.name}")
        print(f"  Volatility: {state.current_volatility:.2f}%")
        print(f"  ATR: {state.current_atr:.4f}")
        print(f"  Position Size: ${adjusted_risk:,.0f} ({state.position_size_multiplier*100:.0f}% of normal)")
        print(f"  Recommended Shares: {shares}")
        print(f"  Stop Width: {state.stop_widening_factor:.1f}x ATR")
        print(f"  Trade Confidence: {state.trade_confidence.upper()}")


def example_risk_management():
    """Show risk management based on regime transitions."""
    print("\n" + "=" * 70)
    print("Risk Management by Transitions")
    print("=" * 70)
    
    detector = VolatilityRegimeDetector()
    
    transitions = [
        (VolatilityRegime.NORMAL, RegimeTransition.STABLE, "Normal conditions"),
        (VolatilityRegime.HIGH, RegimeTransition.ESCALATING, "Vol increasing"),
        (VolatilityRegime.EXTREME_HIGH, RegimeTransition.SPIKE, "Vol spike!"),
        (VolatilityRegime.HIGH, RegimeTransition.DEESCALATING, "Calming down"),
        (VolatilityRegime.LOW, RegimeTransition.COLLAPSE, "Vol collapse"),
    ]
    
    for regime, trans, desc in transitions:
        size_mult, stop_factor, confidence = detector._generate_recommendations(regime, trans)
        
        action = "TRADE"
        if trans == RegimeTransition.SPIKE:
            action = "REDUCE/EXIT"
        elif trans == RegimeTransition.ESCALATING:
            action = "SIZE DOWN"
        elif trans == RegimeTransition.COLLAPSE:
            action = "SIZE UP"
        
        emoji = "✅" if confidence == "high" else "⚠️" if confidence == "medium" else "❌"
        
        print(f"\n{desc} ({regime.name}, {trans.name}):")
        print(f"  Action: {action}")
        print(f"  Size: {size_mult*100:.0f}% of normal")
        print(f"  Stop: {stop_factor:.1f}x normal width")
        print(f"  Signal: {emoji} {confidence.upper()}")


if __name__ == "__main__":
    example_regime_detection()
    example_position_sizing()
    example_risk_management()
    
    print("\n" + "=" * 70)
    print("KEY PRINCIPLES:")
    print("=" * 70)
    print("""
1. Size DOWN in high volatility (wider stops, more noise)
2. Size UP in low volatility (tighter stops, cleaner moves)
3. Avoid new trades during volatility spikes (unpredictable)
4. Widen stops in high volatility to avoid whipsaws
5. Narrow stops in low volatility to maximize R

Position size ∝ 1/Volatility
    """)
    print("=" * 70)
```

## Regime-Based Position Sizing

| Regime | Size Multiplier | Stop Width | Confidence | Action |
|--------|-----------------|------------|------------|--------|
| **Extreme Low** | 150% | 0.8x | High | Size up |
| **Low** | 125% | 0.9x | High | Normal+ |
| **Normal** | 100% | 1.0x | Medium | Baseline |
| **High** | 60% | 1.5x | Low | Size down |
| **Extreme High** | 30% | 2.0x | Low | Avoid |

## Transition Signals

| Transition | Meaning | Action |
|------------|---------|--------|
| **Stable** | No change | Continue strategy |
| **Escalating** | Vol increasing | Reduce size |
| **De-escalating** | Vol decreasing | Prepare to increase |
| **Spike** | Sudden jump | Exit/reduce immediately |
| **Collapse** | Sudden drop | Opportunity to increase |

## Quick Reference

```python
detector = VolatilityRegimeDetector(lookback_period=252)

for bar in price_data:
    regime = detector.update(bar.high, bar.low, bar.close)
    
    # Adjust position size
    base_size = account * 0.02 / atr
    adjusted_size = base_size * regime.position_size_multiplier
    
    # Only trade in acceptable conditions
    if regime.regime not in [VolatilityRegime.EXTREME_HIGH]:
        enter_trade(size=adjusted_size)
```

## Why This Matters

- **High volatility = wider stops needed** — Or you'll get stopped out on noise
- **High volatility = smaller positions** — Same dollar risk requires fewer shares
- **Volatility spikes = danger** — Markets become unpredictable
- **Low volatility = opportunity** — Clean moves, tight stops, bigger size

**Rule: Cut size in half when volatility doubles.**

---

**Created by Ghost 👻 | Feb 20, 2026 | 13-min learning sprint**  
*Lesson: "Volatility is not your enemy—ignoring it is." High volatility demands smaller positions and wider stops. Trade smaller when markets are wild, trade bigger when they're calm. Position size ∝ 1/Volatility.*
