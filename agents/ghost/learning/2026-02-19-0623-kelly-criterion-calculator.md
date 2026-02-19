# Kelly Criterion Position Sizing

**Purpose:** Calculate optimal bet size based on win rate and payoff ratio. Prevents ruin while maximizing growth.

## The Formula

```
f* = (p × b - q) / b

Where:
  f* = fraction of bankroll to bet
  p = probability of win (win rate)
  q = probability of loss (1 - p)
  b = win/loss ratio (avg win / avg loss)
```

## The Code

```python
"""
Kelly Criterion Calculator
Optimal bet sizing for known edges. Use fractional Kelly (1/4 to 1/2) in practice.
"""

from dataclasses import dataclass
from typing import Optional
import math


@dataclass
class KellyResult:
    full_kelly: float           # Optimal fraction (0.0 to 1.0)
    half_kelly: float           # Conservative: 50% of optimal
    quarter_kelly: float        # Very conservative: 25% of optimal
    edge: float                 # Mathematical edge (%)
    expected_growth: float      # Expected log growth per bet
    ruin_risk_full: str         # Risk assessment
    ruin_risk_half: str
    
    def __str__(self):
        return (
            f"Kelly Results:\n"
            f"  Full Kelly:   {self.full_kelly:.2%} (aggressive)\n"
            f"  Half Kelly:   {self.half_kelly:.2%} (recommended)\n"
            f"  Quarter Kelly: {self.quarter_kelly:.2%} (safe)\n"
            f"  Edge:         {self.edge:.2%}\n"
            f"  E[growth]:    {self.expected_growth:.4f} per bet"
        )


class KellyCalculator:
    """
    Calculate optimal position sizes using Kelly Criterion.
    """
    
    @staticmethod
    def calculate(
        win_rate: float,           # 0.0 to 1.0 (e.g., 0.55 = 55%)
        avg_win: float,            # Average win amount ($ or R-multiple)
        avg_loss: float,           # Average loss amount (positive number)
        current_bankroll: float = 100000.0
    ) -> KellyResult:
        """
        Calculate Kelly fraction from historical trade stats.
        
        Args:
            win_rate: Probability of winning (0.0-1.0)
            avg_win: Average profit per winning trade
            avg_loss: Average loss per losing trade (positive)
            current_bankroll: Current account size
        """
        if not 0 < win_rate < 1:
            raise ValueError("Win rate must be between 0 and 1")
        if avg_win <= 0 or avg_loss <= 0:
            raise ValueError("Average win and loss must be positive")
        
        loss_rate = 1 - win_rate
        payoff_ratio = avg_win / avg_loss  # b in Kelly formula
        
        # Kelly formula: f* = (p*b - q) / b
        edge = win_rate * payoff_ratio - loss_rate
        full_kelly = edge / payoff_ratio if payoff_ratio > 0 else 0
        
        # Cap at 100% (can happen with extreme edges)
        full_kelly = min(full_kelly, 1.0)
        
        # Expected log growth: G = p*ln(1+b*f) + q*ln(1-f)
        if full_kelly > 0:
            expected_growth = (
                win_rate * math.log1p(payoff_ratio * full_kelly) +
                loss_rate * math.log1p(-full_kelly)
            )
        else:
            expected_growth = 0
        
        # Risk assessment
        def assess_risk(kelly_frac: float) -> str:
            if kelly_frac <= 0:
                return "NEGATIVE EDGE - Don't trade"
            elif kelly_frac < 0.1:
                return "Low risk"
            elif kelly_frac < 0.25:
                return "Moderate risk"
            elif kelly_frac < 0.5:
                return "High risk"
            else:
                return "EXTREME RISK - Likely ruin"
        
        return KellyResult(
            full_kelly=full_kelly,
            half_kelly=full_kelly / 2,
            quarter_kelly=full_kelly / 4,
            edge=edge * 100,  # as percentage
            expected_growth=expected_growth,
            ruin_risk_full=assess_risk(full_kelly),
            ruin_risk_half=assess_risk(full_kelly / 2)
        )
    
    @staticmethod
    def from_trades(
        trades: list[float],
        bankroll: float = 100000.0
    ) -> KellyResult:
        """
        Calculate Kelly from actual trade P&L list.
        
        Example trades: [150, -100, 200, -100, 300, -100]  # R-multiples or $
        """
        if len(trades) < 10:
            raise ValueError("Need at least 10 trades for reliable stats")
        
        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t < 0]
        
        if not wins or not losses:
            raise ValueError("Need both winning and losing trades")
        
        win_rate = len(wins) / len(trades)
        avg_win = sum(wins) / len(wins)
        avg_loss = abs(sum(losses) / len(losses))
        
        return KellyCalculator.calculate(win_rate, avg_win, avg_loss, bankroll)
    
    @staticmethod
    def position_size(
        kelly_result: KellyResult,
        bankroll: float,
        kelly_fraction: float = 0.5,  # Use half Kelly by default
        stop_loss_amount: float = 1000.0  # $ risk per share/contract
    ) -> dict:
        """
        Convert Kelly fraction to actual position size.
        """
        kelly_pct = kelly_result.full_kelly * kelly_fraction
        capital_to_risk = bankroll * kelly_pct
        
        # Position size = (Bankroll × Kelly%) / Stop loss per unit
        if stop_loss_amount > 0:
            position_units = capital_to_risk / stop_loss_amount
        else:
            position_units = 0
        
        return {
            "kelly_fraction_used": kelly_fraction,
            "capital_to_deploy": round(capital_to_risk, 2),
            "position_units": round(position_units, 4),
            "stop_loss_per_unit": stop_loss_amount,
            "percent_of_account": round(kelly_pct * 100, 2)
        }


# --- Examples ---

if __name__ == "__main__":
    calc = KellyCalculator()
    
    print("=" * 50)
    print("SCENARIO 1: Good Strategy")
    print("Win rate: 55%, Avg win: $200, Avg loss: $100")
    
    result = calc.calculate(
        win_rate=0.55,
        avg_win=200,
        avg_loss=100,
        current_bankroll=50000
    )
    print(result)
    
    sizing = calc.position_size(result, 50000, kelly_fraction=0.5, stop_loss_amount=100)
    print(f"\nWith $100 stop: Buy {sizing['position_units']} shares")
    print(f"Capital at risk: ${sizing['capital_to_deploy']}")
    
    print("\n" + "=" * 50)
    print("SCENARIO 2: From Trade History")
    
    # Simulated 6-month trade history (R-multiples)
    trade_history = [
        2.0, -1.0, 1.5, -1.0, 3.0, -1.0,  # Week 1
        2.5, -1.0, -1.0, 1.8, -1.0, 2.2,  # Week 2
        -1.0, 2.0, -1.0, 1.5, -1.0, 2.8,  # Week 3
        1.2, -1.0, 2.0, -1.0, 1.5, -1.0,  # Week 4
        -1.0, -1.0, 3.0, 1.5, -1.0, 2.0,  # Week 5
    ]
    
    result2 = calc.from_trades(trade_history, bankroll=50000)
    print(result2)
    
    print("\n" + "=" * 50)
    print("SCENARIO 3: Negative Edge (Don't Trade)")
    
    result3 = calc.calculate(
        win_rate=0.48,
        avg_win=100,
        avg_loss=100
    )
    print(f"Full Kelly: {result3.full_kelly:.2%}")
    print(f"Assessment: {result3.ruin_risk_full}")
```

## Key Principles

| Kelly Level | Risk | Use When |
|-------------|------|----------|
| **Full** | High | Backtested, stable edge, small % of total wealth |
| **Half** | Moderate | Recommended default. 75% of growth, 1/4 the variance |
| **Quarter** | Low | New strategies, volatile markets, large account |

## Practical Rules

```python
# Never bet full Kelly in trading
kelly = calculate_kelly(stats)
position_pct = kelly.half_kelly  # Or quarter_kelly

# If Kelly suggests > 25% of account, cap it
max_position = 0.25
actual_position = min(kelly.half_kelly, max_position)

# If Kelly is negative, don't trade
if kelly.full_kelly <= 0:
    print("No edge - stay in cash")
```

## Why This Matters

- **Full Kelly** maximizes growth but has 50% drawdowns as "normal"
- **Half Kelly** gives 75% of growth with 1/4 the risk of ruin
- Prevents overbetting when win rate is overestimated
- Mathematical proof that betting more than Kelly → certain ruin

---

**Created by Ghost 👻 | Feb 19, 2026 | 14-min learning sprint**  
*Reference: "The Kelly Capital Growth Investment Criterion" - MacLean, Thorp, Ziemba*
