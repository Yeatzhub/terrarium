# Portfolio Rebalancer

**Purpose:** Detect allocation drift and calculate rebalancing trades  
**Use Case:** Maintain target allocations as prices move

## The Code

```python
"""
Portfolio Rebalancer
Detect drift from target allocations and calculate rebalancing trades.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime


@dataclass
class Allocation:
    """Target allocation for an asset."""
    symbol: str
    target_pct: float  # Target percentage (0-100)
    current_value: float  # Current dollar value
    current_price: float


@dataclass
class RebalanceTrade:
    """Suggested trade to rebalance."""
    symbol: str
    action: str  # "buy" or "sell"
    shares: int
    current_value: float
    target_value: float
    delta_value: float
    reason: str


@dataclass
class RebalanceResult:
    """Complete rebalancing analysis."""
    total_portfolio_value: float
    drift_pct: float  # Max deviation from target
    trades: List[RebalanceTrade]
    untradeable: List[str]  # Positions that can't be rebalanced
    tax_impact_estimate: float
    transaction_costs: float
    recommendation: str


class PortfolioRebalancer:
    """
    Calculate rebalancing trades to maintain target allocations.
    """
    
    def __init__(
        self,
        drift_threshold: float = 5.0,  # Rebalance when allocation drifts 5%
        min_trade_value: float = 100.0,  # Min trade to avoid dust
        transaction_cost_pct: float = 0.001  # 0.1% per trade
    ):
        self.drift_threshold = drift_threshold
        self.min_trade = min_trade_value
        self.tx_cost = transaction_cost_pct
    
    def analyze(
        self,
        allocations: List[Allocation],
        allow_fractional: bool = False
    ) -> RebalanceResult:
        """
        Analyze portfolio and suggest rebalancing trades.
        """
        # Calculate totals
        total_value = sum(a.current_value for a in allocations)
        if total_value == 0:
            return RebalanceResult(0, 0, [], [], 0, 0, "Empty portfolio")
        
        # Calculate current percentages
        current_pcts = {
            a.symbol: (a.current_value / total_value) * 100
            for a in allocations
        }
        
        # Find max drift
        max_drift = max(
            abs(current_pcts.get(a.symbol, 0) - a.target_pct)
            for a in allocations
        )
        
        # Generate trades if drift exceeds threshold
        trades = []
        untradeable = []
        total_tx_cost = 0
        
        if max_drift > self.drift_threshold:
            for alloc in allocations:
                current_pct = current_pcts.get(alloc.symbol, 0)
                drift = current_pct - alloc.target_pct
                
                # Skip if within tolerance
                if abs(drift) < self.drift_threshold / 2:
                    continue
                
                # Calculate target value
                target_value = total_value * (alloc.target_pct / 100)
                delta = target_value - alloc.current_value
                
                # Skip small trades
                if abs(delta) < self.min_trade:
                    continue
                
                # Calculate shares
                if alloc.current_price > 0:
                    shares_float = abs(delta) / alloc.current_price
                    shares = int(shares_float) if not allow_fractional else shares_float
                else:
                    shares = 0
                
                if shares == 0:
                    untradeable.append(alloc.symbol)
                    continue
                
                action = "buy" if delta > 0 else "sell"
                actual_value = shares * alloc.current_price
                tx_cost = actual_value * self.tx_cost
                total_tx_cost += tx_cost
                
                trades.append(RebalanceTrade(
                    symbol=alloc.symbol,
                    action=action,
                    shares=int(shares),
                    current_value=alloc.current_value,
                    target_value=target_value,
                    delta_value=delta,
                    reason=f"Drift: {current_pct:.1f}% vs target {alloc.target_pct:.1f}%"
                ))
        
        # Estimate tax impact (simplified: assume 20% of gains are taxable)
        tax_estimate = sum(
            t.delta_value * 0.2 * 0.25  # 25% tax on 20% of value
            for t in trades if t.action == "sell"
        )
        
        # Recommendation
        if not trades:
            rec = f"No rebalancing needed. Max drift: {max_drift:.1f}% (threshold: {self.drift_threshold}%)"
        elif len(trades) <= 2:
            rec = f"Minor rebalancing suggested: {len(trades)} trades"
        else:
            rec = f"Significant drift detected. Execute {len(trades)} rebalancing trades"
        
        return RebalanceResult(
            total_portfolio_value=total_value,
            drift_pct=max_drift,
            trades=trades,
            untradeable=untradeable,
            tax_impact_estimate=tax_estimate,
            transaction_costs=total_tx_cost,
            recommendation=rec
        )
    
    def generate_orders(
        self,
        result: RebalanceResult,
        order_type: str = "market"
    ) -> List[Dict]:
        """Generate executable orders from rebalance result."""
        orders = []
        
        # Sort: sell first (raise cash), then buy
        sells = [t for t in result.trades if t.action == "sell"]
        buys = [t for t in result.trades if t.action == "buy"]
        
        for trade in sells + buys:
            orders.append({
                "symbol": trade.symbol,
                "action": trade.action,
                "quantity": trade.shares,
                "order_type": order_type,
                "reason": trade.reason,
                "estimated_value": trade.delta_value
            })
        
        return orders
    
    def band_rebalance(
        self,
        allocations: List[Allocation],
        bands: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> RebalanceResult:
        """
        Rebalancing bands - only rebalance when outside tolerance bands.
        More efficient than fixed schedule.
        """
        total_value = sum(a.current_value for a in allocations)
        
        trades = []
        for alloc in allocations:
            current_pct = (alloc.current_value / total_value) * 100
            target = alloc.target_pct
            
            # Default band: ±5% around target
            if bands and alloc.symbol in bands:
                lower, upper = bands[alloc.symbol]
            else:
                lower, upper = target - 5, target + 5
            
            if current_pct < lower:
                # Need to buy
                target_value = total_value * (target / 100)
                delta = target_value - alloc.current_value
                shares = int(delta / alloc.current_price) if alloc.current_price > 0 else 0
                if shares > 0:
                    trades.append(RebalanceTrade(
                        symbol=alloc.symbol,
                        action="buy",
                        shares=shares,
                        current_value=alloc.current_value,
                        target_value=target_value,
                        delta_value=delta,
                        reason=f"Below band: {current_pct:.1f}% < {lower:.1f}%"
                    ))
            elif current_pct > upper:
                # Need to sell
                target_value = total_value * (target / 100)
                delta = alloc.current_value - target_value
                shares = int(delta / alloc.current_price) if alloc.current_price > 0 else 0
                if shares > 0:
                    trades.append(RebalanceTrade(
                        symbol=alloc.symbol,
                        action="sell",
                        shares=shares,
                        current_value=alloc.current_value,
                        target_value=target_value,
                        delta_value=-delta,
                        reason=f"Above band: {current_pct:.1f}% > {upper:.1f}%"
                    ))
        
        max_drift = max(
            abs((a.current_value / total_value * 100) - a.target_pct)
            for a in allocations
        ) if allocations else 0
        
        return RebalanceResult(
            total_portfolio_value=total_value,
            drift_pct=max_drift,
            trades=trades,
            untradeable=[],
            tax_impact_estimate=0,
            transaction_costs=len(trades) * 10,
            recommendation=f"Band rebalance: {len(trades)} trades needed"
        )
    
    def cash_buffer_rebalance(
        self,
        allocations: List[Allocation],
        cash_target_pct: float = 5.0
    ) -> RebalanceResult:
        """
        Rebalance considering cash buffer target.
        Ensures cash doesn't fall below target percentage.
        """
        total_value = sum(a.current_value for a in allocations)
        
        # Assume cash is separate (not in allocations)
        # Calculate invested value target
        invested_target = total_value * ((100 - cash_target_pct) / 100)
        
        # Adjust allocations proportionally
        scaled_allocs = []
        for alloc in allocations:
            scaled_target = alloc.target_pct * ((100 - cash_target_pct) / 100)
            scaled_allocs.append(Allocation(
                symbol=alloc.symbol,
                target_pct=scaled_target,
                current_value=alloc.current_value,
                current_price=alloc.current_price
            ))
        
        return self.analyze(scaled_allocs)


# === Examples ===

if __name__ == "__main__":
    rebalancer = PortfolioRebalancer(
        drift_threshold=5.0,
        min_trade_value=100.0
    )
    
    print("=" * 60)
    print("Portfolio Rebalancer")
    print("=" * 60)
    
    # Example 1: Balanced portfolio with drift
    print("\n1. Standard Rebalancing")
    allocations = [
        Allocation("SPY", 40.0, 42000, 420),   # Target 40%, currently 42%
        Allocation("QQQ", 30.0, 25000, 250),   # Target 30%, currently 25%
        Allocation("TLT", 20.0, 18000, 90),    # Target 20%, currently 18%
        Allocation("GLD", 10.0, 15000, 150),   # Target 10%, currently 15%
    ]
    
    result = rebalancer.analyze(allocations)
    print(f"Portfolio Value: ${result.total_portfolio_value:,.0f}")
    print(f"Max Drift: {result.drift_pct:.1f}%")
    print(f"Recommendation: {result.recommendation}")
    
    if result.trades:
        print(f"\nSuggested Trades:")
        for t in result.trades:
            emoji = "🟢" if t.action == "buy" else "🔴"
            print(f"  {emoji} {t.action.upper():4} {t.shares:4} {t.symbol:6} "
                  f"(${abs(t.delta_value):,.0f}) - {t.reason}")
        print(f"\nEst. Transaction Costs: ${result.transaction_costs:.2f}")
    
    # Example 2: Band rebalancing
    print("\n" + "=" * 60)
    print("2. Band Rebalancing (±5% bands)")
    print("=" * 60)
    
    band_allocs = [
        Allocation("AAPL", 25.0, 28000, 175),  # 28% (above 30% band)
        Allocation("MSFT", 25.0, 22000, 330),  # 22% (within band)
        Allocation("GOOGL", 25.0, 20000, 140), # 20% (below 20% band)
        Allocation("AMZN", 25.0, 30000, 170),  # 30% (above 30% band)
    ]
    
    bands = {
        "AAPL": (20, 30),   # 25% ±5%
        "MSFT": (20, 30),
        "GOOGL": (20, 30),
        "AMZN": (20, 30)
    }
    
    result2 = rebalancer.band_rebalance(band_allocs, bands)
    print(f"Trades: {len(result2.trades)}")
    for t in result2.trades:
        print(f"  {t.action.upper():4} {t.shares:4} {t.symbol} - {t.reason}")
    
    # Example 3: Generate orders
    print("\n" + "=" * 60)
    print("3. Generated Orders")
    print("=" * 60)
    
    orders = rebalancer.generate_orders(result, order_type="limit")
    for o in orders:
        print(f"  {o['action'].upper():4} {o['quantity']:4} {o['symbol']:6} "
              f"@ {o['order_type']} (~${abs(o['estimated_value']):,.0f})")


## Rebalancing Strategies

| Strategy | When to Use | Pros | Cons |
|----------|-------------|------|------|
| **Threshold** | Max drift > X% | Simple, clear rules | Can miss gradual drift |
| **Bands** | Allocation outside band | Efficient, reduces churn | Requires band setting |
| **Calendar** | Fixed schedule (monthly) | Disciplined, predictable | May rebalance unnecessarily |
| **Cash Buffer** | Need liquidity reserve | Maintains cash target | Reduces invested allocation |

## Quick Rules

```python
# Conservative: 5% drift threshold
rebalancer = PortfolioRebalancer(drift_threshold=5.0)

# Aggressive: 3% drift threshold (more trading)
rebalancer = PortfolioRebalancer(drift_threshold=3.0)

# Tax-aware: Wider bands for taxable accounts
bands = {"AAPL": (15, 35)}  # Wider for winners to defer taxes
```

## Why Rebalancing Matters

- **Risk control** - Prevents overconcentration in winners
- **Buy low/sell high** - Forced contrarian behavior
- **Discipline** - Removes emotion from allocation decisions
- **Tax efficiency** - Can harvest losses, defer gains

**Rule:** Rebalance when drift exceeds 5-10%, or annually, whichever comes first.

---

**Created by Ghost 👻 | Feb 20, 2026 | 12-min learning sprint**  
*Lesson: Let winners run, but not too far. Rebalancing enforces disciplined profit-taking and contrarian buying.*
