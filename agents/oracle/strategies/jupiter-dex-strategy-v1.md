# Jupiter DEX Trading Strategy v1.0

**Oracle (🔮) Trading Strategist**  
**Network**: Solana (mainnet)  
**DEX**: Jupiter Aggregator  
**Last Updated**: 2026-02-18  
**Version**: 1.0-alpha

---

## Executive Summary

This strategy is specifically designed for **decentralized exchange trading on Jupiter**, accounting for the unique constraints and opportunities of the Solana ecosystem:

| Constraint | DEX Impact | Strategy Adaptation |
|------------|-----------|---------------------|
| **Higher Gas Fees** | ~0.00025-0.001 SOL per swap | Fewer trades, larger moves needed |
| **Slippage Risk** | 0.5-3% on low liquidity | Wider profit targets (3-5% minimum) |
| **MEV Bots** | Front/back-running trades | Randomized delays, stealth orders |
| **Liquidity Fragmentation** | Varies across pools | Minimum $1M TVL requirement |
| **Wallet Safety** | Smart contract risk | Multi-sig + hot wallet rotation |

---

## 1. Market Regime Detection

### 1.1 DEX-Specific Regime Classification

Unlike centralized exchanges, DEX volume patterns differ. On-chain data requires special handling:

```python
class JupiterRegimeDetector:
    """
    Solana-specific regime detection using on-chain metrics
    """
    
    def detect_regime(self, token_pair: str, timeframe: str = '5m') -> dict:
        params = {
            # Solana-specific thresholds (crypto adjusted)
            'adx_threshold': {
                'trending': 30,      # Higher threshold for crypto volatility
                'ranging': 20
            },
            'atr_percentile': {
                'low': 30,           # Crypto has naturally higher volatility
                'high': 70
            },
            'volume_confirmation': {
                'min_rvol': 1.5,     # Higher volume spike requirement
                'min_sol_value': 500_000  # Minimum SOL volume in 24h
            }
        }
        
        # Fetch on-chain data
        ohlcv = self.fetch_jupiter_ohlcv(token_pair, timeframe)
        onchain = self.fetch_onchain_metrics(token_pair)
        
        # Calculate regime score
        regime = self.calculate_regime(ohlcv, onchain, params)
        
        return regime
```

### 1.2 Regime Definitions for Jupiter

| Regime | Conditions | Trade Frequency | Min Profit Target |
|--------|-----------|-----------------|-------------------|
| **Strong Uptrend** | ADX > 30, +DI > -DI, Close > VWAP(24h), Volume > 1.5x avg | Every setup | 5% |
| **Weak Uptrend** | ADX 20-30, +DI > -DI, Close near VWAP | Selective | 7% |
| **Range Bound** | ADX < 20, BB width < 40th percentile | Rare | 10% |
| **High Volatility** | ATR percentile > 80, Gap > 3σ | Avoid (slippage risk) | N/A |
| **Low Liquidity** | Jupiter quote slippage > 1% | Avoid | N/A |

### 1.3 Solana Network Health Check

Before any trade, verify network conditions:

```python
def check_network_health():
    """
    Verify Solana network is healthy for trading
    """
    metrics = {
        'tps': fetch_current_tps(),
        'slot_time': fetch_slot_time(),
        'block_production': fetch_block_production_rate()
    }
    
    # Avoid trading during network congestion
    if metrics['tps'] < 1500 or metrics['slot_time'] > 500:
        return {
            'trade_allowed': False,
            'reason': 'Network congestion detected - high gas/risk'
        }
    
    # Priority fee multiplier during congestion
    if metrics['tps'] < 2500:
        return {
            'trade_allowed': True,
            'priority_fee_multiplier': 1.5,
            'compute_unit_budget': 300_000
        }
    
    return {
        'trade_allowed': True,
        'priority_fee_multiplier': 1.0,
        'compute_unit_budget': 200_000
    }
```

### 1.4 Jupiter-Specific Liquidity Regime

Monitor Jupiter pool depth for each token:

```python
def analyze_liquidity_regime(token: str) -> dict:
    """
    Analyze Jupiter liquidity conditions
    """
    # Get Jupiter quote for $10k swap
    quote_10k = jupiter_quote(token, 'USDC', 10_000)
    quote_50k = jupiter_quote(token, 'USDC', 50_000)
    quote_100k = jupiter_quote(token, 'USDC', 100_000)
    
    slippage_10k = (quote_10k['expected_output'] - quote_10k['minimum_output']) / quote_10k['expected_output']
    slippage_50k = (quote_50k['expected_output'] - quote_50k['minimum_output']) / quote_50k['expected_output']
    slippage_100k = (quote_100k['expected_output'] - quote_100k['minimum_output']) / quote_100k['expected_output']
    
    regime = {
        'deep_liquidity': slippage_100k < 0.01,      # <1% on $100k
        'medium_liquidity': slippage_50k < 0.01,      # <1% on $50k
        'low_liquidity': slippage_10k > 0.005,        # >0.5% on $10k
        'avoid': slippage_10k > 0.02                  # >2% on $10k
    }
    
    return {
        'regime': regime,
        'max_position_size': calculate_max_size(slippage_10k),
        'recommended_slippage_bps': int(slippage_10k * 10000 * 1.5)  # 50% buffer
    }
```

---

## 2. Entry Conditions

### 2.1 Long Entry Criteria

**Primary Setup - Trend Continuation:**

