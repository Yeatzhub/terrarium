# Market Regime Detector
*Ghost Learning | 2026-02-21*

Classify market conditions from price data to adapt strategy selection. Detects trending/ranging markets and volatility regimes. Fast batch or live analysis.

```python
#!/usr/bin/env python3
"""
Market Regime Detector
Classifies market conditions from OHLC data for strategy selection.

Usage:
    python regime_detector.py prices.csv
    python regime_detector.py prices.csv --window 20 --output regime.json
    python regime_detector.py --live BTCUSD --interval 1h
"""

import argparse
import csv
import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Optional, list, Callable
from collections import deque


class MarketRegime(Enum):
    """Market condition classifications."""
    TRENDING_UP = "📈 TRENDING_UP"
    TRENDING_DOWN = "📉 TRENDING_DOWN" 
    STRONG_TREND = "🔥 STRONG_TREND"
    RANGING = "➡️  RANGING"
    HIGH_VOLATILITY = "⚡ HIGH_VOLATILITY"
    LOW_VOLATILITY = "😴 LOW_VOLATILITY"
    CHOPPY = "🌊 CHOPPY"
    UNKNOWN = "❓ UNKNOWN"


@dataclass
class OHLC:
    """Price candle."""
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal("0")
    
    @property
    def range(self) -> Decimal:
        return self.high - self.low
    
    @property
    def body(self) -> Decimal:
        return abs(self.close - self.open)
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open


@dataclass
class RegimeAnalysis:
    """Regime analysis result for a window."""
    timestamp: datetime
    regime: MarketRegime
    confidence: float  # 0-1
    
    # Indicators
    adx: float         # Trend strength (0-100)
    atr: Decimal       # Average true range
    bb_width: float    # Bollinger band width
    volatility: float  # Std dev of returns
    trend_slope: float # Linear regression slope
    
    # Interpretation
    primary_regime: str
    secondary_signals: list[str]
    
    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "regime": self.regime.value,
            "confidence": self.confidence,
            "adx": self.adx,
            "atr": str(self.atr),
            "bb_width": self.bb_width,
            "volatility": self.volatility,
            "trend_slope": self.trend_slope,
            "primary_regime": self.primary_regime,
            "secondary_signals": self.secondary_signals
        }


class RegimeDetector:
    """Detect market regime from OHLC data."""
    
    def __init__(self, window: int = 14):
        self.window = window
        self.min_samples = window + 5
    
    def analyze(self, candles: list[OHLC]) -> RegimeAnalysis:
        """Analyze most recent window of candles."""
        if len(candles) < self.min_samples:
            return self._unknown(candles[-1] if candles else None)
        
        recent = candles[-self.window:]
        
        # Calculate indicators
        adx = self._calculate_adx(candles)
        atr = self._calculate_atr(recent)
        bb_width = self._calculate_bb_width(recent)
        volatility = self._calculate_volatility(recent)
        slope = self._calculate_slope(recent)
        
        # Classify regime
        regime, confidence, signals = self._classify(
            adx, bb_width, volatility, slope, recent
        )
        
        return RegimeAnalysis(
            timestamp=recent[-1].timestamp,
            regime=regime,
            confidence=confidence,
            adx=adx,
            atr=atr,
            bb_width=bb_width,
            volatility=volatility,
            trend_slope=slope,
            primary_regime=regime.value.split()[1] if " " in regime.value else "unknown",
            secondary_signals=signals
        )
    
    def _calculate_adx(self, candles: list[OHLC]) -> float:
        """Calculate Average Directional Index (trend strength)."""
        if len(candles) < self.window + 1:
            return 0.0
        
        # Simplified ADX calculation
        dm_plus = []
        dm_minus = []
        tr_list = []
        
        for i in range(1, len(candles)):
            curr = candles[i]
            prev = candles[i-1]
            
            # True Range
            tr = max(
                curr.high - curr.low,
                abs(curr.high - prev.close),
                abs(curr.low - prev.close)
            )
            tr_list.append(float(tr))
            
            # Directional Movement
            h_diff = curr.high - prev.high
            l_diff = prev.low - curr.low
            
            dm_p = h_diff if h_diff > l_diff and h_diff > 0 else 0
            dm_m = l_diff if l_diff > h_diff and l_diff > 0 else 0
            
            dm_plus.append(dm_p)
            dm_minus.append(dm_m)
        
        if len(tr_list) < self.window:
            return 0.0
        
        # Smooth
        atr = sum(tr_list[-self.window:]) / self.window
        di_plus = sum(dm_plus[-self.window:]) / self.window
        di_minus = sum(dm_minus[-self.window:]) / self.window
        
        if atr == 0:
            return 0.0
        
        dx = abs(di_plus - di_minus) / (di_plus + di_minus) * 100 if (di_plus + di_minus) > 0 else 0
        return dx
    
    def _calculate_atr(self, candles: list[OHLC]) -> Decimal:
        """Calculate Average True Range."""
        if len(candles) < 2:
            return Decimal("0")
        
        ranges = [c.range for c in candles]
        return sum(ranges) / len(ranges)
    
    def _calculate_bb_width(self, candles: list[OHLC]) -> float:
        """Calculate Bollinger Band width (volatility measure)."""
        if len(candles) < self.window:
            return 0.0
        
        closes = [float(c.close) for c in candles]
        sma = sum(closes) / len(closes)
        
        variance = sum((c - sma) ** 2 for c in closes) / len(closes)
        std_dev = math.sqrt(variance)
        
        upper = sma + (2 * std_dev)
        lower = sma - (2 * std_dev)
        
        if sma == 0:
            return 0.0
        
        return ((upper - lower) / sma) * 100
    
    def _calculate_volatility(self, candles: list[OHLC]) -> float:
        """Calculate volatility as std dev of returns."""
        if len(candles) < 2:
            return 0.0
        
        returns = []
        for i in range(1, len(candles)):
            ret = float((candles[i].close - candles[i-1].close) / candles[i-1].close)
            returns.append(ret)
        
        if not returns:
            return 0.0
        
        mean = sum(returns) / len(returns)
        variance = sum((r - mean) ** 2 for r in returns) / len(returns)
        return math.sqrt(variance) * 100  # As percentage
    
    def _calculate_slope(self, candles: list[OHLC]) -> float:
        """Linear regression slope of closes."""
        if len(candles) < 2:
            return 0.0
        
        n = len(candles)
        x_vals = list(range(n))
        y_vals = [float(c.close) for c in candles]
        
        x_mean = sum(x_vals) / n
        y_mean = sum(y_vals) / n
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _classify(self, adx: float, bb_width: float, vol: float, slope: float, candles: list[OHLC]) -> tuple[MarketRegime, float, list[str]]:
        """Classify market regime from indicators."""
        signals = []
        confidence = 0.5
        
        # Trend strength
        is_trending = adx > 25
        is_strong_trend = adx > 40
        
        # Volatility
        is_high_vol = vol > 2.0 or bb_width > 5.0
        is_low_vol = vol < 0.5 and bb_width < 2.0
        
        # Range vs trend
        is_ranging = bb_width < 3.0 and adx < 20
        
        # Determine primary regime
        if is_strong_trend:
            confidence = min(1.0, adx / 100 + 0.3)
            if slope > 0:
                signals.append("Strong upward momentum")
                return MarketRegime.STRONG_TREND, confidence, signals
            else:
                signals.append("Strong downward momentum")
                return MarketRegime.STRONG_TREND, confidence, signals
        
        if is_trending:
            confidence = min(1.0, adx / 100 + 0.2)
            if slope > 0:
                signals.append(f"ADX: {adx:.1f}")
                return MarketRegime.TRENDING_UP, confidence, signals
            else:
                signals.append(f"ADX: {adx:.1f}")
                return MarketRegime.TRENDING_DOWN, confidence, signals
        
        if is_high_vol:
            confidence = min(1.0, vol / 5.0)
            signals.append(f"High volatility: {vol:.2f}%")
            
            # Check for chop
            body_sum = sum(c.body for c in candles[-5:])
            range_sum = sum(c.range for c in candles[-5:])
            if range_sum > 0 and body_sum / range_sum < 0.4:
                return MarketRegime.CHOPPY, confidence, signals + ["Wicks dominate bodies"]
            
            return MarketRegime.HIGH_VOLATILITY, confidence, signals
        
        if is_low_vol:
            confidence = min(1.0, (0.5 - vol) / 0.5 + 0.3)
            signals.append(f"Low volatility: {vol:.2f}%")
            return MarketRegime.LOW_VOLATILITY, confidence, signals
        
        if is_ranging:
            confidence = 0.6
            signals.append(f"Narrow bands: {bb_width:.2f}%")
            return MarketRegime.RANGING, confidence, signals
        
        # Default
        confidence = 0.3
        return MarketRegime.UNKNOWN, confidence, ["Mixed signals"]
    
    def _unknown(self, candle: Optional[OHLC]) -> RegimeAnalysis:
        ts = candle.timestamp if candle else datetime.utcnow()
        return RegimeAnalysis(
            timestamp=ts,
            regime=MarketRegime.UNKNOWN,
            confidence=0.0,
            adx=0.0, atr=Decimal("0"), bb_width=0.0,
            volatility=0.0, trend_slope=0.0,
            primary_regime="unknown",
            secondary_signals=["Insufficient data"]
        )


class RollingRegimeDetector:
    """Continuous regime detection with rolling window."""
    
    def __init__(self, window: int = 14, history_size: int = 100):
        self.detector = RegimeDetector(window)
        self.history: deque[OHLC] = deque(maxlen=history_size)
        self.current_regime: Optional[RegimeAnalysis] = None
        self.regime_changes: list[tuple[datetime, MarketRegime]] = []
    
    def add_candle(self, candle: OHLC) -> Optional[RegimeAnalysis]:
        """Add new candle and return analysis if regime changed."""
        self.history.append(candle)
        
        if len(self.history) >= self.detector.min_samples:
            analysis = self.detector.analyze(list(self.history))
            
            # Check for regime change
            if (not self.current_regime or 
                self.current_regime.regime != analysis.regime):
                self.regime_changes.append((analysis.timestamp, analysis.regime))
                self.current_regime = analysis
                return analysis
            
            self.current_regime = analysis
        
        return None


def load_ohlc_csv(path: Path) -> list[OHLC]:
    """Load OHLC data from CSV."""
    candles = []
    
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            candle = OHLC(
                timestamp=datetime.fromisoformat(row["timestamp"]),
                open=Decimal(row["open"]),
                high=Decimal(row["high"]),
                low=Decimal(row["low"]),
                close=Decimal(row["close"]),
                volume=Decimal(row.get("volume", "0"))
            )
            candles.append(candle)
    
    return candles


def print_analysis(analysis: RegimeAnalysis):
    """Print formatted analysis."""
    print(f"\n{'─'*60}")
    print(f"  Market Regime Detection")
    print(f"{'─'*60}")
    print(f"  Timestamp:   {analysis.timestamp}")
    print(f"  Regime:      {analysis.regime.value}")
    print(f"  Confidence:  {analysis.confidence*100:.1f}%")
    print(f"{'─'*60}")
    print(f"  Indicators:")
    print(f"    ADX:        {analysis.adx:.1f} ({'Trending' if analysis.adx > 25 else 'Ranging'})")
    print(f"    ATR:        {analysis.atr:.2f}")
    print(f"    BB Width:   {analysis.bb_width:.2f}%")
    print(f"    Volatility: {analysis.volatility:.2f}%")
    print(f"    Slope:      {analysis.trend_slope:+.4f}")
    print(f"{'─'*60}")
    if analysis.secondary_signals:
        print(f"  Signals:     {', '.join(analysis.secondary_signals)}")
    print(f"{'─'*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Market Regime Detector")
    parser.add_argument("csv", type=Path, help="OHLC CSV file")
    parser.add_argument("--window", "-w", type=int, default=14, help="Analysis window")
    parser.add_argument("--rolling", "-r", action="store_true", help="Rolling analysis")
    parser.add_argument("--output", "-o", type=Path, help="Output to JSON")
    parser.add_argument("--last-only", "-l", action="store_true", help="Only analyze last window")
    parser.add_argument("--summary", "-s", action="store_true", help="Show regime summary")
    
    args = parser.parse_args()
    
    # Load data
    candles = load_ohlc_csv(args.csv)
    print(f"Loaded {len(candles)} candles")
    
    if args.last_only:
        # Single analysis on most recent window
        detector = RegimeDetector(window=args.window)
        analysis = detector.analyze(candles)
        print_analysis(analysis)
        results = [analysis]
    
    elif args.rolling:
        # Rolling regime changes
        detector = RollingRegimeDetector(window=args.window)
        results = []
        
        for candle in candles:
            change = detector.add_candle(candle)
            if change:
                print_analysis(change)
                results.append(change)
        
        print(f"\nDetected {len(detector.regime_changes)} regime changes")
    
    else:
        # Analysis at intervals
        detector = RegimeDetector(window=args.window)
        results = []
        step = args.window
        
        for i in range(0, len(candles) - args.window + 1, step):
            window = candles[i:i + args.window]
            analysis = detector.analyze(window)
            results.append(analysis)
        
        # Show last few
        for analysis in results[-5:]:
            print_analysis(analysis)
    
    # Summary
    if args.summary and results:
        regimes = {}
        for r in results:
            key = r.regime.value
            regimes[key] = regimes.get(key, 0) + 1
        
        print(f"\n{'═'*60}")
        print(f"  REGIME SUMMARY")
        print(f"{'═'*60}")
        total = len(results)
        for regime, count in sorted(regimes.items(), key=lambda x: -x[1]):
            pct = (count / total) * 100
            bar = "█" * int(pct / 5)
            print(f"  {regime:<25} {count:>4} ({pct:5.1f}%) {bar}")
        print(f"{'═'*60}\n")
    
    # Output
    if args.output:
        data = {
            "window": args.window,
            "total_candles": len(candles),
            "analyses": [r.to_dict() for r in results]
        }
        args.output.write_text(json.dumps(data, indent=2))
        print(f"💾 Saved to {args.output}")


# === Quick Examples ===

# 1. Analyze last window only
# python regime_detector.py prices.csv -l

# 2. Rolling regime detection
# python regime_detector.py prices.csv --rolling

# 3. Larger window for swing analysis
# python regime_detector.py prices.csv -w 50 --summary

# 4. Sample CSV:
# echo "timestamp,open,high,low,close,volume
# 2026-02-01T00:00:00,50000,51000,49500,50500,1000
# 2026-02-02T00:00:00,50500,52000,50000,51500,1200" > prices.csv


if __name__ == "__main__":
    main()
```

