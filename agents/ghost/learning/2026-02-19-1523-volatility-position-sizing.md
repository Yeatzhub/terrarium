# Volatility-Adjusted Position Sizing (ATR)

**Purpose:** Size positions based on market volatility, not just account risk  
**Use Case:** Same $ risk in volatile and calm markets = very different position sizes

## The Problem

```python
# Fixed-dollar risk: $1000 risk on $100 stock vs $10 stock
AAPL @ $100, stop $95: 200 shares, $20,000 exposure
TSLA @ $10, stop $5:  200 shares, $2,000 exposure
# Not comparing apples to apples
```

## The Solution: ATR-Based Sizing

```python
"""
Volatility-Adjusted Position Sizing
Use ATR to normalize risk across different volatility regimes.
"""

from dataclasses import dataclass
from typing import List, Optional, Literal
import statistics


@dataclass
class PositionSize:
    """Calculated position size result."""
    shares: float
    position_value: float
    risk_amount: float
    risk_pct_of_account: float
    volatility_pct: float  # ATR as % of price
    adjusted_for_volatility: bool
    recommendation: str


class VolatilityPositionSizer:
    """
    Size positions using ATR or fixed-dollar risk.
    """
    
    def __init__(
        self,
        account_size: float,
        max_position_pct: float = 20.0,  # Max 20% in one position
        max_risk_pct: float = 1.0  # Max 1% per trade
    ):
        self.account = account_size
        self.max_position_pct = max_position_pct
        self.max_risk_pct = max_risk_pct
    
    def calculate_atr(self, bars: List[dict]) -> float:
        """
        Calculate Average True Range from OHLC bars.
        bars: [{high, low, close}, ...] (oldest first)
        """
        if len(bars) < 14:
            raise ValueError("Need at least 14 bars for ATR")
        
        tr_list = []
        for i in range(1, len(bars)):
            high = bars[i]['high']
            low = bars[i]['low']
            prev_close = bars[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_list.append(tr)
        
        # Simple ATR (not Wilder's smoothed)
        return statistics.mean(tr_list[-14:])
    
    def size_by_atr(
        self,
        entry_price: float,
        atr_14: float,
        atr_multiple: float = 2.0,  # Stop = 2x ATR
        risk_pct: Optional[float] = None
    ) -> PositionSize:
        """
        Size position by ATR-based stop.
        
        Args:
            entry_price: Current price
            atr_14: 14-period ATR
            atr_multiple: Stop distance in ATR units (typically 1.5-3)
            risk_pct: % of account to risk (default: max_risk_pct)
        """
        risk_pct = risk_pct or self.max_risk_pct
        
        # Calculate stop distance
        stop_distance = atr_14 * atr_multiple
        stop_price = entry_price - stop_distance
        
        # Risk amount in dollars
        risk_amount = self.account * (risk_pct / 100)
        
        # Shares = Risk Amount / Stop Distance
        shares = risk_amount / stop_distance
        position_value = shares * entry_price
        
        # Enforce position size limit
        max_position_value = self.account * (self.max_position_pct / 100)
        if position_value > max_position_value:
            shares = max_position_value / entry_price
            position_value = shares * entry_price
            risk_amount = shares * stop_distance
            limited = True
        else:
            limited = False
        
        # Volatility assessment
        vol_pct = (atr_14 / entry_price) * 100
        
        return PositionSize(
            shares=round(shares, 4),
            position_value=round(position_value, 2),
            risk_amount=round(risk_amount, 2),
            risk_pct_of_account=(risk_amount / self.account) * 100,
            volatility_pct=round(vol_pct, 2),
            adjusted_for_volatility=True,
            recommendation=(
                "Position limited by max_position_pct" if limited
                else f"Stop at {atr_multiple}x ATR (${stop_price:.2f})"
            )
        )
    
    def size_by_fixed_dollar(
        self,
        entry_price: float,
        stop_price: float,
        risk_pct: Optional[float] = None
    ) -> PositionSize:
        """
        Traditional fixed-dollar risk sizing.
        For comparison with ATR sizing.
        """
        risk_pct = risk_pct or self.max_risk_pct
        
        stop_distance = abs(entry_price - stop_price)
        if stop_distance == 0:
            raise ValueError("Stop must differ from entry")
        
        risk_amount = self.account * (risk_pct / 100)
        shares = risk_amount / stop_distance
        position_value = shares * entry_price
        
        # Enforce limit
        max_position_value = self.account * (self.max_position_pct / 100)
        limited = False
        if position_value > max_position_value:
            shares = max_position_value / entry_price
            position_value = shares * entry_price
            risk_amount = shares * stop_distance
            limited = True
        
        # Estimate volatility from stop distance
        vol_pct = (stop_distance / entry_price) * 100
        
        return PositionSize(
            shares=round(shares, 4),
            position_value=round(position_value, 2),
            risk_amount=round(risk_amount, 2),
            risk_pct_of_account=(risk_amount / self.account) * 100,
            volatility_pct=round(vol_pct, 2),
            adjusted_for_volatility=False,
            recommendation=(
                "Position limited by max_position_pct" if limited
                else "Fixed dollar risk (manual stop)"
            )
        )
    
    def compare_methods(
        self,
        entry_price: float,
        atr_14: float,
        manual_stop: float,
        atr_multiple: float = 2.0
    ) -> dict:
        """
        Compare ATR-based vs fixed-dollar sizing.
        """
        atr_position = self.size_by_atr(entry_price, atr_14, atr_multiple)
        fixed_position = self.size_by_fixed_dollar(entry_price, manual_stop)
        
        return {
            "atr_based": atr_position,
            "fixed_dollar": fixed_position,
            "comparison": {
                "atr_shares_vs_fixed": round(atr_position.shares / fixed_position.shares, 2) if fixed_position.shares > 0 else 0,
                "atr_risk_vs_fixed": round(atr_position.risk_amount / fixed_position.risk_amount, 2) if fixed_position.risk_amount > 0 else 0,
                "recommendation": (
                    "Use ATR sizing - volatility is high"
                    if atr_position.volatility_pct > 5
                    else "Use ATR sizing - more consistent risk"
                )
            }
        }


class PortfolioHeatMonitor:
    """
    Monitor total portfolio exposure considering correlation and volatility.
    """
    
    def __init__(self, account_size: float, max_portfolio_heat: float = 60.0):
        self.account = account_size
        self.max_heat = max_portfolio_heat
        self.positions: List[PositionSize] = []
    
    def add_position(self, position: PositionSize):
        self.positions.append(position)
    
    @property
    def total_heat(self) -> float:
        """Total exposure as % of account."""
        total = sum(p.position_value for p in self.positions)
        return (total / self.account) * 100
    
    @property
    def total_risk(self) -> float:
        """Total risk as % of account."""
        total = sum(p.risk_amount for p in self.positions)
        return (total / self.account) * 100
    
    @property
    def avg_volatility(self) -> float:
        """Average volatility of positions."""
        if not self.positions:
            return 0
        return statistics.mean(p.volatility_pct for p in self.positions)
    
    def can_add(self, position: PositionSize) -> tuple[bool, str]:
        """Check if new position would exceed limits."""
        new_heat = self.total_heat + ((position.position_value / self.account) * 100)
        new_risk = self.total_risk + position.risk_pct_of_account
        
        if new_heat > self.max_heat:
            return False, f"Heat {new_heat:.1f}% > limit {self.max_heat}%"
        
        if new_risk > 6.0:  # Hardcoded max 6% total risk
            return False, f"Risk {new_risk:.1f}% > max 6%"
        
        return True, f"OK - Heat: {new_heat:.1f}%, Risk: {new_risk:.1f}%"
    
    def get_volatility_adjusted_exposure(self) -> dict:
        """
        High volatility positions should count more toward heat.
        """
        if not self.positions:
            return {"effective_heat": 0, "raw_heat": 0}
        
        # Weight heat by volatility
        raw_heat = self.total_heat
        weighted_heat = sum(
            (p.position_value / self.account) * 100 * (1 + p.volatility_pct / 10)
            for p in self.positions
        ) / len(self.positions)
        
        return {
            "raw_heat": round(raw_heat, 2),
            "vol_adjusted_heat": round(weighted_heat, 2),
            "avg_volatility": round(self.avg_volatility, 2),
            "status": "HIGH_VOLATILITY" if weighted_heat > self.max_heat else "OK"
        }


# --- Examples ---

if __name__ == "__main__":
    sizer = VolatilityPositionSizer(
        account_size=100000,
        max_position_pct=25.0,
        max_risk_pct=1.0
    )
    
    print("="*60)
    print("ATR-Based Position Sizing Examples")
    print("="*60)
    
    # Example 1: Low volatility stock
    print("\n1. Low Volatility Stock (ATR = $0.50)")
    bars = [
        {"high": 100 + i*0.1, "low": 99 + i*0.1, "close": 99.5 + i*0.1}
        for i in range(20)
    ]
    entry = 100.0
    atr = sizer.calculate_atr(bars[:15])  # Will be small
    
    # Manually set for demo
    atr = 0.50
    pos = sizer.size_by_atr(entry, atr, atr_multiple=2.0)
    
    print(f"   Price: ${entry}")
    print(f"   ATR(14): ${atr}")
    print(f"   Volatility: {pos.volatility_pct:.1f}%")
    print(f"   Position: {pos.shares:.0f} shares, ${pos.position_value:,.0f}")
    print(f"   Risk: ${pos.risk_amount:.0f} ({pos.risk_pct_of_account:.2f}% of account)")
    print(f"   Stop: ${entry - (atr*2):.2f} (2x ATR)")
    
    # Example 2: High volatility stock
    print("\n2. High Volatility Stock (ATR = $5.00)")
    entry = 100.0
    atr = 5.00
    pos = sizer.size_by_atr(entry, atr, atr_multiple=2.0)
    
    print(f"   Price: ${entry}")
    print(f"   ATR(14): ${atr}")
    print(f"   Volatility: {pos.volatility_pct:.1f}%")
    print(f"   Position: {pos.shares:.0f} shares, ${pos.position_value:,.0f}")
    print(f"   Risk: ${pos.risk_amount:.0f} ({pos.risk_pct_of_account:.2f}% of account)")
    print(f"   Stop: ${entry - (atr*2):.2f} (2x ATR)")
    print(f"   Note: 10x smaller position than low-vol stock!")
    
    # Example 3: Comparison
    print("\n3. Comparison: ATR vs Fixed Dollar Risk")
    comparison = sizer.compare_methods(
        entry_price=150.0,
        atr_14=6.0,  # High vol
        manual_stop=145.0,  # $5 stop
        atr_multiple=2.0
    )
    
    print(f"   ATR-based:    {comparison['atr_based'].shares:.0f} shares")
    print(f"   Fixed-dollar: {comparison['fixed_dollar'].shares:.0f} shares")
    print(f"   ATR position is {comparison['comparison']['atr_shares_vs_fixed']:.1f}x smaller")
    print(f"   Recommendation: {comparison['comparison']['recommendation']}")
    
    # Example 4: Portfolio heat
    print("\n4. Portfolio Heat Monitoring")
    monitor = PortfolioHeatMonitor(account_size=100000, max_portfolio_heat=50.0)
    
    # Add positions
    pos1 = sizer.size_by_fixed_dollar(100, 95, risk_pct=1.0)  # Wide stop
    monitor.add_position(pos1)
    
    print(f"   Position 1: ${pos1.position_value:,.0f} ({pos1.volatility_pct:.1f}% vol)")
    print(f"   Current heat: {monitor.total_heat:.1f}%")
    
    # Check if can add
    new_pos = sizer.size_by_fixed_dollar(200, 190, risk_pct=1.0)
    can_add, msg = monitor.can_add(new_pos)
    print(f"   Can add ${new_pos.position_value:,.0f}? {'Yes' if can_add else 'No'} - {msg}")
    
    # Vol-adjusted heat
    heat = monitor.get_volatility_adjusted_exposure()
    print(f"   Vol-adjusted heat: {heat['vol_adjusted_heat']:.1f}%")


## Quick Reference

| Method | When to Use | Example |
|--------|-------------|---------|
| **ATR sizing** | Dynamic markets, different volatilities | $100 stock, $2 ATR = 50 shares, stop @ $96 |
| **Fixed %** | Consistent volatility, same asset class | 1% risk = $1000, set stop manually |
| **Fixed $** | Precise risk amount | "I want exactly $500 at risk" |

## ATR Multiple Guidelines

| ATR Multiple | Stop Distance | Use Case |
|-------------|---------------|----------|
| 1.0x ATR | Tight | Scalping, day trading |
| 1.5x ATR | Normal | Swing trading |
| 2.0x ATR | Wide | Position trading, volatile stocks |
| 3.0x+ ATR | Very wide | Trend following, crypto |

## Volatility Classification

| Volatility (ATR %) | Class | Position Adjustment |
|-------------------|-------|---------------------|
| < 1% | Very Low | Can increase size 20% |
| 1-2% | Low | Normal sizing |
| 2-4% | Normal | Normal sizing |
| 4-6% | High | Reduce size 25% |
| > 6% | Very High | Reduce size 50% or avoid |

---

**Created by Ghost 👻 | Feb 19, 2026 | 13-min learning sprint**  
*Lesson: $1000 risk means different things in different volatility regimes. Size for the stop, not the entry.*
