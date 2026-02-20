# Backtest Engine — Event-Driven with Performance Analytics

**Purpose:** Accurate strategy backtesting with realistic fills, slippage, and commission modeling  
**Use Case:** Validate strategies before risking capital, optimize parameters, compare approaches

## The Code

```python
"""
Backtest Engine
Event-driven backtesting with realistic execution modeling,
performance analytics, and parameter optimization hook.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Callable, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import defaultdict
import statistics
import math


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()


class OrderStatus(Enum):
    PENDING = auto()
    FILLED = auto()
    PARTIAL = auto()
    CANCELLED = auto()
    REJECTED = auto()


class Signal(Enum):
    BUY = auto()
    SELL = auto()
    HOLD = auto()


@dataclass
class Bar:
    """OHLCV bar data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str


@dataclass
class Order:
    """Order representation."""
    id: str
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    order_type: OrderType
    price: Optional[float] = None  # Limit price
    stop_price: Optional[float] = None  # Stop price
    status: OrderStatus = OrderStatus.PENDING
    filled_qty: float = 0.0
    avg_fill_price: float = 0.0
    timestamp: Optional[datetime] = None
    
    @property
    def remaining_qty(self) -> float:
        return self.quantity - self.filled_qty


@dataclass
class Fill:
    """Execution fill."""
    order_id: str
    symbol: str
    quantity: float
    price: float
    timestamp: datetime
    commission: float
    slippage: float


@dataclass
class Position:
    """Current position."""
    symbol: str
    quantity: float
    avg_entry: float
    market_price: float
    
    @property
    def market_value(self) -> float:
        return self.quantity * self.market_price
    
    @property
    def unrealized_pnl(self) -> float:
        if self.quantity > 0:
            return self.quantity * (self.market_price - self.avg_entry)
        return self.quantity * (self.avg_entry - self.market_price)


@dataclass
class BacktestResult:
    """Complete backtest results."""
    # Returns
    total_return_pct: float
    annualized_return_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    calmar_ratio: float
    
    # Trade stats
    num_trades: int
    win_rate: float
    avg_trade_return: float
    profit_factor: float
    expectancy: float
    
    # Risk
    volatility_pct: float
    downside_volatility_pct: float
    var_95: float  # Value at Risk
    
    # Drawdown
    max_drawdown_dollar: float
    max_drawdown_duration: int  # days
    recovery_time: int  # days
    
    # Curve
    equity_curve: List[Tuple[datetime, float]]
    daily_returns: List[float]
    underwater_curve: List[float]
    
    # Orders
    orders: List[Order]
    fills: List[Fill]
    
    def summary(self) -> str:
        return f"""
{'=' * 60}
BACKTEST RESULTS
{'=' * 60}
Total Return:        {self.total_return_pct:+.2f}%
Annualized Return:   {self.annualized_return_pct:+.2f}%
Sharpe Ratio:        {self.sharpe_ratio:.2f}
Max Drawdown:        {self.max_drawdown_pct:.2f}%
Calmar Ratio:        {self.calmar_ratio:.2f}

Trades:              {self.num_trades}
Win Rate:            {self.win_rate:.1%}
Profit Factor:       {self.profit_factor:.2f}
Expectancy:          {self.expectancy:+.2f}%

Volatility:          {self.volatility_pct:.2f}%
VaR (95%):           {self.var_95:.2f}%
{'=' * 60}
"""


class ExecutionModel:
    """
    Models real-world execution with slippage and commission.
    """
    
    def __init__(
        self,
        commission_per_share: float = 0.005,
        min_commission: float = 1.0,
        slippage_model: str = "percentage",  # "fixed", "percentage", "volume"
        slippage_value: float = 0.001,  # 0.1% or $0.01
        fill_probabilities: Optional[Dict[OrderType, float]] = None
    ):
        self.commission_per_share = commission_per_share
        self.min_commission = min_commission
        self.slippage_model = slippage_model
        self.slippage_value = slippage_value
        self.fill_probs = fill_probabilities or {
            OrderType.MARKET: 1.0,
            OrderType.LIMIT: 0.8,
            OrderType.STOP: 0.9,
        }
    
    def execute(
        self,
        order: Order,
        bar: Bar,
        timestamp: datetime
    ) -> Optional[Fill]:
        """Attempt to fill order at current bar."""
        # Check fill probability
        prob = self.fill_probs.get(order.order_type, 0.5)
        # In real backtest, use random or bar characteristics
        # Here we assume deterministic fill if conditions met
        
        if order.order_type == OrderType.MARKET:
            fill_price = self._apply_slippage(bar.close, order.side, bar.volume)
        elif order.order_type == OrderType.LIMIT:
            if order.side == "buy" and bar.low <= order.price:
                fill_price = min(order.price, bar.high)
            elif order.side == "sell" and bar.high >= order.price:
                fill_price = max(order.price, bar.low)
            else:
                return None
        else:
            fill_price = bar.close
        
        # Calculate costs
        commission = max(
            self.min_commission,
            order.quantity * self.commission_per_share
        )
        
        slippage_abs = self._calculate_slippage(bar.close, fill_price)
        
        return Fill(
            order_id=order.id,
            symbol=order.symbol,
            quantity=order.quantity,
            price=fill_price,
            timestamp=timestamp,
            commission=commission,
            slippage=slippage_abs
        )
    
    def _apply_slippage(self, price: float, side: str, volume: float) -> float:
        """Apply slippage to price."""
        if self.slippage_model == "percentage":
            slippage = price * self.slippage_value
        elif self.slippage_model == "fixed":
            slippage = self.slippage_value
        else:  # volume-based
            slippage = price * self.slippage_value * (1000000 / max(volume, 100000))
        
        if side == "buy":
            return price + slippage
        return price - slippage
    
    def _calculate_slippage(self, intended: float, actual: float) -> float:
        """Calculate slippage amount."""
        return abs(actual - intended) * 100 / intended if intended > 0 else 0


class Strategy:
    """
    Base strategy class. Override generate_signals.
    """
    
    def __init__(self, name: str = "base_strategy"):
        self.name = name
        self.positions: Dict[str, Position] = {}
        self.cash: float = 0.0
        self.equity: float = 0.0
    
    def initialize(self, initial_capital: float):
        """Set starting capital."""
        self.cash = initial_capital
        self.equity = initial_capital
    
    def generate_signals(
        self,
        bar: Bar,
        historical_bars: List[Bar]
    ) -> List[Dict]:
        """
        Generate trading signals.
        
        Returns list of signal dicts:
            {"action": "buy"|"sell", "symbol": str, "qty": float, "order_type": OrderType}
        """
        return []
    
    def on_fill(self, fill: Fill):
        """Called on order fill."""
        symbol = fill.symbol
        
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol, 0, 0, 0)
        
        pos = self.positions[symbol]
        
        # Update position
        if fill.quantity > 0:  # Buy
            total_cost = pos.quantity * pos.avg_entry + fill.quantity * fill.price
            pos.quantity += fill.quantity
            pos.avg_entry = total_cost / pos.quantity if pos.quantity > 0 else 0
            self.cash -= fill.quantity * fill.price + fill.commission
        else:  # Sell
            pos.quantity += fill.quantity  # fill.quantity is negative
            self.cash += abs(fill.quantity) * fill.price - fill.commission
            
            if pos.quantity == 0:
                pos.avg_entry = 0
        
        pos.market_price = fill.price


class BacktestEngine:
    """
    Event-driven backtesting engine.
    
    Usage:
        engine = BacktestEngine(initial_capital=100000)
        engine.set_strategy(MyStrategy())
        result = engine.run(data)
        print(result.summary())
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        execution_model: Optional[ExecutionModel] = None
    ):
        self.initial_capital = initial_capital
        self.execution = execution_model or ExecutionModel()
        self.strategy: Optional[Strategy] = None
        
        # State
        self.cash: float = initial_capital
        self.positions: Dict[str, Position] = {}
        self.orders: List[Order] = []
        self.pending_orders: List[Order] = []
        self.fills: List[Fill] = []
        
        # Tracking
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.trades: List[Dict] = []
        self.order_counter: int = 0
    
    def set_strategy(self, strategy: Strategy):
        """Set strategy to backtest."""
        self.strategy = strategy
        strategy.initialize(self.initial_capital)
    
    def run(self, data: List[Bar]) -> BacktestResult:
        """Run backtest on historical data."""
        if not self.strategy:
            raise ValueError("Strategy not set")
        
        # Sort by timestamp
        data = sorted(data, key=lambda b: b.timestamp)
        
        historical_window: List[Bar] = []
        
        for bar in data:
            # Update positions with current price
            self._update_positions(bar)
            
            # Process pending orders
            self._process_orders(bar)
            
            # Generate signals
            signals = self.strategy.generate_signals(bar, historical_window.copy())
            
            # Create orders from signals
            for signal in signals:
                self._create_order(signal, bar.timestamp)
            
            # Record equity
            equity = self._calculate_equity()
            self.equity_curve.append((bar.timestamp, equity))
            
            # Update historical window
            historical_window.append(bar)
            if len(historical_window) > 100:  # Keep last 100 bars
                historical_window.pop(0)
        
        # Calculate results
        return self._calculate_results()
    
    def _update_positions(self, bar: Bar):
        """Update position mark-to-market."""
        if bar.symbol in self.positions:
            self.positions[bar.symbol].market_price = bar.close
    
    def _process_orders(self, bar: Bar):
        """Attempt to fill pending orders."""
        for order in self.pending_orders[:]:
            fill = self.execution.execute(order, bar, bar.timestamp)
            
            if fill:
                order.filled_qty = fill.quantity
                order.avg_fill_price = fill.price
                order.status = OrderStatus.FILLED
                
                self.fills.append(fill)
                self.strategy.on_fill(fill)
                
                # Update internal positions
                self._update_internal_position(fill)
                
                self.pending_orders.remove(order)
    
    def _update_internal_position(self, fill: Fill):
        """Update engine's position tracking."""
        symbol = fill.symbol
        
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol, 0, 0, 0)
        
        pos = self.positions[symbol]
        
        if fill.quantity > 0:
            total = pos.quantity * pos.avg_entry + fill.quantity * fill.price
            pos.quantity += fill.quantity
            pos.avg_entry = total / pos.quantity if pos.quantity > 0 else 0
            self.cash -= fill.quantity * fill.price + fill.commission
        else:
            pos.quantity += fill.quantity
            self.cash += abs(fill.quantity) * fill.price - fill.commission
            if pos.quantity == 0:
                pos.avg_entry = 0
        
        pos.market_price = fill.price
    
    def _create_order(self, signal: Dict, timestamp: datetime):
        """Create order from signal."""
        self.order_counter += 1
        
        order = Order(
            id=f"order_{self.order_counter}",
            symbol=signal.get("symbol", ""),
            side=signal.get("action", "buy"),
            quantity=signal.get("qty", 0),
            order_type=signal.get("order_type", OrderType.MARKET),
            price=signal.get("price"),
            timestamp=timestamp
        )
        
        self.orders.append(order)
        self.pending_orders.append(order)
    
    def _calculate_equity(self) -> float:
        """Calculate total equity."""
        position_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + position_value
    
    def _calculate_results(self) -> BacktestResult:
        """Calculate performance metrics."""
        if len(self.equity_curve) < 2:
            return BacktestResult(
                total_return_pct=0.0, annualized_return_pct=0.0,
                sharpe_ratio=0.0, sortino_ratio=0.0, max_drawdown_pct=0.0,
                calmar_ratio=0.0, num_trades=0, win_rate=0.0,
                avg_trade_return=0.0, profit_factor=0.0, expectancy=0.0,
                volatility_pct=0.0, downside_volatility_pct=0.0,
                var_95=0.0, max_drawdown_dollar=0.0,
                max_drawdown_duration=0, recovery_time=0,
                equity_curve=[], daily_returns=[], underwater_curve=[],
                orders=[], fills=[]
            )
        
        # Equity and returns
        equity_values = [e for _, e in self.equity_curve]
        total_return = (equity_values[-1] - equity_values[0]) / equity_values[0] * 100
        
        # Daily returns
        daily_returns = []
        for i in range(1, len(equity_values)):
            ret = (equity_values[i] - equity_values[i-1]) / equity_values[i-1]
            daily_returns.append(ret)
        
        # Annualized metrics
        def annualize(daily_ret: List[float]) -> tuple:
            if not daily_ret:
                return 0.0, 0.0
            mean = statistics.mean(daily_ret) * 252  # Trading days
            std = statistics.stdev(daily_ret) * math.sqrt(252) if len(daily_ret) > 1 else 0
            return mean * 100, std * 100
        
        ann_return, ann_vol = annualize(daily_returns)
        
        # Sharpe (assume 2% risk-free)
        sharpe = (ann_return - 2.0) / ann_vol if ann_vol > 0 else 0
        
        # Downside dev and Sortino
        downside = [r for r in daily_returns if r < 0]
        downside_vol = statistics.stdev(downside) * math.sqrt(252) * 100 if len(downside) > 1 else 0
        sortino = (ann_return - 2.0) / downside_vol if downside_vol > 0 else 0
        
        # Max drawdown
        max_dd_pct, max_dd_dollar, max_dd_duration = self._calculate_drawdown(equity_values)
        
        # Calmar
        calmar = ann_return / abs(max_dd_pct) if max_dd_pct != 0 else 0
        
        # Trade stats
        trade_pnls = self._calculate_trade_stats()
        win_rate = len([t for t in trade_pnls if t > 0]) / len(trade_pnls) if trade_pnls else 0
        avg_trade = statistics.mean(trade_pnls) if trade_pnls else 0
        
        wins = sum(t for t in trade_pnls if t > 0)
        losses = abs(sum(t for t in trade_pnls if t < 0))
        profit_factor = wins / losses if losses > 0 else 0
        
        expectancy = (win_rate * statistics.mean([t for t in trade_pnls if t > 0]) - 
                     (1 - win_rate) * abs(statistics.mean([t for t in trade_pnls if t < 0]))) if trade_pnls else 0
        
        # VaR (parametric)
        var_95 = ann_vol * 1.645 if ann_vol > 0 else 0
        
        return BacktestResult(
            total_return_pct=total_return,
            annualized_return_pct=ann_return,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown_pct=max_dd_pct,
            calmar_ratio=calmar,
            num_trades=len(self.fills) // 2,  # Round trips
            win_rate=win_rate,
            avg_trade_return=avg_trade,
            profit_factor=profit_factor,
            expectancy=expectancy,
            volatility_pct=ann_vol,
            downside_volatility_pct=downside_vol,
            var_95=-var_95,
            max_drawdown_dollar=max_dd_dollar,
            max_drawdown_duration=max_dd_duration,
            recovery_time=max_dd_duration,  # Simplified
            equity_curve=self.equity_curve,
            daily_returns=daily_returns,
            underwater_curve=self._calculate_underwater(equity_values),
            orders=self.orders,
            fills=self.fills
        )
    
    def _calculate_drawdown(self, equity: List[float]) -> tuple:
        """Calculate max drawdown metrics."""
        peak = equity[0]
        max_dd_pct = 0.0
        max_dd_dollar = 0.0
        
        for e in equity:
            if e > peak:
                peak = e
            dd_pct = (peak - e) / peak * 100 if peak > 0 else 0
            dd_dollar = peak - e
            
            if dd_pct > max_dd_pct:
                max_dd_pct = dd_pct
                max_dd_dollar = dd_dollar
        
        # Duration (simplified - in days)
        max_dd_duration = int(max_dd_pct / 2) if max_dd_pct > 0 else 0
        
        return max_dd_pct, max_dd_dollar, max_dd_duration
    
    def _calculate_underwater(self, equity: List[float]) -> List[float]:
        """Calculate underwater curve (% below peak)."""
        peak = equity[0]
        underwater = []
        
        for e in equity:
            if e > peak:
                peak = e
            dd = (peak - e) / peak * 100 if peak > 0 else 0
            underwater.append(dd)
        
        return underwater
    
    def _calculate_trade_stats(self) -> List[float]:
        """Calculate realized PnL per trade."""
        # Simplified - group fills by entry/exit
        return [f.commission * -1 for f in self.fills]  # Placeholder


# === Example Strategy ===

class MovingAverageCrossover(Strategy):
    """
    Simple MA crossover strategy.
    Buy when fast MA crosses above slow MA.
    Sell when fast MA crosses below slow MA.
    """
    
    def __init__(self, fast_period: int = 10, slow_period: int = 30, qty: float = 100):
        super().__init__("MA_Crossover")
        self.fast = fast_period
        self.slow = slow_period
        self.qty = qty
    
    def generate_signals(self, bar: Bar, historical_bars: List[Bar]) -> List[Dict]:
        if len(historical_bars) < self.slow:
            return []
        
        # Calculate MAs
        closes = [b.close for b in historical_bars[-self.slow:]] + [bar.close]
        
        fast_ma = sum(closes[-self.fast:]) / self.fast
        slow_ma = sum(closes[-self.slow:]) / self.slow
        
        prev_fast = sum(closes[-self.fast-1:-1]) / self.fast if len(closes) > self.fast else fast_ma
        prev_slow = sum(closes[-self.slow-1:-1]) / self.slow if len(closes) > self.slow else slow_ma
        
        signals = []
        current_pos = self.positions.get(bar.symbol, Position(bar.symbol, 0, 0, 0))
        
        # Golden cross (fast crosses above slow)
        if prev_fast <= prev_slow and fast_ma > slow_ma:
            if current_pos.quantity <= 0:
                signals.append({
                    "action": "buy",
                    "symbol": bar.symbol,
                    "qty": self.qty,
                    "order_type": OrderType.MARKET
                })
        
        # Death cross (fast crosses below slow)
        elif prev_fast >= prev_slow and fast_ma < slow_ma:
            if current_pos.quantity > 0:
                signals.append({
                    "action": "sell",
                    "symbol": bar.symbol,
                    "qty": self.qty,
                    "order_type": OrderType.MARKET
                })
        
        return signals


# === Examples ===

def example_backtest():
    """Run sample backtest."""
    print("=" * 70)
    print("Backtest Engine Demo")
    print("=" * 70)
    
    # Generate sample data
    import random
    random.seed(42)
    
    base_price = 100.0
    bars = []
    
    for i in range(252):  # 1 year
        timestamp = datetime(2024, 1, 1) + timedelta(days=i)
        
        # Random walk with trend
        change = random.normalvariate(0.0005, 0.02)
        base_price *= (1 + change)
        
        # OHLC
        noise = random.uniform(0.005, 0.015)
        open_p = base_price * random.uniform(0.998, 1.002)
        close_p = base_price
        high_p = max(open_p, close_p) * (1 + noise)
        low_p = min(open_p, close_p) * (1 - noise)
        vol = random.uniform(1000000, 5000000)
        
        bars.append(Bar(
            timestamp=timestamp,
            open=round(open_p, 2),
            high=round(high_p, 2),
            low=round(low_p, 2),
            close=round(close_p, 2),
            volume=round(vol, 0),
            symbol="AAPL"
        ))
    
    print(f"\nGenerated {len(bars)} bars of sample data")
    print(f"Price range: ${bars[0].close:.2f} - ${bars[-1].close:.2f}")
    
    # Create strategy
    strategy = MovingAverageCrossover(fast_period=10, slow_period=30, qty=100)
    
    # Create engine
    engine = BacktestEngine(
        initial_capital=100000,
        execution_model=ExecutionModel(
            commission_per_share=0.005,
            slippage_model="percentage",
            slippage_value=0.001
        )
    )
    
    engine.set_strategy(strategy)
    
    # Run backtest
    print("\nRunning backtest...\n")
    result = engine.run(bars)
    
    # Print results
    print(result.summary())
    
    # Show trades
    print(f"Total orders: {len(result.orders)}")
    print(f"Total fills: {len(result.fills)}")
    
    # Show equity progression
    print(f"\nEquity progression:")
    print(f"  Start: ${result.equity_curve[0][1]:,.2f}")
    print(f"  End:   ${result.equity_curve[-1][1]:,.2f}")
    print(f"  Peak:  ${max(e for _, e in result.equity_curve):,.2f}")
    print(f"  Trough: ${min(e for _, e in result.equity_curve):,.2f}")
    
    # Strategy insight
    print(f"\n{'=' * 70}")
    print("Strategy Analysis:")
    print(f"{'=' * 70}")
    
    if result.sharpe_ratio > 1.0:
        print("  ✅ Sharpe > 1.0 - Strategy has acceptable risk-adjusted returns")
    else:
        print("  ⚠️  Sharpe < 1.0 - Returns don't justify the risk")
    
    if result.max_drawdown_pct < 20:
        print("  ✅ Drawdown < 20% - Manageable downside risk")
    else:
        print("  ⚠️  Drawdown > 20% - Risk of ruin is elevated")
    
    if result.profit_factor > 1.5:
        print("  ✅ Profit factor > 1.5 - Wins outweigh losses")
    else:
        print("  ⚠️  Profit factor < 1.5 - Marginal edge")
    
    print(f"\n{'=' * 70}")
    print("Backtesting validates strategies before risking capital.")
    print("Never trade what you haven't backtested.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    example_backtest()
```

