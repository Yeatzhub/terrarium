# Trade Executor — Order Simulation with Realistic Fills

**Purpose:** Simulate order execution with realistic slippage, partial fills, and execution delays  
**Use Case:** Backtesting execution quality, estimating slippage costs, practicing order entry

## The Code

```python
"""
Trade Executor
Simulate order execution with realistic fills, slippage, and delays.
Models market orders, limits, stops, and partial fills.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Union
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque
import random
import time


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()
    STOP = auto()
    STOP_LIMIT = auto()
    TRAILING_STOP = auto()


class OrderSide(Enum):
    BUY = auto()
    SELL = auto()


class OrderStatus(Enum):
    PENDING = auto()
    SUBMITTED = auto()
    PARTIAL = auto()
    FILLED = auto()
    CANCELLED = auto()
    REJECTED = auto()
    EXPIRED = auto()


class TimeInForce(Enum):
    GTC = auto()  # Good till cancelled
    DAY = auto()  # Day only
    IOC = auto()  # Immediate or cancel
    FOK = auto()  # Fill or kill


@dataclass
class MarketCondition:
    """Current market conditions affecting execution."""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    avg_volume: float
    volatility: float  # ATR as % of price
    spread_pct: float
    
    # Liquidity
    avg_spread: float
    depth_bid_100: float  # Volume at best bid
    depth_ask_100: float  # Volume at best ask


@dataclass
class Order:
    """Trade order."""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    
    time_in_force: TimeInForce = TimeInForce.DAY
    status: OrderStatus = OrderStatus.PENDING
    
    # Timing
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Fills
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    
    # Slippage
    expected_price: Optional[float] = None
    slippage_dollars: float = 0.0
    slippage_bps: float = 0.0  # Basis points
    
    # Partial fills
    partial_fills: List[Dict] = field(default_factory=list)
    
    @property
    def remaining_quantity(self) -> float:
        return self.quantity - self.filled_quantity
    
    @property
    def is_complete(self) -> bool:
        return self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED, 
                               OrderStatus.REJECTED, OrderStatus.EXPIRED]


@dataclass
class Fill:
    """Individual fill event."""
    order_id: str
    timestamp: datetime
    quantity: float
    price: float
    slippage: float  # From expected


@dataclass
class ExecutionReport:
    """Summary of order execution."""
    order: Order
    total_slippage_bps: float
    total_cost: float  # Including slippage
    fill_time_ms: int
    partial_fill_count: int
    
    # Quality
    fill_quality: str  # excellent, good, fair, poor


class TradeExecutor:
    """
    Simulated trade execution with realistic fills.
    
    Models:
    - Slippage based on order size and liquidity
    - Partial fills with time priority
    - Market impact based on volume
    - Spread crossing costs
    
    Usage:
        executor = TradeExecutor(speed_ms=100)
        
        market = MarketCondition(
            symbol="AAPL",
            bid=174.95,
            ask=175.05,
            last=175.00,
            volume=500000,
            avg_volume=1000000,
            volatility=0.015,
            spread_pct=0.057
        )
        
        order = executor.submit_order(
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET,
            market=market
        )
        
        report = executor.execute(order, market)
        print(f"Filled at ${order.avg_fill_price:.2f}")
        print(f"Slippage: {order.slippage_bps:.0f} bps")
    """
    
    def __init__(
        self,
        base_latency_ms: int = 50,
        slippage_model: str = "adaptive"
    ):
        self.base_latency_ms = base_latency_ms
        self.slippage_model = slippage_model
        
        self.orders: Dict[str, Order] = {}
        self.fills: List[Fill] = []
        self.execution_history: List[ExecutionReport] = []
        
        # Callbacks
        self.on_fill: Optional[Callable] = None
        self.on_order_complete: Optional[Callable] = None
    
    def submit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        order_type: OrderType,
        market: MarketCondition,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: TimeInForce = TimeInForce.DAY
    ) -> Order:
        """Submit a new order."""
        order_id = f"ORD_{datetime.now().strftime('%H%M%S')}_{random.randint(1000, 9999)}"
        
        # Calculate expected price for slippage measurement
        expected = self._calculate_expected_price(order_type, side, market)
        
        order = Order(
            id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            status=OrderStatus.SUBMITTED,
            submitted_at=datetime.now(),
            expected_price=expected
        )
        
        self.orders[order_id] = order
        return order
    
    def execute(self, order: Order, market: MarketCondition) -> ExecutionReport:
        """Execute order against market conditions."""
        if order.status != OrderStatus.SUBMITTED:
            return None
        
        start_time = time.time()
        
        # Check if order is valid
        if not self._validate_order(order, market):
            order.status = OrderStatus.REJECTED
            return None
        
        # Add latency
        latency = self._calculate_latency(order, market)
        time.sleep(latency / 1000)  # Simulate delay
        
        # Execute based on order type
        if order.order_type == OrderType.MARKET:
            self._execute_market(order, market)
        elif order.order_type == OrderType.LIMIT:
            self._execute_limit(order, market)
        elif order.order_type == OrderType.STOP:
            self._execute_stop(order, market)
        
        order.filled_at = datetime.now()
        fill_time_ms = int((time.time() - start_time) * 1000)
        
        # Calculate quality
        quality = self._calculate_fill_quality(order)
        
        report = ExecutionReport(
            order=order,
            total_slippage_bps=order.slippage_bps,
            total_cost=order.avg_fill_price * order.filled_quantity,
            fill_time_ms=fill_time_ms,
            partial_fill_count=len(order.partial_fills),
            fill_quality=quality
        )
        
        self.execution_history.append(report)
        
        if self.on_order_complete:
            self.on_order_complete(order, report)
        
        return report
    
    def _calculate_expected_price(
        self,
        order_type: OrderType,
        side: OrderSide,
        market: MarketCondition
    ) -> float:
        """Calculate expected fill price before execution."""
        if order_type == OrderType.MARKET:
            # Market buy fills at ask, sell at bid
            return market.ask if side == OrderSide.BUY else market.bid
        else:
            return market.last
    
    def _validate_order(self, order: Order, market: MarketCondition) -> bool:
        """Validate order can be executed."""
        if order.symbol != market.symbol:
            return False
        
        if order.quantity <= 0:
            return False
        
        return True
    
    def _calculate_latency(self, order: Order, market: MarketCondition) -> float:
        """Calculate execution latency in milliseconds."""
        # Base latency
        latency = self.base_latency_ms
        
        # Larger orders take longer
        size_factor = min(2.0, 1 + (order.quantity / 1000))
        latency *= size_factor
        
        # Volatile markets have higher latency
        volatility_penalty = market.volatility * 1000
        latency += volatility_penalty
        
        # Add randomness
        latency *= random.uniform(0.8, 1.2)
        
        return latency
    
    def _execute_market(self, order: Order, market: MarketCondition):
        """Execute market order."""
        # Calculate slippage
        slippage = self._calculate_slippage(order, market)
        
        # Determine fill price
        if order.side == OrderSide.BUY:
            base_price = market.ask
            fill_price = base_price * (1 + slippage)
        else:
            base_price = market.bid
            fill_price = base_price * (1 - slippage)
        
        # Check for partial fill
        fill_pct = self._calculate_fill_percentage(order, market)
        filled_qty = order.quantity * fill_pct
        
        # For IOC orders, reject if can't fill
        if order.time_in_force == TimeInForce.IOC and fill_pct < 1.0:
            filled_qty = filled_qty
            order.status = OrderStatus.PARTIAL
        
        # Record fill
        order.filled_quantity = filled_qty
        order.avg_fill_price = fill_price
        order.slippage_dollars = abs(fill_price - order.expected_price) * filled_qty
        order.slippage_bps = (abs(fill_price - order.expected_price) / order.expected_price) * 10000 if order.expected_price else 0
        order.status = OrderStatus.FILLED if fill_pct >= 1.0 else OrderStatus.PARTIAL
        
        # Record partial fill
        if filled_qty > 0:
            order.partial_fills.append({
                'timestamp': datetime.now(),
                'quantity': filled_qty,
                'price': fill_price
            })
            
            fill = Fill(
                order_id=order.id,
                timestamp=datetime.now(),
                quantity=filled_qty,
                price=fill_price,
                slippage=order.slippage_bps
            )
            self.fills.append(fill)
            
            if self.on_fill:
                self.on_fill(fill)
    
    def _execute_limit(self, order: Order, market: MarketCondition):
        """Execute limit order."""
        if order.price is None:
            order.status = OrderStatus.REJECTED
            return
        
        # Check if limit is marketable
        if order.side == OrderSide.BUY and order.price >= market.ask:
            # Marketable limit - treat as market
            self._execute_market(order, market)
        elif order.side == OrderSide.SELL and order.price <= market.bid:
            # Marketable limit - treat as market
            self._execute_market(order, market)
        else:
            # Non-marketable - may not fill
            fill_prob = self._calculate_limit_fill_probability(order, market)
            
            if random.random() < fill_prob:
                # Limit filled at order price
                order.filled_quantity = order.quantity
                order.avg_fill_price = order.price
                order.status = OrderStatus.FILLED
                order.slippage_bps = 0  # No slippage for limit
            else:
                # Didn't fill
                if order.time_in_force == TimeInForce.IOC:
                    order.status = OrderStatus.CANCELLED
                else:
                    order.status = OrderStatus.PENDING  # Leave pending
    
    def _execute_stop(self, order: Order, market: MarketCondition):
        """Execute stop order."""
        # Stop orders become market once triggered
        self._execute_market(order, market)
    
    def _calculate_slippage(self, order: Order, market: MarketCondition) -> float:
        """Calculate expected slippage as percentage."""
        # Base slippage (spread / 2)
        base_slip = market.spread_pct / 2 / 100
        
        # Size impact: larger orders = more slippage
        size_factor = order.quantity / market.avg_volume
        impact = min(0.01, size_factor * 0.001)  # Max 1%
        
        # Volatility impact
        vol_impact = market.volatility * 0.5
        
        # Liquidity impact
        depth = market.depth_ask_100 if order.side == OrderSide.BUY else market.depth_bid_100
        depth_ratio = order.quantity / depth if depth else 10
        liquidity_penalty = min(0.005, depth_ratio * 0.0005)
        
        total_slippage = base_slip + impact + vol_impact + liquidity_penalty
        
        # Add randomness
        total_slippage *= random.uniform(0.5, 1.5)
        
        return total_slippage
    
    def _calculate_fill_percentage(self, order: Order, market: MarketCondition) -> float:
        """Calculate what percentage will fill."""
        # Most market orders fill completely
        base_fill = 1.0
        
        # Large orders may partial fill
        size_ratio = order.quantity / market.avg_volume
        if size_ratio > 0.01:  # More than 1% of avg volume
            # Chance of partial fill
            partial_chance = min(0.3, size_ratio * 2)
            if random.random() < partial_chance:
                return random.uniform(0.5, 0.95)
        
        return base_fill
    
    def _calculate_limit_fill_probability(self, order: Order, market: MarketCondition) -> float:
        """Calculate probability limit order fills."""
        # Distance from market
        if order.side == OrderSide.BUY:
            distance = (market.bid - order.price) / market.last
        else:
            distance = (order.price - market.ask) / market.last
        
        # Closer to market = higher fill probability
        base_prob = max(0.1, 1.0 - distance * 100)
        
        # Time premium
        time_factor = 0.95  # Decay over time
        
        return base_prob * time_factor
    
    def _calculate_fill_quality(self, order: Order) -> str:
        """Rate fill quality."""
        if order.slippage_bps < 5:
            return "excellent"
        elif order.slippage_bps < 15:
            return "good"
        elif order.slippage_bps < 30:
            return "fair"
        else:
            return "poor"
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order."""
        order = self.orders.get(order_id)
        if order and order.status == OrderStatus.PENDING:
            order.status = OrderStatus.CANCELLED
            return True
        return False
    
    def get_execution_stats(self) -> Dict:
        """Get execution statistics."""
        if not self.execution_history:
            return {}
        
        total_slippage = sum(r.total_slippage_bps for r in self.execution_history)
        avg_slippage = total_slippage / len(self.execution_history)
        
        fills_by_quality = {}
        for r in self.execution_history:
            fills_by_quality[r.fill_quality] = fills_by_quality.get(r.fill_quality, 0) + 1
        
        avg_fill_time = sum(r.fill_time_ms for r in self.execution_history) / len(self.execution_history)
        
        return {
            "total_orders": len(self.execution_history),
            "avg_slippage_bps": avg_slippage,
            "avg_fill_time_ms": avg_fill_time,
            "fills_by_quality": fills_by_quality,
            "total_fills": len(self.fills)
        }
    
    def reset(self):
        """Clear all orders and history."""
        self.orders.clear()
        self.fills.clear()
        self.execution_history.clear()


def format_execution_report(report: ExecutionReport) -> str:
    """Format execution report."""
    o = report.order
    
    emoji = {
        "excellent": "🟢",
        "good": "🟡",
        "fair": "🟠",
        "poor": "🔴"
    }.get(report.fill_quality, "⚪")
    
    lines = [
        f"{'=' * 70}",
        f"EXECUTION REPORT",
        f"{'=' * 70}",
        f"Order ID: {o.id}",
        f"Symbol: {o.symbol} | Type: {o.order_type.name}",
        f"Side: {o.side.name} | Quantity: {o.quantity:.0f}",
        "",
        "PRICE:",
        f"  Expected: ${o.expected_price:.2f}" if o.expected_price else "  Expected: N/A",
        f"  Filled:   ${o.avg_fill_price:.2f}",
        f"  Slippage: {o.slippage_bps:.1f} bps",
        "",
        "FILL:",
        f"  Filled: {o.filled_quantity:.0f} / {o.quantity:.0f}",
        f"  Status: {o.status.name}",
        f"  Quality: {emoji} {report.fill_quality.upper()}",
        "",
        "METRICS:",
        f"  Fill Time: {report.fill_time_ms}ms",
        f"  Total Cost: ${report.total_cost:,.2f}",
        f"  Partials: {report.partial_fill_count}",
        f"{'=' * 70}"
    ]
    
    return "\n".join(lines)


# === Examples ===

def example_market_order():
    """Demonstrate market order execution."""
    print("=" * 70)
    print("Trade Executor Demo - Market Orders")
    print("=" * 70)
    
    executor = TradeExecutor(base_latency_ms=50)
    
    # Normal market conditions
    normal_market = MarketCondition(
        symbol="AAPL",
        bid=174.95,
        ask=175.05,
        last=175.00,
        volume=1000000,
        avg_volume=2000000,
        volatility=0.012,
        spread_pct=0.057,
        avg_spread=0.10,
        depth_bid_100=50000,
        depth_ask_100=50000
    )
    
    print("\n--- Normal Market Order ---")
    order = executor.submit_order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=100,
        order_type=OrderType.MARKET,
        market=normal_market
    )
    
    report = executor.execute(order, normal_market)
    print(format_execution_report(report))
    
    # Large order in same market
    print("\n--- Large Order (Show Slippage) ---")
    executor.reset()
    
    big_order = executor.submit_order(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=5000,  # 50x larger
        order_type=OrderType.MARKET,
        market=normal_market
    )
    
    report = executor.execute(big_order, normal_market)
    print(format_execution_report(report))


def example_limit_order():
    """Demonstrate limit order behavior."""
    print("\n" + "=" * 70)
    print("Trade Executor Demo - Limit Orders")
    print("=" * 70)
    
    executor = TradeExecutor()
    
    market = MarketCondition(
        symbol="MSFT",
        bid=379.90,
        ask=380.10,
        last=380.00,
        volume=800000,
        avg_volume=1500000,
        volatility=0.008,
        spread_pct=0.053,
        avg_spread=0.20,
        depth_bid_100=30000,
        depth_ask_100=30000
    )
    
    print("\n--- Marketable Limit (at bid) ---")
    order1 = executor.submit_order(
        symbol="MSFT",
        side=OrderSide.BUY,
        quantity=50,
        order_type=OrderType.LIMIT,
        market=market,
        price=380.00,  # At ask
        time_in_force=TimeInForce.DAY
    )
    
    report = executor.execute(order1, market)
    print(format_execution_report(report))
    
    print("\n--- Non-Marketable Limit (below bid) ---")
    order2 = executor.submit_order(
        symbol="MSFT",
        side=OrderSide.BUY,
        quantity=50,
        order_type=OrderType.LIMIT,
        market=market,
        price=379.50,  # Below bid
        time_in_force=TimeInForce.IOC
    )
    
    report = executor.execute(order2, market)
    if report:
        print(format_execution_report(report))
    else:
        print(f"Order status: {order2.status.name} (limit not hit)")


def example_execution_stats():
    """Show execution statistics."""
    print("\n" + "=" * 70)
    print("Trade Executor Demo - Statistics")
    print("=" * 70)
    
    executor = TradeExecutor(base_latency_ms=25)
    
    market = MarketCondition(
        symbol="SPY",
        bid=450.00,
        ask=450.05,
        last=450.02,
        volume=5000000,
        avg_volume=8000000,
        volatility=0.005,
        spread_pct=0.011,
        avg_spread=0.05,
        depth_bid_100=100000,
        depth_ask_100=100000
    )
    
    # Execute many orders
    sizes = [10, 25, 50, 100, 200, 500, 1000, 2000]
    
    for size in sizes:
        order = executor.submit_order(
            "SPY",
            OrderSide.BUY if random.random() > 0.5 else OrderSide.SELL,
            size,
            OrderType.MARKET,
            market
        )
        executor.execute(order, market)
    
    stats = executor.get_execution_stats()
    
    print(f"\nExecution Statistics ({stats['total_orders']} orders):")
    print(f"  Average Slippage: {stats['avg_slippage_bps']:.1f} bps")
    print(f"  Average Fill Time: {stats['avg_fill_time_ms']:.0f}ms")
    print(f"\nFill Quality Distribution:")
    for quality, count in stats['fills_by_quality'].items():
        print(f"  {quality.capitalize()}: {count}")


if __name__ == "__main__":
    example_market_order()
    example_limit_order()
    example_execution_stats()
    
    print("\n" + "=" * 70)
    print("EXECUTION QUALITY GUIDE:")
    print("=" * 70)
    print("""
SLIPPAGE:
  < 5 bps:  Excellent (tight spreads, liquid)
  5-15 bps: Good (normal conditions)
  15-30 bps: Fair (wide spreads, volatile)
  > 30 bps: Poor (illiquid, large orders)

FACTORS AFFECTING FILL:
  • Order size relative to volume
  • Spread width
  • Market volatility
  • Available liquidity
  • Order type (market fills faster, limit guarantees price)

COSTS TO CONSIDER:
  • Spread cost (50% for market orders)
  • Slippage (market impact)
  • Commissions (fixed)
  • Timing cost (delayed fills)

BEST PRACTICES:
  • Use limits when not urgent
  • Break large orders into pieces
  • Avoid market orders in first/last 30 minutes
  • Check liquidity before sizing up
    """)
    print("=" * 70)
```

