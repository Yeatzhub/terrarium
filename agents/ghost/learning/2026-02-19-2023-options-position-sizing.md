# Options Position Sizing Calculator

**Purpose:** Calculate options position sizes accounting for delta, gamma, and time decay  
**Use Case:** Options have different risk characteristics than stock

## The Code

```python
"""
Options Position Sizing Calculator
Accounts for delta, implied volatility, and time decay.
"""

from dataclasses import dataclass
from typing import Literal, Optional
from math import log, sqrt, exp
from enum import Enum


class OptionType(Enum):
    CALL = "call"
    PUT = "put"


@dataclass
class OptionPosition:
    """Calculated options position."""
    underlying: str
    option_type: OptionType
    strike: float
    expiration_days: int
    delta: float
    contracts: int
    premium: float
    total_cost: float
    max_risk: float
    notional_exposure: float
    delta_exposure: float
    theta_daily: float
    iv_rank: Optional[float]
    
    def __str__(self):
        return (f"{self.contracts} {self.option_type.value.upper()} {self.strike} "
                f"({self.delta:.2f}Δ) | Cost: ${self.total_cost:.0f} | "
                f"Δ-Exp: ${self.delta_exposure:.0f}")


class OptionsSizer:
    """
    Size options positions for defined risk strategies.
    """
    
    def __init__(
        self,
        account_size: float,
        max_position_pct: float = 10.0,
        max_delta_exposure: float = 100.0  # Delta dollars
    ):
        self.account = account_size
        self.max_position_pct = max_position_pct
        self.max_delta = max_delta_exposure
    
    def calculate_covered_call(
        self,
        underlying: str,
        stock_price: float,
        strike: float,
        premium: float,
        delta: float,
        days_to_expiry: int
    ) -> OptionPosition:
        """
        Covered call: Long stock + short call.
        Risk is opportunity cost (capped upside).
        """
        # 100 shares covered by 1 call contract
        shares_needed = 100
        stock_cost = shares_needed * stock_price
        
        # Collect premium
        premium_received = premium * 100
        
        # Max profit if called away
        max_profit = (strike - stock_price) * 100 + premium_received
        
        # Breakeven
        breakeven = stock_price - premium
        
        return OptionPosition(
            underlying=underlying,
            option_type=OptionType.CALL,
            strike=strike,
            expiration_days=days_to_expiry,
            delta=delta,
            contracts=1,
            premium=premium,
            total_cost=stock_cost - premium_received,  # Net cost
            max_risk=stock_cost - premium_received,  # If stock goes to 0
            notional_exposure=stock_cost,
            delta_exposure=(1 - delta) * stock_cost,  # Reduced delta
            theta_daily=0,  # Beneficiary of theta
            iv_rank=None
        )
    
    def calculate_cash_secured_put(
        self,
        underlying: str,
        stock_price: float,
        strike: float,
        premium: float,
        delta: float,
        days_to_expiry: int
    ) -> OptionPosition:
        """
        Cash secured put: Keep cash to buy if assigned.
        """
        # Cash required if assigned
        cash_required = strike * 100
        
        # Premium collected
        premium_received = premium * 100
        
        # Check if we have enough cash
        if cash_required > self.account * 0.5:
            return OptionPosition(
                underlying=underlying,
                option_type=OptionType.PUT,
                strike=strike,
                expiration_days=days_to_expiry,
                delta=delta,
                contracts=0,
                premium=premium,
                total_cost=0,
                max_risk=0,
                notional_exposure=0,
                delta_exposure=0,
                theta_daily=0,
                iv_rank=None
            )
        
        return OptionPosition(
            underlying=underlying,
            option_type=OptionType.PUT,
            strike=strike,
            expiration_days=days_to_expiry,
            delta=delta,
            contracts=1,
            premium=premium,
            total_cost=cash_required,  # Cash set aside
            max_risk=strike * 100 - premium_received,  # If stock to 0
            notional_exposure=cash_required,
            delta_exposure=abs(delta) * cash_required,
            theta_daily=0,
            iv_rank=None
        )
    
    def calculate_spread(
        self,
        underlying: str,
        spread_type: Literal["bull_call", "bear_put", "iron_condor"],
        lower_strike: float,
        upper_strike: float,
        lower_premium: float,
        upper_premium: float,
        days_to_expiry: int,
        risk_pct: float = 1.0
    ) -> OptionPosition:
        """
        Calculate spread position size based on defined risk.
        """
        # Width of spread
        width = upper_strike - lower_strike
        
        # Net debit/credit
        if spread_type in ["bull_call", "bear_put"]:
            net_debit = abs(lower_premium - upper_premium)
            max_loss = net_debit * 100
            max_profit = (width - net_debit) * 100
        else:  # Iron condor
            net_credit = upper_premium - lower_premium
            max_loss = (width - net_credit) * 100
            max_profit = net_credit * 100
        
        # Size based on risk
        risk_amount = self.account * (risk_pct / 100)
        max_contracts = int(risk_amount / max_loss) if max_loss > 0 else 0
        
        # Cap by position size limit
        max_position_value = self.account * (self.max_position_pct / 100)
        contracts_by_size = int(max_position_value / (width * 100))
        
        contracts = min(max_contracts, contracts_by_size, 10)  # Max 10 spreads
        
        return OptionPosition(
            underlying=underlying,
            option_type=OptionType.CALL if spread_type == "bull_call" else OptionType.PUT,
            strike=lower_strike,
            expiration_days=days_to_expiry,
            delta=0.5,  # Approximate
            contracts=contracts,
            premium=net_debit if spread_type in ["bull_call", "bear_put"] else net_credit,
            total_cost=max_loss * contracts,
            max_risk=max_loss * contracts,
            notional_exposure=width * 100 * contracts,
            delta_exposure=width * 50 * contracts,  # Approximate
            theta_daily=0,
            iv_rank=None
        )
    
    def calculate_buy_option(
        self,
        underlying: str,
        option_type: OptionType,
        strike: float,
        stock_price: float,
        premium: float,
        delta: float,
        days_to_expiry: int,
        risk_pct: float = 0.5
    ) -> OptionPosition:
        """
        Long call or put - limited risk, time working against you.
        """
        # Options are leveraged - reduce size significantly
        max_risk_amount = self.account * (risk_pct / 100)
        
        # Cost per contract
        cost_per_contract = premium * 100
        
        # Max contracts
        max_contracts = int(max_risk_amount / cost_per_contract) if cost_per_contract > 0 else 0
        
        # Delta exposure check
        delta_dollars = abs(delta) * strike * 100
        contracts_by_delta = int(self.max_delta / delta_dollars) if delta_dollars > 0 else max_contracts
        
        contracts = min(max_contracts, contracts_by_delta, 5)  # Max 5 long options
        
        return OptionPosition(
            underlying=underlying,
            option_type=option_type,
            strike=strike,
            expiration_days=days_to_expiry,
            delta=delta,
            contracts=contracts,
            premium=premium,
            total_cost=cost_per_contract * contracts,
            max_risk=cost_per_contract * contracts,  # Max loss = premium paid
            notional_exposure=strike * 100 * contracts,
            delta_exposure=abs(delta) * strike * 100 * contracts,
            theta_daily=-premium * 0.01 * contracts,  # Approximate theta
            iv_rank=None
        )
    
    def get_position_summary(self, positions: list) -> dict:
        """Summarize options portfolio."""
        total_cost = sum(p.total_cost for p in positions)
        total_risk = sum(p.max_risk for p in positions)
        total_delta = sum(p.delta_exposure for p in positions)
        total_notional = sum(p.notional_exposure for p in positions)
        
        return {
            "positions": len(positions),
            "total_cost": total_cost,
            "total_risk": total_risk,
            "total_delta_exposure": total_delta,
            "total_notional": total_notional,
            "cost_pct": (total_cost / self.account) * 100,
            "delta_pct": (total_delta / self.account) * 100,
            "notional_pct": (total_notional / self.account) * 100
        }


# === Quick Reference ===

if __name__ == "__main__":
    sizer = OptionsSizer(account_size=100000)
    
    print("="*60)
    print("Options Position Sizing Examples")
    print("="*60)
    
    # Covered Call
    print("\n1. COVERED CALL")
    cc = sizer.calculate_covered_call(
        "AAPL", stock_price=150, strike=155,
        premium=2.50, delta=0.30, days_to_expiry=30
    )
    print(f"   Strategy: Buy 100 shares @ $150, Sell 155C @ $2.50")
    print(f"   Cost: ${cc.total_cost:,.0f} (${cc.total_cost/1000:.1f}k)")
    print(f"   Max Profit: ${(155-150)*100 + 250:.0f}")
    print(f"   Breakeven: ${150 - 2.50:.2f}")
    print(f"   % Account: {(cc.total_cost/100000)*100:.1f}%")
    
    # Cash Secured Put
    print("\n2. CASH SECURED PUT")
    csp = sizer.calculate_cash_secured_put(
        "TSLA", stock_price=200, strike=190,
        premium=3.00, delta=-0.30, days_to_expiry=30
    )
    if csp.contracts > 0:
        print(f"   Strategy: Sell 190P @ $3.00 (Cash secured)")
        print(f"   Cash Required: ${csp.total_cost:,.0f}")
        print(f"   Premium: ${csp.premium * 100:.0f}")
        print(f"   % Account: {(csp.total_cost/100000)*100:.1f}%")
    else:
        print("   REJECTED: Insufficient cash")
    
    # Bull Call Spread
    print("\n3. BULL CALL SPREAD")
    spread = sizer.calculate_spread(
        "SPY", spread_type="bull_call",
        lower_strike=440, upper_strike=450,
        lower_premium=5.00, upper_premium=2.00,
        days_to_expiry=30, risk_pct=1.0
    )
    print(f"   Strategy: Buy 440C @ $5.00, Sell 450C @ $2.00")
    print(f"   Net Debit: ${spread.premium * 100:.0f}")
    print(f"   Max Profit: ${(10 - spread.premium) * 100:.0f}")
    print(f"   Contracts: {spread.contracts}")
    print(f"   Max Risk: ${spread.max_risk:.0f}")
    
    # Long Call (speculative)
    print("\n4. LONG CALL (Speculative)")
    lc = sizer.calculate_buy_option(
        "NVDA", OptionType.CALL,
        strike=500, stock_price=480,
        premium=15.00, delta=0.40,
        days_to_expiry=45, risk_pct=0.5
    )
    print(f"   Strategy: Buy 500C @ $15.00")
    print(f"   Cost: ${lc.total_cost:.0f}")
    print(f"   Max Risk: ${lc.max_risk:.0f} (premium only)")
    print(f"   Breakeven: ${500 + 15:.2f}")
    print(f"   % Account: {(lc.total_cost/100000)*100:.2f}%")
    
    # Portfolio summary
    print("\n" + "="*60)
    print("Portfolio Summary")
    print("="*60)
    positions = [cc, csp, spread, lc]
    summary = sizer.get_position_summary(positions)
    print(f"   Total Cost: ${summary['total_cost']:,.0f} ({summary['cost_pct']:.1f}% of account)")
    print(f"   Total Risk: ${summary['total_risk']:,.0f}")
    print(f"   Delta Exposure: ${summary['total_delta_exposure']:,.0f}")
    print(f"   Notional: ${summary['total_notional']:,.0f}")


## Options Sizing Rules

| Strategy | Max % Account | Max Contracts | Notes |
|----------|---------------|---------------|-------|
| **Covered Call** | 20% | 1-2 | Requires 100 shares |
| **Cash Secured Put** | 30% | 1-2 | Cash must be available |
| **Credit Spread** | 5% risk | 5-10 | Defined risk |
| **Debit Spread** | 2% risk | 5-10 | Defined risk |
| **Long Call/Put** | 0.5% | 1-5 | High theta decay |
| **Iron Condor** | 3% risk | 3-5 | Defined risk |

## Quick Calculations

```python
# Covered Call
shares = 100
stock_cost = shares * stock_price
premium = option_premium * 100
max_profit = (strike - stock_price) * 100 + premium

# Cash Secured Put
cash_required = strike * 100
premium = option_premium * 100
max_risk = strike * 100 - premium

# Spread
width = upper_strike - lower_strike
max_risk = abs(net_premium) * 100
max_profit = (width - abs(net_premium)) * 100
```

---

**Created by Ghost 👻 | Feb 19, 2026 | 10-min learning sprint**  
*Lesson: Options leverage amplifies both gains and losses. Size for the max risk, not the max gain.*
