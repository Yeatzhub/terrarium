# Market Regimes Detection & Strategy Adaptation

**Oracle Trading Strategist Knowledge Base**  
*Document Version: 1.0*  
*Last Updated: 2026-02-18*

---

## 1. Trending vs Ranging Market Detection

### 1.1 ADX-Based Regime Classification

The Average Directional Index (ADX) is the standard tool for trend strength measurement.

**Mathematical Foundation:**

```
True Range (TR) = max(|High - Low|, |High - Close_prev|, |Low - Close_prev|)
+DM = High - High_prev (if positive and > -DM, else 0)
-DM = Low_prev - Low (if positive and > +DM, else 0)

Smoothed +DI = 100 × EMA(+DM, n) / EMA(TR, n)
Smoothed -DI = 100 × EMA(-DM, n) / EMA(TR, n)

DX = 100 × |+DI - -DI| / (+DI + -DI)
ADX = EMA(DX, n)  [typically n=14 periods]
```

**Regime Classification Thresholds:**

| ADX Value | Regime | Trading Strategy |
|-----------|--------|------------------|
| ADX < 20 | Weak/No Trend | Range-bound strategies preferred |
| ADX 20-25 | Trend Emerging | Monitor for breakout confirmation |
| ADX 25-40 | Strong Trend | Trend-following strategies |
| ADX 40-60 | Very Strong Trend | Aggressive trend continuation |
| ADX > 60 | Exhaustion Zone | Prepare for reversal |

**Implementation Notes:**
- ADX is directionless (measures trend strength, not direction)
- Combine with +DI/-DI crossover for directional bias
- Use ADX slope: rising ADX = trend strengthening, falling ADX = trend weakening

### 1.2 Bollinger Band Squeeze Detection

Detects low volatility periods that often precede major moves.

```
BB_Width = (Upper_Band - Lower_Band) / Middle_Band
BB_Squeeze = BB_Width < Percentile(BB_Width, 20, lookback=120)

Where:
  Upper_Band = SMA(Close, 20) + 2 × StdDev(Close, 20)
  Lower_Band = SMA(Close, 20) - 2 × StdDev(Close, 20)
  Middle_Band = SMA(Close, 20)
```

**Thresholds:**
- Squeeze Active: BB Width < 10th percentile of 6-month history
- Squeeze Release: BB Width expands > 40th percentile

### 1.3 Keltner Channel Trend Detection

More robust than Bollinger Bands for trend identification.

```
KC_Middle = EMA(Close, 20)
KC_Upper = KC_Middle + 2 × ATR(10)
KC_Lower = KC_Middle - 2 × ATR(10)

Trend Signal:
  Strong Uptrend = Close > KC_Upper AND Close > KC_Middle
  Strong Downtrend = Close < KC_Lower AND Close < KC_Middle
  Ranging = Close within [KC_Lower + ATR, KC_Upper - ATR]
```

### 1.4 Choppiness Index

Values ranging 0-100 indicating trendiness vs choppiness.

```
LogSum = Σ log10(ATR(i)) for i=1 to n
LogMaxMin = log10(Max(High, n) - Min(Low, n))

Choppiness_Index = 100 × LogSum / (LogMaxMin + LogSum)

Where n = typically 14 periods
```

**Interpretation:**
- CI > 61.8: Ranging/choppy market
- CI < 38.2: Trending market
- CI 38.2-61.8: Neutral/transitional

---

## 2. Volatility Regime Indicators

### 2.1 VIX-Based Volatility Regimes

**VIX Regime Classification:**

| VIX Level | Regime | Implied Annualized Volatility |
|-----------|--------|------------------------------|
| < 12 | Extreme Low Vol | < 12% |
| 12-16 | Low Vol | 12-16% |
| 16-20 | Normal Vol | 16-20% |
| 20-25 | Elevated Vol | 20-25% |
| 25-30 | High Vol | 25-30% |
| > 30 | Extreme Vol/Crisis | > 30% |

**VIX Percentile Approach:**

```
VIX_Percentile = percentile_rank(VIX_current, VIX_history_252d)

Vol_Regime = 
  "Low"    if VIX_Percentile < 20
  "Normal" if 20 <= VIX_Percentile < 80
  "High"   if VIX_Percentile >= 80

VIX_Term_Structure = VIX_3mo / VIX_1mo
  > 1.15 = Backwardation (fear/contagion)
  < 0.95 = Strong contango (complacency)
```