```python
class JupiterLongStrategy:
    
    def check_long_entry(self, data: dict) -> dict:
        # Technical Conditions
        price_above_vwap = close > vwap_24h * 1.01  # 1% above VWAP
        adx_confirmed = adx_14 > 30
        trend_aligned = plus_di > minus_di
        volume_spike = rvol_5 > 1.5
        
        # Momentum Confirmation
        price_above_sma = close > sma_20
        rsi_not_overbought = rsi_14 < 70
        bb_position = (close - bb_lower) / (bb_upper - bb_lower)
        momentum_healthy = 0.3 < bb_position < 0.8
        
        # On-chain Confirmation
        whale_inflow = onchain_metrics['large_buy_volume_1h'] > \
                      onchain_metrics['large_sell_volume_1h'] * 1.3
        
        # Scoring System (0-100)
        score = 0
        if price_above_vwap: score += 25
        if adx_confirmed: score += 20
        if trend_aligned: score += 15
        if volume_spike: score += 10
        if price_above_sma: score += 10
        if momentum_healthy: score += 10
        if whale_inflow: score += 10
        
        return {
            'entry_signal': score >= 75,
            'score': score,
            'confidence': score / 100,
            'conditions_met': [flag for flag, met in {
                'price_above_vwap': price_above_vwap,
                'adx_confirmed': adx_confirmed,
                'trend_aligned': trend_aligned,
                'volume_spike': volume_spike,
                'price_above_sma': price_above_sma,
                'momentum_healthy': momentum_healthy,
                'whale_inflow': whale_inflow
            }.items() if met]
        }
```

**Secondary Setup - Breakout Pullback:**

```python
def breakout_pullback_entry(self, data: dict) -> dict:
    """
    Enter on pullback to breakout level after confirmed breakout
    """
    # Wait for breakout confirmation
    recent_breakout = close > resistance_level * 1.05  # 5% breakout
    pullback_zone = close < resistance_level * 1.02  # Within 2% of breakout
    volume_confirmed = volume_24h > avg_volume_20d * 1.5
    
    # Avoid immediate re-entry
    time_since_last_trade = (current_time - last_trade_time).hours
    cooldown_ok = time_since_last_trade > 4
    
    return {
        'entry_signal': recent_breakout and pullback_zone and 
                       volume_confirmed and cooldown_ok,
        'entry_price': close,
        'invalidation_level': resistance_level * 0.98  # 2% below breakout
    }
```

### 2.2 Short Entry Criteria

**Note**: Shorting on Jupiter/Solana requires special handling (margin markets, perps, or spot swaps to stables).

```python
class JupiterShortStrategy:
    
    def check_short_entry(self, data: dict) -> dict:
        # Primary short conditions (inverse of long)
        price_below_vwap = close < vwap_24h * 0.99
        adx_confirmed = adx_14 > 30
        trend_down = minus_di > plus_di
        volume_spike = rvol_5 > 1.5
        
        # Short-specific: Check funding rates if using perps
        if self.using_perps:
            funding_rate = fetch_funding_rate(data['token'])
            funding_favorable = funding_rate > 0.01  # Positive funding = shorts get paid
        else:
            funding_favorable = True
        
        # Bearish momentum
        below_sma = close < sma_20
        rsi_not_oversold = rsi_14 > 30
        
        # Scoring
        score = 0
        if price_below_vwap: score += 25
        if adx_confirmed: score += 20
        if trend_down: score += 15
        if volume_spike: score += 10
        if below_sma: score += 10
        if funding_favorable: score += 10
        
        return {
            'entry_signal': score >= 70,
            'score': score,
            'conditions_met': [...]
        }
```

### 2.3 MEV Protection - Entry Randomization

```python
import random
from time import sleep

class MEVProtectedEntry:
    """
    Protect against sandwich attacks and frontrunning
    """
    
    def execute_entry(self, order: dict) -> dict:
        # Randomize execution timing
        delay_ms = random.randint(500, 3000)  # 0.5-3 second delay
        sleep(delay_ms / 1000)
        
        # Split large orders if needed
        if order['size_usd'] > 50000:
            chunks = self.split_order(order, max_chunk=25000)
        else:
            chunks = [order]
        
        # Use Jupiter's exactOut feature when possible
        # (specify output amount, let input vary slightly)
        for chunk in chunks:
            if self.should_use_exact_out(chunk):
                swap_params = {
                    'mode': 'ExactOut',
                    'slippage_bps': self.calculate_slippage(chunk),
                    'priority_fee': self.calculate_priority_fee()
                }
            else:
                swap_params = {
                    'mode': 'ExactIn',
                    'slippage_bps': self.calculate_slippage(chunk),
                    'priority_fee': self.calculate_priority_fee()
                }
            
            # Submit with private mempool if available
            result = self.submit_jupiter_swap(chunk, swap_params)
            
        return {'status': 'completed', 'chunks_executed': len(chunks)}
    
    def calculate_slippage(self, order: dict) -> int:
        """
        Dynamic slippage based on market conditions
        """
        base_slippage = 50  # 0.5%
        
        # Increase slippage during high volatility
        if atr_percentile > 70:
            base_slippage += 100  # +1%
        
        # Increase for larger orders
        if order['size_usd'] > 25000:
            base_slippage += 50  # +0.5%
        
        # Jupiter-specific: check recommended slippage
        jupiter_recommended = self.get_jupiter_slippage(order['token_in'])
        
        return max(base_slippage, jupiter_recommended)
```

---

## 3. Exit Conditions

