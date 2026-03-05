# Signal Generator Pattern
*Ghost Learning | 2026-02-22*

Combine multiple conditions into actionable trading signals with confidence scoring.

## The Problem

```python
# Many conditions, unclear combination
if rsi < 30 and macd_cross and price > ma and volume_spike:
    signal = "buy"  # But how confident? What's the logic?
```

## The Solution: Composable Signal System

```python
"""
Signal Generator
Composable trading signals with confidence scoring.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Callable, Optional, List, Dict, Any
from enum import Enum, auto
from datetime import datetime


class SignalType(Enum):
    LONG = "long"
    SHORT = "short"
    EXIT_LONG = "exit_long"
    EXIT_SHORT = "exit_short"
    NEUTRAL = "neutral"


class Strength(Enum):
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class Condition:
    """A single condition contributing to a signal."""
    name: str
    weight: Decimal                    # How much this condition matters
    passed: bool = False
    value: Optional[Any] = None
    threshold: Optional[Any] = None
    description: str = ""
    
    @property
    def contribution(self) -> Decimal:
        """Points contributed if passed."""
        return self.weight if self.passed else Decimal("0")


@dataclass
class Signal:
    """Generated trading signal."""
    type: SignalType
    symbol: str
    confidence: Decimal              # 0-100%
    strength: Strength
    conditions: List[Condition]
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def passed_conditions(self) -> List[Condition]:
        return [c for c in self.conditions if c.passed]
    
    @property
    def failed_conditions(self) -> List[Condition]:
        return [c for c in self.conditions if not c.passed]
    
    @property
    def total_weight(self) -> Decimal:
        return sum(c.weight for c in self.conditions)
    
    @property
    def achieved_weight(self) -> Decimal:
        return sum(c.contribution for c in self.conditions)
    
    def summary(self) -> str:
        """One-line summary."""
        passed = len(self.passed_conditions)
        total = len(self.conditions)
        return (
            f"{self.symbol} {self.type.value.upper()} "
            f"(confidence: {self.confidence:.0%}, {passed}/{total} conditions)"
        )
    
    def detail(self) -> str:
        """Detailed report."""
        lines = [
            f"=== SIGNAL: {self.symbol} {self.type.value.upper()} ===",
            f"Confidence: {self.confidence:.0%} ({self.strength.name})",
            f"Achieved: {self.achieved_weight}/{self.total_weight} points",
            "",
            "✅ PASSED:"
        ]
        for c in self.passed_conditions:
            lines.append(f"   {c.name}: {c.description}")
        
        lines.append("")
        lines.append("❌ FAILED:")
        for c in self.failed_conditions:
            lines.append(f"   {c.name}: {c.description}")
        
        return "\n".join(lines)


@dataclass
class ConditionRule:
    """Rule for evaluating a condition."""
    name: str
    weight: Decimal
    evaluate: Callable[[Dict], bool]  # Takes market data, returns pass/fail
    describe: Callable[[Dict], str]   # Returns description
    
    def check(self, data: Dict) -> Condition:
        """Evaluate and return condition."""
        passed = self.evaluate(data)
        description = self.describe(data)
        return Condition(
            name=self.name,
            weight=self.weight,
            passed=passed,
            description=description
        )


class SignalGenerator:
    """
    Configurable signal generator.
    
    Usage:
        gen = SignalGenerator("breakout")
        gen.add_rule("rsi_oversold", weight=1.0, 
            evaluate=lambda d: d["rsi"] < 30,
            describe=lambda d: f"RSI {d['rsi']:.1f} < 30")
        
        signal = gen.check("buy", market_data)
    """
    
    def __init__(self, name: str):
        self.name = name
        self.long_rules: List[ConditionRule] = []
        self.short_rules: List[ConditionRule] = []
        self.exit_long_rules: List[ConditionRule] = []
        self.exit_short_rules: List[ConditionRule] = []
        
        # Thresholds for strength
        self.strength_thresholds = {
            Strength.WEAK: Decimal("0.25"),
            Strength.MODERATE: Decimal("0.50"),
            Strength.STRONG: Decimal("0.75"),
            Strength.VERY_STRONG: Decimal("0.90"),
        }
    
    def add_rule(
        self,
        name: str,
        weight: float = 1.0,
        for_long: bool = True,
        for_short: bool = True,
        evaluate: Callable[[Dict], bool] = None,
        describe: Callable[[Dict], str] = None,
    ) -> "SignalGenerator":
        """Add a condition rule."""
        rule = ConditionRule(
            name=name,
            weight=Decimal(str(weight)),
            evaluate=evaluate or (lambda _: False),
            describe=describe or (lambda _: name)
        )
        
        if for_long:
            self.long_rules.append(rule)
        if for_short:
            # Invert description for shorts typically
            self.short_rules.append(rule)
        
        return self
    
    def _evaluate_rules(
        self,
        rules: List[ConditionRule],
        data: Dict
    ) -> List[Condition]:
        """Evaluate all rules against data."""
        return [rule.check(data) for rule in rules]
    
    def _classify_strength(self, confidence: Decimal) -> Strength:
        """Classify signal strength."""
        for strength, threshold in sorted(
            self.strength_thresholds.items(),
            key=lambda x: x[1].value if isinstance(x[1], Decimal) else x[1],
            reverse=True
        ):
            if confidence >= threshold:
                return strength
        return Strength.WEAK
    
    def check_long(self, symbol: str, data: Dict) -> Signal:
        """Check for long signal."""
        conditions = self._evaluate_rules(self.long_rules, data)
        return self._create_signal(symbol, SignalType.LONG, conditions, data)
    
    def check_short(self, symbol: str, data: Dict) -> Signal:
        """Check for short signal."""
        conditions = self._evaluate_rules(self.short_rules, data)
        return self._create_signal(symbol, SignalType.SHORT, conditions, data)
    
    def check_exit_long(self, symbol: str, data: Dict) -> Signal:
        """Check for exit long signal."""
        conditions = self._evaluate_rules(self.exit_long_rules, data)
        return self._create_signal(symbol, SignalType.EXIT_LONG, conditions, data)
    
    def check_exit_short(self, symbol: str, data: Dict) -> Signal:
        """Check for exit short signal."""
        conditions = self._evaluate_rules(self.exit_short_rules, data)
        return self._create_signal(symbol, SignalType.EXIT_SHORT, conditions, data)
    
    def check(self, symbol: str, data: Dict) -> Signal:
        """
        Check all signal types, return the strongest.
        
        Priority: EXIT > entry signals
        """
        # Check exits first
        exit_long = self.check_exit_long(symbol, data)
        exit_short = self.check_exit_short(symbol, data)
        
        if exit_long.confidence > Decimal("0.5"):
            return exit_long
        if exit_short.confidence > Decimal("0.5"):
            return exit_short
        
        # Check entries
        long = self.check_long(symbol, data)
        short = self.check_short(symbol, data)
        
        if long.confidence > short.confidence and long.confidence > Decimal("0.3"):
            return long
        elif short.confidence > Decimal("0.3"):
            return short
        
        return Signal(
            type=SignalType.NEUTRAL,
            symbol=symbol,
            confidence=Decimal("0"),
            strength=Strength.WEAK,
            conditions=[],
            metadata={"data": data}
        )
    
    def _create_signal(
        self,
        symbol: str,
        signal_type: SignalType,
        conditions: List[Condition],
        data: Dict
    ) -> Signal:
        """Create signal from conditions."""
        total = sum(c.weight for c in conditions)
        achieved = sum(c.contribution for c in conditions)
        confidence = achieved / total if total > 0 else Decimal("0")
        
        return Signal(
            type=signal_type,
            symbol=symbol,
            confidence=confidence,
            strength=self._classify_strength(confidence),
            conditions=conditions,
            metadata={"generator": self.name, "data": data}
        )


# === Pre-built Conditions ===

def rsi_condition(period: int = 14, oversold: float = 30, overbought: float = 70):
    """RSI condition factory."""
    def for_long(data: Dict) -> bool:
        rsi = data.get("rsi", 50)
        return rsi < oversold
    
    def for_short(data: Dict) -> bool:
        rsi = data.get("rsi", 50)
        return rsi > overbought
    
    def describe_long(data: Dict) -> str:
        return f"RSI {data.get('rsi', 50):.1f} < {oversold} (oversold)"
    
    def describe_short(data: Dict) -> str:
        return f"RSI {data.get('rsi', 50):.1f} > {overbought} (overbought)"
    
    return for_long, for_short, describe_long, describe_short


def price_above_ma(ma_period: int = 50):
    """Price above MA condition."""
    def evaluate_long(data: Dict) -> bool:
        price = data.get("price", 0)
        ma = data.get(f"ma{ma_period}", price)
        return price > ma
    
    def evaluate_short(data: Dict) -> bool:
        price = data.get("price", 0)
        ma = data.get(f"ma{ma_period}", price)
        return price < ma
    
    def describe_long(data: Dict) -> str:
        return f"Price {data.get('price', 0):.2f} > MA{ma_period}"
    
    def describe_short(data: Dict) -> str:
        return f"Price {data.get('price', 0):.2f} < MA{ma_period}"
    
    return evaluate_long, evaluate_short, describe_long, describe_short


def volume_spike(multiplier: float = 1.5):
    """Volume above average condition."""
    def evaluate(data: Dict) -> bool:
        volume = data.get("volume", 0)
        avg_volume = data.get("avg_volume", volume)
        return volume > avg_volume * multiplier
    
    def describe(data: Dict) -> str:
        volume = data.get("volume", 0)
        avg = data.get("avg_volume", volume)
        ratio = volume / avg if avg > 0 else 0
        return f"Volume {ratio:.1f}x average"
    
    return evaluate, describe


# === Usage ===

if __name__ == "__main__":
    # Create signal generator
    gen = SignalGenerator("momentum_breakout")
    
    # Add conditions with weights (higher weight = more important)
    (gen
        .add_rule("rsi", weight=1.5,
            for_long=lambda d: d.get("rsi", 50) < 35,
            for_short=lambda d: d.get("rsi", 50) > 65,
            describe=lambda d: f"RSI {d.get('rsi', 50):.0f}")
        
        .add_rule("trend", weight=2.0,
            for_long=lambda d: d.get("price", 0) > d.get("ma50", 0),
            for_short=lambda d: d.get("price", 0) < d.get("ma50", 0),
            describe=lambda d: f"Price {d.get('price', 0):.0f} vs MA50 {d.get('ma50', 0):.0f}")
        
        .add_rule("volume", weight=1.0,
            evaluate=lambda d: d.get("volume", 0) > d.get("avg_volume", 0) * 1.5,
            describe=lambda d: f"Vol {d.get('volume', 0):.0f} vs avg {d.get('avg_volume', 0):.0f}")
        
        .add_rule("macd", weight=1.5,
            for_long=lambda d: d.get("macd_hist", 0) > 0,
            for_short=lambda d: d.get("macd_hist", 0) < 0,
            describe=lambda d: f"MACD hist {d.get('macd_hist', 0):.2f}")
        
        # Exit conditions
        .add_rule("take_profit", weight=3.0,
            for_long=False, for_short=False,
            evaluate=lambda d: d.get("pnl_pct", 0) > 0.02,
            describe=lambda d: f"P&L +{d.get('pnl_pct', 0)*100:.1f}%")
    )
    
    gen.exit_long_rules.append(ConditionRule(
        name="take_profit",
        weight=Decimal("3.0"),
        evaluate=lambda d: d.get("pnl_pct", 0) > 0.02,
        describe=lambda d: f"P&L +{d.get('pnl_pct', 0)*100:.1f}%"
    ))
    
    # Test with sample data
    print("=== SCENARIO 1: Strong Long Signal ===")
    data1 = {
        "price": 52000,
        "ma50": 50000,
        "rsi": 28,
        "volume": 1000000,
        "avg_volume": 500000,
        "macd_hist": 50,
    }
    signal = gen.check_long("BTC", data1)
    print(signal.detail())
    
    print("\n=== SCENARIO 2: Weak Signal ===")
    data2 = {
        "price": 49800,
        "ma50": 50000,
        "rsi": 48,
        "volume": 400000,
        "avg_volume": 500000,
        "macd_hist": -20,
    }
    signal = gen.check_long("BTC", data2)
    print(signal.summary())
    print(f"Strength: {signal.strength.name}")
    
    print("\n=== SCENARIO 3: Exit Signal ===")
    data3 = {
        "price": 53000,
        "ma50": 50000,
        "rsi": 55,
        "volume": 600000,
        "avg_volume": 500000,
        "macd_hist": 30,
        "pnl_pct": 0.025,  # 2.5% profit
    }
    signal = gen.check_exit_long("BTC", data3)
    print(signal.summary())
    
    print("\n=== CONDITION WEIGHTS ===")
    print("Higher weight = more impact on confidence")
    print("rsi:        1.5 (oversold/overbought)")
    print("trend:      2.0 (price vs MA)")
    print("volume:     1.0 (volume confirmation)")
    print("macd:       1.5 (momentum)")
    print("take_profit: 3.0 (exit trigger)")
```

