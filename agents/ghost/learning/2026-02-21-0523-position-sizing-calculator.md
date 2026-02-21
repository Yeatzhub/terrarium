# Position Sizing Calculator CLI
*Ghost Learning | 2026-02-21*

A lightning-fast CLI for calculating position sizes using multiple methods. Copy-paste ready.

```python
#!/usr/bin/env python3
"""
Position Sizing Calculator
Usage: python position_sizer.py <method> [options]

Methods:
  fixed    - Fixed % of account per trade
  kelly    - Kelly Criterion (fractional)
  atr      - ATR-based volatility sizing
  risk     - Fixed $ risk amount
"""

import sys
import argparse
from decimal import Decimal, ROUND_DOWN
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class PositionSize:
    """Result with all relevant metrics."""
    shares: Decimal
    position_value: Decimal
    risk_amount: Decimal
    risk_pct: Decimal
    method: str


class PositionSizer:
    """Multiple position sizing methods for different strategies."""
    
    def __init__(self, account_size: Decimal):
        self.account = account_size
    
    # === Method 1: Fixed Percentage ===
    def fixed_pct(self, entry: Decimal, stop: Decimal, pct: Decimal = Decimal("0.02")) -> PositionSize:
        """Risk fixed % of account per trade."""
        risk_amount = self.account * pct
        risk_per_share = abs(entry - stop)
        shares = (risk_amount / risk_per_share).quantize(Decimal("0.0001"), rounding=ROUND_DOWN)
        
        return PositionSize(
            shares=shares,
            position_value=shares * entry,
            risk_amount=risk_amount,
            risk_pct=pct * 100,
            method="fixed_pct"
        )
    
    # === Method 2: Kelly Criterion ===
    def kelly(self, win_rate: Decimal, avg_win: Decimal, avg_loss: Decimal, 
              fraction: Decimal = Decimal("0.25")) -> PositionSize:
        """Kelly C = (WR * W - LR * L) / W. Uses fraction for safety."""
        loss_rate = 1 - win_rate
        kelly_pct = (win_rate * avg_win - loss_rate * avg_loss) / avg_win
        
        if kelly_pct <= 0:
            return PositionSize(
                shares=Decimal("0"), position_value=Decimal("0"),
                risk_amount=Decimal("0"), risk_pct=Decimal("0"), method="kelly"
            )
        
        adjusted_pct = kelly_pct * fraction
        position_value = self.account * adjusted_pct
        
        # Estimate risk based on avg_loss ratio
        risk_amount = position_value * (avg_loss / avg_win)
        
        return PositionSize(
            shares=Decimal("N/A"),  # Need entry price for shares
            position_value=position_value,
            risk_amount=risk_amount,
            risk_pct=adjusted_pct * 100,
            method=f"kelly_{fraction}"
        )
    
    # === Method 3: ATR-Based Volatility ===
    def atr_based(self, entry: Decimal, atr: Decimal, 
                  risk_mult: Decimal = Decimal("2"), risk_pct: Decimal = Decimal("0.02")) -> PositionSize:
        """Size by volatility: stop = entry - (ATR * multiplier)."""
        risk_amount = self.account * risk_pct
        risk_per_share = atr * risk_mult
        shares = (risk_amount / risk_per_share).quantize(Decimal("0.0001"), rounding=ROUND_DOWN)
        
        return PositionSize(
            shares=shares,
            position_value=shares * entry,
            risk_amount=risk_amount,
            risk_pct=risk_pct * 100,
            method=f"atr_{risk_mult}x"
        )
    
    # === Method 4: Fixed Dollar Risk ===
    def fixed_risk(self, entry: Decimal, stop: Decimal, dollar_risk: Decimal) -> PositionSize:
        """Risk exactly $X per trade."""
        risk_per_share = abs(entry - stop)
        shares = (dollar_risk / risk_per_share).quantize(Decimal("0.0001"), rounding=ROUND_DOWN)
        
        return PositionSize(
            shares=shares,
            position_value=shares * entry,
            risk_amount=dollar_risk,
            risk_pct=(dollar_risk / self.account) * 100,
            method="fixed_$"
        )


def fmt_currency(d: Decimal) -> str:
    """Pretty print currency."""
    return f"${d:,.2f}"


def main():
    parser = argparse.ArgumentParser(description="Position Sizing Calculator")
    parser.add_argument("--account", "-a", type=Decimal, default=Decimal("10000"), help="Account size")
    parser.add_argument("--entry", "-e", type=Decimal, required=True, help="Entry price")
    parser.add_argument("--stop", "-s", type=Decimal, help="Stop price")
    parser.add_argument("--atr", type=Decimal, help="ATR value for volatility sizing")
    parser.add_argument("--win-rate", "-w", type=Decimal, help="Win rate (0-1) for Kelly")
    parser.add_argument("--avg-win", type=Decimal, help="Average win $ for Kelly")
    parser.add_argument("--avg-loss", type=Decimal, help="Average loss $ for Kelly")
    parser.add_argument("--risk-pct", "-r", type=Decimal, default=Decimal("0.02"), help="Risk %% of account")
    parser.add_argument("--dollar-risk", "-d", type=Decimal, help="Fixed $ risk amount")
    parser.add_argument("--method", "-m", choices=["fixed", "kelly", "atr", "risk"], 
                       default="fixed", help="Sizing method")
    
    args = parser.parse_args()
    
    sizer = PositionSizer(args.account)
    
    # Calculate based on method
    if args.method == "fixed":
        if not args.stop:
            print("Error: --stop required for fixed method")
            sys.exit(1)
        result = sizer.fixed_pct(args.entry, args.stop, args.risk_pct)
        
    elif args.method == "kelly":
        if not all([args.win_rate, args.avg_win, args.avg_loss]):
            print("Error: --win-rate, --avg-win, --avg-loss required for Kelly")
            sys.exit(1)
        result = sizer.kelly(args.win_rate, args.avg_win, args.avg_loss)
        
    elif args.method == "atr":
        if not args.atr:
            print("Error: --atr required for ATR method")
            sys.exit(1)
        result = sizer.atr_based(args.entry, args.atr, risk_pct=args.risk_pct)
        
    elif args.method == "risk":
        if not args.stop or not args.dollar_risk:
            print("Error: --stop and --dollar-risk required for fixed $ risk")
            sys.exit(1)
        result = sizer.fixed_risk(args.entry, args.stop, args.dollar_risk)
    
    # Output
    print(f"\n{'='*50}")
    print(f"Position Sizing | {result.method.upper()}")
    print(f"{'='*50}")
    print(f"Account:        {fmt_currency(args.account)}")
    print(f"Entry:          ${args.entry}")
    print(f"{'='*50}")
    print(f"Shares:         {result.shares}")
    print(f"Position Value: {fmt_currency(result.position_value)}")
    print(f"Risk Amount:    {fmt_currency(result.risk_amount)}")
    print(f"Risk %%:        {result.risk_pct:.2f}%")
    print(f"{'='*50}\n")


# === Quick Examples ===

# 1. Fixed % risk: 2% of $10k account, entry $100, stop $95
# python position_sizer.py -e 100 -s 95 -r 0.02
# Result: 40 shares, $4k position, $200 risk (2%)

# 2. Kelly Criterion: 55% win rate, avg win $200, avg loss $100
# python position_sizer.py -m kelly -e 100 -w 0.55 --avg-win 200 --avg-loss 100

# 3. ATR-based: 2x ATR stop, $10 ATR, $150 entry
# python position_sizer.py -m atr -e 150 --atr 10 -r 0.015
# Result: 7.5 shares, $1,125 position, $150 risk (1.5%)

# 4. Fixed $ risk: Risk exactly $500
# python position_sizer.py -m risk -e 50 -s 45 --dollar-risk 500
# Result: 100 shares, $5k position, $500 risk


if __name__ == "__main__":
    main()
```