### 3.1 Take Profit Levels (DEX-Optimized)

Due to slippage, DEX trades require **wider profit targets**:

```python
class JupiterExitManager:
    """
    Multi-level take profit with DEX considerations
    """
    
    def __init__(self):
        # Wider targets for DEX vs CEX
        self.tp_levels = {
            'conservative': {
                'tp1': 0.05,    # 5% (was 3% for CEX)
                'tp2': 0.10,    # 10% (was 6%)
                'tp3': 0.18,    # 18% (was 12%)
                'tp4': 0.30     # 30% runner
            },
            'aggressive': {
                'tp1': 0.08,
                'tp2': 0.15,
                'tp3': 0.25,
                'tp4': 0.50
            }
        }
        
        self.position_exits = {
            'tp1': 0.25,  # Close 25% at TP1
            'tp2': 0.35,  # Close 35% at TP2
            'tp3': 0.25,  # Close 25% at TP3
            'tp4': 0.15   # 15% runner
        }
    
    def calculate_exit_prices(self, entry_price: float, 
                              direction: str, 
                              volatility_regime: str) -> dict:
        """
        Calculate exit levels based on regime
        """
        targets = self.tp_levels['conservative'] if volatility_regime == 'high' \
                                              else self.tp_levels['aggressive']
        
        if direction == 'long':
            return {
                'tp1': entry_price * (1 + targets['tp1']),
                'tp2': entry_price * (1 + targets['tp2']),
                'tp3': entry_price * (1 + targets['tp3']),
                'tp4': entry_price * (1 + targets['tp4'])
            }
        else:  # short
            return {
                'tp1': entry_price * (1 - targets['tp1']),
                'tp2': entry_price * (1 - targets['tp2']),
                'tp3': entry_price * (1 - targets['tp3']),
                'tp4': entry_price * (1 - targets['tp4'])
            }
```

### 3.2 Stop Loss Strategy

```python
def calculate_stop_loss(self, entry: dict, position: dict) -> dict:
    """
    ATR-based stop with DEX-specific adjustments
    """
    atr = entry['atr_14']
    entry_price = entry['price']
    
    # DEX: Wider stops due to volatility and slippage
    base_multiplier = 2.5  # vs 2.0 for CEX
    
    # Adjust for token volatility class
    if entry['token_category'] == 'meme':
        multiplier = base_multiplier * 1.5  # 3.75x for memes
    elif entry['token_category'] == 'major':
        multiplier = base_multiplier * 0.8  # 2.0x for majors
    else:
        multiplier = base_multiplier
    
    stop_distance = atr * multiplier
    
    if position['direction'] == 'long':
        stop_price = entry_price - stop_distance
        # Hard stop at 8% loss max for DEX
        hard_stop = entry_price * 0.92
        final_stop = max(stop_price, hard_stop)
    else:
        stop_price = entry_price + stop_distance
        hard_stop = entry_price * 1.08
        final_stop = min(stop_price, hard_stop)
    
    return {
        'initial_stop': final_stop,
        'stop_distance_pct': abs(final_stop - entry_price) / entry_price,
        'atr_multiple': multiplier
    }
```

### 3.3 Trailing Stop (Chandelier Exit)

```python
def trailing_stop_logic(self, position: dict, current_data: dict) -> dict:
    """
    ATR trailing stop with Jupiter-specific adjustments
    """
    direction = position['direction']
    entry_price = position['entry_price']
    highest_since_entry = position['highest_price'] if direction == 'long' \
                                                   else position['lowest_price']
    current_price = current_data['close']
    atr = current_data['atr_14']
    
    # Update highest/lowest since entry
    if direction == 'long':
        highest_since_entry = max(highest_since_entry, current_price)
        # Trail stop: highest - (ATR * multiplier)
        trail_distance = atr * 3.0  # 3x ATR for crypto
        new_stop = highest_since_entry - trail_distance
        
        # Don't move stop below initial
        effective_stop = max(new_stop, position['initial_stop'])
        
        # Exit triggers
        stop_triggered = current_price < effective_stop
        vwap_break = current_price < current_data['vwap_24h'] * 0.97
        adx_weakening = current_data['adx_14'] < 20 and current_data['adx_slope'] < 0
        
    else:  # short
        lowest_since_entry = min(position['lowest_price'], current_price)
        trail_distance = atr * 3.0
        new_stop = lowest_since_entry + trail_distance
        effective_stop = min(new_stop, position['initial_stop'])
        
        stop_triggered = current_price > effective_stop
        vwap_break = current_price > current_data['vwap_24h'] * 1.03
        adx_weakening = current_data['adx_14'] < 20 and current_data['adx_slope'] < 0
    
    return {
        'exit_signal': stop_triggered or (vwap_break and adx_weakening),
        'current_stop': effective_stop,
        'exit_reason': 'trailing_stop' if stop_triggered else 'technical_break',
        'unrealized_pnl_pct': (current_price - entry_price) / entry_price * 
                             (1 if direction == 'long' else -1)
    }
```

### 3.4 Time-Based Exits

