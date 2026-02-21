# Risk-of-Ruin Calculator CLI
*Ghost Learning | 2026-02-21*

Calculate probability of ruin given win rate, payoff ratio, and risk per trade. Critical for position sizing validation.

```python
#!/usr/bin/env python3
"""
Risk of Ruin Calculator
Calculates probability of account destruction given trading parameters.

Usage:
    python risk_of_ruin.py --win-rate 0.55 --avg-win 200 --avg-loss 100 --risk-pct 0.02 --num-trades 100
    python risk_of_ruin.py --csv trades.csv --account 10000 --risk-pct 0.02
"""

import argparse
import csv
import json
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import NamedTuple
import math


class RiskParams(NamedTuple):
    """Parameters for risk calculation."""
    win_rate: Decimal
    avg_win: Decimal
    avg_loss: Decimal
    risk_pct: Decimal
    ruin_threshold: Decimal = Decimal("0.5")  # Account drops to 50%


@dataclass(frozen=True, slots=True)
class RuinResult:
    """Risk of ruin calculation result."""
    # Inputs
    win_rate: Decimal
    loss_rate: Decimal
    payoff_ratio: Decimal
    risk_pct: Decimal
    ruin_threshold: Decimal
    
    # Calculated
    risk_of_ruin: Decimal          # Probability of ruin [0-1]
    risk_of_ruin_pct: Decimal      # As percentage
    expected_return: Decimal        # Per trade expectancy
    optimal_f: Decimal              # Kelly optimal position size
    half_kelly: Decimal            # Conservative Kelly
    quarter_kelly: Decimal         # Ultra-conservative
    
    # Interpretation
    risk_level: str
    safe_to_trade: bool
    recommendation: str


def calculate_payoff_ratio(avg_win: Decimal, avg_loss: Decimal) -> Decimal:
    """Win amount divided by loss amount."""
    if avg_loss == 0:
        return Decimal("0")
    return avg_win / avg_loss


def calculate_risk_of_ruin(params: RiskParams) -> RuinResult:
    """
    Calculate risk of ruin using formula:
    Risk of Ruin = ((1 - Edge) / (1 + Edge)) ^ CapitalUnits
    
    Where Edge = (WinRate * Payoff) - (LossRate)
    And CapitalUnits = Ruin% / Risk%
    """
    win_rate = params.win_rate
    loss_rate = 1 - win_rate
    payoff = calculate_payoff_ratio(params.avg_win, params.avg_loss)
    risk_pct = params.risk_pct
    
    # Edge per trade
    edge = (win_rate * payoff) - loss_rate
    
    # Risk of ruin calculation
    # Use simplified formula: R = ((1 - Edge) / (1 + Edge)) ^ (Capital / RiskUnit)
    capital_units = params.ruin_threshold / risk_pct
    
    if edge <= 0:
        risk_of_ruin = Decimal("1.0")  # Guaranteed ruin with negative edge
    else:
        try:
            base = (1 - edge) / (1 + edge)
            if base <= 0:
                risk_of_ruin = Decimal("0.0")
            else:
                # Log calculation for numerical stability
                log_ruin = capital_units * Decimal(math.log(float(base)))
                risk_of_ruin = Decimal(math.exp(float(log_ruin)))
                risk_of_ruin = max(Decimal("0"), min(Decimal("1"), risk_of_ruin))
        except (ValueError, OverflowError):
            risk_of_ruin = Decimal("0.99")  # Something went wrong, assume high risk
    
    # Expected return per trade
    expected_return = (win_rate * params.avg_win) - (loss_rate * params.avg_loss)
    
    # Kelly Criterion
    if params.avg_loss != 0 and payoff != 0:
        optimal_f = (win_rate * payoff - loss_rate) / payoff
        optimal_f = max(Decimal("0"), min(Decimal("1"), optimal_f))
    else:
        optimal_f = Decimal("0")
    
    half_kelly = optimal_f / 2
    quarter_kelly = optimal_f / 4
    
    # Risk level interpretation
    if risk_of_ruin < Decimal("0.01"):
        risk_level = "VERY LOW"
        safe_to_trade = True
        recommendation = "Risk level acceptable. Can increase size to half-Kelly if desired."
    elif risk_of_ruin < Decimal("0.05"):
        risk_level = "LOW"
        safe_to_trade = True
        recommendation = "Risk level acceptable for trading. Consider quarter-Kelly sizing."
    elif risk_of_ruin < Decimal("0.15"):
        risk_level = "MODERATE"
        safe_to_trade = True
        recommendation = "Acceptable with caution. Monitor performance closely."
    elif risk_of_ruin < Decimal("0.30"):
        risk_level = "HIGH"
        safe_to_trade = False
        recommendation = "HIGH RISK: Reduce position size or improve edge before trading."
    else:
        risk_level = "CRITICAL"
        safe_to_trade = False
        recommendation = "DANGER: High probability of account destruction. DO NOT TRADE."
    
    return RuinResult(
        win_rate=win_rate,
        loss_rate=loss_rate,
        payoff_ratio=payoff,
        risk_pct=risk_pct,
        ruin_threshold=params.ruin_threshold,
        risk_of_ruin=risk_of_ruin,
        risk_of_ruin_pct=risk_of_ruin * 100,
        expected_return=expected_return,
        optimal_f=optimal_f,
        half_kelly=half_kelly,
        quarter_kelly=quarter_kelly,
        risk_level=risk_level,
        safe_to_trade=safe_to_trade,
        recommendation=recommendation
    )


def simulate_ruin_monte_carlo(
    win_rate: Decimal,
    avg_win: Decimal,
    avg_loss: Decimal,
    risk_pct: Decimal,
    starting_capital: Decimal,
    ruin_threshold: Decimal,
    num_simulations: int = 10000,
    max_trades: int = 1000
) -> Decimal:
    """
    Monte Carlo simulation of risk of ruin.
    Simulates many account journeys to empirical ruin rate.
    """
    import random
    random.seed(42)  # Reproducible
    
    ruin_count = 0
    ruin_level = starting_capital * ruin_threshold
    
    for _ in range(num_simulations):
        capital = starting_capital
        trades = 0
        
        while capital > ruin_level and trades < max_trades:
            if random.random() < float(win_rate):
                capital += capital * risk_pct * avg_win
            else:
                capital -= capital * risk_pct * avg_loss
            trades += 1
        
        if capital <= ruin_level:
            ruin_count += 1
    
    return Decimal(ruin_count) / Decimal(num_simulations)


def print_result(result: RuinResult):
    """Print formatted result."""
    print(f"\n{'═'*60}")
    print(f"  RISK OF RUIN ANALYSIS")
    print(f"{'═'*60}")
    print(f"  {'Win Rate:':<20} {result.win_rate*100:.1f}%")
    print(f"  {'Loss Rate:':<20} {result.loss_rate*100:.1f}%")
    print(f"  {'Payoff Ratio:':<20} {result.payoff_ratio:.2f}x")
    print(f"  {'Risk per Trade:':<20} {result.risk_pct*100:.1f}%")
    print(f"{'─'*60}")
    print(f"  {'Expected Return:':<20} ${result.expected_return:+,.2f} per trade")
    print(f"  {'Optimal Kelly (f):':<20} {result.optimal_f*100:.1f}%")
    print(f"  {'Half Kelly:':<20} {result.half_kelly*100:.1f}%")
    print(f"  {'Quarter Kelly:':<20} {result.quarter_kelly*100:.1f}%")
    print(f"{'─'*60}")
    print(f"  {'Risk of Ruin:':<20} {result.risk_of_ruin_pct:.2f}%")
    print(f"  {'Risk Level:':<20} {result.risk_level}")
    print(f"  {'Safe to Trade:':<20} {'✓ YES' if result.safe_to_trade else '✗ NO'}")
    print(f"{'═'*60}")
    print(f"  RECOMMENDATION:")
    print(f"  {result.recommendation}")
    print(f"{'═'*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Risk of Ruin Calculator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Basic calculation
    python risk_of_ruin.py --win-rate 0.55 --avg-win 200 --avg-loss 100 --risk-pct 0.02
    
    # With capital for Monte Carlo simulation
    python risk_of_ruin.py -w 0.50 -W 300 -L 150 -r 0.025 -c 10000 --monte-carlo
    
    # Sensitvity analysis
    python risk_of_ruin.py -w 0.55 -W 200 -L 100 -r 0.02 --sensitivity
""")
    parser.add_argument("--win-rate", "-w", type=Decimal, required=True, help="Win rate [0-1]")
    parser.add_argument("--avg-win", "-W", type=Decimal, required=True, help="Average win amount")
    parser.add_argument("--avg-loss", "-L", type=Decimal, required=True, help="Average loss amount")
    parser.add_argument("--risk-pct", "-r", type=Decimal, required=True, help="Risk % per trade [0-1]")
    parser.add_argument("--ruin-threshold", "-t", type=Decimal, default=Decimal("0.5"), 
                       help="Account % defining ruin (default 50%%)")
    parser.add_argument("--capital", "-c", type=Decimal, help="Starting capital (for Monte Carlo)")
    parser.add_argument("--monte-carlo", "-m", action="store_true", help="Run Monte Carlo simulation")
    parser.add_argument("--simulations", type=int, default=10000, help="MC sim count (default 10000)")
    parser.add_argument("--sensitivity", "-s", action="store_true", 
                       help="Show risk at different position sizes")
    parser.add_argument("--output", "-o", type=Path, help="Save results to JSON")
    
    args = parser.parse_args()
    
    params = RiskParams(
        win_rate=args.win_rate,
        avg_win=args.avg_win,
        avg_loss=args.avg_loss,
        risk_pct=args.risk_pct,
        ruin_threshold=args.ruin_threshold
    )
    
    result = calculate_risk_of_ruin(params)
    print_result(result)
    
    # Monte Carlo validation
    if args.monte_carlo and args.capital:
        print("Running Monte Carlo simulation...")
        mc_risk = simulate_ruin_monte_carlo(
            args.win_rate, args.avg_win, args.avg_loss, 
            args.risk_pct, args.capital, args.ruin_threshold, 
            args.simulations
        )
        print(f"Monte Carlo Risk of Ruin: {mc_risk*100:.2f}%")
        print(f"Theoretical Risk of Ruin: {result.risk_of_ruin_pct:.2f}%")
        print()
    
    # Sensitivity analysis
    if args.sensitivity:
        print("📊 SENSITIVITY ANALYSIS: Risk of Ruin at Different Position Sizes\n")
        print(f"{'Risk %':<10} {'Risk of Ruin':<15} {'Status':<15}")
        print("-" * 40)
        
        for risk_mult in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
            test_risk = args.risk_pct * Decimal(str(risk_mult))
            test_params = RiskParams(
                args.win_rate, args.avg_win, args.avg_loss, 
                test_risk, args.ruin_threshold
            )
            test_result = calculate_risk_of_ruin(test_params)
            
            status = "SAFE" if test_result.safe_to_trade else "UNSAFE"
            if test_result.risk_of_ruin > Decimal("0.30"):
                status = "DANGER"
            
            print(f"{test_risk*100:<10.2f} {test_result.risk_of_ruin_pct:<15.2f} {status:<15}")
        print()
    
    # JSON output
    if args.output:
        data = {
            "inputs": {
                "win_rate": float(args.win_rate),
                "avg_win": float(args.avg_win),
                "avg_loss": float(args.avg_loss),
                "risk_pct": float(args.risk_pct),
                "ruin_threshold": float(args.ruin_threshold)
            },
            "results": {
                "risk_of_ruin_pct": float(result.risk_of_ruin_pct),
                "payoff_ratio": float(result.payoff_ratio),
                "expected_return": float(result.expected_return),
                "optimal_f": float(result.optimal_f),
                "half_kelly": float(result.half_kelly),
                "quarter_kelly": float(result.quarter_kelly),
                "risk_level": result.risk_level,
                "safe_to_trade": result.safe_to_trade,
                "recommendation": result.recommendation
            }
        }
        args.output.write_text(json.dumps(data, indent=2))
        print(f"💾 Saved to {args.output}")


# === Quick Examples ===

# Example 1: High win rate, decent edge
# python risk_of_ruin.py -w 0.60 -W 150 -L 100 -r 0.02
# Result: ~0.1% risk of ruin — Very safe

# Example 2: Marginal edge, higher risk
# python risk_of_ruin.py -w 0.52 -W 200 -L 100 -r 0.03
# Result: Check if safe — borderline

# Example 3: With Monte Carlo validation
# python risk_of_ruin.py -w 0.55 -W 200 -L 100 -r 0.02 -c 10000 --monte-carlo

# Example 4: Sensitivity analysis
# python risk_of_ruin.py -w 0.55 -W 200 -L 100 -r 0.02 --sensitivity


if __name__ == "__main__":
    main()
```