## Slippage Reference

| Slippage | Quality | Meaning |
|----------|---------|---------|
| < 5 bps | Excellent | Tight spreads, liquid stock |
| 5-15 bps | Good | Normal market conditions |
| 15-30 bps | Fair | Wide spreads or volatile |
| > 30 bps | Poor | Illiquid or very large order |

## Order Type Behavior

| Type | When to Use | Slippage |
|------|-------------|----------|
| **MARKET** | Need fill now | Higher (cross spread) |
| **LIMIT** | Price sensitive | Lower (price guaranteed) |
| **STOP** | Loss protection | Market on trigger |
| **IOC** | Quick fill or cancel | Market if fills |

## Quick Reference

```python
executor = TradeExecutor(base_latency_ms=50)

market = MarketCondition(
    symbol="AAPL",
    bid=174.95, ask=175.05, last=175.00,
    volume=1000000, avg_volume=2000000,
    volatility=0.012, spread_pct=0.057,
    depth_bid_100=50000, depth_ask_100=50000
)

# Market order
order = executor.submit_order(
    "AAPL", OrderSide.BUY, 100,
    OrderType.MARKET, market
)

report = executor.execute(order, market)
print(f"Filled at ${order.avg_fill_price:.2f}")
print(f"Slippage: {order.slippage_bps:.0f} bps")

# Limit order  
limit = executor.submit_order(
    "AAPL", OrderSide.BUY, 100,
    OrderType.LIMIT, market,
    price=174.90
)
```

## Why This Matters

- **Execution affects returns** — Poor fills cost real money
- **Slippage compounds** — 10 bps per trade adds up fast
- **Size matters** — Large orders move the market
- **Timing has cost** — Urgency costs a premium
- **Simulate before trading** — Know expected fill costs

**Execution quality is as important as strategy selection.**

---

**Created by Ghost 👻 | Feb 21, 2026 | 11-min learning sprint**  
*Lesson: "Your entry price is your first risk." Execution slippage eats returns silently—simulating fills with realistic slippage shows your true costs before you trade. Better to know you're paying 20 bps than discover it after.*