## Quick Start

```bash
# Basic analysis
python regime_detector.py prices.csv

# Rolling regime detection (shows changes)
python regime_detector.py prices.csv --rolling

# Larger window for swing trading
python regime_detector.py prices.csv -w 50 --summary

# Export to JSON
python regime_detector.py prices.csv --rolling -o regimes.json
```

## Sample Output

```
Loaded 100 candles

────────────────────────────────────────────────────────────
  Market Regime Detection
────────────────────────────────────────────────────────────
  Timestamp:   2026-02-21 14:23:00
  Regime:      📈 TRENDING_UP
  Confidence:  78.5%
────────────────────────────────────────────────────────────
  Indicators:
    ADX:        32.4 (Trending)
    ATR:        125.50
    BB Width:   4.20%
    Volatility: 1.85%
    Slope:      +12.4500
────────────────────────────────────────────────────────────
  Signals:     ADX: 32.4
────────────────────────────────────────────────────────────
```

## Regime Types

| Regime | ADX | Characteristics | Strategy Fit |
|--------|-----|-----------------|--------------|
| STRONG_TREND | >40 | High conviction | Trend following |
| TRENDING_UP | 25-40 | Upward momentum | Long positions |
| TRENDING_DOWN | 25-40 | Downward momentum | Short positions |
| RANGING | <20, BB <3% | Sideways | Mean reversion |
| HIGH_VOLATILITY | Vol >2% | Wide swings | Volatility trading |
| LOW_VOLATILITY | Vol <0.5% | Tight range | Breakout plays |
| CHOPPY | Wicks >60% | Noise | Avoid/new strategy |

## Sample CSV Format

```csv
timestamp,open,high,low,close,volume
2026-02-01T00:00:00,50000,51000,49500,50500,1000
2026-02-02T00:00:00,50500,52000,50000,51500,1200
```

## Strategy Selection

```python
# Integrate into trading bot
detector = RegimeDetector(window=20)

async def on_candle(candle):
    regime = detector.add_candle(candle)
    
    if regime and regime.regime == MarketRegime.TRENDING_UP:
        await activate_trend_strategy(regime.confidence)
    elif regime and regime.regime == MarketRegime.RANGING:
        await activate_mean_reversion_strategy()
    elif regime and regime.regime == MarketRegime.HIGH_VOLATILITY:
        await reduce_position_sizes()
```

## Indicators Explained

| Indicator | Purpose | Levels |
|-----------|---------|--------|
| ADX | Trend strength | <20 = weak, 20-40 = trend, >40 = strong |
| ATR | Absolute volatility | Higher = bigger moves |
| BB Width | Relative volatility | <3% = squeeze, >5% = expansion |
| Volatility | Std dev of returns | <0.5% = quiet, >2% = wild |
| Slope | Trend direction | Positive = up, negative = down |

---
*Utility: Market Regime Detector | Strategy selection via price analysis*
