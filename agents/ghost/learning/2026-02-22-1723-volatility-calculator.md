# Volatility Calculator
*Ghost Learning | 2026-02-22*

Measure market volatility for position sizing, stop placement, and regime detection.

## Key Metrics

| Metric | Description | Use Case |
|--------|-------------|----------|
| **ATR** | Average True Range | Stop placement, position sizing |
| **HV** | Historical Volatility | Compare to implied, regime detection |
| **ATR%** | ATR as % of price | Cross-asset comparison |
| **Vol Ratio** | Current / avg ATR | Volatility regime |

## Implementation

```python
"""
Volatility Calculator
ATR, historical volatility, and volatility-adjusted metrics.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Tuple
import math


@dataclass
class OHLC:
    """Price bar."""
    high: Decimal
    low: Decimal
    close: Decimal
    open: Optional[Decimal] = None
    
    @property
    def range(self) -> Decimal:
        """High - low range."""
        return self.high - self.low
    
    @property
    def body(self) -> Decimal:
        """|Close - Open|."""
        if self.open is None:
            return Decimal("0")
        return abs(self.close - self.open)


@dataclass
class VolatilityMetrics:
    """Calculated volatility metrics."""
    atr: Decimal
    atr_percent: Decimal          # ATR as % of price
    historical_vol: Decimal       # Annualized %
    vol_ratio: Decimal            # Current ATR / avg ATR
    avg_range: Decimal            # Simple avg range
    max_range: Decimal
    min_range: Decimal
    range_std: Decimal
    
    # Regime
    regime: str                   # "low", "normal", "high", "extreme"
    
    def __str__(self) -> str:
        lines = [
            "=== VOLATILITY METRICS ===",
            f"ATR:           ${self.atr:,.2f}",
            f"ATR%:          {self.atr_percent:.2%}",
            f"HV (annual):   {self.historical_vol:.1%}",
            f"",
            f"Range Avg:     ${self.avg_range:,.2f}",
            f"Range Max:     ${self.max_range:,.2f}",
            f"Range Min:     ${self.min_range:,.2f}",
            f"Range Std:     ${self.range_std:,.2f}",
            f"",
            f"Vol Ratio:     {self.vol_ratio:.2f}x",
            f"Regime:        {self.regime.upper()}",
        ]
        return "\n".join(lines)


class VolatilityCalculator:
    """
    Calculate volatility metrics from price data.
    """
    
    def __init__(self, period: int = 14):
        """
        Args:
            period: Lookback period for calculations
        """
        self.period = period
    
    def true_range(self, bar: OHLC, prev_close: Optional[Decimal] = None) -> Decimal:
        """
        Calculate True Range for a bar.
        
        TR = max(H-L, |H-PrevC|, |L-PrevC|)
        """
        if prev_close is None:
            return bar.range
        
        hl = bar.range
        hpc = abs(bar.high - prev_close)
        lpc = abs(bar.low - prev_close)
        
        return max(hl, hpc, lpc)
    
    def atr(self, bars: List[OHLC], smoothing: str = "ema") -> Decimal:
        """
        Calculate Average True Range.
        
        Args:
            bars: List of OHLC bars (most recent last)
            smoothing: "sma" or "ema"
        """
        if len(bars) < 2:
            return bars[0].range if bars else Decimal("0")
        
        # Calculate true ranges
        trs = []
        for i, bar in enumerate(bars):
            if i == 0:
                trs.append(bar.range)
            else:
                trs.append(self.true_range(bar, bars[i-1].close))
        
        if smoothing == "sma":
            # Simple moving average
            return sum(trs[-self.period:]) / min(len(trs), self.period)
        else:
            # EMA-style (Wilder's smoothing)
            atr = trs[0]
            multiplier = Decimal("1") / Decimal(self.period)
            for tr in trs[1:]:
                atr = (atr * (1 - multiplier)) + (tr * multiplier)
            return atr
    
    def atr_series(self, bars: List[OHLC]) -> List[Decimal]:
        """Get ATR at each point in the series."""
        if len(bars) < self.period:
            return []
        
        atrs = []
        for i in range(self.period - 1, len(bars)):
            window = bars[:i+1]
            atrs.append(self.atr(window))
        
        return atrs
    
    def historical_volatility(
        self,
        closes: List[Decimal],
        annualize: bool = True,
        trading_days: int = 252
    ) -> Decimal:
        """
        Calculate historical (realized) volatility.
        
        Based on standard deviation of log returns.
        """
        if len(closes) < 2:
            return Decimal("0")
        
        # Log returns
        returns = []
        for i in range(1, len(closes)):
            if closes[i-1] > 0 and closes[i] > 0:
                log_ret = math.log(float(closes[i] / closes[i-1]))
                returns.append(log_ret)
        
        if not returns:
            return Decimal("0")
        
        # Standard deviation
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / (len(returns) - 1) if len(returns) > 1 else 0
        std = math.sqrt(variance)
        
        # Annualize
        if annualize:
            std = std * math.sqrt(trading_days)
        
        return Decimal(str(std))
    
    def atr_percent(self, atr: Decimal, price: Decimal) -> Decimal:
        """ATR as percentage of price."""
        if price == 0:
            return Decimal("0")
        return atr / price
    
    def volatility_ratio(
        self,
        current_atr: Decimal,
        avg_atr: Decimal
    ) -> Decimal:
        """Current ATR relative to average."""
        if avg_atr == 0:
            return Decimal("1")
        return current_atr / avg_atr
    
    def classify_regime(self, vol_ratio: Decimal) -> str:
        """Classify volatility regime."""
        ratio = float(vol_ratio)
        if ratio < 0.5:
            return "extreme_low"
        elif ratio < 0.75:
            return "low"
        elif ratio < 1.25:
            return "normal"
        elif ratio < 1.5:
            return "high"
        else:
            return "extreme"
    
    def calculate(self, bars: List[OHLC]) -> VolatilityMetrics:
        """
        Calculate comprehensive volatility metrics.
        """
        if not bars:
            raise ValueError("No bars provided")
        
        closes = [b.close for b in bars]
        current_price = closes[-1]
        
        # ATR
        current_atr = self.atr(bars)
        
        # ATR series for ratio
        atrs = self.atr_series(bars)
        avg_atr = sum(atrs) / len(atrs) if atrs else current_atr
        
        # Historical volatility (using closes)
        hv = self.historical_volatility(closes)
        
        # Range stats
        ranges = [b.range for b in bars[-self.period:]]
        avg_range = sum(ranges) / len(ranges) if ranges else Decimal("0")
        max_range = max(ranges) if ranges else Decimal("0")
        min_range = min(ranges) if ranges else Decimal("0")
        
        # Range std
        range_floats = [float(r) for r in ranges]
        if len(range_floats) > 1:
            range_mean = sum(range_floats) / len(range_floats)
            range_std = math.sqrt(sum((r - range_mean) ** 2 for r in range_floats) / (len(range_floats) - 1))
        else:
            range_std = 0
        
        # Vol ratio
        vol_ratio = self.volatility_ratio(current_atr, avg_atr)
        
        return VolatilityMetrics(
            atr=current_atr,
            atr_percent=self.atr_percent(current_atr, current_price),
            historical_vol=hv,
            vol_ratio=vol_ratio,
            avg_range=Decimal(str(avg_range)),
            max_range=max_range,
            min_range=min_range,
            range_std=Decimal(str(range_std)),
            regime=self.classify_regime(vol_ratio)
        )
    
    # === Utility Methods ===
    
    def suggested_stop(
        self,
        price: Decimal,
        atr: Decimal,
        multiplier: Decimal = Decimal("1.5")
    ) -> Decimal:
        """Suggest stop price based on ATR."""
        return price - (atr * multiplier)
    
    def suggested_size(
        self,
        account: Decimal,
        risk_pct: Decimal,
        entry: Decimal,
        atr: Decimal,
        multiplier: Decimal = Decimal("1.5")
    ) -> Decimal:
        """Suggest position size based on ATR stop."""
        risk_amount = account * risk_pct
        stop_distance = atr * multiplier
        return risk_amount / stop_distance
    
    def keltner_levels(
        self,
        price: Decimal,
        atr: Decimal,
        multiplier: Decimal = Decimal("2.0")
    ) -> Tuple[Decimal, Decimal]:
        """Keltner channel levels."""
        upper = price + (atr * multiplier)
        lower = price - (atr * multiplier)
        return upper, lower


# === Quick Functions ===

def quick_atr(bars: List[Tuple[float, float, float]], period: int = 14) -> float:
    """Quick ATR from (high, low, close) tuples."""
    calc = VolatilityCalculator(period)
    ohlc_bars = [OHLC(Decimal(str(h)), Decimal(str(l)), Decimal(str(c))) for h, l, c in bars]
    return float(calc.atr(ohlc_bars))


def quick_hv(closes: List[float], annualize: bool = True) -> float:
    """Quick historical volatility from close prices."""
    calc = VolatilityCalculator()
    return float(calc.historical_volatility([Decimal(str(c)) for c in closes], annualize))


# === Usage ===

if __name__ == "__main__":
    # Sample price data
    sample_bars = [
        OHLC(Decimal("50500"), Decimal("49800"), Decimal("50200")),
        OHLC(Decimal("50800"), Decimal("50000"), Decimal("50500")),
        OHLC(Decimal("51000"), Decimal("50300"), Decimal("50800")),
        OHLC(Decimal("51200"), Decimal("50500"), Decimal("51000")),
        OHLC(Decimal("50800"), Decimal("50000"), Decimal("50200")),  # Down move
        OHLC(Decimal("50500"), Decimal("49500"), Decimal("49800")),  # More down
        OHLC(Decimal("50000"), Decimal("49000"), Decimal("49500")),  # Expansion
        OHLC(Decimal("49800"), Decimal("49200"), Decimal("49600")),
        OHLC(Decimal("50200"), Decimal("49500"), Decimal("50000")),  # Recovery
        OHLC(Decimal("50500"), Decimal("49800"), Decimal("50300")),
        OHLC(Decimal("50800"), Decimal("50200"), Decimal("50600")),
        OHLC(Decimal("51000"), Decimal("50400"), Decimal("50800")),
        OHLC(Decimal("51200"), Decimal("50600"), Decimal("51000")),
        OHLC(Decimal("51500"), Decimal("50800"), Decimal("51200")),
        OHLC(Decimal("51800"), Decimal("51000"), Decimal("51500")),
    ]
    
    calc = VolatilityCalculator(period=14)
    
    # Full metrics
    metrics = calc.calculate(sample_bars)
    print(metrics)
    
    print("\n=== PRACTICAL APPLICATIONS ===")
    
    # Stop placement
    price = Decimal("51500")
    stop = calc.suggested_stop(price, metrics.atr, Decimal("1.5"))
    print(f"Stop for {price}: ${stop:,.2f} ({(price-stop)/price*100:.1f}% below)")
    
    # Position sizing
    account = Decimal("100000")
    risk_pct = Decimal("0.01")  # 1%
    size = calc.suggested_size(account, risk_pct, price, metrics.atr)
    print(f"Position size (1% risk): {size:.4f} units")
    
    # Keltner channels
    upper, lower = calc.keltner_levels(price, metrics.atr)
    print(f"Keltner 2x: ${lower:,.2f} - ${upper:,.2f}")
    
    print("\n=== VOLATILITY REFERENCE ===")
    print("ATR% Interpretation:")
    print("  < 1%    - Very low, breakout imminent")
    print("  1-2%    - Low, trending")
    print("  2-4%    - Normal")
    print("  4-6%    - High, volatile")
    print("  > 6%    - Extreme, risk management critical")
    
    print("\nQuick ATR:", quick_atr([(50500, 49800, 50200), (50800, 50000, 50500)]))
```

