# Strategy Pattern (Pluggable Algorithms)

**Pattern:** Swap algorithms at runtime without changing client code  
**Perfect for:** Trading strategies, risk models, execution algorithms

## The Pattern

```python
"""
Strategy Pattern for Trading
Swap entry, exit, sizing, and risk algorithms at runtime.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional, Literal
from datetime import datetime


@dataclass
class MarketData:
    """Current market state."""
    symbol: str
    price: float
    volume: float
    timestamp: datetime
    indicators: Dict[str, float]  # RSI, MACD, etc.


@dataclass
class Signal:
    """Trading signal from a strategy."""
    action: Literal["buy", "sell", "hold"]
    confidence: float  # 0.0 to 1.0
    reason: str
    suggested_size: Optional[float] = None


# === Strategy Interface ===

class EntryStrategy(ABC):
    """Abstract base for entry strategies."""
    
    @abstractmethod
    def generate_signal(self, data: MarketData, position: Optional[Dict]) -> Signal:
        """Generate entry signal."""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Strategy name for logging."""
        pass


class ExitStrategy(ABC):
    """Abstract base for exit strategies."""
    
    @abstractmethod
    def should_exit(self, data: MarketData, position: Dict) -> Signal:
        """Determine if position should be closed."""
        pass


class PositionSizingStrategy(ABC):
    """Abstract base for sizing strategies."""
    
    @abstractmethod
    def calculate_size(self, account: float, risk: float, data: MarketData) -> float:
        """Calculate position size."""
        pass


# === Concrete Strategies ===

class RSIEntryStrategy(EntryStrategy):
    """Enter on RSI oversold/overbought."""
    
    def __init__(self, oversold: float = 30, overbought: float = 70):
        self.oversold = oversold
        self.overbought = overbought
    
    def generate_signal(self, data: MarketData, position: Optional[Dict]) -> Signal:
        rsi = data.indicators.get("rsi", 50)
        
        if rsi < self.oversold:
            return Signal(
                action="buy",
                confidence=(self.oversold - rsi) / self.oversold,
                reason=f"RSI oversold ({rsi:.1f})"
            )
        elif rsi > self.overbought:
            return Signal(
                action="sell",
                confidence=(rsi - self.overbought) / (100 - self.overbought),
                reason=f"RSI overbought ({rsi:.1f})"
            )
        
        return Signal(action="hold", confidence=0, reason="RSI neutral")
    
    def get_name(self) -> str:
        return f"RSI({self.oversold},{self.overbought})"


class MACDEntryStrategy(EntryStrategy):
    """Enter on MACD crossover."""
    
    def generate_signal(self, data: MarketData, position: Optional[Dict]) -> Signal:
        macd = data.indicators.get("macd", 0)
        signal = data.indicators.get("macd_signal", 0)
        
        if macd > signal and macd > 0:
            return Signal(
                action="buy",
                confidence=min(abs(macd - signal) / 0.5, 1.0),
                reason="MACD bullish crossover"
            )
        elif macd < signal and macd < 0:
            return Signal(
                action="sell",
                confidence=min(abs(macd - signal) / 0.5, 1.0),
                reason="MACD bearish crossover"
            )
        
        return Signal(action="hold", confidence=0, reason="MACD no signal")
    
    def get_name(self) -> str:
        return "MACD"


class BreakoutEntryStrategy(EntryStrategy):
    """Enter on price breakout above/below levels."""
    
    def __init__(self, lookback: int = 20):
        self.lookback = lookback
        self.highs: List[float] = []
        self.lows: List[float] = []
    
    def generate_signal(self, data: MarketData, position: Optional[Dict]) -> Signal:
        self.highs.append(data.price)
        self.lows.append(data.price)
        
        if len(self.highs) > self.lookback:
            self.highs.pop(0)
            self.lows.pop(0)
        
        if len(self.highs) < self.lookback:
            return Signal(action="hold", confidence=0, reason="Gathering data")
        
        highest = max(self.highs)
        lowest = min(self.lows)
        
        if data.price > highest * 0.995:  # Within 0.5% of high
            return Signal(
                action="buy",
                confidence=0.8,
                reason=f"Breakout above ${highest:.2f}"
            )
        elif data.price < lowest * 1.005:  # Within 0.5% of low
            return Signal(
                action="sell",
                confidence=0.8,
                reason=f"Breakdown below ${lowest:.2f}"
            )
        
        return Signal(action="hold", confidence=0, reason="In range")
    
    def get_name(self) -> str:
        return f"Breakout({self.lookback})"


class FixedRRExitStrategy(ExitStrategy):
    """Exit at fixed risk:reward ratio."""
    
    def __init__(self, take_profit_rr: float = 2.0, stop_loss_rr: float = 1.0):
        self.tp_rr = take_profit_rr
        self.sl_rr = stop_loss_rr
    
    def should_exit(self, data: MarketData, position: Dict) -> Signal:
        entry = position["entry_price"]
        direction = position["direction"]
        current = data.price
        
        if direction == "long":
            # Calculate R
            risk = position.get("risk_amount", entry * 0.02)
            pnl = current - entry
            r = pnl / risk if risk > 0 else 0
            
            if r >= self.tp_rr:
                return Signal(action="sell", confidence=1.0, reason=f"Target {self.tp_rr}R reached")
            elif r <= -self.sl_rr:
                return Signal(action="sell", confidence=1.0, reason=f"Stop {-self.sl_rr}R hit")
        else:  # short
            risk = position.get("risk_amount", entry * 0.02)
            pnl = entry - current
            r = pnl / risk if risk > 0 else 0
            
            if r >= self.tp_rr:
                return Signal(action="buy", confidence=1.0, reason=f"Target {self.tp_rr}R reached")
            elif r <= -self.sl_rr:
                return Signal(action="buy", confidence=1.0, reason=f"Stop {-self.sl_rr}R hit")
        
        return Signal(action="hold", confidence=0, reason="Within R bounds")


class TrailingStopExitStrategy(ExitStrategy):
    """Trailing stop that moves with favorable price."""
    
    def __init__(self, activation_r: float = 1.0, trail_pct: float = 0.02):
        self.activation_r = activation_r
        self.trail_pct = trail_pct
        self.max_favorable: Optional[float] = None
    
    def should_exit(self, data: MarketData, position: Dict) -> Signal:
        entry = position["entry_price"]
        direction = position["direction"]
        current = data.price
        
        if direction == "long":
            # Track highest price
            if self.max_favorable is None or current > self.max_favorable:
                self.max_favorable = current
            
            # Check if activated
            activation_price = entry * (1 + self.activation_r * 0.02)
            if current < self.max_favorable * (1 - self.trail_pct) and current > activation_price:
                return Signal(action="sell", confidence=1.0, 
                            reason=f"Trailing stop hit (${self.max_favorable:.2f} → ${current:.2f})")
        
        return Signal(action="hold", confidence=0, reason="Trailing active")


class FixedPctSizingStrategy(PositionSizingStrategy):
    """Risk fixed % of account per trade."""
    
    def __init__(self, risk_pct: float = 1.0):
        self.risk_pct = risk_pct
    
    def calculate_size(self, account: float, risk: float, data: MarketData) -> float:
        risk_amount = account * (self.risk_pct / 100)
        return risk_amount / risk if risk > 0 else 0


class KellySizingStrategy(PositionSizingStrategy):
    """Size using Kelly Criterion."""
    
    def __init__(self, win_rate: float = 0.55, payoff: float = 2.0, fraction: float = 0.25):
        self.win_rate = win_rate
        self.payoff = payoff
        self.fraction = fraction
        # Kelly = (p*b - q) / b
        edge = win_rate * payoff - (1 - win_rate)
        self.kelly = (edge / payoff) * fraction if payoff > 0 else 0
    
    def calculate_size(self, account: float, risk: float, data: MarketData) -> float:
        position_value = account * self.kelly
        return position_value / data.price if data.price > 0 else 0


# === Trading Engine (Strategy Context) ===

class TradingEngine:
    """
    Uses strategies to make trading decisions.
    Strategies can be swapped at runtime.
    """
    
    def __init__(
        self,
        entry_strategy: EntryStrategy,
        exit_strategy: ExitStrategy,
        sizing_strategy: PositionSizingStrategy,
        account: float = 100000
    ):
        self.entry = entry_strategy
        self.exit = exit_strategy
        self.sizing = sizing_strategy
        self.account = account
        self.position: Optional[Dict] = None
        self.trades: List[Dict] = []
    
    def set_strategy(self, strategy_type: str, strategy: ABC):
        """Swap strategy at runtime."""
        if strategy_type == "entry":
            self.entry = strategy
        elif strategy_type == "exit":
            self.exit = strategy
        elif strategy_type == "sizing":
            self.sizing = strategy
        print(f"Switched to {strategy.get_name() if hasattr(strategy, 'get_name') else strategy.__class__.__name__}")
    
    def on_data(self, data: MarketData):
        """Process new market data."""
        # Check exit first (if in position)
        if self.position:
            exit_signal = self.exit.should_exit(data, self.position)
            if exit_signal.action != "hold":
                self._close_position(data, exit_signal)
                return
        
        # Check entry (if flat)
        if not self.position:
            signal = self.entry.generate_signal(data, None)
            if signal.action in ["buy", "sell"]:
                self._open_position(data, signal)
    
    def _open_position(self, data: MarketData, signal: Signal):
        """Open new position."""
        direction = "long" if signal.action == "buy" else "short"
        
        # Calculate size
        risk = data.price * 0.02  # Assume 2% stop
        size = self.sizing.calculate_size(self.account, risk, data)
        
        self.position = {
            "symbol": data.symbol,
            "direction": direction,
            "entry_price": data.price,
            "size": size,
            "risk_amount": self.account * 0.01,
            "entry_time": data.timestamp,
            "entry_reason": signal.reason
        }
        
        print(f"ENTRY: {direction} {size:.0f} {data.symbol} @ ${data.price:.2f} ({signal.reason})")
    
    def _close_position(self, data: MarketData, signal: Signal):
        """Close existing position."""
        if not self.position:
            return
        
        pnl = (data.price - self.position["entry_price"]) * self.position["size"]
        if self.position["direction"] == "short":
            pnl = -pnl
        
        self.account += pnl
        
        print(f"EXIT: {self.position['direction']} {self.position['symbol']} @ ${data.price:.2f}")
        print(f"      P&L: ${pnl:.2f} | Reason: {signal.reason}")
        print(f"      Account: ${self.account:.2f}")
        
        self.trades.append({
            **self.position,
            "exit_price": data.price,
            "exit_time": data.timestamp,
            "pnl": pnl,
            "exit_reason": signal.reason
        })
        
        self.position = None
    
    def get_stats(self) -> Dict:
        """Generate performance stats."""
        if not self.trades:
            return {}
        
        wins = [t for t in self.trades if t["pnl"] > 0]
        return {
            "trades": len(self.trades),
            "win_rate": len(wins) / len(self.trades),
            "total_pnl": sum(t["pnl"] for t in self.trades),
            "final_account": self.account
        }


# === Example: Runtime Strategy Switching ===

if __name__ == "__main__":
    from datetime import datetime, timedelta
    import random
    
    print("=" * 70)
    print("Strategy Pattern Demo: Runtime Strategy Switching")
    print("=" * 70)
    
    # Create engine with RSI strategy
    engine = TradingEngine(
        entry_strategy=RSIEntryStrategy(oversold=30, overbought=70),
        exit_strategy=FixedRRExitStrategy(take_profit_rr=2.0),
        sizing_strategy=FixedPctSizingStrategy(risk_pct=1.0),
        account=100000
    )
    
    # Simulate market data
    base_time = datetime.now()
    price = 100
    
    print("\n--- Phase 1: RSI Strategy ---")
    for i in range(20):
        # Oscillate price for RSI signals
        price = 100 + 10 * (i % 4 - 1.5) + random.uniform(-2, 2)
        
        data = MarketData(
            symbol="AAPL",
            price=price,
            volume=1000,
            timestamp=base_time + timedelta(minutes=i),
            indicators={
                "rsi": 20 + 60 * ((i % 4) / 3),  # Oscillate 20-80
                "macd": random.uniform(-1, 1)
            }
        )
        engine.on_data(data)
    
    print("\n--- Switching to MACD Strategy ---")
    engine.set_strategy("entry", MACDEntryStrategy())
    
    for i in range(20, 40):
        price = 100 + (i - 20) * 0.5 + random.uniform(-1, 1)  # Trend up
        
        data = MarketData(
            symbol="AAPL",
            price=price,
            volume=1000,
            timestamp=base_time + timedelta(minutes=i),
            indicators={
                "rsi": 50,
                "macd": 0.5 + (i - 20) * 0.1,  # Rising MACD
                "macd_signal": 0.3 + (i - 20) * 0.05
            }
        )
        engine.on_data(data)
    
    print("\n--- Switching to Breakout Strategy ---")
    engine.set_strategy("entry", BreakoutEntryStrategy(lookback=10))
    
    for i in range(40, 60):
        price = 110 + random.uniform(-5, 5)  # Range
        
        data = MarketData(
            symbol="AAPL",
            price=price,
            volume=1000,
            timestamp=base_time + timedelta(minutes=i),
            indicators={"rsi": 50}
        )
        engine.on_data(data)
    
    # Results
    print("\n" + "=" * 70)
    print("Final Statistics")
    print("=" * 70)
    stats = engine.get_stats()
    for k, v in stats.items():
        print(f"{k}: {v}")


## Strategy Pattern Benefits

| Benefit | Example |
|---------|---------|
| **Interchangeable** | Swap RSI → MACD without changing engine |
| **Testable** | Test each strategy in isolation |
| **Composable** | Mix entry, exit, sizing independently |
| **Extensible** | Add new strategy without touching existing code |

## When to Use

- ✅ Multiple algorithms for same problem (entries, exits, sizing)
- ✅ Need to switch at runtime (market regime change)
- ✅ Want to backtest different strategies
- ✅ Team develops strategies independently

## Real-World Application

```python
# Morning: Use trend strategy
engine.set_strategy("entry", MACDEntryStrategy())

# Afternoon chop: Switch to mean reversion  
engine.set_strategy("entry", RSIEntryStrategy())

# High volatility: Switch to breakout
engine.set_strategy("entry", BreakoutEntryStrategy())

# Always use same exit and sizing
# Exit and sizing strategies remain constant
```

---

**Created by Ghost 👻 | Feb 19, 2026 | 14-min learning sprint**  
*Pattern: Define the family of algorithms, encapsulate each one, and make them interchangeable.*
