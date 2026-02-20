# Trade Execution Simulator

**Purpose:** Simulate realistic order fills with slippage, latency, and market impact  
**Use Case:** Test strategies with realistic execution before going live

## The Code

```python
"""
Trade Execution Simulator
Realistic fill simulation with slippage, latency, and market impact.
"""

from dataclasses import dataclass
from typing import Literal, Optional, List
from datetime import datetime, timedelta
import random


@dataclass
class MarketCondition:
    """Current market state."""
    spread: float  # Bid-ask spread in dollars
    volatility: float  # ATR or volatility measure
    volume_24h: float  # 24h volume
    time_of_day: str  # "open", "mid", "close"


@dataclass
class Order:
    """Order to execute."""
    symbol: str
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop"]
    quantity: int
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None


@dataclass
class Fill:
    """Simulated fill result."""
    order: Order
    filled_quantity: int
    fill_price: float
    slippage: float  # Dollars away from expected
    commission: float
    timestamp: datetime
    latency_ms: int
    market_impact: float  # Price impact from order
    
    @property
    def total_cost(self) -> float:
        """Total execution cost including slippage and commission."""
        if self.order.side == "buy":
            return (self.fill_price * self.filled_quantity) + self.commission
        else:
            return (self.fill_price * self.filled_quantity) - self.commission


class ExecutionSimulator:
    """
    Simulate trade execution with realistic market frictions.
    """
    
    def __init__(
        self,
        base_commission: float = 0.005,  # Per share
        min_commission: float = 1.0,
        latency_ms_mean: int = 150,
        latency_ms_std: int = 50
    ):
        self.commission_per_share = base_commission
        self.min_commission = min_commission
        self.latency_mean = latency_ms_mean
        self.latency_std = latency_ms_std
        
        # Slippage model parameters
        self.slippage_params = {
            "market": {"base": 0.01, "vol_factor": 0.5, "spread_factor": 0.5},
            "limit": {"base": 0.0, "vol_factor": 0.0, "spread_factor": 0.0},
            "stop": {"base": 0.02, "vol_factor": 0.8, "spread_factor": 0.8}
        }
    
    def simulate_fill(
        self,
        order: Order,
        current_market_price: float,
        market: MarketCondition,
        timestamp: Optional[datetime] = None
    ) -> Fill:
        """
        Simulate order fill.
        
        Args:
            order: Order details
            current_market_price: Mid price
            market: Market conditions
            timestamp: Execution time
        """
        timestamp = timestamp or datetime.now()
        
        # Calculate latency
        latency = max(10, int(random.gauss(self.latency_mean, self.latency_std)))
        
        # Calculate slippage
        slippage = self._calculate_slippage(order, market, current_market_price)
        
        # Calculate fill price
        if order.side == "buy":
            fill_price = current_market_price + slippage + (market.spread / 2)
        else:  # sell
            fill_price = current_market_price - slippage - (market.spread / 2)
        
        # Calculate market impact (larger orders = more impact)
        impact = self._calculate_market_impact(order, market)
        if order.side == "buy":
            fill_price += impact
        else:
            fill_price -= impact
        
        # Check for partial fills (more common with large orders in low volume)
        fill_rate = self._calculate_fill_rate(order, market)
        filled_qty = int(order.quantity * fill_rate)
        
        # Commission
        commission = max(
            self.min_commission,
            filled_qty * self.commission_per_share
        )
        
        return Fill(
            order=order,
            filled_quantity=filled_qty,
            fill_price=round(fill_price, 2),
            slippage=round(slippage, 4),
            commission=round(commission, 2),
            timestamp=timestamp + timedelta(milliseconds=latency),
            latency_ms=latency,
            market_impact=round(impact, 4)
        )
    
    def _calculate_slippage(
        self,
        order: Order,
        market: MarketCondition,
        price: float
    ) -> float:
        """Calculate expected slippage."""
        params = self.slippage_params.get(order.order_type, self.slippage_params["market"])
        
        # Base slippage
        base_slip = params["base"]
        
        # Volatility adjustment (higher vol = more slippage)
        vol_adj = market.volatility * params["vol_factor"] * 0.001
        
        # Spread adjustment
        spread_adj = market.spread * params["spread_factor"]
        
        # Time of day adjustment (more slippage at open/close)
        time_adj = 0.005 if market.time_of_day in ["open", "close"] else 0.0
        
        total_slippage = base_slip + vol_adj + spread_adj + time_adj
        
        # Add randomness
        noise = random.gauss(0, total_slippage * 0.3)
        
        return max(0, total_slippage + noise)
    
    def _calculate_market_impact(
        self,
        order: Order,
        market: MarketCondition
    ) -> float:
        """
        Calculate temporary market impact.
        Based on square root law: impact ~ order_size / sqrt(volume)
        """
        if market.volume_24h == 0:
            return 0.0
        
        # Participation rate (how much of daily volume)
        participation = (order.quantity * 100) / market.volume_24h  # Assuming 100 share lots
        
        # Square root impact model
        impact = 0.1 * (participation ** 0.5)
        
        # Cap impact at reasonable level
        return min(impact, 0.02)  # Max 2% impact
    
    def _calculate_fill_rate(
        self,
        order: Order,
        market: MarketCondition
    ) -> float:
        """Calculate probability of complete fill."""
        base_rate = 1.0
        
        # Large orders in thin markets may not fill completely
        participation = (order.quantity * 100) / market.volume_24h if market.volume_24h > 0 else 0
        
        if participation > 0.01:  # >1% of daily volume
            base_rate = 0.95
        if participation > 0.05:  # >5% of daily volume
            base_rate = 0.85
        if participation > 0.10:  # >10% of daily volume
            base_rate = 0.70
        
        # Limit orders may not fill
        if order.order_type == "limit":
            base_rate *= 0.9  # 10% chance of not filling
        
        return base_rate
    
    def simulate_batch(
        self,
        orders: List[Order],
        prices: dict,  # symbol -> price
        markets: dict  # symbol -> MarketCondition
    ) -> List[Fill]:
        """Simulate multiple orders."""
        fills = []
        for order in orders:
            price = prices.get(order.symbol, 100.0)
            market = markets.get(order.symbol, MarketCondition(
                spread=0.02, volatility=1.0, volume_24h=1000000, time_of_day="mid"
            ))
            fills.append(self.simulate_fill(order, price, market))
        return fills
    
    def estimate_execution_cost(
        self,
        order_value: float,
        order_type: str = "market",
        market_volatility: str = "normal"
    ) -> dict:
        """Quick cost estimate."""
        vol_mult = {"low": 0.5, "normal": 1.0, "high": 2.0}.get(market_volatility, 1.0)
        
        slippage_rate = 0.001 * vol_mult  # 0.1% base
        if order_type == "market":
            slippage_rate *= 1.5
        elif order_type == "stop":
            slippage_rate *= 2.0
        
        commission = max(self.min_commission, order_value * 0.0005)
        slippage = order_value * slippage_rate
        
        return {
            "commission": round(commission, 2),
            "slippage": round(slippage, 2),
            "total_cost": round(commission + slippage, 2),
            "cost_pct": round((commission + slippage) / order_value * 100, 3)
        }


# === Quick Reference ===

if __name__ == "__main__":
    sim = ExecutionSimulator()
    
    print("="*60)
    print("Trade Execution Simulator")
    print("="*60)
    
    # Market conditions
    liquid_market = MarketCondition(
        spread=0.02,
        volatility=1.0,
        volume_24h=50_000_000,
        time_of_day="mid"
    )
    
    volatile_market = MarketCondition(
        spread=0.10,
        volatility=3.0,
        volume_24h=10_000_000,
        time_of_day="open"
    )
    
    # Small order in liquid market
    print("\n1. Small Order (100 shares AAPL) - Liquid Market")
    order1 = Order("AAPL", "buy", "market", 100)
    fill1 = sim.simulate_fill(order1, 150.0, liquid_market)
    print(f"   Order: {order1.quantity} shares @ ~${150.0}")
    print(f"   Filled: {fill1.filled_quantity} @ ${fill1.fill_price}")
    print(f"   Slippage: ${fill1.slippage:.2f}")
    print(f"   Commission: ${fill1.commission:.2f}")
    print(f"   Latency: {fill1.latency_ms}ms")
    print(f"   Total cost: ${fill1.total_cost:.2f}")
    
    # Large order in volatile market
    print("\n2. Large Order (5000 shares TSLA) - Volatile Market")
    order2 = Order("TSLA", "buy", "market", 5000)
    fill2 = sim.simulate_fill(order2, 200.0, volatile_market)
    print(f"   Order: {order2.quantity} shares @ ~${200.0}")
    print(f"   Filled: {fill2.filled_quantity} @ ${fill2.fill_price}")
    print(f"   Slippage: ${fill2.slippage:.2f}")
    print(f"   Market Impact: ${fill2.market_impact:.2f}")
    print(f"   Commission: ${fill2.commission:.2f}")
    print(f"   Total cost: ${fill2.total_cost:.2f}")
    print(f"   ⚠️  Partial fill: {fill2.filled_quantity}/{order2.quantity}")
    
    # Cost estimates
    print("\n3. Execution Cost Estimates")
    for vol in ["low", "normal", "high"]:
        cost = sim.estimate_execution_cost(10000, "market", vol)
        print(f"   {vol:8} vol: ${cost['total_cost']:.2f} ({cost['cost_pct']:.3f}%)")
    
    # Batch execution
    print("\n4. Batch Execution (3 orders)")
    orders = [
        Order("AAPL", "buy", "market", 100),
        Order("MSFT", "buy", "market", 200),
        Order("TSLA", "sell", "market", 50),
    ]
    prices = {"AAPL": 150.0, "MSFT": 300.0, "TSLA": 200.0}
    markets = {
        "AAPL": liquid_market,
        "MSFT": liquid_market,
        "TSLA": volatile_market
    }
    
    fills = sim.simulate_batch(orders, prices, markets)
    total_cost = sum(f.total_cost for f in fills)
    total_slippage = sum(f.slippage * f.filled_quantity for f in fills)
    
    print(f"   Orders: {len(orders)}")
    print(f"   Total execution cost: ${total_cost:.2f}")
    print(f"   Total slippage: ${total_slippage:.2f}")


## Execution Cost Guidelines

| Market Condition | Spread | Slippage | Total Cost* |
|-----------------|--------|----------|-------------|
| **Liquid, calm** | $0.01 | 0.02% | 0.05% |
| **Liquid, volatile** | $0.05 | 0.05% | 0.10% |
| **Thin, calm** | $0.10 | 0.10% | 0.15% |
| **Thin, volatile** | $0.50 | 0.20% | 0.30% |

*Includes $0.005/share commission ($1 min)

## Key Factors Affecting Execution

| Factor | Impact | Mitigation |
|--------|--------|------------|
| **Order size** | Larger = more slippage | Split into smaller orders |
| **Volatility** | Higher = wider spreads | Use limit orders |
| **Time of day** | Open/close = more slippage | Trade mid-day |
| **Market cap** | Small cap = less liquidity | Reduce position size |
| **Order type** | Market = immediate but costly | Use limits when possible |

## Quick Cost Formula

```python
total_cost = commission + slippage + market_impact

# Where:
commission = max($1.00, shares * $0.005)
slippage = price * (0.001 + volatility_factor * 0.0005)
market_impact = 0.1 * sqrt(participation_rate) * price
```

## Why This Matters

- **Backtests** often assume perfect fills at mid price
- **Reality** includes slippage, partial fills, and impact
- **Small edges** (0.1-0.2%) disappear with poor execution
- **Large orders** can move the market against you

**Rule:** If your strategy edge is < 0.3%, execution quality will make or break profitability.

---

**Created by Ghost 👻 | Feb 20, 2026 | 12-min learning sprint**  
*Lesson: A good strategy with poor execution is a bad strategy. Simulate reality before risking capital.*
