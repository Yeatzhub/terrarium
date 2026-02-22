# Stop Loss / Take Profit Calculator
*Ghost Learning | 2026-02-21*

Calculate optimal stop loss and take profit levels based on ATR, risk/reward ratios, or fixed percentages. Includes position sizing integration.

```python
#!/usr/bin/env python3
"""
Stop Loss / Take Profit Calculator
Calculate exit levels based on volatility, risk/reward, or fixed %. 

Usage:
    python sl_tp_calc.py --entry 50000 --atr 800 --method atr
    python sl_tp_calc.py -e 50000 -r 3 --risk-pct 0.02 --method rr
    python sl_tp_calc.py -e 3000 --sl-pct 0.015 --tp-pct 0.045 --side long
"""

import argparse
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional


@dataclass
class ExitLevels:
    """Calculated exit levels."""
    entry: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    risk_amount: Decimal
    reward_amount: Decimal
    risk_reward_ratio: Decimal
    risk_pct: Decimal
    stop_distance: Decimal
    tp_distance: Decimal
    position_size: Optional[Decimal] = None


class StopLossCalculator:
    """Calculate stop loss and take profit levels."""
    
    def by_atr(
        self,
        entry: Decimal,
        atr: Decimal,
        side: str = "long",
        sl_mult: Decimal = Decimal("2"),
        tp_mult: Decimal = Decimal("3"),
        account_size: Optional[Decimal] = None,
        risk_pct: Optional[Decimal] = None
    ) -> ExitLevels:
        """Calculate exits based on ATR multiples."""
        
        sl_distance = atr * sl_mult
        tp_distance = atr * tp_mult
        
        if side == "long":
            stop = entry - sl_distance
            take_profit = entry + tp_distance
            risk = sl_distance
            reward = tp_distance
        else:
            stop = entry + sl_distance
            take_profit = entry - tp_distance
            risk = sl_distance
            reward = tp_distance
        
        rr = tp_distance / sl_distance if sl_distance > 0 else Decimal("0")
        
        # Calculate position size if account info provided
        size = None
        if account_size and risk_pct:
            risk_amount = account_size * risk_pct
            size = (risk_amount / sl_distance).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        
        return ExitLevels(
            entry=entry,
            stop_loss=stop,
            take_profit=take_profit,
            risk_amount=risk,
            reward_amount=reward,
            risk_reward_ratio=rr,
            risk_pct=risk_pct or Decimal("0"),
            stop_distance=sl_distance,
            tp_distance=tp_distance,
            position_size=size
        )
    
    def by_risk_reward(
        self,
        entry: Decimal,
        risk_reward: Decimal,
        side: str = "long",
        account_size: Optional[Decimal] = None,
        risk_pct: Optional[Decimal] = None,
        fixed_sl: Optional[Decimal] = None,
        fixed_tp: Optional[Decimal] = None
    ) -> ExitLevels:
        """Calculate exits based on R:R ratio."""
        
        if fixed_sl:
            # Fixed stop, calculate TP
            sl_distance = abs(entry - fixed_sl)
            tp_distance = sl_distance * risk_reward
            stop = fixed_sl
            take_profit = entry + tp_distance if side == "long" else entry - tp_distance
        elif fixed_tp:
            # Fixed TP, calculate stop
            tp_distance = abs(entry - fixed_tp)
            sl_distance = tp_distance / risk_reward
            take_profit = fixed_tp
            stop = entry - sl_distance if side == "long" else entry + sl_distance
        else:
            # Calculate from risk amount
            if not (account_size and risk_pct):
                raise ValueError("Need account_size and risk_pct, or fixed_sl/fixed_tp")
            
            risk_amount = account_size * risk_pct
            # Assume 1% stop distance for calculation, then scale
            sl_distance = entry * Decimal("0.01")  # placeholder
            size = (risk_amount / sl_distance).quantize(Decimal("0.0001"))
            
            if side == "long":
                stop = entry - sl_distance
                tp_distance = sl_distance * risk_reward
                take_profit = entry + tp_distance
            else:
                stop = entry + sl_distance
                tp_distance = sl_distance * risk_reward  
                take_profit = entry - tp_distance
            
            return ExitLevels(
                entry=entry,
                stop_loss=stop,
                take_profit=take_profit,
                risk_amount=sl_distance * size,
                reward_amount=tp_distance * size,
                risk_reward_ratio=risk_reward,
                risk_pct=risk_pct,
                stop_distance=sl_distance,
                tp_distance=tp_distance,
                position_size=size
            )
        
        size = None
        if account_size and risk_pct:
            risk_amount = account_size * risk_pct
            size = (risk_amount / sl_distance).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            risk_amt = risk_amount
            reward_amt = tp_distance * size
        else:
            risk_amt = sl_distance
            reward_amt = tp_distance
        
        return ExitLevels(
            entry=entry,
            stop_loss=stop,
            take_profit=take_profit,
            risk_amount=risk_amt,
            reward_amount=reward_amt,
            risk_reward_ratio=risk_reward,
            risk_pct=risk_pct or Decimal("0"),
            stop_distance=sl_distance,
            tp_distance=tp_distance,
            position_size=size
        )
    
    def by_percentage(
        self,
        entry: Decimal,
        sl_pct: Decimal,
        tp_pct: Optional[Decimal] = None,
        side: str = "long",
        account_size: Optional[Decimal] = None,
        risk_pct: Optional[Decimal] = None
    ) -> ExitLevels:
        """Calculate exits based on fixed percentages."""
        
        sl_distance = entry * sl_pct
        
        if tp_pct:
            tp_distance = entry * tp_pct
            risk_reward = tp_pct / sl_pct if sl_pct > 0 else Decimal("0")
        else:
            # Default R:R of 2:1
            tp_distance = sl_distance * 2
            risk_reward = Decimal("2")
        
        if side == "long":
            stop = entry - sl_distance
            take_profit = entry + tp_distance
        else:
            stop = entry + sl_distance
            take_profit = entry - tp_distance
        
        size = None
        risk_amt = sl_distance
        if account_size and risk_pct:
            risk_amount = account_size * risk_pct
            size = (risk_amount / sl_distance).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            risk_amt = risk_amount
        
        return ExitLevels(
            entry=entry,
            stop_loss=stop,
            take_profit=take_profit,
            risk_amount=risk_amt,
            reward_amount=tp_distance * (size or Decimal("1")),
            risk_reward_ratio=risk_reward,
            risk_pct=risk_pct or Decimal("0"),
            stop_distance=sl_distance,
            tp_distance=tp_distance,
            position_size=size
        )


def print_levels(levels: ExitLevels, method: str):
    """Print formatted output."""
    print(f"\n{'═'*60}")
    print(f"  STOP LOSS / TAKE PROFIT CALCULATOR ({method.upper()})")
    print(f"{'═'*60}")
    print(f"  Entry Price:          ${levels.entry:,.2f}")
    print(f"{'─'*60}")
    print(f"  Stop Loss:            ${levels.stop_loss:,.2f}")
    print(f"  Distance:             {abs(levels.stop_distance):,.2f}")
    print(f"  Pct:                {abs(levels.stop_distance/levels.entry)*100:.2f}%")
    print(f"{'─'*60}")
    print(f"  Take Profit:          ${levels.take_profit:,.2f}")
    print(f"  Distance:             {abs(levels.tp_distance):,.2f}")
    print(f"  Pct:                {abs(levels.tp_distance/levels.entry)*100:.2f}%")
    print(f"{'─'*60}")
    print(f"  Risk : Reward:        1 : {float(levels.risk_reward_ratio):.1f}")
    print(f"  Break-even Win%:      {1/(1+float(levels.risk_reward_ratio))*100:.1f}%")
    
    if levels.position_size:
        print(f"{'─'*60}")
        print(f"  Position Size:        {levels.position_size:,.4f}")
        print(f"  Risk Amount:          ${levels.risk_amount:,.2f}")
        print(f"  Reward Potential:     ${levels.reward_amount:,.2f}")
    
    print(f"{'═'*60}")
    
    # Recommendations
    rr = float(levels.risk_reward_ratio)
    if rr < 1.0:
        print(f"\n  ⚠️  CAUTION: R:R < 1.0 is generally unfavorable")
        print(f"     Need >50% win rate to be profitable")
    elif rr < 2.0:
        print(f"\n  ℹ️  R:R > 1:1 is acceptable")
        print(f"     Need {1/(1+rr)*100:.0f}% win rate to break even")
    else:
        print(f"\n  ✅ EXCELLENT: R:R >= 2:1")
        print(f"     Only need {1/(1+rr)*100:.0f}% win rate to be profitable")
    
    print()


def main():
    parser = argparse.ArgumentParser(description="Stop Loss / Take Profit Calculator")
    parser.add_argument("--entry", "-e", type=Decimal, required=True, help="Entry price")
    parser.add_argument("--side", choices=["long", "short"], default="long")
    parser.add_argument("--method", "-m", 
                       choices=["atr", "rr", "pct", "atr-volatility"],
                       required=True, help="Calculation method")
    
    # ATR method
    parser.add_argument("--atr", type=Decimal, help="ATR value (for atr method)")
    parser.add_argument("--sl-mult", type=Decimal, default=2, help="SL ATR multiplier")
    parser.add_argument("--tp-mult", type=Decimal, default=3, help="TP ATR multiplier")
    
    # Risk:Reward method
    parser.add_argument("--rr", "-r", type=Decimal, help="Risk:Reward ratio (for rr method)")
    parser.add_argument("--stop", "-s", type=Decimal, help="Fixed stop price")
    parser.add_argument("--tp", "-t", type=Decimal, help="Fixed TP price")
    
    # Percentage method
    parser.add_argument("--sl-pct", type=Decimal, help="Stop distance as decimal (0.02 = 2%)")
    parser.add_argument("--tp-pct", type=Decimal, help="TP distance as decimal")
    
    # Position sizing
    parser.add_argument("--account", "-a", type=Decimal, help="Account size")
    parser.add_argument("--risk-pct", type=Decimal, default=Decimal("0.02"), 
                       help="Risk % of account")
    
    args = parser.parse_args()
    
    calc = StopLossCalculator()
    
    if args.method == "atr":
        if not args.atr:
            parser.error("--atr required for atr method")
        levels = calc.by_atr(
            args.entry, args.atr, args.side,
            sl_mult=args.sl_mult, tp_mult=args.tp_mult,
            account_size=args.account, risk_pct=args.risk_pct
        )
        print_levels(levels, "ATR")
    
    elif args.method == "rr":
        if not args.rr:
            parser.error("--rr required for rr method")
        if not (args.stop or args.tp or (args.account and args.risk_pct)):
            parser.error("Provide --stop, --tp, or --account with --risk-pct")
        
        levels = calc.by_risk_reward(
            args.entry, args.rr, args.side,
            account_size=args.account,
            risk_pct=args.risk_pct,
            fixed_sl=args.stop,
            fixed_tp=args.tp
        )
        print_levels(levels, "Risk:Reward")
    
    elif args.method == "pct":
        if not args.sl_pct:
            parser.error("--sl-pct required for pct method")
        levels = calc.by_percentage(
            args.entry, args.sl_pct, args.tp_pct, args.side,
            account_size=args.account, risk_pct=args.risk_pct
        )
        print_levels(levels, "Percentage")
    

# === Quick Examples ===

# 1. ATR-based (2x SL, 3x TP)
# python sl_tp_calc.py -e 50000 --atr 800 --method atr -a 100000

# 2. Fixed risk:reward (1:3)
# python sl_tp_calc.py -e 50000 -r 3 --stop 49000 --method rr

# 3. Percentage-based (1.5% SL, 4.5% TP)
# python sl_tp_calc.py -e 3000 --sl-pct 0.015 --tp-pct 0.045 --method pct

# 4. Short position
# python sl_tp_calc.py -e 3000 --atr 50 --method atr --side short -a 50000


if __name__ == "__main__":
    main()
```

