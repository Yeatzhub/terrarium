# Smart Stop & Target Calculator

**Purpose:** Calculate optimal stop and profit targets using multiple methods  
**Use Case:** ATR stops, support/resistance, volatility exits, time-based

## The Code

```python
"""
Smart Stop Loss & Profit Target Calculator
Multiple methods: ATR, support/resistance, vol expansion, time-based.
"""

from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple, Dict
from datetime import datetime, timedelta
import statistics


@dataclass
class OHLC:
    """Price bar for calculations."""
    high: float
    low: float
    close: float
    volume: float = 0


@dataclass
class Level:
    """Support/resistance level."""
    price: float
    touches: int
    strength: str  # weak, moderate, strong


@dataclass
class ExitPlan:
    """Complete exit strategy."""
    entry: float
    stop_loss: float
    take_profit: float
    risk: float
    reward: float
    risk_reward: float
    position_size: Optional[float] = None
    
    def __str__(self):
        return (f"Entry: ${self.entry:.2f} | "
                f"Stop: ${self.stop_loss:.2f} | "
                f"Target: ${self.take_profit:.2f} | "
                f"R:R = 1:{self.risk_reward:.1f}")


class StopCalculator:
    """
    Calculate stops and targets using multiple methods.
    """
    
    def __init__(self, account_size: float = 100000):
        self.account = account_size
    
    # === STOP LOSS METHODS ===
    
    def atr_stop(
        self,
        bars: List[OHLC],
        entry: float,
        atr_multiple: float = 2.0,
        direction: Literal["long", "short"] = "long"
    ) -> float:
        """
        ATR-based stop.
        
        Args:
            bars: Recent price bars (at least 14)
            entry: Entry price
            atr_multiple: Stop distance in ATR units (1.5-3 typical)
            direction: long or short
        """
        atr = self._calculate_atr(bars, period=14)
        
        if direction == "long":
            return entry - (atr * atr_multiple)
        else:
            return entry + (atr * atr_multiple)
    
    def fixed_pct_stop(
        self,
        entry: float,
        pct: float,
        direction: Literal["long", "short"] = "long"
    ) -> float:
        """Fixed percentage stop (e.g., 2% stop)."""
        if direction == "long":
            return entry * (1 - pct / 100)
        else:
            return entry * (1 + pct / 100)
    
    def swing_stop(
        self,
        bars: List[OHLC],
        direction: Literal["long", "short"] = "long",
        lookback: int = 5
    ) -> float:
        """
        Stop below/above recent swing point.
        Uses lowest low (long) or highest high (short) of lookback.
        """
        recent = bars[-lookback:]
        
        if direction == "long":
            lowest = min(b.low for b in recent)
            return lowest * 0.995  # Slight buffer
        else:
            highest = max(b.high for b in recent)
            return highest * 1.005  # Slight buffer
    
    def volatility_stop(
        self,
        bars: List[OHLC],
        entry: float,
        direction: Literal["long", "short"] = "long"
    ) -> float:
        """
        Volatility expansion stop.
        Places stop outside recent volatility range.
        """
        recent = bars[-20:]
        avg_range = statistics.mean(b.high - b.low for b in recent)
        
        if direction == "long":
            return entry - (avg_range * 1.5)
        else:
            return entry + (avg_range * 1.5)
    
    def support_resistance_stop(
        self,
        levels: List[Level],
        entry: float,
        direction: Literal["long", "short"] = "long",
        max_distance_pct: float = 5.0
    ) -> Optional[float]:
        """
        Place stop at nearest support (long) or resistance (short).
        
        Args:
            levels: Pre-calculated S/R levels
            direction: Trade direction
            max_distance_pct: Reject if stop > X% away
        """
        if direction == "long":
            # Find support below entry
            supports = [l for l in levels if l.price < entry]
            if not supports:
                return None
            best = max(supports, key=lambda l: l.price)  # Highest support
        else:
            # Find resistance above entry
            resistances = [l for l in levels if l.price > entry]
            if not resistances:
                return None
            best = min(resistances, key=lambda l: l.price)  # Lowest resistance
        
        # Check distance
        distance = abs(best.price - entry) / entry * 100
        if distance > max_distance_pct:
            return None  # Too far, use another method
        
        return best.price * (0.99 if direction == "long" else 1.01)
    
    # === TAKE PROFIT METHODS ===
    
    def fixed_rr_target(
        self,
        entry: float,
        stop: float,
        risk_reward: float = 2.0,
        direction: Literal["long", "short"] = "long"
    ) -> float:
        """Target based on fixed risk:reward ratio."""
        risk = abs(entry - stop)
        
        if direction == "long":
            return entry + (risk * risk_reward)
        else:
            return entry - (risk * risk_reward)
    
    def atr_target(
        self,
        bars: List[OHLC],
        entry: float,
        atr_multiple: float = 3.0,
        direction: Literal["long", "short"] = "long"
    ) -> float:
        """ATR-based target (wider than stop)."""
        atr = self._calculate_atr(bars, period=14)
        
        if direction == "long":
            return entry + (atr * atr_multiple)
        else:
            return entry - (atr * atr_multiple)
    
    def measured_move_target(
        self,
        entry: float,
        consolidation_low: float,
        consolidation_high: float,
        direction: Literal["long", "short"] = "long"
    ) -> float:
        """
        Target based on measured move from consolidation.
        
        Args:
            consolidation_low: Low of the range
            consolidation_high: High of the range
            entry: Breakout entry price
        """
        range_size = consolidation_high - consolidation_low
        
        if direction == "long":
            return entry + range_size
        else:
            return entry - range_size
    
    def resistance_target(
        self,
        levels: List[Level],
        entry: float,
        direction: Literal["long", "short"] = "long",
        min_rr: float = 1.5
    ) -> Optional[float]:
        """
        Target at next resistance (long) or support (short).
        Returns None if R:R would be < min_rr.
        """
        if direction == "long":
            targets = [l for l in levels if l.price > entry]
            if not targets:
                return None
            best = min(targets, key=lambda l: l.price)
        else:
            targets = [l for l in levels if l.price < entry]
            if not targets:
                return None
            best = max(targets, key=lambda l: l.price)
        
        # Verify R:R
        risk = entry - (levels[0].price if direction == "long" else levels[-1].price)
        reward = abs(best.price - entry)
        if reward / risk < min_rr:
            return None
        
        return best.price
    
    # === COMPLETE PLANS ===
    
    def create_plan(
        self,
        entry: float,
        stop_method: Literal["atr", "fixed_pct", "swing", "volatility"],
        target_method: Literal["fixed_rr", "atr", "measured", "resistance"],
        bars: List[OHLC],
        direction: Literal["long", "short"] = "long",
        risk_pct: float = 1.0,
        levels: Optional[List[Level]] = None,
        **kwargs
    ) -> ExitPlan:
        """
        Create complete exit plan with chosen methods.
        """
        # Calculate stop
        if stop_method == "atr":
            multiple = kwargs.get("atr_multiple", 2.0)
            stop = self.atr_stop(bars, entry, multiple, direction)
        elif stop_method == "fixed_pct":
            pct = kwargs.get("pct", 2.0)
            stop = self.fixed_pct_stop(entry, pct, direction)
        elif stop_method == "swing":
            lookback = kwargs.get("lookback", 5)
            stop = self.swing_stop(bars, direction, lookback)
        else:  # volatility
            stop = self.volatility_stop(bars, entry, direction)
        
        # Calculate target
        if target_method == "fixed_rr":
            rr = kwargs.get("risk_reward", 2.0)
            target = self.fixed_rr_target(entry, stop, rr, direction)
        elif target_method == "atr":
            multiple = kwargs.get("target_atr_multiple", 4.0)
            target = self.atr_target(bars, entry, multiple, direction)
        elif target_method == "measured":
            low = kwargs.get("consolidation_low", entry * 0.95)
            high = kwargs.get("consolidation_high", entry * 1.05)
            target = self.measured_move_target(entry, low, high, direction)
        else:  # resistance
            if levels:
                min_rr = kwargs.get("min_rr", 1.5)
                target = self.resistance_target(levels, entry, direction, min_rr)
                if target is None:
                    target = self.fixed_rr_target(entry, stop, 2.0, direction)
            else:
                target = self.fixed_rr_target(entry, stop, 2.0, direction)
        
        risk = abs(entry - stop)
        reward = abs(target - entry)
        
        return ExitPlan(
            entry=round(entry, 2),
            stop_loss=round(stop, 2),
            take_profit=round(target, 2),
            risk=round(risk, 2),
            reward=round(reward, 2),
            risk_reward=round(reward / risk, 2) if risk > 0 else 0
        )
    
    def compare_methods(
        self,
        entry: float,
        bars: List[OHLC],
        levels: Optional[List[Level]] = None,
        direction: Literal["long", "short"] = "long"
    ) -> Dict[str, ExitPlan]:
        """
        Compare all stop/target combinations.
        Returns dict of method names to plans.
        """
        plans = {}
        
        stop_methods = [
            ("atr_2x", lambda: self.atr_stop(bars, entry, 2.0, direction)),
            ("swing_5", lambda: self.swing_stop(bars, direction, 5)),
            ("volatility", lambda: self.volatility_stop(bars, entry, direction)),
        ]
        
        for stop_name, stop_fn in stop_methods:
            try:
                stop = stop_fn()
                target = self.fixed_rr_target(entry, stop, 2.0, direction)
                risk = abs(entry - stop)
                reward = abs(target - entry)
                
                plans[f"{stop_name}_rr2"] = ExitPlan(
                    entry=entry, stop_loss=stop, take_profit=target,
                    risk=risk, reward=reward,
                    risk_reward=reward/risk if risk > 0 else 0
                )
            except:
                pass
        
        return plans
    
    # === HELPERS ===
    
    def _calculate_atr(self, bars: List[OHLC], period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(bars) < period + 1:
            # Fallback: use average range
            return statistics.mean(b.high - b.low for b in bars[-10:])
        
        tr_list = []
        for i in range(1, len(bars)):
            tr = max(
                bars[i].high - bars[i].low,
                abs(bars[i].high - bars[i-1].close),
                abs(bars[i].low - bars[i-1].close)
            )
            tr_list.append(tr)
        
        return statistics.mean(tr_list[-period:])
    
    def position_size(self, entry: float, stop: float, risk_pct: float) -> float:
        """Calculate shares for given risk %."""
        risk_amount = self.account * (risk_pct / 100)
        risk_per_share = abs(entry - stop)
        return risk_amount / risk_per_share if risk_per_share > 0 else 0


# === Examples ===

if __name__ == "__main__":
    # Create sample data
    base = 100
    bars = [
        OHLC(high=base + i*0.5, low=base - 2 + i*0.3, close=base + i*0.4)
        for i in range(30)
    ]
    
    # Add some structure
    bars[-5].low = 105  # Recent swing low
    bars[-5].high = 112
    
    calc = StopCalculator(account_size=50000)
    entry = 110
    
    print("=" * 70)
    print("Smart Stop & Target Calculator")
    print("=" * 70)
    
    print(f"\nEntry: ${entry}")
    print(f"Recent range: ${bars[-5].low:.2f} - ${bars[-1].high:.2f}")
    print(f"ATR(14): ${calc._calculate_atr(bars, 14):.2f}")
    
    # Different stop methods
    print("\n--- Stop Methods (Long Position) ---")
    print(f"ATR 2x:       ${calc.atr_stop(bars, entry, 2.0, 'long'):.2f}")
    print(f"Swing 5-bar:  ${calc.swing_stop(bars, 'long', 5):.2f}")
    print(f"Volatility:   ${calc.volatility_stop(bars, entry, 'long'):.2f}")
    print(f"Fixed 2%:     ${calc.fixed_pct_stop(entry, 2.0, 'long'):.2f}")
    
    # Complete plans
    print("\n--- Complete Plans ---")
    
    plan1 = calc.create_plan(
        entry=entry,
        stop_method="atr",
        target_method="fixed_rr",
        bars=bars,
        direction="long",
        atr_multiple=2.0,
        risk_reward=2.0
    )
    print(f"ATR Stop + 2R Target: {plan1}")
    shares = calc.position_size(plan1.entry, plan1.stop_loss, 1.0)
    print(f"  Position size: {shares:.0f} shares for 1% risk")
    
    plan2 = calc.create_plan(
        entry=entry,
        stop_method="swing",
        target_method="measured",
        bars=bars,
        direction="long",
        consolidation_low=105,
        consolidation_high=108
    )
    print(f"\nSwing Stop + Measured Move: {plan2}")
    
    # Comparison
    print("\n--- Method Comparison ---")
    comparisons = calc.compare_methods(entry, bars, direction="long")
    for name, plan in comparisons.items():
        print(f"{name:15} | {plan}")
    
    print("\n" + "=" * 70)
    print("Recommendations:")
    print("- ATR stop: Best for normal volatility")
    print("- Swing stop: Best for clear structure")
    print("- 2R target: Minimum for positive expectancy")
    print("- Measured move: Best for breakout plays")


## Method Selection Guide

| Market Condition | Best Stop | Best Target |
|-----------------|-----------|-------------|
| Trending, volatile | ATR 2x | ATR 4x or measured move |
| Clear swing points | Swing low/high | Next S/R level |
| Range breakout | Below range | Measured move |
| Low volatility | Fixed % (tight) | Fixed 2R |
| News/earnings | Volatility stop | Quick 1.5R |

## Quick Rules

1. **Never risk > 1-2% per trade**
2. **Minimum 1.5R reward**, preferably 2R+
3. **Stop must make sense** technically, not just mathematically
4. **Wider stop = smaller position** (not wider stop = hold through)
5. **Move stop to breakeven** after 1R profit

---

**Created by Ghost 👻 | Feb 19, 2026 | 14-min learning sprint**  
*Lesson: The stop defines the trade. Choose method that fits the setup, not the risk you want.*