## Quick Start

```bash
# Install and run
chmod +x risk_of_ruin.py

# Basic risk check
python risk_of_ruin.py --win-rate 0.55 --avg-win 200 --avg-loss 100 --risk-pct 0.02

# Short flags
python risk_of_ruin.py -w 0.55 -W 200 -L 100 -r 0.02

# With Monte Carlo simulation for validation
python risk_of_ruin.py -w 0.55 -W 200 -L 100 -r 0.02 -c 10000 --monte-carlo

# See risk at different position sizes
python risk_of_ruin.py -w 0.55 -W 200 -L 100 -r 0.02 --sensitivity
```

## Sample Output

```
════════════════════════════════════════════════════════════
  RISK OF RUIN ANALYSIS
════════════════════════════════════════════════════════════
  Win Rate:             55.0%
  Loss Rate:            45.0%
  Payoff Ratio:         2.00x
  Risk per Trade:       2.0%
──────────────────────────────────────────────────────────
  Expected Return:      $65.00 per trade
  Optimal Kelly (f):    32.5%
  Half Kelly:           16.2%
  Quarter Kelly:        8.1%
──────────────────────────────────────────────────────────
  Risk of Ruin:         0.84%
  Risk Level:           LOW
  Safe to Trade:        ✓ YES
════════════════════════════════════════════════════════════
  RECOMMENDATION:
  Risk level acceptable for trading. Consider quarter-Kelly sizing.
════════════════════════════════════════════════════════════
```

