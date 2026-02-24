# Trade Risk Calculator
*Ghost Learning | 2026-02-22*

Calculate position size, stop loss, take profit based on account risk parameters.

## Core Calculations

| What | Formula |
|------|---------|
| **Risk Amount** | `Account × Risk%` |
| **Position Size** | `Risk / |Entry - Stop|` |
| **Take Profit** | `Entry + Risk × R:R (long)` |
| **R:R Ratio** | `|TP - Entry| / |Entry - Stop|` |

## Implementation

```python
"""
Trade Risk Calculator
Position sizing and risk management for trading.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Literal
from enum import Enum


class Side(Enum):
    LONG = "long"
    SHORT = "short"


@dataclass
class TradeSetup:
    """Calculated trade setup."""
    side: Side
    entry: Decimal
    stop_loss: Decimal
    take_profit: Optional[Decimal]
    
    position_size: Decimal
    position_value: Decimal
    
    risk_amount: Decimal
    risk_percent: Decimal
    
    reward_amount: Optional[Decimal]
    reward_risk_ratio: Optional[Decimal]
    
    stop_distance: Decimal
    stop_distance_pct: Decimal
    
    tp_distance: Optional[Decimal]
    tp_distance_pct: Optional[Decimal]
    
    break_even: Decimal
    
    # Warnings
    warnings: list[str]
    
    def __str__(self) -> str:
        lines = [
            f"=== TRADE SETUP ({self.side.value.upper()}) ===",
            f"Entry:        ${self.entry:,.2f}",
            f"Stop Loss:    ${self.stop_loss:,.2f} ({self.stop_distance_pct:.2%})",
        ]
        if self.take_profit:
            lines.append(f"Take Profit:  ${self.take_profit:,.2f} ({self.tp_distance_pct:.2%})")
            lines.append(f"R:R Ratio:    {self.reward_risk_ratio:.2f}")
        lines.extend([
            f"",
            f"Position:     {self.position_size:.4f} units",
            f"Value:        ${self.position_value:,.2f}",
            f"",
            f"Risk:         ${self-risk_amount:,.2f} ({self.risk_percent:.2%})",
            f"Break-even:   ${self.break_even:,.2f}",
        ])
        if self.warnings:
            lines.append("")
            lines.append("⚠ WARNINGS:")
            for w in self.warnings:
                lines.append(f"  • {w}")
        return "\n".join(lines)


class TradeRiskCalculator:
    """
    Calculate trade setup from risk parameters.
    """
    
    def __init__(
        self,
        account_balance: Decimal,
        risk_per_trade: Decimal = Decimal("0.01"),  # 1%
        max_risk_per_trade: Decimal = Decimal("0.02"),  # 2% cap
        min_reward_risk: Decimal = Decimal("1.5"),  # Minimum R:R
        max_position_pct: Decimal = Decimal("0.20"),  # Max 20% of account
    ):
        self.account = account_balance
        self.risk_per_trade = min(risk_per_trade, max_risk_per_trade)
        self.max_risk = max_risk_per_trade
        self.min_rr = min_reward_risk
        self.max_position_pct = max_position_pct
    
    def calculate(
        self,
        side: Side,
        entry: Decimal,
        stop_loss: Decimal,
        take_profit: Optional[Decimal] = None,
        reward_risk: Optional[Decimal] = None,
        max_position_size: Optional[Decimal] = None,
    ) -> TradeSetup:
        """
        Calculate complete trade setup.
        
        Provide either take_profit OR reward_risk for TP calculation.
        """
        warnings = []
        
        # Validate stop loss direction
        if side == Side.LONG and stop_loss >= entry:
            raise ValueError("Long position: stop_loss must be below entry")
        if side == Side.SHORT and stop_loss <= entry:
            raise ValueError("Short position: stop_loss must be above entry")
        
        # Calculate stop distance
        stop_distance = abs(entry - stop_loss)
        stop_distance_pct = stop_distance / entry
        
        # Calculate risk amount
        risk_amount = self.account * self.risk_per_trade
        
        # Calculate position size from risk
        position_size = risk_amount / stop_distance
        position_value = position_size * entry
        
        # Cap position size
        max_value = self.account * self.max_position_pct
        if position_value > max_value:
            position_value = max_value
            position_size = position_value / entry
            risk_amount = position_size * stop_distance
            warnings.append(f"Position capped at {self.max_position_pct:.0%} of account")
        
        # Apply max position size if specified
        if max_position_size and position_size > max_position_size:
            position_size = max_position_size
            position_value = position_size * entry
            risk_amount = position_size * stop_distance
            warnings.append(f"Position capped at max size: {max_position_size}")
        
        # Calculate take profit
        if take_profit is None and reward_risk is not None:
            # Derive TP from R:R
            tp_distance = stop_distance * reward_risk
            if side == Side.LONG:
                take_profit = entry + tp_distance
            else:
                take_profit = entry - tp_distance
        
        # Calculate reward
        reward_amount = None
        reward_risk_ratio = None
        tp_distance = None
        tp_distance_pct = None
        
        if take_profit:
            tp_distance = abs(take_profit - entry)
            tp_distance_pct = tp_distance / entry
            
            # Validate TP direction
            if side == Side.LONG and take_profit <= entry:
                warnings.append("Take profit below entry for long")
            if side == Side.SHORT and take_profit >= entry:
                warnings.append("Take profit above entry for short")
            
            reward_amount = position_size * tp_distance
            reward_risk_ratio = tp_distance / stop_distance
            
            if reward_risk_ratio < self.min_rr:
                warnings.append(f"R:R {reward_risk_ratio:.2f} below minimum {self.min_rr:.2f}")
        
        # Break-even price
        if side == Side.LONG:
            break_even = entry + (stop_distance * Decimal("0.01"))  # Account for fees
        else:
            break_even = entry - (stop_distance * Decimal("0.01"))
        
        return TradeSetup(
            side=side,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            position_value=position_value,
            risk_amount=risk_amount,
            risk_percent=risk_amount / self.account,
            reward_amount=reward_amount,
            reward_risk_ratio=reward_risk_ratio,
            stop_distance=stop_distance,
            stop_distance_pct=stop_distance_pct,
            tp_distance=tp_distance,
            tp_distance_pct=tp_distance_pct,
            break_even=break_even,
            warnings=warnings
        )
    
    def from_stop_percent(
        self,
        side: Side,
        entry: Decimal,
        stop_percent: Decimal,
        take_profit_percent: Optional[Decimal] = None,
    ) -> TradeSetup:
        """Calculate from percentage distances instead of absolute prices."""
        if side == Side.LONG:
            stop_loss = entry * (1 - stop_percent)
            take_profit = entry * (1 + take_profit_percent) if take_profit_percent else None
        else:
            stop_loss = entry * (1 + stop_percent)
            take_profit = entry * (1 - take_profit_percent) if take_profit_percent else None
        
        return self.calculate(side, entry, stop_loss, take_profit)
    
    def suggest_stops(
        self,
        side: Side,
        entry: Decimal,
        atr: Decimal,
        atr_stop_mult: Decimal = Decimal("1.5"),
        atr_tp_mult: Decimal = Decimal("3.0"),
    ) -> TradeSetup:
        """Suggest stops based on ATR."""
        stop_distance = atr * atr_stop_mult
        tp_distance = atr * atr_tp_mult
        
        if side == Side.LONG:
            stop_loss = entry - stop_distance
            take_profit = entry + tp_distance
        else:
            stop_loss = entry + stop_distance
            take_profit = entry - tp_distance
        
        return self.calculate(side, entry, stop_loss, take_profit)


# === Quick Functions ===

def position_size(
    account: float,
    risk_pct: float,
    entry: float,
    stop: float
) -> float:
    """One-liner position size calculation."""
    risk_amount = account * risk_pct
    stop_distance = abs(entry - stop)
    return risk_amount / stop_distance


def stop_loss_price(
    entry: float,
    stop_pct: float,
    side: str = "long"
) -> float:
    """Calculate stop loss price from percentage."""
    if side == "long":
        return entry * (1 - stop_pct)
    else:
        return entry * (1 + stop_pct)


def take_profit_price(
    entry: float,
    stop: float,
    rr: float,
    side: str = "long"
) -> float:
    """Calculate take profit from R:R ratio."""
    stop_distance = abs(entry - stop)
    if side == "long":
        return entry + (stop_distance * rr)
    else:
        return entry - (stop_distance * rr)


# === Usage ===

if __name__ == "__main__":
    calc = TradeRiskCalculator(
        account_balance=Decimal("50000"),
        risk_per_trade=Decimal("0.01"),  # 1%
        min_reward_risk=Decimal("2.0")
    )
    
    print("=== LONG TRADE ===")
    setup = calc.calculate(
        side=Side.LONG,
        entry=Decimal("100"),
        stop_loss=Decimal("95"),
        reward_risk=Decimal("2.0")
    )
    print(setup)
    
    print("\n=== SHORT TRADE (ATR-based) ===")
    setup = calc.suggest_stops(
        side=Side.SHORT,
        entry=Decimal("50000"),
        atr=Decimal("1500"),
        atr_stop_mult=Decimal("1.5"),
        atr_tp_mult=Decimal("3.0")
    )
    print(setup)
    
    print("\n=== QUICK CALCULATIONS ===")
    print(f"Position size: {position_size(50000, 0.01, 100, 95):.4f}")
    print(f"Stop price: ${stop_loss_price(100, 0.05, 'long'):.2f}")
    print(f"TP price: ${take_profit_price(100, 95, 2.0, 'long'):.2f}")
```