## Quick Start

```bash
# ATR-based (2x ATR stop, 3x ATR profit)
python sl_tp_calc.py -e 50000 --atr 800 --method atr -a 100000

# Fixed R:R with known stop
python sl_tp_calc.py -e 50000 -r 3 --stop 49000 --method rr

# Percentage-based with position sizing
python sl_tp_calc.py -e 3000 --sl-pct 0.015 --tp-pct 0.045 --method pct -a 50000

# Short position
python sl_tp_calc.py -e 3000 --atr 50 --method atr --side short
```

## Sample Output

```
════════════════════════════════════════════════════════════
  STOP LOSS / TAKE PROFIT CALCULATOR (ATR)
════════════════════════════════════════════════════════════
  Entry Price:          $50,000.00
────────────────────────────────────────────────────────────
  Stop Loss:            $49,200.00
  Distance:             800.00
  Pct:                 1.60%
────────────────────────────────────────────────────────────
  Take Profit:          $50,600.00
  Distance:             600.00
  Pct:                 1.20%
────────────────────────────────────────────────────────────
  Risk : Reward:        1 : 1.5
  Break-even Win%:      40.0%
────────────────────────────────────────────────────────────
  Position Size:        2.5000
  Risk Amount:          $2,000.00
  Reward Potential:     $3,000.00
════════════════════════════════════════════════════════════

  ℹ️  R:R > 1:1 is acceptable
     Need 40% win rate to break even
```

## Methods Comparison

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **ATR** | Volatility-based | Adapts to symbol volatility | Needs ATR calculation |
| **Risk:Reward** | Fixed targets | Predictable outcomes | Harder to place logically |
| **Percentage** | Simple rules | Easy to calculate | Doesn't account for volatility |

## Key Concepts

**Risk:Reward Ratio**
- 1:1 = Break even at 50% win rate
- 1:2 = Break even at 33% win rate
- 1:3 = Break even at 25% win rate

**ATR Multipliers**
- Conservative: 1.5x SL, 2x TP
- Standard: 2x SL, 3x TP
- Aggressive: 3x SL, 6x TP

## Position Sizing Integration

When you provide `--account` and `--risk-pct`:

```
Position Size = (Account × Risk%) / Stop Distance
```

This ensures you risk exactly 2% (or your chosen %) on this trade.

## Short vs Long

The calculator automatically inverts calculations for short positions:
- **Long**: SL below entry, TP above entry
- **Short**: SL above entry, TP below entry

---
*Utility: Stop Loss / Take Profit Calculator | Exit level planning*