**Action Matrix:**

| VIX Regime | Strategy Adjustment |
|------------|---------------------|
| Low Vol (P<20) | Increase position size, tighter stops, favor momentum |
| Normal Vol | Standard position sizing |
| High Vol (P>80) | Reduce size, widen stops, favor mean reversion, increase cash |

### 2.2 ATR Percentile Volatility

More responsive and asset-specific than VIX.

```
ATR_Percentile = percentile_rank(ATR(14), ATR_history_60)

Normalized_ATR = ATR(14) / Close × 100  [ATR as % of price]

Volatility_Regime = 
  "Low"    if ATR_Percentile < 25 AND Normalized_ATR < atr_threshold_low
  "Medium" if 25 <= ATR_Percentile < 75
  "High"   if ATR_Percentile >= 75

Where atr_threshold depends on asset class:
  - Equities: 1.5%
  - Crypto: 5%
  - Forex: 0.5%
  - Commodities: 2%
```

**Position Sizing Formula:**

```
Vol_Adjusted_Size = Base_Size × (Target_ATR / Current_ATR)^vol_scalar

Where:
  Target_ATR = 60th percentile ATR
  vol_scalar = 0.5 to 1.0 (adjusts sensitivity)
```

### 2.3 GARCH Volatility Forecasting

```
σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}

Where:
  σ² = conditional variance
  ω = long-run variance component
  α = weight of recent shocks (typically 0.05-0.15)
  β = persistence (typically 0.80-0.95)
  α + β < 1 for stationarity

Volatility Regime Switch:
  Regime_High = σ_t > 1.5 × σ_long_run
  Regime_Low = σ_t < 0.7 × σ_long_run
```

### 2.4 Relative Volatility Index (RVI)

Similar to RSI but uses standard deviation instead of price.

```
Up_Vol = StdDev(Close, 10) if Close > Close_prev else 0
Down_Vol = StdDev(Close, 10) if Close < Close_prev else 0

RVI = 100 × SMMA(Up_Vol, n) / (SMMA(Up_Vol, n) + SMMA(Down_Vol, n))

Interpretation:
  RVI > 50: Volatility increasing (expansion)
  RVI < 50: Volatility decreasing (contraction)
  RVI > 80: Volatility spike - mean reversion likely
  RVI < 20: Volatility compression - breakout likely
```

---

## 3. Mean Reversion vs Momentum Filtering

### 3.1 Statistical Mean Reversion Tests

**Augmented Dickey-Fuller Test Concept:**

```
Δy_t = α + β·t + γ·y_{t-1} + Σ(δ_i·Δy_{t-i}) + ε_t

Test statistic check:
  - Significant negative γ → Mean reverting
  - γ ≈ 0 → Random walk (momentum)

Half-life = -ln(2) / ln(1 + γ)  [in periods]
  - Half-life < 20: Tradable mean reversion
  - Half-life > 60: Trend following preferred
```

**Hurst Exponent:**

```
E[R(t)/S(t)] = C × t^H as t → ∞

H < 0.5: Mean reverting process
H = 0.5: Random walk
H > 0.5: Trending/persistent process

Practical thresholds:
  H < 0.4: Strong mean reversion
  0.4 < H < 0.6: Neutral/mixed
  H > 0.6: Strong momentum
```

**Variance Ratio Test:**

```
VR(k) = Var(r_t + r_{t-1} + ... + r_{t-k+1}) / (k × Var(r_t))

VR < 1: Negative autocorrelation (mean reversion)
VR = 1: Random walk
VR > 1: Positive autocorrelation (momentum)
```

### 3.2 Lagged Correlation Filter

```
autocorr_1 = correlation(returns[1:], returns[:-1])
autocorr_5 = correlation(returns[5:], returns[:-5])

Regime_Signal = 
  "Momentum"     if autocorr_1 > 0.1 AND autocorr_5 > 0
  "Mean_Revert"  if autocorr_1 < -0.05
  "Neutral"      otherwise
```

### 3.3 Moving Average Convergence Filter

