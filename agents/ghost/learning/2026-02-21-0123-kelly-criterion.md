# Kelly Criterion Calculator — Optimal Bet Sizing

**Purpose:** Calculate optimal position size using Kelly Criterion to maximize long-term growth  
**Use Case:** Determine the mathematically optimal bet size based on win rate and risk/reward

## The Code

```python
"""
Kelly Criterion Calculator
Calculate optimal bet/position sizes using the Kelly Criterion.
Maximizes long-term portfolio growth while managing risk.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict
from enum import Enum, auto
import math


class KellyVariant(Enum):
    """Different Kelly Criterion variations."""
    FULL = auto()           # Full Kelly (can be volatile)
    HALF = auto()           # Half Kelly (more conservative)
    QUARTER = auto()        # Quarter Kelly (very conservative)
    FRACTIONAL = auto()     # Custom fraction
    MAX_PAIN = auto()       # Kelly limited by max pain threshold


@dataclass
class KellyInput:
    """Input parameters for Kelly calculation."""
    win_rate: float           # 0.0 to 1.0
    avg_win: float            # Average win amount (e.g., $100)
    avg_loss: float           # Average loss amount (e.g., $50)
    
    # Optional: if you have actual trade data instead of averages
    wins: Optional[List[float]] = None
    losses: Optional[List[float]] = None
    
    # Constraints
    max_position_pct: float = 0.25  # Max 25% of account
    min_position_pct: float = 0.01  # Min 1% of account


@dataclass
class KellyResult:
    """Kelly calculation result."""
    full_kelly: float         # Full Kelly percentage (0-1)
    half_kelly: float         # Half Kelly percentage
    quarter_kelly: float      # Quarter Kelly percentage
    
    # Position sizes
    full_kelly_position: float
    half_kelly_position: float
    quarter_kelly_position: float
    
    # Edge metrics
    edge: float               # Mathematical edge
    expected_value: float     # EV per dollar bet
    profit_factor: float      # Gross wins / gross losses
    
    # Risk metrics
    variance: float           # Variance of outcome
    std_dev: float           # Standard deviation
    sharpe_like: float       # Edge / std_dev
    
    # Recommended
    recommended_fraction: float
    recommended_position: float
    risk_level: str          # aggressive, moderate, conservative


@dataclass
class Scenario:
    """Growth projection scenario."""
    trades: int
    start_capital: float
    win_rate: float
    avg_win: float
    avg_loss: float
    kelly_fraction: float
    
    # Results
    final_capital: float
    peak_capital: float
    max_drawdown: float
    sharpe: float


class KellyCalculator:
    """
    Kelly Criterion calculator for optimal bet sizing.
    
    The Kelly Criterion formula:
    f* = (bp - q) / b
    
    Where:
    - f* = optimal fraction of capital to bet
    - b = average win / average loss (odds)
    - p = probability of win
    - q = probability of loss (1 - p)
    
    Usage:
        calc = KellyCalculator()
        
        result = calc.calculate(
            win_rate=0.55,      # 55% win rate
            avg_win=150,        # $150 avg win
            avg_loss=100        # $100 avg loss
        )
        
        print(f"Full Kelly: {result.full_kelly:.1%}")
        print(f"Half Kelly: {result.half_kelly:.1%}")
        print(f"Recommended: {result.recommended_position:.0f}% of account")
    """
    
    def __init__(self, default_fraction: float = 0.5):
        """
        Initialize calculator.
        
        Args:
            default_fraction: Default Kelly fraction (0.5 = Half Kelly)
        """
        self.default_fraction = default_fraction
    
    def calculate(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        account_size: float = 10000,
        fraction: Optional[float] = None
    ) -> KellyResult:
        """
        Calculate Kelly Criterion position sizes.
        
        Args:
            win_rate: Probability of winning (0.0 to 1.0)
            avg_win: Average win amount
            avg_loss: Average loss amount (positive number)
            account_size: Total account size
            fraction: Custom Kelly fraction (default: 0.5)
        
        Returns:
            KellyResult with various position sizing options
        """
        if not (0 < win_rate < 1):
            raise ValueError("Win rate must be between 0 and 1")
        
        if avg_win <= 0 or avg_loss <= 0:
            raise ValueError("Average win and loss must be positive")
        
        # Kelly formula components
        p = win_rate
        q = 1 - p
        b = avg_win / avg_loss  # Odds
        
        # Calculate Kelly percentage
        # f* = (bp - q) / b
        if b > 0:
            full_kelly = (b * p - q) / b
        else:
            full_kelly = 0
        
        # Ensure Kelly is positive (negative means don't bet)
        if full_kelly <= 0:
            full_kelly = 0
        
        # Calculate variants
        half_kelly = full_kelly * 0.5
        quarter_kelly = full_kelly * 0.25
        
        # Calculate position sizes
        full_pos = full_kelly * account_size
        half_pos = half_kelly * account_size
        quarter_pos = quarter_kelly * account_size
        
        # Calculate edge metrics
        edge = (p * avg_win) - (q * avg_loss)  # Expected value per trade
        expected_value = edge / avg_loss if avg_loss > 0 else 0
        profit_factor = (p * avg_win) / (q * avg_loss) if (q * avg_loss) > 0 else 0
        
        # Calculate variance and std dev
        # E[X^2] - (E[X])^2
        expected_square = p * (avg_win ** 2) + q * (avg_loss ** 2)
        expected_value_squared = edge ** 2
        variance = expected_square - expected_value_squared
        std_dev = math.sqrt(max(0, variance))
        
        # Sharpe-like ratio
        sharpe_like = edge / std_dev if std_dev > 0 else 0
        
        # Determine recommended fraction
        use_fraction = fraction if fraction is not None else self.default_fraction
        recommended_fraction = full_kelly * use_fraction
        recommended_position = recommended_fraction * account_size
        
        # Risk level
        if full_kelly > 0.25:
            risk_level = "aggressive"
        elif full_kelly > 0.15:
            risk_level = "moderate"
        else:
            risk_level = "conservative"
        
        return KellyResult(
            full_kelly=full_kelly,
            half_kelly=half_kelly,
            quarter_kelly=quarter_kelly,
            full_kelly_position=full_pos,
            half_kelly_position=half_pos,
            quarter_kelly_position=quarter_pos,
            edge=edge,
            expected_value=expected_value,
            profit_factor=profit_factor,
            variance=variance,
            std_dev=std_dev,
            sharpe_like=sharpe_like,
            recommended_fraction=recommended_fraction,
            recommended_position=recommended_position,
            risk_level=risk_level
        )
    
    def calculate_from_trades(
        self,
        trades: List[float],
        account_size: float = 10000,
        fraction: Optional[float] = None
    ) -> KellyResult:
        """
        Calculate Kelly from actual trade P&L history.
        
        Args:
            trades: List of trade P&L values (positive=win, negative=loss)
            account_size: Total account size
            fraction: Custom Kelly fraction
        
        Returns:
            KellyResult
        """
        if not trades:
            raise ValueError("Trade list cannot be empty")
        
        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t < 0]
        
        if not wins or not losses:
            raise ValueError("Need both wins and losses to calculate Kelly")
        
        win_rate = len(wins) / len(trades)
        avg_win = sum(wins) / len(wins)
        avg_loss = abs(sum(losses) / len(losses))  # Make positive
        
        return self.calculate(win_rate, avg_win, avg_loss, account_size, fraction)
    
    def simulate_growth(
        self,
        start_capital: float,
        trades: int,
        kelly_fraction: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> Scenario:
        """
        Simulate portfolio growth using Kelly position sizing.
        
        Args:
            start_capital: Starting capital
            trades: Number of trades to simulate
            kelly_fraction: Kelly fraction to use (0.25 = Quarter Kelly)
            win_rate: Probability of win
            avg_win: Average win amount (as % of bet)
            avg_loss: Average loss amount (as % of bet)
        
        Returns:
            Scenario with growth projection
        """
        import random
        random.seed(42)
        
        capital = start_capital
        peak = capital
        max_dd = 0
        returns = []
        
        for _ in range(trades):
            # Calculate bet size based on current capital
            bet_size = capital * kelly_fraction
            
            # Simulate trade
            if random.random() < win_rate:
                result = bet_size * (avg_win / 100)  # Convert % to decimal
            else:
                result = -bet_size * (avg_loss / 100)
            
            capital += result
            returns.append(result / bet_size if bet_size > 0 else 0)
            
            if capital > peak:
                peak = capital
            
            drawdown = (peak - capital) / peak if peak > 0 else 0
            max_dd = max(max_dd, drawdown)
        
        # Calculate Sharpe
        if len(returns) > 1:
            mean_ret = sum(returns) / len(returns)
            variance = sum((r - mean_ret) ** 2 for r in returns) / len(returns)
            std = variance ** 0.5
            sharpe = mean_ret / std if std > 0 else 0
        else:
            sharpe = 0
        
        return Scenario(
            trades=trades,
            start_capital=start_capital,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            kelly_fraction=kelly_fraction,
            final_capital=capital,
            peak_capital=peak,
            max_drawdown=max_dd,
            sharpe=sharpe
        )
    
    def compare_kelly_fractions(
        self,
        start_capital: float,
        trades: int,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> Dict[float, Scenario]:
        """Compare different Kelly fractions."""
        fractions = [1.0, 0.5, 0.25, 0.125, 0.0]
        results = {}
        
        for frac in fractions:
            scenario = self.simulate_growth(
                start_capital, trades, frac,
                win_rate, avg_win, avg_loss
            )
            results[frac] = scenario
        
        return results


def format_kelly_result(result: KellyResult, account_size: float = 10000) -> str:
    """Format Kelly result for display."""
    lines = [
        f"{'=' * 70}",
        f"KELLY CRITERION ANALYSIS",
        f"{'=' * 70}",
        "",
        f"Account Size: ${account_size:,.2f}",
        "",
        "KELLY FRACTIONS:",
        f"  Full Kelly:    {result.full_kelly:>6.1%} = ${result.full_kelly_position:>10,.2f}",
        f"  Half Kelly:    {result.half_kelly:>6.1%} = ${result.half_kelly_position:>10,.2f}",
        f"  Quarter Kelly: {result.quarter_kelly:>6.1%} = ${result.quarter_kelly_position:>10,.2f}",
        "",
        f"RECOMMENDED (Half Kelly): {result.recommended_fraction:.1%} = ${result.recommended_position:,.2f}",
        f"Risk Level: {result.risk_level.upper()}",
        "",
        "EDGE METRICS:",
        f"  Expected Value:  ${result.edge:+.2f} per trade",
        f"  Profit Factor:   {result.profit_factor:.2f}",
        f"  Win/Loss Ratio:  {result.avg_win / result.avg_loss if result.avg_loss else 0:.2f}:1",
        "",
        "RISK METRICS:",
        f"  Std Deviation:   ${result.std_dev:.2f}",
        f"  Sharpe-like:     {result.sharpe_like:.2f}",
        f"{'=' * 70}"
    ]
    
    return "\n".join(lines)


# === Examples ===

def example_basic_kelly():
    """Basic Kelly calculation."""
    print("=" * 70)
    print("Kelly Criterion Demo - Basic Calculation")
    print("=" * 70)
    
    calc = KellyCalculator()
    
    # Example: 55% win rate, $150 avg win, $100 avg loss
    result = calc.calculate(
        win_rate=0.55,
        avg_win=150,
        avg_loss=100,
        account_size=10000
    )
    
    print(format_kelly_result(result))
    
    print("\n" + "-" * 70)
    print("INTERPRETATION:")
    print(f"  • Math says bet {result.full_kelly:.0%} of account")
    print(f"  • But {result.full_kelly:.0%} is too volatile for most traders")
    print(f"  • Half Kelly ({result.half_kelly:.0%}) is more realistic")
    print(f"  • Quarter Kelly ({result.quarter_kelly:.0%}) for safety")


def example_from_trades():
    """Kelly from actual trade history."""
    print("\n" + "=" * 70)
    print("Kelly Criterion Demo - From Trade History")
    print("=" * 70)
    
    # Simulate 20 trades
    trades = [
        150, -80, 120, -100, 200, 180, -90, 110, -120, 160,
        140, -70, 130, -110, 190, 170, -85, 125, -105, 155
    ]
    
    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t < 0]
    
    print(f"\nTrade History:")
    print(f"  Total Trades: {len(trades)}")
    print(f"  Wins: {len(wins)} ({len(wins)/len(trades)*100:.0f}%)")
    print(f"  Losses: {len(losses)}")
    print(f"  Avg Win: ${sum(wins)/len(wins):.0f}")
    print(f"  Avg Loss: ${abs(sum(losses)/len(losses)):.0f}")
    
    calc = KellyCalculator()
    result = calc.calculate_from_trades(trades, account_size=10000)
    
    print("\n" + format_kelly_result(result))


def example_comparison():
    """Compare Kelly vs fixed sizing."""
    print("\n" + "=" * 70)
    print("Kelly Criterion Demo - Kelly vs Fixed Sizing")
    print("=" * 70)
    
    calc = KellyCalculator()
    
    # System: 40% win rate, 2:1 R/R
    win_rate = 0.40
    avg_win = 200  # 2% on a $10k bet
    avg_loss = 100  # 1% on a $10k bet
    
    print(f"\nSystem: {win_rate:.0%} win rate, {avg_win/avg_loss:.1f}:1 R/R")
    
    result = calc.calculate(win_rate, avg_win, avg_loss, account_size=10000)
    
    print(f"\nKelly Optimal: {result.full_kelly:.1%}")
    print(f"Half Kelly: {result.half_kelly:.1%}")
    
    # Show why Kelly matters
    scenarios = calc.compare_kelly_fractions(
        start_capital=10000,
        trades=100,
        win_rate=win_rate,
        avg_win=2.0,  # As percentage
        avg_loss=1.0
    )
    
    print("\n" + "-" * 70)
    print("100 Trade Simulation Results:")
    print(f"{'Fraction':<12} {'Final $':<12} {'Peak $':<12} {'Drawdown':<12}")
    print("-" * 70)
    
    for frac in [1.0, 0.5, 0.25, 0.125]:
        s = scenarios[frac]
        print(f"{frac*100:>5.0f}% Kelly   ${s.final_capital:<11,.0f} ${s.peak_capital:<11,.0f} {s.max_drawdown*100:<11.1f}%")


def example_edge_cases():
    """Edge cases and warnings."""
    print("\n" + "=" * 70)
    print("Kelly Criterion Demo - Edge Cases")
    print("=" * 70)
    
    calc = KellyCalculator()
    
    cases = [
        ("50% win, 1:1 R/R (breakeven)", 0.50, 100, 100),
        ("40% win, 2:1 R/R (positive edge)", 0.40, 200, 100),
        ("60% win, 1:2 R/R (negative edge)", 0.60, 100, 200),
        ("70% win, 1:1 R/R (high win rate)", 0.70, 100, 100),
    ]
    
    for name, wr, win, loss in cases:
        result = calc.calculate(wr, win, loss, account_size=10000)
        
        print(f"\n{name}:")
        print(f"  Kelly: {result.full_kelly:+.1%}")
        
        if result.full_kelly <= 0:
            print(f"  ⚠️  NEGATIVE KELLY - Don't trade this system")
        elif result.full_kelly > 0.5:
            print(f"  ⚠️  OVER 50% - Extremely aggressive, high volatility")
        else:
            print(f"  ✅ Valid Kelly")


def example_kelly_formula():
    """Show the Kelly formula math."""
    print("\n" + "=" * 70)
    print("The Kelly Criterion Formula")
    print("=" * 70)
    
    print("""
    THE MATH:
    
    f* = (bp - q) / b
    
    Where:
    - f* = optimal fraction of capital to bet
    - b = average win / average loss (odds against)
    - p = probability of win
    - q = probability of loss = 1 - p
    
    EXAMPLE CALCULATION:
    
    Given: 55% win rate, $150 avg win, $100 avg loss
    
    b = 150 / 100 = 1.5 (you win 1.5x what you lose)
    p = 0.55
    q = 0.45
    
    f* = (1.5 × 0.55 - 0.45) / 1.5
    f* = (0.825 - 0.45) / 1.5
    f* = 0.375 / 1.5
    f* = 0.25 = 25%
    
    ANSWER: Bet 25% of account per trade
    
    PRACTICAL RECOMMENDATION:
    
    Most traders use Half Kelly or Quarter Kelly because:
    
    1. Full Kelly is too volatile (can have 50%+ drawdowns)
    2. Estimates of p, b have error
    3. Quarter Kelly still grows fast with less pain
    
    Half Kelly gives 75% of growth with half the volatility.
    """)


if __name__ == "__main__":
    example_basic_kelly()
    example_from_trades()
    example_comparison()
    example_edge_cases()
    example_kelly_formula()
    
    print("\n" + "=" * 70)
    print("KELLY CRITERION GUIDE:")
    print("=" * 70)
    print("""
WHEN TO USE:
  ✅ You have positive expected value (edge > 0)
  ✅ Win rate and R/R are stable/predictable
  ✅ You can calculate average wins/losses
  ✅ You want to maximize long-term growth

WHEN NOT TO USE:
  ❌ Negative expected value (you'll lose over time)
  ❌ High volatility in win/loss sizes
  ❌ Can't survive full Kelly drawdowns
  ❌ You care more about smooth equity than max growth

KELLY FRACTION RECOMMENDATIONS:

  Full Kelly (100%):
    - Aggressive growth
    - Expect 50%+ drawdowns
    - Most traders can't handle
    
  Half Kelly (50%):
    - 75% of full Kelly growth
    - Much smoother equity curve
    - Most common recommendation
    
  Quarter Kelly (25%):
    - 50% of full Kelly growth
    - Very smooth, manageable
    - Good for conservative traders
    
  Less than Quarter:
    - Too conservative
    - Better to find better system

THE KELLY PARADOX:

Two equal systems with same edge:
  System A: 60% wins, 1:1 R/R → Kelly = 20%
  System B: 40% wins, 2:1 R/R → Kelly = 10%

System A has lower volatility for same growth.
Prefer higher win rate when Kelly is equal.

KEY INSIGHT:

"It's not how much you make, it's how you make it."
A system with 60% win rate and 1:1 R/R grows 
more smoothly than 40% with 2:1, even if 
expected value is same.
    """)
    print("=" * 70)
```

