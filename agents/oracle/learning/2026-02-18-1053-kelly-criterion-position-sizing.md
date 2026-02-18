# Kelly Criterion for Position Sizing

**Date:** 2026-02-18 | **Time:** 10:53 AM CST | **Topic:** Risk Management / Position Sizing

---

## What It Is

The Kelly Criterion calculates the optimal fraction of capital to risk on a trade to maximize long-term growth.

## The Formula

```
f* = (p × b - q) / b

Where:
- f* = optimal fraction of capital to risk
- p = probability of win
- q = probability of loss (1 - p)
- b = win/loss ratio (avg win / avg loss)
```

## Practical Example

**Scenario:** Your backtest shows:
- Win rate (p) = 55% (0.55)
- Avg win = $200
- Avg loss = $100
- Win/loss ratio (b) = 200/100 = 2

**Calculation:**
```
f* = (0.55 × 2 - 0.45) / 2
f* = (1.10 - 0.45) / 2
f* = 0.65 / 2
f* = 0.325 (32.5% of capital)
```

## Practical Application

| Scenario | Kelly % | Recommended (Half-Kelly) |
|----------|---------|--------------------------|
| Strong edge | 25-35% | 12-18% |
| Moderate edge | 15-25% | 8-12% |
| Weak edge | 5-15% | 2-8% |

## Key Insights

1. **Use Half-Kelly**: Full Kelly is volatile. Most traders use 0.25x–0.5x Kelly for psychological comfort and drawdown protection.

2. **Inputs Matter**: Garbage in = garbage out. Accurate p and b require substantial sample size (100+ trades minimum).

3. **Multiple Positions**: If Kelly suggests 20% per trade but you hold 5 positions simultaneously, scale accordingly (e.g., 4% each).

## Quick Formula (Simplified)

```python
def kelly(p_win, avg_win, avg_loss):
    b = avg_win / avg_loss
    q = 1 - p_win
    return (p_win * b - q) / b

# Example
kelly(0.55, 200, 100)  # Returns: 0.325
```

## Bottom Line

Kelly tells you the _upper bound_ of rational risk. Size below it, never above.

---
*Source: Edge from "Fortune's Formula" (Poundstone) + practical trading experience*