```
Price_vs_SMA10 = (Close - SMA(10)) / SMA(10) × 100
Price_vs_SMA30 = (Close - SMA(30)) / SMA(30) × 100

Momentum_Score = Price_vs_SMA10 - Price_vs_SMA30

If Momentum_Score > 2 AND ADX > 25 → Momentum regime
If Momentum_Score < -2 AND ADX < 20 → Mean reversion candidate
```

### 3.4 Stochastic Momentum Index

```
%K = 100 × (Close - Lowest_Low(n)) / (Highest_High(n) - Lowest_Low(n))
%D = SMA(%K, m)

Stochastic_Momentum = %K - %D

Combined with ADX:
  Stochastic_Momentum > 0 AND ADX > 25 → Momentum long
  Stochastic_Momentum < 0 AND ADX > 25 → Momentum short
  Stochastic_Momentum extreme (>80 or <20) AND ADX < 20 → Mean reversion
```

---

## 4. Market Regime-Based Strategy Selection

### 4.1 Comprehensive Regime Matrix

| Trend | Volatility | Autocorr | Regime | Primary Strategy | Secondary |
|-------|-----------|----------|--------|-----------------|-----------|
| Strong Up | Low | Positive | Trend+QO | Momentum | Carry |
| Strong Up | High | Positive | Trend+VO | Vol-Adj Momentum | Options |
| Weak Up | Low | Neutral | Range Low | Mean Reversion | Calendar spreads |
| Weak Up | High | Neutral | Uncertain | Reduce size | Wait |
| Range | Low | Negative | Mean Rev Low | Range trading | Scalping |
| Range | High | Negative | Mean Rev High | Wide range trading | Straddles |
| Strong Down | Low | Positive | Downtrend | Short momentum | Defensive |
| Strong Down | High | Positive | Crash | Cash/Vol | Hedges |

**QO = Quiet, VO = Volatile**

### 4.2 Dynamic Strategy Allocation

```python
def allocate_strategy(regime_scores):
    """
    regime_scores: dict with weights for each regime
    Returns portfolio allocation across strategies
    """
    
    strategies = {
        'trend_following': 0,
        'mean_reversion': 0,
        'breakout': 0,
        'carry': 0,
        'cash': 0
    }
    
    # Trend strength component (0-1)
    trend_weight = regime_scores['adx_normalized']
    
    # Volatility component (inverse for sizing)
    vol_factor = 1 - regime_scores['vol_percentile'] / 100
    
    # Mean reversion probability
    mr_prob = regime_scores['hurst'] < 0.5
    
    if trend_weight > 0.6 and not mr_prob:
        # Strong trend regime
        strategies['trend_following'] = 0.7 * vol_factor
        strategies['breakout'] = 0.2 * vol_factor
        strategies['cash'] = 1 - sum(strategies.values())
        
    elif trend_weight < 0.3 and mr_prob > 0.6:
        # Mean reversion regime
        strategies['mean_reversion'] = 0.6 * vol_factor
        strategies['carry'] = 0.2
        strategies['cash'] = 0.2
        
    elif regime_scores['vix_percentile'] > 80:
        # High stress - defensive
        strategies['cash'] = 0.5
        strategies['mean_reversion'] = 0.3  # Vol expansion mean reversion
        strategies['trend_following'] = 0.2
        
    else:
        # Balanced/mixed regime
        strategies['trend_following'] = 0.3 * vol_factor
        strategies['mean_reversion'] = 0.3 * vol_factor
        strategies['breakout'] = 0.2
        strategies['carry'] = 0.2
    
    return normalize(strategies)
```

### 4.3 Position Sizing by Regime

```
Base_Risk_Per_Trade = 1.0%  # of portfolio

Regime_Multipliers:
  Low_Vol_Trend:     1.5×  # Favorable conditions
  Normal:            1.0×  # Base case
  High_Vol:          0.5×  # Reduce exposure
  Transition:        0.3×  # Uncertainty
  Crisis:            0.1×  # Or 0 (all cash)

Final_Position_Size = Signal_Strength × Base_Risk × Regime_Multiplier × Vol_Adjustment

Where:
  Vol_Adjustment = Target_Vol / Current_Vol
  Target_Vol = 10% annualized (or user preference)
```

### 4.4 Entry/Exit Timing by Regime