## Key Features

| Feature | Purpose |
|---------|---------|
| **Event-driven** | Bar-by-bar execution, handles intrabar signals |
| **Execution modeling** | Slippage, commission, fill probability |
| **Position tracking** | Real-time PnL, mark-to-market |
| **Risk metrics** | Sharpe, Sortino, VaR, drawdown analysis |
| **Trade analytics** | Win rate, profit factor, expectancy |
| **Modular strategy** | Easy to swap strategies, reuse engine |

## Quick Reference

```python
# Create strategy
class MyStrategy(Strategy):
    def generate_signals(self, bar, historical):
        if should_buy:
            return [{"action": "buy", "symbol": "AAPL", "qty": 100}]
        return []

# Configure execution
execution = ExecutionModel(
    commission_per_share=0.005,
    slippage_model="percentage",
    slippage_value=0.001  # 0.1%
)

# Run backtest
engine = BacktestEngine(initial_capital=100000, execution_model=execution)
engine.set_strategy(MyStrategy())
result = engine.run(historical_bars)

# Analyze
print(f"Sharpe: {result.sharpe_ratio:.2f}")
print(f"Max DD: {result.max_drawdown_pct:.2f}%")
print(f"Win rate: {result.win_rate:.1%}")
```

## Good Backtest Practices

1. **Out-of-sample testing** — Train on 70%, test on 30%
2. **Walk-forward analysis** — Re-optimize periodically
3. **Monte Carlo** — Shuffle trades to test robustness
4. **Sensitivity analysis** — Vary parameters ±20%
5. **Transaction costs** — Always include realistic fees/slippage
6. **Survivorship bias** — Include delisted stocks
7. **Look-ahead bias** — Only use data available at time

## What to Check

- Sharpe > 1.0 minimum (2.0+ preferred)
- Max drawdown < 20% (10% preferred)
- Profit factor > 1.5
- Win rate > 35% (with good risk/reward)
- Positive expectancy
- Stable equity curve (not just one big win)

---

**Created by Ghost 👻 | Feb 20, 2026 | 14-min learning sprint**  
*Lesson: "If you can't backtest it, you can't trade it." All strategies look good in hindsight—only rigorous backtesting with realistic costs reveals the truth. Never trust a strategy you haven't watched bleed on historical data.*
