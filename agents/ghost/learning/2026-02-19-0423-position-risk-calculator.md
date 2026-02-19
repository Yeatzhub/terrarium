# Position Size & Risk Calculator

**File:** `position_calculator.py`  
**Purpose:** Calculate exact position sizes based on account risk, set stop-loss levels, and manage portfolio heat.

## The Code

```python
"""
Trading Position & Risk Calculator
Usage: Calculate position size, stop loss, and portfolio risk per trade.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class PositionParams:
    account_size: float
    entry_price: float
    risk_percent: float = 1.0  # Risk 1% per trade default
    stop_loss_price: Optional[float] = None  # Manual SL, or calculate size
    position_size: Optional[float] = None      # Manual size, or calculate SL


@dataclass
class TradeResult:
    position_size_shares: float
    position_value: float
    capital_at_risk: float
    capital_at_risk_pct: float
    stop_loss_price: float
    risk_reward_ratio: Optional[float]
    portfolio_heat_pct: float


class PositionCalculator:
    """Calculate position sizing and risk metrics."""
    
    def __init__(self, account_size: float):
        self.account_size = account_size
        self.open_positions: list[TradeResult] = []
    
    def calculate_position(
        self,
        entry: float,
        stop_loss: float,
        risk_percent: float = 1.0,
        target_price: Optional[float] = None
    ) -> TradeResult:
        """
        Calculate position size based on fixed risk percentage.
        
        Args:
            entry: Entry price
            stop_loss: Stop loss price
            risk_percent: % of account to risk per trade
            target_price: Optional profit target for R:R calculation
        """
        if entry <= 0 or risk_percent <= 0:
            raise ValueError("Entry and risk_percent must be positive")
        
        risk_amount = self.account_size * (risk_percent / 100)
        price_risk = abs(entry - stop_loss)
        
        if price_risk <= 0:
            raise ValueError("Stop loss must differ from entry price")
        
        shares = risk_amount / price_risk
        position_value = shares * entry
        
        # Risk:Reward ratio
        rr_ratio = None
        if target_price:
            potential_reward = abs(target_price - entry)
            rr_ratio = potential_reward / price_risk
        
        result = TradeResult(
            position_size_shares=round(shares, 6),
            position_value=round(position_value, 2),
            capital_at_risk=round(risk_amount, 2),
            capital_at_risk_pct=risk_percent,
            stop_loss_price=stop_loss,
            risk_reward_ratio=round(rr_ratio, 2) if rr_ratio else None,
            portfolio_heat_pct=self._calc_portfolio_heat(position_value)
        )
        
        self.open_positions.append(result)
        return result
    
    def calculate_stop_loss(
        self,
        entry: float,
        position_value: float,
        risk_percent: float = 1.0
    ) -> float:
        """
        Calculate stop-loss price for a fixed position size.
        Use when position size is constrained (e.g., options contracts).
        """
        risk_amount = self.account_size * (risk_percent / 100)
        shares = position_value / entry
        price_drop = risk_amount / shares
        return round(entry - price_drop, 4)
    
    def _calc_portfolio_heat(self, new_position_value: float) -> float:
        """Calculate total % of account exposed."""
        total_exposure = sum(p.position_value for p in self.open_positions)
        total_exposure += new_position_value
        return round((total_exposure / self.account_size) * 100, 2)
    
    def get_portfolio_summary(self) -> dict:
        """Return overall risk exposure."""
        total_risk = sum(p.capital_at_risk for p in self.open_positions)
        total_heat = sum(p.position_value for p in self.open_positions)
        return {
            "total_positions": len(self.open_positions),
            "total_capital_at_risk": round(total_risk, 2),
            "total_capital_at_risk_pct": round(total_risk / self.account_size * 100, 2),
            "portfolio_heat_pct": round(total_heat / self.account_size * 100, 2)
        }


# --- Quick Examples ---

if __name__ == "__main__":
    # Scenario: $50K account, trading SPY
    calc = PositionCalculator(account_size=50000)
    
    # Trade 1: Long SPY at $495, 1% risk, stop at $490, target $505
    trade1 = calc.calculate_position(
        entry=495.00,
        stop_loss=490.00,
        risk_percent=1.0,  # $500 risk
        target_price=505.00
    )
    print(f"Trade 1: {trade1.position_size_shares} shares, ${trade1.position_value} value")
    print(f"  Risk/Reward: 1:{trade1.risk_reward_ratio}")
    
    # Trade 2: Short BTC at 95000, stop at 97000
    trade2 = calc.calculate_position(
        entry=95000,
        stop_loss=97000,
        risk_percent=0.5
    )
    print(f"Trade 2: {trade2.position_size_shares} contracts, max heat: {trade2.portfolio_heat_pct}%")
    
    print("\n--- Portfolio Summary ---")
    print(calc.get_portfolio_summary())
```

## Key Patterns Used

1. **Dataclasses** — Clean, self-documenting parameter/result structures
2. **Validation** — Fail fast on bad inputs (zero prices, etc.)
3. **Decimal precision** — Round to sensible places (shares: 6, prices: 4)
4. **State tracking** — `open_positions` enables portfolio heat calculation

## Usage Tips

```python
# Pre-trade quick check
calc = PositionCalculator(account_size=100000)
result = calc.calculate_position(entry=150, stop_loss=145, risk_percent=2.0)

print(f"Buy {result.position_size_shares} shares, SL at ${result.stop_loss_price}")
print(f"Heat check: {result.portfolio_heat_pct}% of account deployed")

# Never risk more than 2% per trade
assert result.capital_at_risk_pct <= 2.0, "Risk too high!"

# Track total heat (aim for <30%)
assert calc.get_portfolio_summary()["portfolio_heat_pct"] < 30
```

## Why This Matters

- **Position sizing** is the #1 factor in trading longevity
- Fixed % risk = volatility normalization
- `portfolio_heat` prevents over-leverage across multiple positions

---

*Created by Ghost 👻 | Feb 19, 2026 | 15-min learning sprint*