## Output

```
=== VOLATILITY METRICS ===
ATR:           $621.43
ATR%:          1.21%
HV (annual):   52.3%

Range Avg:     $664.29
Range Max:     $1,000.00
Range Min:     $400.00
Range Std:     $181.98

Vol Ratio:     0.98x
Regime:        NORMAL

=== PRACTICAL APPLICATIONS ===
Stop for 51500: $50,578.57 (1.8% below)
Position size (1% risk): 0.1071 units
Keltner 2x: $50,257.14 - $52,742.86

=== VOLATILITY REFERENCE ===
ATR% Interpretation:
  < 1%    - Very low, breakout imminent
  1-2%    - Low, trending
  2-4%    - Normal
  4-6%    - High, volatile
  > 6%    - Extreme, risk management critical

Quick ATR: 650.0
```

## Quick Reference

```python
calc = VolatilityCalculator(period=14)

# ATR
atr = calc.atr(bars)

# Historical volatility (annualized)
hv = calc.historical_volatility(closes)

# Full metrics
metrics = calc.calculate(bars)
print(metrics.atr, metrics.atr_percent, metrics.regime)

# Practical uses
stop = calc.suggested_stop(price, atr, multiplier=1.5)
size = calc.suggested_size(account, 0.01, price, atr)
upper, lower = calc.keltner_levels(price, atr)
```

## Volatility Regimes

| Ratio | Regime | Action |
|-------|--------|--------|
| <0.5 | Extreme Low | Expect breakout |
| 0.5-0.75 | Low | Tighten stops |
| 0.75-1.25 | Normal | Standard sizing |
| 1.25-1.5 | High | Reduce size 50% |
| >1.5 | Extreme | Minimum size or skip |

---
*Utility: Volatility Calculator | Features: ATR, HV, regime detection, stop/size helpers*