```python
def time_exit_logic(self, position: dict, entry_time: datetime) -> dict:
    """
    Exit if trade doesn't work within expected timeframe
    """
    hours_elapsed = (datetime.now() - entry_time).total_seconds() / 3600
    
    # DEX positions need more time due to gas considerations
    time_limits = {
        'scalp': 8,      # 8 hours max for scalp
        'swing': 72,     # 3 days for swing
        'trend': 168     # 1 week for trend
    }
    
    position_type = position['type']
    max_hours = time_limits.get(position_type, 24)
    
    # Time decay exit if not profitable
    if hours_elapsed > max_hours / 2:  # Halfway through
        unrealized = self.calculate_pnl(position)
        if unrealized < 0.005:  # Less than 0.5% profit
            return {
                'exit_signal': True,
                'exit_reason': f'time_decay_{position_type}',
                'recommendation': 'close_position'
            }
    
    if hours_elapsed > max_hours:
        return {
            'exit_signal': True,
            'exit_reason': f'max_time_{position_type}',
            'recommendation': 'close_position'
        }
    
    return {'exit_signal': False}
```

---

## 4. Position Sizing

### 4.1 Risk-Based Sizing for DEX

```python
class JupiterPositionSizer:
    """
    Position sizing accounting for gas costs and slippage
    """
    
    def __init__(self, portfolio_value: float):
        self.portfolio = portfolio_value
        self.base_risk_per_trade = 0.015  # 1.5% (lower than CEX 2%)
        
        # DEX-specific costs
        self.avg_gas_cost_sol = 0.001
        self.sol_price = self.fetch_sol_price()
        self.entry_gas_usd = self.avg_gas_cost_sol * self.sol_price
        self.exit_gas_usd = self.entry_gas_cost * 1.2  # 20% buffer
        
    def calculate_position_size(self, setup: dict) -> dict:
        """
        Calculate position size with DEX cost considerations
        """
        entry_price = setup['entry_price']
        stop_price = setup['stop_price']
        token = setup['token']
        
        # Risk amount in USD
        risk_usd = self.portfolio * self.base_risk_per_trade
        
        # Adjust for regime
        regime_multiplier = setup.get('regime_multiplier', 1.0)
        risk_usd *= regime_multiplier
        
        # Stop distance
        stop_distance = abs(entry_price - stop_price)
        stop_pct = stop_distance / entry_price
        
        # Base position size (without fees)
        base_position_size = risk_usd / stop_pct
        
        # Apply slippage adjustment
        liquidity_data = self.analyze_liquidity_regime(token)
        expected_slippage = liquidity_data['slippage_bps'] / 10000
        
        # Adjust stop to account for slippage
        adjusted_stop_pct = stop_pct + expected_slippage
        
        # Recalculate with slippage
        adjusted_position_size = risk_usd / adjusted_stop_pct
        
        # Apply maximum size constraint based on liquidity
        max_size = min(
            adjusted_position_size,
            liquidity_data['max_position_size'],
            self.portfolio * 0.15  # Max 15% in one trade
        )
        
        # Minimum viable size (gas must be < 1% of trade value)
        min_trade_value = (self.entry_gas_usd + self.exit_gas_usd) * 100
        if max_size < min_trade_value:
            return {
                'viable': False,
                'reason': f'Trade value ${max_size:.2f} below minimum ${min_trade_value:.2f}'
            }
        
        return {
            'viable': True,
            'position_size_usd': max_size,
            'position_size_token': max_size / entry_price,
            'risk_usd': risk_usd,
            'stop_pct': adjusted_stop_pct,
            'expected_slippage_entry': expected_slippage,
            'breakeven_move_pct': self.calculate_breakeven(max_size, expected_slippage)
        }
    
    def calculate_breakeven(self, size: float, slippage: float) -> float:
        """
        Calculate minimum move needed to breakeven (gas + slippage)
        """
        total_cost = self.entry_gas_usd + self.exit_gas_usd + (size * slippage)
        breakeven_pct = total_cost / size
        return breakeven_pct
```

### 4.2 Kelly Criterion Adjustment

```python
def kelly_position_size(self, win_rate: float, avg_win: float, avg_loss: float) -> dict:
    """
    Kelly criterion with fractional multiplier for safety
    """
    # Kelly % = (WinRate × AvgWin - LossRate × AvgLoss) / AvgWin
    loss_rate = 1 - win_rate
    
    if avg_win == 0:
        return {'kelly_pct': 0, 'recommended_pct': 0}
    
    kelly = (win_rate * avg_win - loss_rate * abs(avg_loss)) / avg_win
    
    # Fractional Kelly for risk management (1/4 Kelly for DEX)
    fractional_kelly = max(0, kelly * 0.25)
    
    # Cap at portfolio limits
    max_pct = min(fractional_kelly, 0.20)  # Max 20% per trade
    
    return {
        'kelly_pct': kelly,
        'fractional_kelly_pct': fractional_kelly,
        'recommended_pct': max_pct,
        'recommended_usd': self.portfolio * max_pct
    }
```

### 4.3 Correlation-Based Limits

```python
def check_correlation_exposure(self, new_position: dict, current_portfolio: list) -> dict:
    """
    Limit correlation risk in DEX portfolio
    """
    new_token = new_position['token']
    
    # Calculate correlation with existing positions
    correlations = []
    for pos in current_portfolio:
        corr = self.calculate_correlation(new_token, pos['token'], lookback=30)
        correlations.append(corr)
    
    avg_correlation = np.mean(correlations) if correlations else 0
    max_correlation = max(correlations) if correlations else 0
    
    # DEX concentration limits (stricter due to liquidity)
    limits = {
        'single_token': 0.20,     # 20% max in one token
        'correlated_group': 0.35,  # 35% max in correlated tokens
        'total_exposure': 0.80     # 80% max deployed
    }
    
    # Reduce size if highly correlated
    if max_correlation > 0.80:
        size_multiplier = 0.5
    elif max_correlation > 0.60:
        size_multiplier = 0.75
    else:
        size_multiplier = 1.0
    
    return {
        'approved': True,
        'size_multiplier': size_multiplier,
        'avg_correlation': avg_correlation,
        'max_correlation': max_correlation,
        'portfolio_exposure': sum(p['size_usd'] for p in current_portfolio) / self.portfolio
    }
```

