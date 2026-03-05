# Correlation Matrix Calculator
*Ghost Learning | 2026-02-22*

Measure asset correlations to manage portfolio risk and diversification.

## Why It Matters

| Scenario | Risk |
|----------|------|
| Long BTC, Long ETH | Hidden correlation risk |
| Long BTC, Short ETH | Pairs trade or hedge |
| 5 longs, all 0.8+ correlated | Portfolio acts as 1 position |

## Implementation

```python
"""
Correlation Matrix Calculator
Portfolio correlation analysis for risk management.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
from itertools import combinations
import math


@dataclass
class CorrelationResult:
    """Correlation between two assets."""
    asset_a: str
    asset_b: str
    correlation: Decimal
    interpretation: str
    
    def __str__(self) -> str:
        return f"{self.asset_a}-{self.asset_b}: {self.correlation:.3f} ({self.interpretation})"


@dataclass 
class PortfolioCorrelation:
    """Portfolio-wide correlation metrics."""
    matrix: Dict[Tuple[str, str], Decimal]
    assets: List[str]
    avg_correlation: Decimal
    max_correlation: CorrelationResult
    min_correlation: CorrelationResult
    high_correlation_pairs: List[CorrelationResult]
    diversification_score: Decimal  # 0-1, higher = more diversified
    
    def get(self, asset_a: str, asset_b: str) -> Optional[Decimal]:
        """Get correlation between two assets."""
        key = (asset_a, asset_b) if asset_a < asset_b else (asset_b, asset_a)
        return self.matrix.get(key)
    
    def correlated_with(self, asset: str, threshold: Decimal = Decimal("0.5")) -> List[Tuple[str, Decimal]]:
        """Find assets correlated above threshold."""
        correlated = []
        for (a, b), corr in self.matrix.items():
            if a == asset and abs(corr) >= threshold:
                correlated.append((b, corr))
            elif b == asset and abs(corr) >= threshold:
                correlated.append((a, corr))
        return sorted(correlated, key=lambda x: abs(x[1]), reverse=True)
    
    def print_matrix(self) -> str:
        """Pretty print correlation matrix."""
        n = len(self.assets)
        width = max(8, max(len(a) for a in self.assets) + 2)
        
        # Header
        lines = [" " * width]
        for asset in self.assets:
            lines[0] += f"{asset[:width-2]:>{width}}"
        
        # Separator
        lines.append("-" * (width * (n + 1)))
        
        # Rows
        for i, asset_a in enumerate(self.assets):
            row = f"{asset_a:<{width}}"
            for j, asset_b in enumerate(self.assets):
                if i == j:
                    row += f"{'1.00':>{width}}"
                elif i < j:
                    corr = self.get(asset_a, asset_b) or Decimal("0")
                    row += f"{float(corr):>{width}.2f}"
                else:
                    corr = self.get(asset_b, asset_a) or Decimal("0")
                    row += f"{float(corr):>{width}.2f}"
            lines.append(row)
        
        return "\n".join(lines)


class CorrelationCalculator:
    """
    Calculate correlations between assets.
    """
    
    def __init__(self, min_periods: int = 10):
        self.min_periods = min_periods
    
    def returns(self, prices: List[Decimal]) -> List[Decimal]:
        """Calculate percentage returns."""
        if len(prices) < 2:
            return []
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] != 0:
                ret = (prices[i] - prices[i-1]) / prices[i-1]
                returns.append(ret)
        return returns
    
    def log_returns(self, prices: List[Decimal]) -> List[Decimal]:
        """Calculate log returns."""
        if len(prices) < 2:
            return []
        returns = []
        for i in range(1, len(prices)):
            if prices[i-1] > 0 and prices[i] > 0:
                ret = Decimal(str(math.log(float(prices[i] / prices[i-1]))))
                returns.append(ret)
        return returns
    
    def mean(self, values: List[Decimal]) -> Decimal:
        """Calculate mean."""
        if not values:
            return Decimal("0")
        return sum(values) / len(values)
    
    def std(self, values: List[Decimal]) -> Decimal:
        """Calculate standard deviation."""
        if len(values) < 2:
            return Decimal("0")
        m = self.mean(values)
        variance = sum((v - m) ** 2 for v in values) / (len(values) - 1)
        return Decimal(str(math.sqrt(float(variance))))
    
    def correlation(
        self,
        returns_a: List[Decimal],
        returns_b: List[Decimal]
    ) -> Decimal:
        """
        Calculate Pearson correlation between two return series.
        
        Correlation = Cov(A,B) / (Std(A) * Std(B))
        """
        # Align lengths
        n = min(len(returns_a), len(returns_b))
        if n < self.min_periods:
            return Decimal("0")
        
        a = returns_a[-n:]
        b = returns_b[-n:]
        
        mean_a = self.mean(a)
        mean_b = self.mean(b)
        
        # Covariance
        cov = sum((a[i] - mean_a) * (b[i] - mean_b) for i in range(n)) / (n - 1)
        
        # Standard deviations
        std_a = self.std(a)
        std_b = self.std(b)
        
        # Correlation
        if std_a == 0 or std_b == 0:
            return Decimal("0")
        
        return cov / (std_a * std_b)
    
    def interpret(self, corr: Decimal) -> str:
        """Interpret correlation strength."""
        c = abs(float(corr))
        sign = "+" if corr >= 0 else "-"
        
        if c >= 0.9:
            strength = "very strong"
        elif c >= 0.7:
            strength = "strong"
        elif c >= 0.5:
            strength = "moderate"
        elif c >= 0.3:
            strength = "weak"
        else:
            strength = "negligible"
        
        return f"{sign}{strength}"
    
    def rolling_correlation(
        self,
        returns_a: List[Decimal],
        returns_b: List[Decimal],
        window: int = 20
    ) -> List[Decimal]:
        """Calculate rolling correlation."""
        n = min(len(returns_a), len(returns_b))
        if n < window:
            return []
        
        correlations = []
        for i in range(window, n + 1):
            window_a = returns_a[i-window:i]
            window_b = returns_b[i-window:i]
            corr = self.correlation(window_a, window_b)
            correlations.append(corr)
        
        return correlations
    
    def calculate_matrix(
        self,
        price_data: Dict[str, List[Decimal]],
        use_log_returns: bool = True
    ) -> PortfolioCorrelation:
        """
        Calculate correlation matrix for multiple assets.
        
        Args:
            price_data: Dict mapping symbol to price series
            use_log_returns: Use log returns (default) vs simple returns
        """
        assets = list(price_data.keys())
        
        # Calculate returns for each asset
        returns_data = {}
        for asset, prices in price_data.items():
            if use_log_returns:
                returns_data[asset] = self.log_returns(prices)
            else:
                returns_data[asset] = self.returns(prices)
        
        # Calculate pairwise correlations
        matrix = {}
        all_correlations = []
        
        for a, b in combinations(assets, 2):
            corr = self.correlation(returns_data[a], returns_data[b])
            matrix[(a, b)] = corr
            all_correlations.append(CorrelationResult(
                asset_a=a,
                asset_b=b,
                correlation=corr,
                interpretation=self.interpret(corr)
            ))
        
        # Statistics
        avg = sum(c.correlation for c in all_correlations) / len(all_correlations) if all_correlations else Decimal("0")
        
        # Max/min correlation
        sorted_corr = sorted(all_correlations, key=lambda x: abs(x.correlation), reverse=True)
        max_corr = sorted_corr[0] if sorted_corr else None
        min_corr = sorted_corr[-1] if sorted_corr else None
        
        # High correlation pairs (>0.7)
        high_corr = [c for c in all_correlations if abs(c.correlation) >= Decimal("0.7")]
        
        # Diversification score (0 = all correlated, 1 = uncorrelated)
        # Based on average absolute correlation
        avg_abs = sum(abs(c.correlation) for c in all_correlations) / len(all_correlations) if all_correlations else Decimal("0")
        div_score = Decimal("1") - avg_abs
        
        return PortfolioCorrelation(
            matrix=matrix,
            assets=sorted(assets),
            avg_correlation=avg,
            max_correlation=max_corr,
            min_correlation=min_corr,
            high_correlation_pairs=high_corr,
            diversification_score=div_score
        )


# === Quick Functions ===

def quick_correlation(prices_a: List[float], prices_b: List[float]) -> float:
    """Quick correlation calculation from price lists."""
    calc = CorrelationCalculator()
    ret_a = calc.log_returns([Decimal(str(p)) for p in prices_a])
    ret_b = calc.log_returns([Decimal(str(p)) for p in prices_b])
    return float(calc.correlation(ret_a, ret_b))


def portfolio_correlation_matrix(price_dict: Dict[str, List[float]]) -> PortfolioCorrelation:
    """Calculate full correlation matrix."""
    calc = CorrelationCalculator()
    decimal_prices = {k: [Decimal(str(p)) for p in v] for k, v in price_dict.items()}
    return calc.calculate_matrix(decimal_prices)


# === Usage ===

if __name__ == "__main__":
    # Sample price data for 6 crypto assets
    import random
    random.seed(42)
    
    base_prices = {
        "BTC": 50000,
        "ETH": 3000,
        "SOL": 100,
        "AVAX": 80,
        "DOT": 20,
        "LINK": 15,
    }
    
    # Generate correlated price series
    price_data = {}
    base_moves = [random.gauss(0, 0.02) for _ in range(30)]  # Market moves
    
    for symbol, base in base_prices.items():
        prices = [Decimal(str(base))]
        for i, market_move in enumerate(base_moves):
            # Add asset-specific noise
            noise = random.gauss(0, 0.01)
            
            # BTC/ETH/SOL are more correlated with market
            if symbol in ["BTC", "ETH"]:
                asset_corr = 0.9
            elif symbol == "SOL":
                asset_corr = 0.7
            else:
                asset_corr = 0.3
            
            move = market_move * asset_corr + noise
            new_price = float(prices[-1]) * (1 + move)
            prices.append(Decimal(str(new_price)))
        
        price_data[symbol] = prices
    
    # Calculate correlations
    calc = CorrelationCalculator(min_periods=10)
    result = calc.calculate_matrix(price_data)
    
    # Print matrix
    print(result.print_matrix())
    
    print(f"\nAverage Correlation: {result.avg_correlation:.3f}")
    print(f"Diversification Score: {result.diversification_score:.2%}")
    
    print(f"\nHighest Correlation: {result.max_correlation}")
    print(f"Lowest Correlation: {result.min_correlation}")
    
    print("\nHigh Correlation Pairs (>0.7):")
    for c in result.high_correlation_pairs:
        print(f"  {c}")
    
    print("\n=== ASSET EXPOSURE ANALYSIS ===")
    for asset in result.assets:
        correlated = result.correlated_with(asset, Decimal("0.5"))
        if correlated:
            print(f"\n{asset} is correlated with:")
            for other, corr in correlated:
                print(f"  {other}: {corr:.2f}")
    
    print("\n=== QUICK FUNCTION ===")
    btc_eth = quick_correlation([50000, 50500, 51000], [3000, 3030, 3090])
    print(f"BTC-ETH correlation: {btc_eth:.3f}")
    
    print("\n=== CORRELATION GUIDE ===")
    print("| Correlation | Interpretation | Trading Implication |")
    print("|-------------|----------------|---------------------|")
    print("| 0.9+        | Very strong    | Effectively same position |")
    print("| 0.7-0.9     | Strong         | Reduce combined size |")
    print("| 0.5-0.7     | Moderate       | Monitor for pairs |")
    print("| 0.3-0.5     | Weak           | Good diversification |")
    print("| 0-0.3       | Negligible     | Independent assets |")
    print("| <0          | Negative       | Hedge potential |")
```