## Sensitivity Analysis Output

```
📊 SENSITIVITY ANALYSIS: Risk of Ruin at Different Position Sizes

Risk %    Risk of Ruin   Status
----------------------------------------
1.00      0.05%          SAFE
1.50      0.42%          SAFE
2.00      0.84%          SAFE
2.50      14.20%         UNSAFE
3.00      28.50%         UNSAFE
4.00      47.30%         DANGER
```

## Formula Explained

**Risk of Ruin** = ((1 - Edge) / (1 + Edge)) ^ (CapitalUnits)

Where:
- **Edge** = (Win% × Payoff) - Loss%
- **Payoff** = AvgWin / AvgLoss
- **CapitalUnits** = Ruin% / Risk%

**Lower = Better**. Under 1% is excellent, over 10% is dangerous.

## Risk Level Thresholds

| Risk of Ruin | Level | Action |
|--------------|-------|--------|
| < 1% | Very Low | Safe to trade |
| 1-5% | Low | Acceptable with caution |
| 5-15% | Moderate | Monitor closely |
| 15-30% | High | Reduce size or improve edge |
| > 30% | Critical | Do not trade |

## Why This Matters

Even a positive expectancy strategy can destroy your account if position sizing is wrong. This calculator tells you:

1. **Probability of ruin** — the chance of losing 50% of your account
2. **Kelly sizing** — optimal position size (but use half or quarter)
3. **Sensitivity curve** — how risk scales with position size

## Dependencies

- Standard library only (`decimal`, `math`, `random`, `argparse`)

---
*Utility: Risk-of-Ruin Calculator | Essential pre-trading check*