---

## 5. Timeframe Selection

### 5.1 Recommended Intervals for Jupiter

| Timeframe | Use Case | Indicators | Signal Frequency |
|-----------|----------|------------|------------------|
| **1m** | Entry timing only | Price action, order book | 20-50/day |
| **5m** | Primary entry/exit | All primary indicators | 3-8/day |
| **15m** | Trend confirmation | ADX, EMA, VWAP | 1-3/day |
| **1h** | Regime detection | ADX, Bollinger, Volume | 1-2/week |
| **4h** | Major trend | SMA(50/200), Macro view | Weekly |
| **1d** | Portfolio allocation | Long-term MA, Support/Resist | Monthly |

### 5.2 Multi-Timeframe Confirmation

```python
class MultiTimeframeAnalyzer:
    """
    Require confluence across timeframes for DEX entries
    """
    
    def analyze(self, token: str) -> dict:
        # Fetch multiple timeframes
        tf_5m = self.fetch_ohlcv(token, '5m', limit=100)
        tf_1h = self.fetch_ohlcv(token, '1h', limit=50)
        tf_4h = self.fetch_ohlcv(token, '4h', limit=30)
        
        # Calculate indicators on each timeframe
        analysis_5m = self.calculate_regime(tf_5m)
        analysis_1h = self.calculate_regime(tf_1h)
        analysis_4h = self.calculate_regime(tf_4h)
        
        # Alignment scoring
        alignment = 0
        
        # Higher timeframe trend direction
        if analysis_4h['trend'] == analysis_1h['trend']:
            alignment += 30  # HTF aligned
        
        # Entry timeframe confirmation
        if analysis_1h['trend'] == analysis_5m['setup']:
            alignment += 40  # Entry aligns with HTF
        
        # Volume confirmation across timeframes
        if analysis_5m['rvol'] > 1.5 and analysis_1h['volume_trend'] == 'increasing':
            alignment += 20
        
        # ADX confirmation (trend strength)
        if analysis_1h['adx'] > 25 and analysis_4h['adx'] > 20:
            alignment += 10
        
        return {
            'alignment_score': alignment,
            'trade_signal': alignment >= 70,
            'timeframes': {
                '5m': analysis_5m,
                '1h': analysis_1h,
                '4h': analysis_4h
            }
        }
```

### 5.3 Trading Windows

```python
class TradingSchedule:
    """
    Optimal trading windows for Solana/DEX
    """
    
    def is_trading_window(self) -> dict:
        """
        Check if current time is favorable for Jupiter trading
        """
        from datetime import datetime
        import pytz
        
        now = datetime.now(pytz.UTC)
        utc_hour = now.hour
        day_of_week = now.weekday()  # 0=Monday
        
        # Solana DEX activity peaks (UTC)
        windows = {
            'asian_morning': (0, 4),      # 00:00-04:00 UTC - Low vol, avoid
            'asian_afternoon': (4, 8),    # 04:00-08:00 UTC - Moderate
            'european_morning': (8, 12),  # 08:00-12:00 UTC - High
            'us_morning': (13, 17),       # 13:00-17:00 UTC - Peak
            'us_afternoon': (17, 21),     # 17:00-21:00 UTC - High
            'late_night': (21, 24),       # 21:00-24:00 UTC - Moderate
            'weekend': (day_of_week >= 5) # Sat-Sun - Reduced activity
        }
        
        # Determine current window
        current_window = None
        for window, hours in windows.items():
            if isinstance(hours, tuple) and utc_hour >= hours[0] and utc_hour < hours[1]:
                current_window = window
                break
        
        # Priority scoring
        priority = {
            'asian_morning': 1,
            'weekend': 2,
            'asian_afternoon': 3,
            'late_night': 4,
            'european_morning': 5,
            'us_afternoon': 7,
            'us_morning': 8
        }
        
        score = priority.get(current_window, 0)
        
        return {
            'is_good_window': score >= 4,
            'current_window': current_window,
            'priority_score': score,
            'liquidity_estimate': self.estimate_liquidity(current_window),
            'recommendation': 'trade' if score >= 5 else 'reduce_size' if score >= 3 else 'avoid'
        }
```

---

## 6. Token Selection Criteria

### 6.1 Jupiter-Specific Token Requirements