## Kelly Formula

**f* = (bp - q) / b**

| Variable | Meaning |
|----------|---------|
| f* | Optimal bet fraction |
| b | Average win / Average loss (odds) |
| p | Probability of win |
| q | Probability of loss (1 - p) |

## Kelly Fractions

| Fraction | Risk | Use Case |
|----------|------|----------|
| **Full (100%)** | Very High | Aggressive growth, can handle big drawdowns |
| **Half (50%)** | Moderate | Optimal risk/return tradeoff |
| **Quarter (25%)** | Low | Conservative, smooth equity curve |
| **Eighth (12.5%)** | Very Low | Learning/testing new systems |

## Quick Reference

```python
calc = KellyCalculator()

# From win rate and averages
result = calc.calculate(
    win_rate=0.55,      # 55%
    avg_win=150,        # $150
    avg_loss=100,       # $100
    account_size=10000,
    fraction=0.5       # Half Kelly
)

print(f"Bet size: ${result.recommended_position:.2f}")

# From trade history
result = calc.calculate_from_trades(
    trades=trade_list,
    account_size=10000
)

# Simulate growth
scenario = calc.simulate_growth(
    start_capital=10000,
    trades=100,
    kelly_fraction=0.25,  # Quarter Kelly
    win_rate=0.55,
    avg_win=2.0,          # As %
    avg_loss=1.0
)

print(f"Final: ${scenario.final_capital:.2f}")
```

## Calculator Output

| Metric | Good | Warning |
|--------|------|---------|
| **Kelly %** | 10-25% | >50% or <0% |
| **Edge** | >$0 | ≤$0 |
| **Profit Factor** | >1.5 | <1.2 |
| **Risk Level** | Moderate | Aggressive |

## Why This Matters

- **Maximizes long-term growth** — Mathematically proven optimal
- **Prevents overbetting** — Going "all in" is suicidal
- **Fractional Kelly works** — Half Kelly = 75% growth, half volatility
- **Negative Kelly = don't trade** — Guaranteed to lose
- **Size to survive** — Quarter Kelly often beats full Kelly in reality

**Bet the fraction or go broke.**

---

**Created by Ghost 👻 | Feb 21, 2026 | 11-min learning sprint**  
*Lesson: "Bet too much and you'll go broke. Bet too little and you won't grow." The Kelly Criterion finds the optimal middle ground—fractional Kelly (half or quarter) gives most of the growth with manageable drawdowns. It's the mathematical answer to 'how much should I risk?'*