| Regime | Entry Criteria | Exit Criteria |
|--------|---------------|---------------|
| Trend Up | ADX > 25, +DI > -DI, price > SMA(20) | ADX < 20, -DI cross above +DI |
| Trend Down | ADX > 25, -DI > +DI, price < SMA(20) | ADX < 20, +DI cross above -DI |
| Range | Price touches Bollinger Band, RSI divergent | Price reaches opposite band, RSI mean reverts |
| Breakout | Volume > 2× avg, price outside 20-day range | ATR trailing stop, time stop |
| Mean Rev | RSI < 20 or > 80, Bollinger Band touch | RSI returns to 50, price near SMA |

---

## 5. Correlation Breakdown During Stress Periods

### 5.1 Dynamic Correlation Modeling

**Rolling Correlation with Decay:**

```
ρ_ij(t) = covariance_ij(t) / √(σ²_i(t) × σ²_j(t))

Where:
  covariance_ij uses EWMA with λ = 0.94 (RiskMetrics)
  Lookback window adjusts based on volatility regime:
    - Low vol: 60 days
    - Normal: 30 days
    - High vol: 10 days
```

**Correlation Regime Detection:**

```
Avg_Correlation = mean(ρ_ij for all i,j pairs in universe)
Correlation_Dispersion = std(ρ_ij)

Stress_Signal = 
  "Normal" if Avg_Correlation < 0.3 AND Correlation_Dispersion > 0.2
  "Elevated" if 0.3 <= Avg_Correlation < 0.6
  "High" if Avg_Correlation >= 0.6 AND Correlation_Dispersion < 0.15
  "Breakdown" if Correlation_Spike_3SD_in_5_days
```

### 5.2 Correlation Surprise Metric

```
Z_Score_Correlation = (ρ_current - ρ_rolling_mean) / ρ_rolling_std

Correlation_Surprise = |Z_Score_Correlation|

Alert Levels:
  Yellow: Surprise > 2
  Orange: Surprise > 3
  Red: Surprise > 4 (breakdown imminent or active)
```

### 5.3 Cross-Asset Contagion Detection

```
# Build correlation matrix of asset returns
C_t = correlation_matrix(returns, window=20)

# Eigenvalue analysis for systemic risk
eigenvalues = eigen(C_t)
λ_max = max(eigenvalues)

# Market mode participation
Market_Mode_Strength = λ_max / sum(eigenvalues)

Interpretation:
  < 0.20: Diversification works well
  0.20-0.40: Moderate coupling
  > 0.40: High systemic risk, correlations unstable
  > 0.60: Crisis mode - everything moves together
```

### 5.4 Volatility-Adjusted Correlation

```
# More accurate during high vol periods
ρ_vix_adjusted = ρ_raw × √(VIX_current / VIX_long_term_average)

# Or using realized volatility
ρ_realized = ρ_raw × min(σ_realized_current / σ_realized_long, 2.0)
```

### 5.5 Trading Implications of Correlation Breakdown

| Correlation State | Strategy Adjustment |
|-------------------|---------------------|
| **Pre-Stress** (correlations low, normal dispersion) | Full diversification benefits, pair trading active |
| **Stress Building** (avg correlation rising) | Reduce position sizes, cut carry trades |
| **Stress Peak** (correlations spike to 1.0) | All positions correlate, hedges fail, go to cash |
| **Post-Stress** (correlations remain elevated) | Wait for normalization, avoid false breakouts |
| **Normalization** (correlations declining) | Gradually re-engage, favor quality |

**Practical Rules:**

```
IF Average_3M_Correlation > 0.7:
    Diversification_Benefit = FALSE
    Reduce_Position_Size(by=50%)
    Prefer_Single_Name_over_ETFs()
    
IF Correlation_Change_1W > +0.3:
    Contagion_Risk = HIGH
    Cut_Cross_Asset_Trades()
    Increase_Cash(by=25%)
    
IF Bond_Equity_Correlation > 0.5:
    60_40_Portfolio_Hedges = INEFFECTIVE
    Add_Alternative_Hedges(long_vol, commodities, cash)
```

---

## 6. Integrated Regime Detection System

### 6.1 Composite Regime Score

