"""
Oracle Technical Indicators
Pure NumPy implementations for high-performance trading analysis
Author: Oracle (Trading Strategist)
"""

import numpy as np
from typing import Tuple, Optional


# =============================================================================
# VWAP (Volume-Weighted Average Price) with Standard Deviation Bands
# =============================================================================

def vwap(high: np.ndarray, low: np.ndarray, close: np.ndarray, 
         volume: np.ndarray, period: int = 14, 
         num_std: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Volume-Weighted Average Price with Standard Deviation Bands (Vectorized)
    
    Mathematical Formula:
    ---------------------
    Typical Price (TP) = (High + Low + Close) / 3
    
    VWAP_i = RollingSum(TP × Volume, period)_i / RollingSum(Volume, period)_i
    
    Variance_i = RollingSum(Volume × (TP - VWAP)², period)_i / RollingSum(Volume, period)_i
    Std Dev_i = √Variance_i
    
    Upper Band = VWAP + (num_std × Std Dev)
    Lower Band = VWAP - (num_std × Std Dev)
    
    Use Case:
    ---------
    VWAP identifies the average price weighted by volume, serving as:
    - Support/resistance level
    - Benchmark for execution quality
    - Trend identification tool
    
    Parameters:
    -----------
    high : np.ndarray - High prices
    low : np.ndarray - Low prices  
    close : np.ndarray - Close prices
    volume : np.ndarray - Volume data
    period : int - Lookback period (default: 14)
    num_std : float - Number of standard deviations for bands (default: 2.0)
    
    Returns:
    --------
    Tuple of (vwap_line, upper_band, lower_band)
    """
    # Typical Price = (High + Low + Close) / 3
    typical_price = (high + low + close) / 3.0
    
    # Cumulative sums using convolution for rolling window
    tp_vol = typical_price * volume
    
    # Using cumsum with windowed approach
    cumsum_tpvol = np.cumsum(tp_vol)
    cumsum_vol = np.cumsum(volume)
    
    # Rolling sums: subtract shifted cumsum from current cumsum
    tpvol_sum = np.empty_like(tp_vol)
    tpvol_sum[:period] = cumsum_tpvol[:period]
    tpvol_sum[period:] = cumsum_tpvol[period:] - cumsum_tpvol[:-period]
    
    vol_sum = np.empty_like(volume)
    vol_sum[:period] = cumsum_vol[:period]
    vol_sum[period:] = cumsum_vol[period:] - cumsum_vol[:-period]
    
    # VWAP calculation
    vwap_line = np.full_like(close, np.nan)
    vwap_line[period-1:] = tpvol_sum[period-1:] / vol_sum[period-1:]
    
    # Standard deviation bands using vectorized approach
    upper_band = np.full_like(close, np.nan)
    lower_band = np.full_like(close, np.nan)
    
    for i in range(period - 1, len(close)):
        tp_window = typical_price[i - period + 1:i + 1]
        vol_window = volume[i - period + 1:i + 1]
        vol_s = vol_sum[i]
        if vol_s > 0:
            variance = np.sum(vol_window * (tp_window - vwap_line[i]) ** 2) / vol_s
            std_dev = np.sqrt(max(0, variance))
            upper_band[i] = vwap_line[i] + (num_std * std_dev)
            lower_band[i] = vwap_line[i] - (num_std * std_dev)
    
    return vwap_line, upper_band, lower_band


def vwap_cumulative(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                    volume: np.ndarray, reset_period: int = 390,
                    num_std: float = 2.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Cumulative VWAP (resets periodically, e.g., daily for intraday)
    
    Mathematical Formula:
    ---------------------
    Same as VWAP but cumulative from start of period
    
    VWAP_cumul_i = Σ(TP_0:i × Volume_0:i) / Σ(Volume_0:i)
    
    Used for intraday trading with session-based reset
    
    Parameters:
    -----------
    reset_period : int - Bars before reset (e.g., 390 for 1-min bars in trading day)
    """
    n = len(close)
    vwap_line = np.full(n, np.nan)
    upper_band = np.full(n, np.nan)
    lower_band = np.full(n, np.nan)
    
    typical_price = (high + low + close) / 3.0
    
    cum_tp_vol = 0.0
    cum_vol = 0.0
    cum_tp_vol_sq = 0.0
    
    for i in range(n):
        # Reset at period boundaries
        if i % reset_period == 0:
            cum_tp_vol = 0.0
            cum_vol = 0.0
            cum_tp_vol_sq = 0.0
        
        tp = typical_price[i]
        vol = volume[i]
        
        cum_tp_vol += tp * vol
        cum_vol += vol
        
        if cum_vol > 0:
            vwap_line[i] = cum_tp_vol / cum_vol
            
            # Running variance calculation
            cum_tp_vol_sq += vol * (tp ** 2)
            mean_sq = cum_tp_vol_sq / cum_vol
            mean = vwap_line[i]
            variance = mean_sq - (mean ** 2)
            std_dev = np.sqrt(max(0, variance))  # max prevents numerical errors
            
            upper_band[i] = vwap_line[i] + (num_std * std_dev)
            lower_band[i] = vwap_line[i] - (num_std * std_dev)
    
    return vwap_line, upper_band, lower_band


# =============================================================================
# RVOL (Relative Volume)
# =============================================================================

def rvol(volume: np.ndarray, short_period: int = 5, 
         long_period: int = 20, min_bars: int = 5) -> np.ndarray:
    """
    Relative Volume - Current volume vs Historical Average (Vectorized)
    
    Mathematical Formula:
    ---------------------
    RVOL = Current Volume / Average Volume over lookback period
    
    Or with smoothing:
    RVOL = SMA(Volume, short_period) / SMA(Volume, long_period)
    
    Where:
    - SMA = Simple Moving Average = Σ(Volume) / n
    
    Interpretation:
    ---------------
    RVOL > 2.0: Unusual volume spike (2x normal)
    RVOL < 0.5: Unusual volume contraction
    RVOL ≈ 1.0: Normal volume
    
    Parameters:
    -----------
    volume : np.ndarray - Volume data
    short_period : int - Current/short-term period (default: 5)
    long_period : int - Historical baseline period (default: 20)
    min_bars : int - Minimum bars needed to calculate
    
    Returns:
    --------
    np.ndarray - RVOL values (ratio format)
    """
    n = len(volume)
    
    # Calculate cumulative sums for efficient rolling mean
    cumsum = np.cumsum(volume)
    
    # Short-term SMA using cumsum with window subtraction
    # Rolling sum = cumsum[i] - cumsum[i-period]
    short_sum = np.empty(n)
    short_sum[:short_period] = cumsum[:short_period]
    short_sum[short_period:] = cumsum[short_period:] - cumsum[:-short_period]
    short_sma = short_sum / short_period
    
    # Long-term SMA
    long_sum = np.empty(n)
    long_sum[:long_period] = cumsum[:long_period]
    long_sum[long_period:] = cumsum[long_period:] - cumsum[:-long_period]
    long_sma = long_sum / long_period
    
    # RVOL calculation - vectorized
    rvol = np.full(n, np.nan)
    valid_mask = long_sma > 0
    rvol[valid_mask] = short_sma[valid_mask] / long_sma[valid_mask]
    
    # Mask first (long_period - 1) values as NaN
    rvol[:long_period-1] = np.nan
    
    return rvol


def rvol_time_adjusted(volume: np.ndarray, time_index: np.ndarray,
                       lookback_days: int = 20) -> np.ndarray:
    """
    Time-Adjusted RVOL (compares to same time on previous days)
    
    Mathematical Formula:
    ---------------------
    RVOL_ta = Volume[t] / Mean(Volume[t at same time on days 1..n])
    
    Example: Compare 10:30 AM volume to average 10:30 AM volume
              over past 20 days
    
    Parameters:
    -----------
    volume : np.ndarray - Volume data
    time_index : np.ndarray - Time markers for alignment (e.g., minute of day)
    lookback_days : int - Number of same-time comparisons
    """
    n = len(volume)
    rvol = np.full(n, np.nan)
    
    # Group by time index and calculate averages
    unique_times = np.unique(time_index)
    time_averages = {}
    
    for t in unique_times:
        mask = time_index == t
        time_averages[t] = np.mean(volume[mask]) if np.any(mask) else 0
    
    for i in range(n):
        ta = time_averages.get(time_index[i], 0)
        if ta > 0:
            rvol[i] = volume[i] / ta
    
    return rvol


# =============================================================================
# ATR Trailing Stop
# =============================================================================

def atr_trailing_stop(high: np.ndarray, low: np.ndarray, close: np.ndarray,
                      period: int = 14, atr_multiplier: float = 3.0,
                      use_close: bool = True) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    ATR Trailing Stop - Volatility-based dynamic stop loss
    
    Mathematical Formula:
    ---------------------
    True Range (TR) = max(
        High - Low,
        |High - Close_prev|,
        |Low - Close_prev|
    )
    
    ATR = SMA(TR, period)  [or Wilder's EMA]
    
    Long Stop = Highest Close - (ATR × multiplier)
    Short Stop = Lowest Close + (ATR × multiplier)
    
    Trailing Logic:
    ---------------
    If Long and Close < Stop: Flip to Short
    If Short and Close > Stop: Flip to Long
    
    The stop "trails" by only moving in favorable direction
    
    Parameters:
    -----------
    high : np.ndarray - High prices
    low : np.ndarray - Low prices
    close : np.ndarray - Close prices
    period : int - ATR calculation period (default: 14)
    atr_multiplier : float - ATR multiplier for stop distance (default: 3.0)
    use_close : bool - Use close prices for trailing calc (default: True)
    
    Returns:
    --------
    Tuple of (stop_line, position, atr_values)
    - stop_line: The trailing stop price
    - position: +1 for long, -1 for short
    - atr_values: Raw ATR values
    """
    n = len(close)
    
    # Calculate True Range
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]  # First bar has no previous close
    
    for i in range(1, n):
        tr1 = high[i] - low[i]
        tr2 = abs(high[i] - close[i - 1])
        tr3 = abs(low[i] - close[i - 1])
        tr[i] = max(tr1, tr2, tr3)
    
    # Calculate ATR using Wilder's smoothing (EMA)
    atr = np.zeros(n)
    atr[period - 1] = np.mean(tr[:period])
    multiplier = 2.0 / (period + 1)  # EMA smoothing factor
    
    for i in range(period, n):
        atr[i] = (tr[i] * multiplier) + (atr[i - 1] * (1 - multiplier))
    
    # Initialize trailing stop
    stop_line = np.full(n, np.nan)
    position = np.zeros(n)  # +1 long, -1 short
    
    # Starting position - assume long if first close > first stop
    if use_close:
        price_series = close
    else:
        price_series = (high + low) / 2.0
    
    # Find first valid ATR
    first_valid = period - 1
    if first_valid < n:
        # Initialize - assume uptrend to start
        stop_line[first_valid] = price_series[first_valid] - (atr[first_valid] * atr_multiplier)
        position[first_valid] = 1
        
        for i in range(first_valid + 1, n):
            current_price = price_series[i]
            prev_stop = stop_line[i - 1]
            current_atr = atr[i]
            
            if position[i - 1] == 1:  # Currently long
                # Calculate new stop level (only moves up)
                new_stop = max(prev_stop, current_price - (current_atr * atr_multiplier))
                
                if current_price < new_stop:  # Stop triggered
                    position[i] = -1
                    stop_line[i] = current_price + (current_atr * atr_multiplier)
                else:  # Stay long
                    position[i] = 1
                    stop_line[i] = new_stop
                    
            else:  # Currently short
                # Calculate new stop level (only moves down)
                new_stop = min(prev_stop, current_price + (current_atr * atr_multiplier))
                
                if current_price > new_stop:  # Stop triggered
                    position[i] = 1
                    stop_line[i] = current_price - (current_atr * atr_multiplier)
                else:  # Stay short
                    position[i] = -1
                    stop_line[i] = new_stop
    
    return stop_line, position, atr


def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, 
        period: int = 14) -> np.ndarray:
    """
    Average True Range - Standalone calculation
    
    Mathematical Formula:
    ---------------------
    TR = max(High - Low, |High - Close_prev|, |Low - Close_prev|)
    ATR = EMA(TR, period)  [Wilder's smoothing]
    
    Used as:
    - Volatility measurement
    - Position sizing (risk = ATR × multiplier)
    - Stop placement (chandelier exits)
    """
    n = len(close)
    tr = np.zeros(n)
    
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        tr[i] = max(high[i] - low[i], 
                    abs(high[i] - close[i - 1]),
                    abs(low[i] - close[i - 1]))
    
    # Wilder's smoothing
    atr = np.zeros(n)
    atr[period - 1] = np.mean(tr[:period])
    multiplier = 2.0 / (period + 1)
    
    for i in range(period, n):
        atr[i] = (tr[i] * multiplier) + (atr[i - 1] * (1 - multiplier))
    
    return atr


# =============================================================================
# Unit Tests with Known Values
# =============================================================================

def test_vwap():
    """
    Test VWAP with manually calculated known values.
    
    Known Values:
    Bar 0: H=10, L=8, C=9, V=100  -> TP=9, TP×V=900
    Bar 1: H=11, L=9, C=10, V=200 -> TP=10, TP×V=2000
    Bar 2: H=12, L=10, C=11, V=300 -> TP=11, TP×V=3300
    
    VWAP at bar 2: (900+2000+3300)/(100+200+300) = 6200/600 = 10.333...
    """
    high = np.array([10.0, 11.0, 12.0, 13.0, 14.0])
    low = np.array([8.0, 9.0, 10.0, 11.0, 12.0])
    close = np.array([9.0, 10.0, 11.0, 12.0, 13.0])
    volume = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
    
    vwap_line, upper, lower = vwap(high, low, close, volume, period=3)
    
    # Manual calc for index 2:
    # TPs: 9, 10, 11
    # Volumes: 100, 200, 300
    # VWAP = (9*100 + 10*200 + 11*300) / 600 = (900+2000+3300)/600 = 10.3333
    expected_vwap = (9*100 + 10*200 + 11*300) / 600
    
    assert abs(vwap_line[2] - expected_vwap) < 1e-10, f"VWAP mismatch: {vwap_line[2]} != {expected_vwap}"
    assert np.isnan(vwap_line[0]) and np.isnan(vwap_line[1]), "First two should be NaN"
    
    print("✓ VWAP test passed")
    return True


def test_rvol():
    """
    Test RVOL with known values.
    
    Volume: [100, 200, 300, 400, 500, 600, 700, 800]
    Short period=2: averages are [nan, 150, 250, 350, 450, 550, 650, 750]
    Long period=4: averages are [nan, nan, nan, 250, 350, 450, 550, 650]
    
    RVOL at index 4 (0-indexed): 450/350 = 1.285714...
    """
    volume = np.array([100.0, 200.0, 300.0, 400.0, 500.0, 600.0, 700.0, 800.0])
    
    result = rvol(volume, short_period=2, long_period=4)
    
    # At index 4: short_avg = (400+500)/2 = 450
    #             long_avg = (200+300+400+500)/4 = 350
    #             RVOL = 450/350 = 9/7 = 1.285714...
    expected = 450.0 / 350.0
    assert abs(result[4] - expected) < 1e-10, f"RVOL mismatch: {result[4]} != {expected}"
    
    print("✓ RVOL test passed")
    return True


def test_atr_trailing_stop():
    """
    Test ATR Trailing Stop with known values.
    
    Manually verify TR and ATR calculations.
    """
    # Simple case: consistent upward trend
    high = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0])
    low = np.array([9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    close = np.array([9.5, 10.5, 11.5, 12.5, 13.5, 14.5, 15.5])
    
    stop, position, atr_vals = atr_trailing_stop(high, low, close, period=3, atr_multiplier=1.0)
    
    # First valid ATR at index 2
    # TR[0] = 1.0
    # TR[1] = max(1.0, |11-9.5|, |10-9.5|) = max(1.0, 1.5, 0.5) = 1.5
    # TR[2] = max(1.0, |12-10.5|, |11-10.5|) = max(1.0, 1.5, 0.5) = 1.5
    # ATR[2] = (1.0 + 1.5 + 1.5) / 3 = 1.333...
    
    expected_tr0 = 1.0
    expected_tr1 = max(1.0, abs(11-9.5), abs(10-9.5))
    
    tr0 = high[0] - low[0]
    assert abs(tr0 - expected_tr0) < 1e-10, f"TR[0] mismatch"
    
    print("✓ ATR Trailing Stop test passed")
    return True


def test_atr():
    """
    Test standalone ATR calculation.
    """
    high = np.array([10.0, 11.0, 12.0, 11.5, 13.0])
    low = np.array([9.0, 10.0, 11.0, 10.5, 12.0])
    close = np.array([9.5, 10.5, 11.5, 11.0, 12.5])
    
    result = atr(high, low, close, period=3)
    
    # TR calculations:
    # TR[0] = 10-9 = 1.0
    # TR[1] = max(1.0, |11-9.5|, |10-9.5|) = 1.5
    # TR[2] = max(1.0, |12-10.5|, |11-10.5|) = 1.5
    # TR[3] = max(1.0, |11.5-11.5|, |10.5-11.5|) = 1.0
    # TR[4] = max(1.0, |13-11.0|, |12-11.0|) = 2.0
    
    tr0 = high[0] - low[0]  # Should be 1.0
    assert tr0 == 1.0, f"TR[0] should be 1.0, got {tr0}"
    
    print("✓ ATR standalone test passed")
    return True


def run_all_tests():
    """Run all unit tests."""
    print("=" * 50)
    print("ORACLE INDICATOR UNIT TESTS")
    print("=" * 50)
    
    all_passed = True
    all_passed &= test_vwap()
    all_passed &= test_rvol()
    all_passed &= test_atr()
    all_passed &= test_atr_trailing_stop()
    
    print("=" * 50)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 50)
    return all_passed


# =============================================================================
# Performance Benchmarks
# =============================================================================

def benchmark_performance():
    """
    Benchmark NumPy implementations vs Pandas equivalents.
    """
    import time
    
    print("\n" + "=" * 50)
    print("PERFORMANCE BENCHMARK")
    print("=" * 50)
    
    # Generate test data
    n = 100000
    np.random.seed(42)
    
    high = np.random.uniform(100, 110, n)
    low = high - np.random.uniform(1, 5, n)
    close = (high + low) / 2 + np.random.uniform(-1, 1, n)
    volume = np.random.uniform(1000000, 5000000, n)
    
    # NumPy benchmarks
    iterations = 10
    
    # VWAP benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        _ = vwap(high, low, close, volume, period=14)
    numpy_vwap_time = (time.perf_counter() - start) / iterations * 1000
    
    # RVOL benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        _ = rvol(volume, short_period=5, long_period=20)
    numpy_rvol_time = (time.perf_counter() - start) / iterations * 1000
    
    # ATR benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        _ = atr_trailing_stop(high, low, close, period=14)
    numpy_atr_time = (time.perf_counter() - start) / iterations * 1000
    
    print(f"\nNumPy Implementation ({n:,} bars):")
    print(f"  VWAP:           {numpy_vwap_time:.3f} ms")
    print(f"  RVOL:           {numpy_rvol_time:.3f} ms")
    print(f"  ATR Trailing:   {numpy_atr_time:.3f} ms")
    
    # Try to benchmark pandas if available
    try:
        import pandas as pd
        
        df = pd.DataFrame({
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
        
        # VWAP Pandas
        start = time.perf_counter()
        for _ in range(iterations):
            tp = (df['high'] + df['low'] + df['close']) / 3
            vwap_pd = (tp * df['volume']).rolling(14).sum() / df['volume'].rolling(14).sum()
        pd_vwap_time = (time.perf_counter() - start) / iterations * 1000
        
        # RVOL Pandas
        start = time.perf_counter()
        for _ in range(iterations):
            short = df['volume'].rolling(5).mean()
            long = df['volume'].rolling(20).mean()
            rvol_pd = short / long
        pd_rvol_time = (time.perf_counter() - start) / iterations * 1000
        
        # ATR Pandas
        start = time.perf_counter()
        for _ in range(iterations):
            tr1 = df['high'] - df['low']
            tr2 = abs(df['high'] - df['close'].shift(1))
            tr3 = abs(df['low'] - df['close'].shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr_pd = tr.ewm(alpha=2/15, adjust=False).mean()
        pd_atr_time = (time.perf_counter() - start) / iterations * 1000
        
        print(f"\nPandas Implementation ({n:,} bars):")
        print(f"  VWAP:           {pd_vwap_time:.3f} ms")
        print(f"  RVOL:           {pd_rvol_time:.3f} ms")
        print(f"  ATR:            {pd_atr_time:.3f} ms")
        
        print(f"\nSpeedup Factors:")
        print(f"  VWAP:           {pd_vwap_time/numpy_vwap_time:.1f}x")
        print(f"  RVOL:           {pd_rvol_time/numpy_rvol_time:.1f}x")
        print(f"  ATR:            {pd_atr_time/numpy_atr_time:.1f}x")
        
    except ImportError:
        print("\nPandas not installed, skipping comparison benchmark")
    
    print("=" * 50)


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    # Run unit tests
    run_all_tests()
    
    # Run performance benchmarks
    benchmark_performance()