```python
class TokenScreener:
    """
    Screen tokens for Jupiter trading viability
    """
    
    MINIMUM_REQUIREMENTS = {
        'min_market_cap': 10_000_000,      # $10M minimum
        'min_24h_volume': 1_000_000,        # $1M daily volume
        'min_jupiter_liquidity': 500_000,  # $500k in Jupiter pools
        'max_slippage_10k': 0.01,          # 1% slippage on $10k swap
        'min_holder_count': 1000,          # Decent distribution
        'min_pool_count': 3,               # Multiple DEX routes
        'max_single_pool_pct': 0.80        # No pool >80% of liquidity
    }
    
    def screen_token(self, token_address: str) -> dict:
        """
        Comprehensive token screening for Jupiter trading
        """
        # Basic requirements
        jupiter_data = self.fetch_jupiter_token_info(token_address)
        onchain = self.fetch_onchain_metrics(token_address)
        
        checks = {
            'market_cap_ok': jupiter_data['market_cap'] >= self.MINIMUM_REQUIREMENTS['min_market_cap'],
            'volume_ok': jupiter_data['volume_24h'] >= self.MINIMUM_REQUIREMENTS['min_24h_volume'],
            'liquidity_ok': jupiter_data['jupiter_liquidity'] >= self.MINIMUM_REQUIREMENTS['min_jupiter_liquidity'],
            'holders_ok': onchain['unique_holders'] >= self.MINIMUM_REQUIREMENTS['min_holder_count'],
            'distribution_ok': onchain['top_holder_pct'] < 0.20,  # No whale >20%
            'contract_verified': onchain['contract_verified'],
            'mint_authority_revoked': onchain.get('mint_authority', True) == None,
            'freeze_authority_revoked': onchain.get('freeze_authority', True) == None
        }
        
        # Slippage test
        slippage_test = self.test_slippage(token_address, 10000)
        checks['slippage_ok'] = slippage_test['slippage_pct'] <= self.MINIMUM_REQUIREMENTS['max_slippage_10k']
        
        # Scam/honeypot detection
        checks['not_honeypot'] = self.honeypot_check(token_address)
        checks['not_rug_pull'] = onchain['liquidity_locked'] or onchain['lp_locked_pct'] > 0.80
        
        # Calculate score
        passed = sum(checks.values())
        total = len(checks)
        score = (passed / total) * 100
        
        return {
            'approved': score >= 85 and all([checks['contract_verified'], 
                                             checks['not_honeypot'], 
                                             checks['not_rug_pull']]),
            'score': score,
            'checks': checks,
            'token_data': jupiter_data,
            'risk_level': self.classify_risk(score, checks)
        }
    
    def classify_risk(self, score: float, checks: dict) -> str:
        """
        Classify token risk tier
        """
        if score >= 95 and all([checks['mint_authority_revoked'], 
                                checks['freeze_authority_revoked'],
                                checks['liquidity_ok']]):
            return 'A_grade'
        elif score >= 85:
            return 'B_grade'
        elif score >= 70 and checks['not_honeypot'] and checks['not_rug_pull']:
            return 'C_grade'
        else:
            return 'reject'
```

### 6.2 Recommended Token Tiers

| Tier | Criteria | Examples | Position Size Limit | Slippage Tolerance |
|------|----------|----------|---------------------|-------------------|
| **AAA** | Top 20 MC, >$100M daily vol | SOL, USDC, JUP, BONK | 25% portfolio | 0.3% |
| **AA** | Top 50 MC, >$20M daily vol | WIF, RENDER, PYTH | 15% portfolio | 0.5% |
| **A** | Top 100 MC, >$5M daily vol | Established DeFi | 10% portfolio | 1.0% |
| **B** | Top 200 MC, >$2M daily vol | Emerging projects | 5% portfolio | 2.0% |
| **C** | Top 500 MC, >$500k daily vol | Speculative | 2% portfolio | 3.0% |
| **REJECT** | Below minimums or high risk | New/unknown tokens | 0% | N/A |

### 6.3 Watchlist Management

```python
class JupiterWatchlist:
    """
    Dynamic token watchlist for Jupiter
    """
    
    CORE_TOKENS = [
        'So11111111111111111111111111111111111111112',  # SOL
        'JUPyiwrYJFskUPiHa7hKeRBo7f49nerZuhM5ZsKVFtc',  # JUP
        'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
        'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',  # BONK
    ]
    
    def __init__(self):
        self.watched_tokens = set(self.CORE_TOKENS)
        self.trending_cache = {}
        
    def update_watchlist(self):
        """
        Refresh watchlist with trending tokens
        """
        # Get Jupiter trending tokens
        trending = self.fetch_jupiter_trending(limit=50)
        
        for token in trending:
            screen_result = self.screen_token(token['address'])
            
            if screen_result['approved']:
                self.watched_tokens.add(token['address'])
                self.trending_cache[token['address']] = {
                    'added_date': datetime.now(),
                    'screen_score': screen_result['score'],
                    'risk_tier': screen_result['risk_level']
                }
        
        # Remove stale tokens (not seen in trending for 7 days)
        self._cleanup_stale_tokens()
        
        return list(self.watched_tokens)
    
    def get_tradeable_tokens(self, portfolio_value: float) -> list:
        """
        Get tokens that can be traded given portfolio size
        """
        tradeable = []
        
        for token in self.watched_tokens:
            screen = self.trending_cache.get(token, {})
            tier = screen.get('risk_tier', 'C_grade')
            
            # Limit by portfolio size
            if portfolio_value > 100000:
                allowed_tiers = ['AAA', 'AA', 'A', 'B']
            elif portfolio_value > 10000:
                allowed_tiers = ['AAA', 'AA', 'A']
            else:
                allowed_tiers = ['AAA', 'AA']
            
            if tier in allowed_tiers:
                tradeable.append(token)
        
        return tradeable
```

---

## 7. Backtesting Parameters

### 7.1 DEX-Specific Backtest Configuration

