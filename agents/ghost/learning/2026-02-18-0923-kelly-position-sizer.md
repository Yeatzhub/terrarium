# Trading Utility: Kelly Criterion Position Sizer

**Date:** 2026-02-18 | **Time:** 9:23 AM | **Duration:** ~15 min

## What It Does

Calculates optimal position sizes using the **Kelly Criterion** - a mathematical formula that maximizes long-term growth while managing risk. Includes fractional Kelly for conservative trading.

## The Math

**Full Kelly:** `f* = (p × b - q) / b`
- `p` = win probability
- `q` = loss probability (1 - p)
- `b` = win/loss ratio (avg win / avg loss)

**Fractional Kelly:** `position = f* × fraction × account`

## The Code

```python
"""
Kelly Criterion Position Sizer
Maximize growth while managing ruin risk.
"""
from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal, ROUND_DOWN
import json


@dataclass(frozen=True)
class KellyResult:
    """Immutable result container."""
    full_kelly: Decimal          # Raw Kelly percentage (0-1)
    half_kelly: Decimal          # Conservative 50% Kelly
    quarter_kelly: Decimal       # Very conservative 25% Kelly
    optimal_position: Decimal    # Recommended position size
    max_position: Decimal        # Kelly cap (usually 25%)
    risk_of_ruin: Decimal        # Probability of blowing account
    expected_growth: Decimal     # Geometric mean growth per trade
    
    def to_dict(self) -> dict:
        return {
            k: float(v) for k, v in self.__dict__.items()
        }


class KellyPositionSizer:
    """
    Position sizing using Kelly Criterion with safety constraints.
    
    Usage:
        sizer = KellyPositionSizer(max_kelly_fraction=0.5)
        result = sizer.calculate(
            win_rate=0.55,
            avg_win=150,
            avg_loss=100,
            account_size=10000
        )
        print(f"Optimal position: ${result.optimal_position}")
    """
    
    # Safety caps - never risk more than this per trade
    MAX_POSITION_PCT = Decimal('0.25')  # 25% max per trade
    MIN_KELLY = Decimal('0.01')          # 1% minimum
    
    def __init__(
        self,
        max_kelly_fraction: float = 0.5,  # Use half-Kelly default
        max_position_pct: Optional[float] = None
    ):
        """
        Args:
            max_kelly_fraction: 0.25=quarter-Kelly, 0.5=half-Kelly, 1.0=full
            max_position_pct: Override max position (default 25%)
        """
        self.kelly_fraction = Decimal(str(max_kelly_fraction))
        self.max_position = Decimal(str(max_position_pct or self.MAX_POSITION_PCT))
    
    def calculate(
        self,
        win_rate: float,           # 0.0 to 1.0
        avg_win: float,            # Average win amount ($)
        avg_loss: float,           # Average loss amount ($)
        account_size: float,       # Total account ($)
        current_drawdown: float = 0.0  # Current drawdown % (reduces size)
    ) -> KellyResult:
        """
        Calculate optimal position size.
        
        Raises:
            ValueError: If inputs are invalid
        """
        # Validate inputs
        if not 0 < win_rate < 1:
            raise ValueError(f"win_rate must be 0-1, got {win_rate}")
        if avg_win <= 0 or avg_loss <= 0:
            raise ValueError("avg_win and avg_loss must be positive")
        if account_size <= 0:
            raise ValueError("account_size must be positive")
        
        # Convert to Decimal for precision
        p = Decimal(str(win_rate))
        q = Decimal('1') - p
        b = Decimal(str(avg_win)) / Decimal(str(avg_loss))  # Win/loss ratio
        account = Decimal(str(account_size))
        drawdown = Decimal(str(current_drawdown))
        
        # Kelly Formula: f* = (p*b - q) / b
        # where b is win/loss ratio
        full_kelly = (p * b - q) / b
        
        # Handle negative Kelly (don't trade)
        if full_kelly <= 0:
            return KellyResult(
                full_kelly=Decimal('0'),
                half_kelly=Decimal('0'),
                quarter_kelly=Decimal('0'),
                optimal_position=Decimal('0'),
                max_position=Decimal('0'),
                risk_of_ruin=Decimal('1'),
                expected_growth=Decimal('0')
            )
        
        # Apply Kelly fraction and caps
        half_kelly = full_kelly * Decimal('0.5')
        quarter_kelly = full_kelly * Decimal('0.25')
        
        # Use fractional Kelly with drawdown adjustment
        adjusted_kelly = full_kelly * self.kelly_fraction
        
        # Reduce size during drawdown (conservative)
        drawdown_factor = Decimal('1') - (drawdown * Decimal('2'))  # 10% DD -> 20% reduction
        drawdown_factor = max(drawdown_factor, Decimal('0.5'))  # Max 50% reduction
        
        position_pct = adjusted_kelly * drawdown_factor
        position_pct = min(position_pct, self.max_position)
        position_pct = max(position_pct, self.MIN_KELLY)
        
        # Calculate position size
        optimal_position = (account * position_pct).quantize(
            Decimal('0.01'), rounding=ROUND_DOWN
        )
        
        # Risk metrics
        risk_of_ruin = self._calculate_ruin_risk(p, q, b, position_pct)
        expected_growth = self._calculate_growth(p, q, b, position_pct)
        
        return KellyResult(
            full_kelly=full_kelly.quantize(Decimal('0.0001')),
            half_kelly=half_kelly.quantize(Decimal('0.0001')),
            quarter_kelly=quarter_kelly.quantize(Decimal('0.0001')),
            optimal_position=optimal_position,
            max_position=(account * self.max_position).quantize(Decimal('0.01')),
            risk_of_ruin=risk_of_ruin.quantize(Decimal('0.0001')),
            expected_growth=expected_growth.quantize(Decimal('0.0001'))
        )
    
    def _calculate_ruin_risk(
        self, p: Decimal, q: Decimal, b: Decimal, f: Decimal
    ) -> Decimal:
        """Approximate risk of ruin (simplified formula)."""
        if f <= 0:
            return Decimal('0')
        # Simplified: higher Kelly = higher ruin risk
        edge = p * b - q
        if edge <= 0:
            return Decimal('1')
        # Rough approximation
        return (q / p) ** (Decimal('0.5') / f)
    
    def _calculate_growth(
        self, p: Decimal, q: Decimal, b: Decimal, f: Decimal
    ) -> Decimal:
        """Expected geometric growth rate per trade."""
        if f <= 0:
            return Decimal('0')
        # G = p*log(1 + f*b) + q*log(1 - f)
        # Using natural log approximation
        term1 = p * (f * b).ln()
        term2 = q * (-f).ln()
        return (term1 + term2).exp() - Decimal('1')
    
    def backtest_kelly(
        self,
        trades: List[float],  # List of P&L amounts
        account_size: float,
        window: int = 50
    ) -> List[KellyResult]:
        """
        Calculate rolling Kelly values from trade history.
        
        Args:
            trades: Historical trade P&Ls (positive=win, negative=loss)
            account_size: Current account size
            window: Rolling window size for calculations
        """
        results = []
        for i in range(window, len(trades) + 1):
            window_trades = trades[i-window:i]
            wins = [t for t in window_trades if t > 0]
            losses = [t for t in window_trades if t < 0]
            
            if not wins or not losses:
                continue
            
            win_rate = len(wins) / window
            avg_win = sum(wins) / len(wins)
            avg_loss = abs(sum(losses) / len(losses))
            
            result = self.calculate(
                win_rate=win_rate,
                avg_win=avg_win,
                avg_loss=avg_loss,
                account_size=account_size
            )
            results.append(result)
        
        return results


# === QUICK REFERENCE TABLE ===

def print_kelly_table():
    """Print common Kelly values for reference."""
    sizer = KellyPositionSizer(max_kelly_fraction=1.0)  # Full Kelly
    
    print("\n" + "="*70)
    print("KELLY CRITERION REFERENCE TABLE")
    print("Account: $10,000 | Avg Win: $200 | Avg Loss: $100")
    print("="*70)
    print(f"{'Win Rate':<10} {'Full K':<10} {'Half K':<10} {'Position':<12} {'Risk':<10}")
    print("-"*70)
    
    for win_rate in [0.50, 0.55, 0.60, 0.65, 0.70]:
        try:
            result = sizer.calculate(
                win_rate=win_rate,
                avg_win=200,
                avg_loss=100,
                account_size=10000
            )
            print(
                f"{win_rate:<10.0%} "
                f"{float(result.full_kelly):<10.2%} "
                f"{float(result.half_kelly):<10.2%} "
                f"${float(result.optimal_position):<11,.0f} "
                f"{float(result.risk_of_ruin):<10.2%}"
            )
        except:
            print(f"{win_rate:<10.0%} {'N/A':<10} {'Edge < 0':<10}")
    
    print("="*70)
    print("Note: Risk column shows approximate risk of ruin")
    print("Recommendation: Use Half-Kelly (0.5) for most trading")


# === USAGE EXAMPLES ===

if __name__ == "__main__":
    # Example 1: Basic usage
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Kelly Calculation")
    print("="*70)
    
    sizer = KellyPositionSizer(max_kelly_fraction=0.5)  # Half-Kelly
    
    result = sizer.calculate(
        win_rate=0.55,        # 55% win rate
        avg_win=150,          # $150 average win
        avg_loss=100,         # $100 average loss
        account_size=10000    # $10k account
    )
    
    print(f"\nFull Kelly: {float(result.full_kelly):.2%}")
    print(f"Half Kelly: {float(result.half_kelly):.2%}")
    print(f"Optimal Position: ${float(result.optimal_position):,.2f}")
    print(f"Risk of Ruin: {float(result.risk_of_ruin):.2%}")
    
    # Example 2: During drawdown
    print("\n" + "="*70)
    print("EXAMPLE 2: Position Size During 10% Drawdown")
    print("="*70)
    
    result_dd = sizer.calculate(
        win_rate=0.55,
        avg_win=150,
        avg_loss=100,
        account_size=9000,    # Down from $10k
        current_drawdown=0.10 # 10% drawdown
    )
    
    print(f"Normal Position: ${float(result.optimal_position):,.2f}")
    print(f"During Drawdown: ${float(result_dd.optimal_position):,.2f}")
    print(f"Reduction: {float(1 - result_dd.optimal_position/result.optimal_position):.1%}")
    
    # Example 3: Edge case - negative Kelly
    print("\n" + "="*70)
    print("EXAMPLE 3: Negative Edge (Don't Trade)")
    print("="*70)
    
    result_neg = sizer.calculate(
        win_rate=0.45,  # Below 50% with 1:1 reward
        avg_win=100,
        avg_loss=100,
        account_size=10000
    )
    
    print(f"Full Kelly: {float(result_neg.full_kelly):.2%}")
    print(f"Recommendation: {'DO NOT TRADE' if result_neg.optimal_position == 0 else 'Trade'}")
    
    # Print reference table
    print_kelly_table()
```

## Key Features

| Feature | Purpose |
|---------|---------|
| **Fractional Kelly** | Use 0.25-0.5× Kelly to reduce volatility |
| **Drawdown Adjustment** | Auto-reduce size when losing |
| **25% Position Cap** | Hard limit per trade |
| **Decimal Precision** | Avoid floating-point errors in money |
| **Backtest Method** | Rolling Kelly from trade history |

## When to Use

- **Strategy has edge** (win rate × reward > loss rate)
- **Sufficient sample size** (50+ trades for win rate)
- **Volatile markets** → Use quarter-Kelly
- **Steady performance** → Can use half-Kelly

## Quick Rules

1. **Kelly < 0** → Don't trade (no edge)
2. **Kelly > 25%** → Cap at 25% (ruin risk too high)
3. **In drawdown** → Reduce size 2× drawdown %
4. **New strategy** → Start with quarter-Kelly

---
*End of 15-min learning session*