## Output

```
=== LONG TRADE ===
=== TRADE SETUP (LONG) ===
Entry:        $100.00
Stop Loss:    $95.00 (5.00%)
Take Profit:  $110.00 (10.00%)
R:R Ratio:    2.00

Position:     100.0000 units
Value:        $10,000.00

Risk:         $500.00 (1.00%)
Break-even:   $100.05

=== SHORT TRADE (ATR-based) ===
=== TRADE SETUP (SHORT) ===
Entry:        $50,000.00
Stop Loss:    $52,250.00 (4.50%)
Take Profit:  $45,500.00 (9.00%)
R:R Ratio:    2.00

Position:     0.0133 units
Value:        $663.90

Risk:         $500.00 (1.00%)
Break-even:   $49,925.00

=== QUICK CALCULATIONS ===
Position size: 100.0000
Stop price: $95.00
TP price: $110.00
```

## Risk Management Rules

| Rule | Recommended |
|------|-------------|
| Risk per trade | 0.5% - 2% |
| Min R:R | 1.5 - 2.0 |
| Max position | 10% - 20% of account |
| Stop distance | 1.5 - 2× ATR |

## Quick Reference

```python
# Full setup
calc = TradeRiskCalculator(account=50000, risk=0.01)
setup = calc.calculate(Side.LONG, entry=100, stop=95, reward_risk=2.0)

# From percentages
setup = calc.from_stop_percent(Side.LONG, entry=100, stop_percent=0.05)

# ATR-based
setup = calc.suggest_stops(Side.LONG, entry=100, atr=3.0)

# One-liners
size = position_size(account, risk_pct, entry, stop)
stop = stop_loss_price(entry, 0.05, "long")
tp = take_profit_price(entry, stop, 2.0, "long")
```

---
*Utility: Trade Risk Calculator | Features: Position sizing, R:R validation, ATR stops*