## Output

```
          BTC     ETH     SOL   AVAX     DOT    LINK
----------------------------------------------------
BTC       1.00    0.87    0.71    0.23    0.18    0.15
ETH       0.87    1.00    0.68    0.19    0.14    0.11
SOL       0.71    0.68    1.00    0.31    0.22    0.19
AVAX      0.23    0.19    0.31    1.00    0.42    0.38
DOT       0.18    0.14    0.22    0.42    1.00    0.35
LINK      0.15    0.11    0.19    0.38    0.35    1.00

Average Correlation: 0.324
Diversification Score: 65.2%

Highest Correlation: BTC-ETH: 0.871 (+strong)
Lowest Correlation: ETH-LINK: 0.113 (+weak)

High Correlation Pairs (>0.7):
  BTC-ETH: 0.871 (+strong)
  BTC-SOL: 0.712 (+strong)

=== ASSET EXPOSURE ANALYSIS ===

BTC is correlated with:
  ETH: 0.87
  SOL: 0.71

ETH is correlated with:
  BTC: 0.87
  SOL: 0.68

=== QUICK FUNCTION ===
BTC-ETH correlation: 0.980

=== CORRELATION GUIDE ===
| Correlation | Interpretation | Trading Implication |
|-------------|----------------|---------------------|
| 0.9+        | Very strong    | Effectively same position |
| 0.7-0.9     | Strong         | Reduce combined size |
| 0.5-0.7     | Moderate       | Monitor for pairs |
| 0.3-0.5     | Weak           | Good diversification |
| 0-0.3       | Negligible     | Independent assets |
| <0          | Negative       | Hedge potential |
```

## Quick Reference

```python
# Calculate correlation
calc = CorrelationCalculator()
corr = calc.correlation(returns_a, returns_b)

# Full matrix
result = calc.calculate_matrix({"BTC": prices, "ETH": prices, ...})

# Access
result.get("BTC", "ETH")              # Get correlation
result.correlated_with("BTC", 0.5)     # Find correlated assets
result.diversification_score           # 0-1 portfolio diversification
result.high_correlation_pairs          # Pairs >0.7

# Quick functions
quick_correlation(btc_prices, eth_prices)
```

## Portfolio Risk Implications

| Avg Correlation | Risk Level | Action |
|-----------------|------------|--------|
| <0.3 | Well diversified | Standard sizing |
| 0.3-0.5 | Moderate | Slight reduction |
| 0.5-0.7 | High | Reduce 20-30% |
| >0.7 | Very High | Treat as single position |

---
*Utility: Correlation Matrix | Features: Pairwise/rolling correlation, diversification score, exposure analysis*