## Quick Start

```bash
# Save as position_sizer.py, make executable
chmod +x position_sizer.py

# Fixed % risk (2% of account, $100 entry, $95 stop)
python position_sizer.py -e 100 -s 95 -r 0.02

# Kelly sizing (55% win rate, $200 avg win, $100 avg loss)
python position_sizer.py -m kelly -e 100 -w 0.55 --avg-win 200 --avg-loss 100

# Volatility-based (2x ATR stop)
python position_sizer.py -m atr -e 150 --atr 10 -r 0.015

# Fixed dollar risk ($500 max loss)
python position_sizer.py -m risk -e 50 -s 45 --dollar-risk 500
```

## Key Design Decisions

- **Decimal**: No float rounding errors in money calculations
- **Frozen dataclass result**: Immutable, hashable, safe to cache
- **Method separation**: Each strategy isolated, easy to add more
- **CLI first**: Designed for quick terminal use during market hours
- **Fail fast**: Required args checked, clear error messages

## When to Use Each Method

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| Fixed % | Consistent risk per trade | Simple, predictable | Doesn't account for setup quality |
| Kelly | Proven edge, historical stats | Optimal growth | High variance, requires accurate stats |
| ATR | Volatile markets | Adapts to volatility | Needs ATR data |
| Fixed $ | Absolute capital preservation | Hard limit on loss | % of account varies |

---
*Utility: position_sizing_calculator.py | Ready to use*