```python
class JupiterBacktestConfig:
    """
    Backtesting configuration for Jupiter strategy
    """
    
    def __init__(self):
        # Simulation parameters
        self.config = {
            'initial_capital': 10000,     # Start with $10k
            'fee_model': {
                'jupiter_fee_bps': 5,      # 0.05% platform fee
                'network_fee_sol': 0.001,  # SOL per transaction
                'slippage_model': 'dynamic'  # Use historical slippage data
            },
            'execution': {
                'fill_model': 'probabilistic',  # Probability of fill based on volume
                'slippage_function': lambda size, liquidity: size / liquidity * 0.5,
                'partial_fill': True
            },
            'risk': {
                'max_positions': 5,
                'max_drawdown': 0.15,      # Stop at 15% drawdown
                'daily_loss_limit': 0.05   # Stop trading after 5% daily loss
            },
            'data': {
                'timeframes': ['5m', '1h', '4h'],
                'min_bars_required': 500,
                'train_period': 0.7,       # 70% train
                'test_period': 0.3         # 30% test
            }
        }
    
    def get_bootstrap_config(self):
        """
        Bootstrap backtest for statistical significance
        """
        return {
            'method': 'block_bootstrap',
            'block_length': 24,  # 24 bars (2 hours for 5m)
            'iterations': 1000,
            'confidence_interval': 0.95
        }
```

### 7.2 Key Metrics for DEX Validation

```python
class JupiterBacktestMetrics:
    """
    Metrics to validate Jupiter strategy
    """
    
    def calculate_metrics(self, trades: list, equity_curve: list) -> dict:
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Profit factor
        gross_profit = sum([t['pnl'] for t in trades if t['pnl'] > 0])
        gross_loss = abs(sum([t['pnl'] for t in trades if t['pnl'] < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Average metrics
        avg_win = gross_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = gross_loss / losing_trades if losing_trades > 0 else 0
        win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')
        
        # Expectancy
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        expectancy_pct = expectancy / 10000 * 100  # As % of risk
        
        # DEX-specific metrics
        total_gas_spent = sum([t['gas_cost_usd'] for t in trades])
        total_slippage_paid = sum([t['slippage_cost'] for t in trades])
        slippage_win_rate = len([t for t in trades if t['pnl'] > t['slippage_cost'] * 2]) / total_trades
        
        # Path ratios (account for gas costs)
        gross_return = (equity_curve[-1] - equity_curve[0]) / equity_curve[0]
        net_return = gross_return - (total_gas_spent / equity_curve[0])
        
        # Drawdown analysis
        max_drawdown = self.calculate_max_drawdown(equity_curve)
        calmar_ratio = net_return / max_drawdown if max_drawdown > 0 else 0
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'win_loss_ratio': win_loss_ratio,
            'expectancy_usd': expectancy,
            'expectancy_pct': expectancy_pct,
            'net_return_pct': net_return * 100,
            'gross_return_pct': gross_return * 100,
            'max_drawdown_pct': max_drawdown * 100,
            'calmar_ratio': calmar_ratio,
            'sharpe_ratio': self.calculate_sharpe(equity_curve),
            'sortino_ratio': self.calculate_sortino(equity_curve),
            'dex_specific': {
                'total_gas_spent': total_gas_spent,
                'total_slippage_paid': total_slippage_paid,
                'slippage_win_rate': slippage_win_rate,
                'gas_as_pct_of_pnl': total_gas_spent / gross_profit * 100 if gross_profit > 0 else 0,
                'avg_gas_per_trade': total_gas_spent / total_trades if total_trades > 0 else 0
            }
        }
    
    def _calculate_max_drawdown(self, equity: list) -> float:
        peak = equity[0]
        max_dd = 0
        for value in equity:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            max_dd = max(max_dd, dd)
        return max_dd
```

### 7.3 Minimum Acceptable Backtest Results

| Metric | Minimum | Target | Exceptional |
|--------|---------|--------|-------------|
| **Win Rate** | 45% | 55% | 65%+ |
| **Profit Factor** | 1.3 | 1.6 | 2.0+ |
| **Net Return (Monthly)** | 3% | 8% | 15%+ |
| **Max Drawdown** | <20% | <12% | <8% |
| **Sharpe Ratio** | >0.8 | >1.2 | >1.8 |
| **Calmar Ratio** | >0.5 | >1.0 | >1.5 |
| **Gas Efficiency** | >60% | >75% | >85% |
| **Slippage Recovery** | >50% | >70% | >85% |
| **Expectancy/Trade** | >$10 | >$25 | >$50 |

### 7.4 Walk-Forward Analysis

```python
class WalkForwardAnalyzer:
    """
    Walk-forward optimization for Jupiter strategy
    """
    
    def run_wfo(self, data: pd.DataFrame, strategy_params: dict) -> dict:
        """
        Walk-forward analysis with regime shifts
        """
        results = []
        window_size = int(len(data) * 0.3)  # 30% in-sample
        step_size = int(window_size * 0.2)   # Step 20% forward
        
        for i in range(0, len(data) - window_size, step_size):
            # In-sample period
            is_data = data.iloc[i:i + window_size]
            # Out-of-sample period
            oos_data = data.iloc[i + window_size:i + window_size + step_size]
            
            # Optimize on in-sample
            optimal_params = self.optimize_strategy(is_data, strategy_params)
            
            # Test on out-of-sample
            oos_result = self.backtest(oos_data, optimal_params)
            
            results.append({
                'in_sample_start': is_data.index[0],
                'in_sample_end': is_data.index[-1],
                'oos_start': oos_data.index[0],
                'oos_end': oos_data.index[-1],
                'params': optimal_params,
                'result': oos_result
            })
        
        # Calculate robustness
        is_returns = [r['result']['net_return'] for r in results]
        is_avg = np.mean(is_returns)
        is_std = np.std(is_returns)
        consistency = 1 - (is_std / abs(is_avg)) if is_avg != 0 else 0
        
        return {
            'windows': results,
            'avg_return': is_avg,
            'std_return': is_std,
            'consistency_score': consistency,
            'robust': consistency > 0.7 and is_avg > 0
        }
```