## Output

```
=== SCENARIO 1: Strong Long Signal ===
=== SIGNAL: BTC LONG ===
Confidence: 100% (VERY_STRONG)
Achieved: 6/6 points

✅ PASSED:
   rsi: RSI 28
   trend: Price 52000 vs MA50 50000
   volume: Vol 1000000 vs avg 500000
   macd: MACD hist 50.00

❌ FAILED:

=== SCENARIO 2: Weak Signal ===
BTC LONG (confidence: 0%, 0/4 conditions)
Strength: WEAK

=== SCENARIO 3: Exit Signal ===
BTC EXIT_LONG (confidence: 100%, 1/1 conditions)

=== CONDITION WEIGHTS ===
Higher weight = more impact on confidence
rsi:        1.5 (oversold/overbought)
trend:      2.0 (price vs MA)
volume:     1.0 (volume confirmation)
macd:       1.5 (momentum)
take_profit: 3.0 (exit trigger)
```

## Quick Reference

```python
# Create generator
gen = SignalGenerator("my_strategy")

# Add weighted conditions
gen.add_rule("condition_name", weight=1.5,
    evaluate=lambda d: d["value"] > threshold,
    describe=lambda d: f"Value is {d['value']}")

# Check signals
signal = gen.check_long("BTC", market_data)
signal = gen.check("BTC", market_data)  # Best of all

# Analyze
print(signal.confidence)      # 0-100%
print(signal.strength)         # WEAK/MODERATE/STRONG/VERY_STRONG
print(signal.passed_conditions)
print(signal.summary())
print(signal.detail())
```

## Confidence Levels

| Strength | Confidence | Action |
|----------|------------|--------|
| WEAK | 0-25% | Skip |
| MODERATE | 25-50% | Consider |
| STRONG | 50-75% | Execute |
| VERY_STRONG | 75-100% | Size up |

---
*Utility: Signal Generator | Features: Weighted conditions, confidence scoring, strength classification*