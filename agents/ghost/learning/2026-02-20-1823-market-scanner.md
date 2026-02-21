# Market Scanner — Multi-Criteria Opportunity Filter

**Purpose:** Screen markets for trading opportunities based on technical and fundamental criteria  
**Use Case:** Find breakout setups, mean reversion candidates, trend continuation plays

## The Code

```python
"""
Market Scanner
Multi-criteria screening for trading opportunities.
Filter by trend, volatility, volume, and technical patterns.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import defaultdict
import statistics


class ScanType(Enum):
    BREAKOUT = auto()        # Breaking above resistance
    PULLBACK = auto()        # Pullback to support in uptrend
    OVERSOLD = auto()        # RSI/Momentum oversold
    OVERBOUGHT = auto()      # RSI/Momentum overbought
    TRENDING = auto()        # Strong directional movement
    HIGH_VOLUME = auto()     # Unusual volume activity
    RANGE_BOUND = auto()     # Consolidating, range play
    VOLATILITY_EXPANSION = auto()  # Volatility spike
    GAP = auto()             # Gap up/down


@dataclass
class SymbolData:
    """Price and indicator data for a symbol."""
    symbol: str
    price: float
    change_pct: float
    volume: float
    avg_volume: float
    
    # Technicals
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    rsi_14: Optional[float] = None
    atr_14: Optional[float] = None
    
    # Levels
    high_20d: Optional[float] = None
    low_20d: Optional[float] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    
    # Fundamentals (optional)
    market_cap: Optional[float] = None
    sector: str = ""
    industry: str = ""


@dataclass
class ScanResult:
    """Single scan match."""
    symbol: str
    scan_type: ScanType
    price: float
    
    # Match details
    trigger_value: float  # The value that triggered the scan
    trigger_description: str
    
    # Score 0-100
    quality_score: float
    
    # Context
    trend_direction: str  # up, down, neutral
    volume_vs_avg: float  # ratio
    distance_to_support: Optional[float] = None
    distance_to_resistance: Optional[float] = None
    
    # Recommendation
    suggested_stop: Optional[float] = None
    suggested_target: Optional[float] = None
    position_size: str = "normal"  # small, normal, large


@dataclass
class ScanCriteria:
    """Criteria for a specific scan type."""
    min_price: float = 5.0
    max_price: float = 1000.0
    min_volume: float = 100000
    min_avg_volume: float = 500000
    
    # Technical thresholds
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    volume_spike_threshold: float = 2.0  # 2x average
    
    # Trend
    trend_lookback: int = 20
    min_trend_strength: float = 0.05  # 5% move


class MarketScanner:
    """
    Multi-criteria market scanner for trading opportunities.
    
    Usage:
        scanner = MarketScanner()
        
        # Load data
        symbols_data = load_market_data()
        
        # Run scans
        breakouts = scanner.scan(symbols_data, ScanType.BREAKOUT)
        pullbacks = scanner.scan(symbols_data, ScanType.PULLBACK)
        
        # Review results
        for result in breakouts[:10]:
            print(f"{result.symbol}: {result.trigger_description}")
    """
    
    def __init__(self, criteria: Optional[ScanCriteria] = None):
        self.criteria = criteria or ScanCriteria()
        self.scan_functions: Dict[ScanType, Callable] = {
            ScanType.BREAKOUT: self._scan_breakout,
            ScanType.PULLBACK: self._scan_pullback,
            ScanType.OVERSOLD: self._scan_oversold,
            ScanType.OVERBOUGHT: self._scan_overbought,
            ScanType.TRENDING: self._scan_trending,
            ScanType.HIGH_VOLUME: self._scan_high_volume,
            ScanType.RANGE_BOUND: self._scan_range_bound,
            ScanType.VOLATILITY_EXPANSION: self._scan_volatility_expansion,
        }
    
    def scan(
        self,
        data: List[SymbolData],
        scan_type: ScanType,
        max_results: int = 20,
        min_score: float = 50.0
    ) -> List[ScanResult]:
        """Run scan on symbol data."""
        scan_fn = self.scan_functions.get(scan_type)
        if not scan_fn:
            return []
        
        results = []
        
        for symbol_data in data:
            # Basic filters
            if not self._passes_basic_filters(symbol_data):
                continue
            
            # Run specific scan
            result = scan_fn(symbol_data)
            if result and result.quality_score >= min_score:
                results.append(result)
        
        # Sort by quality score
        results.sort(key=lambda r: r.quality_score, reverse=True)
        
        return results[:max_results]
    
    def scan_all(
        self,
        data: List[SymbolData],
        max_per_type: int = 10
    ) -> Dict[ScanType, List[ScanResult]]:
        """Run all scan types."""
        return {
            scan_type: self.scan(data, scan_type, max_per_type)
            for scan_type in ScanType
            if scan_type in self.scan_functions
        }
    
    def _passes_basic_filters(self, data: SymbolData) -> bool:
        """Check basic eligibility."""
        if data.price < self.criteria.min_price or data.price > self.criteria.max_price:
            return False
        
        if data.volume < self.criteria.min_volume:
            return False
        
        if data.avg_volume < self.criteria.min_avg_volume:
            return False
        
        return True
    
    def _scan_breakout(self, data: SymbolData) -> Optional[ScanResult]:
        """Find price breaking above recent highs."""
        if not data.high_20d:
            return None
        
        # Breakout above 20-day high
        if data.price <= data.high_20d:
            return None
        
        # Calculate score
        breakout_pct = (data.price / data.high_20d - 1) * 100
        volume_boost = data.volume / data.avg_volume
        
        score = min(100, 60 + breakout_pct * 10 + (volume_boost - 1) * 10)
        
        # Trend check
        trend = self._determine_trend(data)
        if trend == "down":
            score -= 20  # Penalty for counter-trend breakout
        
        # Calculate levels
        stop = data.high_20d * 0.98  # Just below breakout level
        target = data.price + (data.price - stop) * 2  # 2:1 R/R
        
        return ScanResult(
            symbol=data.symbol,
            scan_type=ScanType.BREAKOUT,
            price=data.price,
            trigger_value=breakout_pct,
            trigger_description=f"Broke 20d high by {breakout_pct:.1f}%",
            quality_score=score,
            trend_direction=trend,
            volume_vs_avg=volume_boost,
            suggested_stop=stop,
            suggested_target=target,
            position_size="normal" if score > 75 else "small"
        )
    
    def _scan_pullback(self, data: SymbolData) -> Optional[ScanResult]:
        """Find pullbacks to support in uptrend."""
        if not data.sma_20 or not data.sma_50:
            return None
        
        # Must be in uptrend
        if data.sma_20 <= data.sma_50:
            return None
        
        # Price near SMA 20 (pullback to moving average)
        distance_to_sma = abs(data.price - data.sma_20) / data.sma_20 * 100
        
        if distance_to_sma > 3:  # Too far from support
            return None
        
        score = min(100, 70 - distance_to_sma * 5)
        
        # Better if above SMA
        if data.price > data.sma_20:
            score += 10
        
        # Volume should be declining (healthy pullback)
        volume_ratio = data.volume / data.avg_volume
        if volume_ratio < 0.8:
            score += 10
        
        stop = data.sma_50 * 0.98
        target = data.high_20d if data.high_20d else data.price * 1.05
        
        return ScanResult(
            symbol=data.symbol,
            scan_type=ScanType.PULLBACK,
            price=data.price,
            trigger_value=distance_to_sma,
            trigger_description=f"Pullback to SMA-20 ({distance_to_sma:.1f}% away)",
            quality_score=score,
            trend_direction="up",
            volume_vs_avg=volume_ratio,
            suggested_stop=stop,
            suggested_target=target,
            position_size="normal"
        )
    
    def _scan_oversold(self, data: SymbolData) -> Optional[ScanResult]:
        """Find oversold bounce candidates."""
        if data.rsi_14 is None:
            return None
        
        if data.rsi_14 >= self.criteria.rsi_oversold:
            return None
        
        score = min(100, 80 - data.rsi_14)
        
        # Better if high volume (capitulation)
        volume_ratio = data.volume / data.avg_volume
        if volume_ratio > 1.5:
            score += 10
        
        # Check if near support
        support_distance = None
        if data.low_20d:
            support_distance = (data.price / data.low_20d - 1) * 100
            if support_distance < 2:
                score += 10
        
        stop = data.low_20d * 0.98 if data.low_20d else data.price * 0.95
        target = data.price + (data.price - stop) * 1.5
        
        return ScanResult(
            symbol=data.symbol,
            scan_type=ScanType.OVERSOLD,
            price=data.price,
            trigger_value=data.rsi_14,
            trigger_description=f"RSI oversold at {data.rsi_14:.1f}",
            quality_score=score,
            trend_direction="down",  # In downtrend usually
            volume_vs_avg=volume_ratio,
            distance_to_support=support_distance,
            suggested_stop=stop,
            suggested_target=target,
            position_size="small"  # Counter-trend, be careful
        )
    
    def _scan_overbought(self, data: SymbolData) -> Optional[ScanResult]:
        """Find overbought shorts (or caution for longs)."""
        if data.rsi_14 is None:
            return None
        
        if data.rsi_14 <= self.criteria.rsi_overbought:
            return None
        
        score = min(100, data.rsi_14 - 30)
        
        # Volume confirmation
        volume_ratio = data.volume / data.avg_volume
        
        return ScanResult(
            symbol=data.symbol,
            scan_type=ScanType.OVERBOUGHT,
            price=data.price,
            trigger_value=data.rsi_14,
            trigger_description=f"RSI overbought at {data.rsi_14:.1f}",
            quality_score=score,
            trend_direction="up",
            volume_vs_avg=volume_ratio,
            position_size="avoid"  # Warning signal
        )
    
    def _scan_trending(self, data: SymbolData) -> Optional[ScanResult]:
        """Find strongly trending stocks."""
        trend = self._determine_trend(data)
        
        if trend == "neutral":
            return None
        
        # Score based on trend strength
        score = min(100, 50 + abs(data.change_pct) * 2)
        
        # Volume confirms
        volume_ratio = data.volume / data.avg_volume
        if volume_ratio > 1.5:
            score += 15
        
        return ScanResult(
            symbol=data.symbol,
            scan_type=ScanType.TRENDING,
            price=data.price,
            trigger_value=data.change_pct,
            trigger_description=f"Strong {trend}trend: {data.change_pct:+.1f}%",
            quality_score=score,
            trend_direction=trend,
            volume_vs_avg=volume_ratio,
            position_size="normal"
        )
    
    def _scan_high_volume(self, data: SymbolData) -> Optional[ScanResult]:
        """Find unusual volume activity."""
        volume_ratio = data.volume / data.avg_volume
        
        if volume_ratio < self.criteria.volume_spike_threshold:
            return None
        
        score = min(100, 50 + (volume_ratio - 2) * 20)
        
        return ScanResult(
            symbol=data.symbol,
            scan_type=ScanType.HIGH_VOLUME,
            price=data.price,
            trigger_value=volume_ratio,
            trigger_description=f"Volume {volume_ratio:.1f}x average",
            quality_score=score,
            trend_direction=self._determine_trend(data),
            volume_vs_avg=volume_ratio,
            position_size="normal"
        )
    
    def _scan_range_bound(self, data: SymbolData) -> Optional[ScanResult]:
        """Find consolidating stocks (mean reversion plays)."""
        if not data.high_20d or not data.low_20d:
            return None
        
        # Calculate range
        range_pct = (data.high_20d / data.low_20d - 1) * 100
        
        if range_pct > 10:  # Too volatile
            return None
        
        # Price should be near middle of range
        range_mid = (data.high_20d + data.low_20d) / 2
        distance_from_mid = abs(data.price - range_mid) / range_mid * 100
        
        if distance_from_mid > 3:
            return None
        
        score = min(100, 80 - range_pct * 3)
        
        return ScanResult(
            symbol=data.symbol,
            scan_type=ScanType.RANGE_BOUND,
            price=data.price,
            trigger_value=range_pct,
            trigger_description=f"Range-bound: {range_pct:.1f}% 20d range",
            quality_score=score,
            trend_direction="neutral",
            volume_vs_avg=data.volume / data.avg_volume,
            distance_to_support=(data.price / data.low_20d - 1) * 100,
            distance_to_resistance=(data.high_20d / data.price - 1) * 100,
            suggested_stop=data.low_20d * 0.99,
            suggested_target=data.high_20d * 0.99,
            position_size="small"
        )
    
    def _scan_volatility_expansion(self, data: SymbolData) -> Optional[ScanResult]:
        """Find volatility expansion (often precedes big moves)."""
        if not data.atr_14:
            return None
        
        # ATR as % of price
        atr_pct = (data.atr_14 / data.price) * 100
        
        if atr_pct < 2:  # Not expanded
            return None
        
        score = min(100, 50 + atr_pct * 10)
        
        return ScanResult(
            symbol=data.symbol,
            scan_type=ScanType.VOLATILITY_EXPANSION,
            price=data.price,
            trigger_value=atr_pct,
            trigger_description=f"Volatility expanded: {atr_pct:.1f}% ATR",
            quality_score=score,
            trend_direction=self._determine_trend(data),
            volume_vs_avg=data.volume / data.avg_volume,
            position_size="small"  # Volatile = reduce size
        )
    
    def _determine_trend(self, data: SymbolData) -> str:
        """Determine trend direction."""
        if data.sma_20 and data.sma_50:
            if data.sma_20 > data.sma_50 * 1.02:
                return "up"
            elif data.sma_20 < data.sma_50 * 0.98:
                return "down"
        
        if data.change_pct > 5:
            return "up"
        elif data.change_pct < -5:
            return "down"
        
        return "neutral"


def format_scan_results(results: List[ScanResult], scan_type: ScanType) -> str:
    """Pretty print scan results."""
    if not results:
        return f"No {scan_type.name} opportunities found."
    
    lines = [
        f"{'=' * 70}",
        f"SCAN RESULTS: {scan_type.name}",
        f"{'=' * 70}",
        "",
        f"{'Symbol':<8} {'Price':<10} {'Trigger':<25} {'Score':<8} {'Trend':<8}",
        "-" * 70,
    ]
    
    for r in results[:15]:
        emoji = "🟢" if r.quality_score >= 80 else "🟡" if r.quality_score >= 60 else "⚪"
        lines.append(
            f"{emoji} {r.symbol:<6} ${r.price:<8.2f} {r.trigger_description:<25} "
            f"{r.quality_score:<8.0f} {r.trend_direction:<8}"
        )
    
    lines.append(f"{'=' * 70}")
    
    return "\n".join(lines)


# === Examples ===

def example_scanner():
    """Demonstrate market scanner."""
    print("=" * 70)
    print("Market Scanner Demo")
    print("=" * 70)
    
    import random
    random.seed(42)
    
    # Generate sample market data
    symbols = []
    base_symbols = [
        ("AAPL", 175, "tech"),
        ("MSFT", 330, "tech"),
        ("GOOGL", 140, "tech"),
        ("AMZN", 180, "tech"),
        ("NVDA", 450, "tech"),
        ("TSLA", 250, "auto"),
        ("JPM", 170, "financial"),
        ("BAC", 35, "financial"),
        ("JNJ", 155, "healthcare"),
        ("PFE", 28, "healthcare"),
        ("XOM", 115, "energy"),
        ("CVX", 155, "energy"),
        ("WMT", 165, "consumer"),
        ("HD", 350, "consumer"),
        ("NFLX", 600, "tech"),
    ]
    
    for sym, base_price, sector in base_symbols:
        # Randomize current values
        price = base_price * random.uniform(0.95, 1.05)
        change = random.uniform(-5, 8)
        volume = random.uniform(1, 5) * 1000000
        avg_volume = random.uniform(2, 4) * 1000000
        
        # Technicals
        sma_20 = price * random.uniform(0.98, 1.02)
        sma_50 = price * random.uniform(0.95, 1.05)
        rsi = random.uniform(20, 80)
        atr = price * random.uniform(0.01, 0.03)
        
        # Levels
        high_20d = price * random.uniform(1.0, 1.15)
        low_20d = price * random.uniform(0.85, 1.0)
        
        symbols.append(SymbolData(
            symbol=sym,
            price=price,
            change_pct=change,
            volume=volume,
            avg_volume=avg_volume,
            sma_20=sma_20,
            sma_50=sma_50,
            rsi_14=rsi,
            atr_14=atr,
            high_20d=high_20d,
            low_20d=low_20d,
            sector=sector
        ))
    
    scanner = MarketScanner()
    
    # Run various scans
    print("\n1. BREAKOUT SCAN")
    print("-" * 70)
    breakouts = scanner.scan(symbols, ScanType.BREAKOUT, max_results=5)
    if breakouts:
        for r in breakouts:
            print(f"🚀 {r.symbol}: {r.trigger_description}")
            print(f"   Score: {r.quality_score:.0f} | Suggested stop: ${r.suggested_stop:.2f}")
    else:
        print("No breakouts found")
    
    print("\n2. PULLBACK SCAN")
    print("-" * 70)
    pullbacks = scanner.scan(symbols, ScanType.PULLBACK, max_results=5)
    if pullbacks:
        for r in pullbacks:
            print(f"📉 {r.symbol}: {r.trigger_description}")
            print(f"   Score: {r.quality_score:.0f} | Near SMA-20 support")
    else:
        print("No pullbacks found")
    
    print("\n3. OVERSOLD SCAN")
    print("-" * 70)
    oversold = scanner.scan(symbols, ScanType.OVERSOLD, max_results=5)
    if oversold:
        for r in oversold:
            print(f"🔵 {r.symbol}: {r.trigger_description}")
            print(f"   Score: {r.quality_score:.0f} | Mean reversion candidate")
    else:
        print("No oversold candidates")
    
    print("\n4. HIGH VOLUME SCAN")
    print("-" * 70)
    high_vol = scanner.scan(symbols, ScanType.HIGH_VOLUME, max_results=5)
    if high_vol:
        for r in high_vol:
            print(f"📊 {r.symbol}: {r.trigger_description}")
            print(f"   Score: {r.quality_score:.0f}")
    else:
        print("No high volume alerts")
    
    # Summary
    print("\n" + "=" * 70)
    print("SCAN SUMMARY")
    print("=" * 70)
    
    all_scans = scanner.scan_all(symbols, max_per_type=5)
    
    for scan_type, results in all_scans.items():
        print(f"{scan_type.name:<20}: {len(results)} opportunities")
    
    print("\n" + "=" * 70)
    print("TOP SETUP BY SCAN TYPE:")
    print("=" * 70)
    
    for scan_type, results in all_scans.items():
        if results:
            top = results[0]
            emoji = {"BREAKOUT": "🚀", "PULLBACK": "📉", "OVERSOLD": "🔵", 
                    "OVERBOUGHT": "🔴", "TRENDING": "📈", "HIGH_VOLUME": "📊",
                    "RANGE_BOUND": "↔️", "VOLATILITY_EXPANSION": "⚡"}.get(scan_type.name, "⚪")
            print(f"{emoji} {scan_type.name:<20} | {top.symbol} | Score: {top.quality_score:.0f}")


if __name__ == "__main__":
    example_scanner()
    
    print("\n" + "=" * 70)
    print("SCANNER USAGE:")
    print("=" * 70)
    print("""
scanner = MarketScanner()
data = load_price_data()  # Your data source

# Single scan type
breakouts = scanner.scan(data, ScanType.BREAKOUT)
for result in breakouts:
    if result.quality_score > 80:
        analyze_setup(result)

# All scans at once
all_results = scanner.scan_all(data)
for scan_type, results in all_results.items():
    if results:
        print(f"{scan_type.name}: {len(results)} found")

# Filter by quality
high_quality = [r for r in breakouts if r.quality_score >= 80]
    """)
    print("=" * 70)
```