### 7.5 Monte Carlo Simulation

```python
class MonteCarloSimulator:
    """
    Monte Carlo simulation for strategy validation
    """
    
    def run_simulation(self, trades: list, iterations: int = 10000) -> dict:
        """
        Run Monte Carlo simulation of trade sequences
        """
        profits = [t['pnl'] for t in trades]
        equity = 10000  # Starting equity
        
        final_equities = []
        max_drawdowns = []
        
        for _ in range(iterations):
            # Shuffle trades
            shuffled = np.random.permutation(profits)
            
            # Calculate equity curve
            eq_curve = [equity]
            current_equity = equity
            peak = equity
            max_dd = 0
            
            for trade_pnl in shuffled:
                current_equity += trade_pnl
                eq_curve.append(current_equity)
                
                if current_equity > peak:
                    peak = current_equity
                dd = (peak - current_equity) / peak
                max_dd = max(max_dd, dd)
            
            final_equities.append(current_equity)
            max_drawdowns.append(max_dd)
        
        return {
            'median_final_equity': np.median(final_equities),
            'mean_final_equity': np.mean(final_equities),
            'percentile_5': np.percentile(final_equities, 5),
            'percentile_95': np.percentile(final_equities, 95),
            'probability_profit': sum(1 for e in final_equities if e > equity) / len(final_equities),
            'median_max_dd': np.median(max_drawdowns),
            'worst_case_dd': np.percentile(max_drawdowns, 95),
            'risk_of_ruin': sum(1 for e in final_equities if e < equity * 0.5) / len(final_equities)
        }
```

---

## 8. Implementation Checklist

### 8.1 Pre-Trading Setup

```markdown
- [ ] Configure Jupiter API key and RPC endpoints
- [ ] Set up wallet with sufficient SOL for gas (min 0.1 SOL)
- [ ] Verify token approval list (Tier AAA, AA, A only)
- [ ] Test small trades (<$100) on all target tokens
- [ ] Calculate historical slippage for each token
- [ ] Configure Telegram/Discord alerts
- [ ] Set up position monitoring dashboard
```

### 8.2 Daily Operations

```markdown
- [ ] Check Solana network health (TPS, slot time)
- [ ] Update token watchlist (screen for new tokens)
- [ ] Calculate current volatility regime
- [ ] Review open positions (trail stops, partial exits)
- [ ] Scan for entry setups in approved tokens
- [ ] Check correlation exposure across portfolio
- [ ] Log all trades and P&L
```

### 8.3 Risk Monitoring

```markdown
- [ ] Daily P&L vs limit (5% max loss)
- [ ] Maximum drawdown (15% stop trading)
- [ ] Correlation breakdown check (avg correlation > 0.7)
- [ ] Gas costs vs trade value (must be < 1%)
- [ ] Individual position size limits (check at 9am UTC)
- [ ] Token liquidity monitoring (slippage alerts)
```

---

## 9. Emergency Procedures

### 9.1 Circuit Breakers

```python
EMERGENCY_HALTS = {
    'max_daily_loss': 0.05,          # Stop after 5% loss
    'max_drawdown': 0.15,            # Stop at 15% DD
    'network_degradation': True,     # Halt if TPS < 1000
    'extreme_volatility': True,      # Halt if VIX > 60
    'correlation_spike': 0.80,       # Halt if avg corr > 0.8
    'manual_override': True          # Allow manual stop
}
```

### 9.2 Emergency Exit Procedure

```python
def emergency_exit_all_positions(reason: str):
    """
    Close all positions immediately
    """
    for position in get_open_positions():
        # Market sell with increased slippage tolerance
        close_order = {
            'token': position['token'],
            'amount': position['size_token'],
            'slippage_bps': 300,  # 3% slippage in emergency
            'priority_fee_multiplier': 2.0,  # Prioritize execution
            'reason': f'EMERGENCY: {reason}'
        }
        
        execute_jupiter_swap(close_order)
    
    # Send alerts
    send_alert(f'EMERGENCY HALT: {reason}')
    
    # Log and disable trading
    disable_trading(reason)
```

---

## 10. References & Integration

### 10.1 Jupiter API Documentation

- **Swap API**: https://station.jup.ag/docs/apis/swap-api
- **Price API**: https://station.jup.ag/docs/apis/price-api
- **Token List**: https://station.jup.ag/docs/apis/token-list-api

### 10.2 Solana Resources

- **RPC Endpoints**: Helius, QuickNode, Alchemy
- **Transaction Explorer**: Solscan.io, SolanaFM
- **Mempool Monitoring**: Jito MEV, Solana Beach

### 10.3 Related Oracle Files

- `agents/oracle/learning/market-regimes.md` - Regime detection algorithms
- `agents/oracle/learning/indicators.py` - NumPy indicator implementations

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0   | 2026-02-18 | Initial Jupiter DEX strategy |

---

*Document generated by Oracle (🔮) - Trading Strategist*  
*For automated execution on Jupiter DEX/Solana*