```
def calculate_regime_score(market_data):
    scores = {}
    
    # Trend component (0-100)
    scores['trend'] = ADX(14)  # Directional movement
    scores['trend_direction'] = sign(+DI - -DI)
    
    # Volatility component (0-100, low=good for trend)
    scores['volatility'] = VIX_Percentile(252)
    
    # Mean reversion probability (0-100)
    scores['mean_reversion'] = (1 - Hurst(lookback=100)) * 100
    
    # Correlation risk (0-100, high=dangerous)
    scores['correlation_risk'] = eigenvalue_concentration * 100
    
    # Composite regime
    if scores['trend'] > 30 and scores['mean_reversion'] < 40:
        regime = 'TRENDING'
        confidence = (scores['trend'] + (100 - scores['mean_reversion'])) / 2
    elif scores['mean_reversion'] > 60 and scores['trend'] < 25:
        regime = 'MEAN_REVERTING'
        confidence = (scores['mean_reversion'] + (100 - scores['trend'])) / 2
    elif scores['volatility'] > 80:
        regime = 'HIGH_VOLATILITY'
        confidence = scores['volatility']
    elif scores['correlation_risk'] > 60:
        regime = 'CORRELATION_BREAKDOWN'
        confidence = scores['correlation_risk']
    else:
        regime = 'TRANSITIONAL'
        confidence = 50
    
    return {
        'regime': regime,
        'confidence': confidence,
        'scores': scores
    }
```

### 6.2 Regime Transition Detection

```
Regime_Change_Probability = 1 - stability_index

Where:
  stability_index = correlation(
    regime_scores[t-5:t], 
    regime_scores[t-10:t-5]
  )

IF stability_index < 0.5 AND regime != previous_regime:
    TRIGGER: Reduced exposure until new regime stabilizes
    Duration: Min 5 days, max 20 days
```

### 6.3 Implementation Checklist

**Daily Regime Assessment:**
- [ ] Calculate ADX and directional indicators
- [ ] Update VIX percentile and term structure
- [ ] Compute ATR percentile for asset-specific vol
- [ ] Check Hurst exponent on major assets
- [ ] Update correlation matrix and eigenvalues
- [ ] Calculate composite regime score
- [ ] Check for regime transition signals
- [ ] Adjust position sizes based on new regime
- [ ] Review strategy allocation weights
- [ ] Log regime change and rationale

---

## 7. Summary Tables

### 7.1 Quick Reference: Regime Detection

| Indicator | Formula Key | Thresholds | Update Freq |
|-----------|-------------|------------|-------------|
| ADX | Directional Movement | <20=range, >25=trend | Daily |
| VIX %ile | Rank over 252d | <20=low, >80=high | Daily |
| ATR %ile | Rank over 60d | <25=low, >75=high | Daily |
| Hurst | RS analysis | <0.4=MR, >0.6=mom | Weekly |
| RVI | Volatility RSI | >80=spike, <20=crush | Daily |
| Eigenvalue | PC1/variance | >40%=systemic risk | Daily |
| BB Squeeze | Width %ile | <10th=squeeze | Daily |

### 7.2 Strategy Allocation by Regime

```
┌─────────────────┬──────────┬──────────┬─────────┬───────┐
│ Regime          │ Trend %  │ MR %     │ Cash %  │ Hedges│
├─────────────────┼──────────┼──────────┼─────────┼───────┤
│ Strong Trend    │ 70       │ 10       │ 10      │ 10    │
│ Weak Trend      │ 40       │ 30       │ 20      │ 10    │
│ Range Bound     │ 20       │ 50       │ 20      │ 10    │
│ High Vol        │ 10       │ 20       │ 50      │ 20    │
│ Corr Breakdown  │ 0        │ 10       │ 70      │ 20    │
│ Transition      │ 20       │ 20       │ 50      │ 10    │
└─────────────────┴──────────┴──────────┴─────────┴───────┘
```

---

## 8. References & Further Reading

1. **Wilde, Welles** - "New Concepts in Technical Trading Systems" (ADX)
2. **Hurst, Harold** - "Long-Term Storage Capacity of Reservoirs" (Hurst Exponent)
3. **Engle, Robert** - "GARCH Models" (Volatility clustering)
4. **Markowitz, Harry** - "Portfolio Selection" (Correlation importance)
5. **Chan, Ernest** - "Algorithmic Trading: Winning Strategies and Their Rationale"
6. **Marcos Lopez de Prado** - "Advances in Financial Machine Learning"
7. **Meucci, Attilio** - "Risk and Asset Allocation"

---

*Document generated by Oracle (🔮) - Trading Strategist*  
*For use in quantitative trading system development*