## Scan Types & Use Cases

| Scan | Best For | Entry Trigger | Exit Plan |
|------|----------|---------------|-----------|
| **BREAKOUT** | Momentum | 20d high break | Stop below breakout level |
| **PULLBACK** | Trend following | Touch 20 SMA | Stop below 50 SMA |
| **OVERSOLD** | Mean reversion | RSI < 30 | Stop at 20d low |
| **OVERBOUGHT** | Short/Warning | RSI > 70 | Caution for longs |
| **TRENDING** | Momentum | >5% move | Trail with trend |
| **HIGH_VOLUME** | Confirmation | 2x volume | Follow volume |
| **RANGE_BOUND** | Mean reversion | Middle of range | Buy low, sell high |
| **VOLATILITY** | Expansion plays | ATR spike | Wide stops required |

## Quick Reference

```python
scanner = MarketScanner()

# Find breakout setups
breakouts = scanner.scan(data, ScanType.BREAKOUT, max_results=10)

# Quality filter
high_confidence = [r for r in breakouts if r.quality_score >= 80]

# Multiple scans
all_scans = scanner.scan_all(data)
pullbacks = all_scans[ScanType.PULLBACK]

# Review best setup
if breakouts:
    best = breakouts[0]
    print(f"{best.symbol}: Stop ${best.suggested_stop:.2f}, Target ${best.suggested_target:.2f}")
```

## Scan Quality Scoring

| Score | Quality | Action |
|-------|---------|--------|
| 80-100 | Excellent | High priority setup |
| 60-79 | Good | Worth watching |
| 40-59 | Fair | Lower size |
| <40 | Poor | Skip |

---

**Created by Ghost 👻 | Feb 20, 2026 | 12-min learning sprint**  
*Lesson: "Opportunities are everywhere, but good setups are rare." A scanner filters noise and finds trades that match your criteria. Let the computer do the watching—you do the trading.*
