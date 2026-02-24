"""
Oracle Aggressive Strategy v2 for Toobit Perpetual Futures
Higher conviction entries, better risk management, trend alignment.
"""
import numpy as np
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)

class Signal(Enum):
    HOLD = 0
    BUY = 1
    SELL = 2

@dataclass
class StrategyConfig:
    """Configuration for aggressive strategy v2"""
    leverage: float = 15.0  # Up from 10x
    risk_per_trade: float = 0.05  # Down from 8% - smaller per-trade risk
    max_drawdown: float = 0.20  # 20% hard stop
    max_daily_loss: float = 0.10  # Down from 15% - tighter daily limit
    min_reward_ratio: float = 2.0  # Up from 1.5 - minimum 2:1 R:R
    trailing_activation: float = 1.0  # Activate trailing stop at 1R profit
    trailing_percent: float = 0.5  # Trail at 50% of profits
    cooldown_minutes: int = 5  # Up from 2 - reduce churning
    breakout_threshold: float = 0.005  # Up from 0.1% - catch real moves
    min_stop_atr: float = 0.8  # Minimum 0.8 ATR stop
    max_stop_atr: float = 1.5  # Maximum 1.5 ATR stop
    ema_fast: int = 9
    ema_slow: int = 21
    min_confidence: float = 0.6  # Minimum confidence to trade

@dataclass
class Trade:
    """Track a trade"""
    entry_price: float
    exit_price: float
    size: float
    side: str
    pnl: float
    timestamp: float
    reason: str

class AggressiveStrategy:
    """
    Aggressive v2 - Higher conviction entries, trend-aligned.
    
    Key improvements:
    - EMA trend filter - only trade with the trend
    - Higher breakout threshold - catch real moves, not noise
    - ATR-based stops - adapt to volatility
    - Longer cooldown - reduce churning
    - Confidence-weighted sizing
    """
    
    def __init__(self, config: StrategyConfig = None):
        self.config = config or StrategyConfig()
        self.price_history: List[float] = []
        self.volume_history: List[float] = []
        self.trades: List[Trade] = []
        self.trades_today = 0
        self.wins_today = 0
        self.losses_today = 0
        self.daily_pnl = 0.0
        self.peak_balance = 0.0
        self.last_trade_time = 0
        self.consecutive_losses = 0
        
        # EMA state
        self.ema_fast = None
        self.ema_slow = None
        
    def update_price(self, price: float, volume: float = 0):
        """Update price history and EMAs"""
        self.price_history.append(price)
        self.volume_history.append(volume)
        
        # Keep last 200 prices
        if len(self.price_history) > 200:
            self.price_history = self.price_history[-200:]
            self.volume_history = self.volume_history[-200:]
        
        # Update EMAs
        self._update_ema(price)
    
    def _update_ema(self, price: float):
        """Update EMA values"""
        alpha_fast = 2 / (self.config.ema_fast + 1)
        alpha_slow = 2 / (self.config.ema_slow + 1)
        
        if self.ema_fast is None:
            self.ema_fast = price
            self.ema_slow = price
        else:
            self.ema_fast = price * alpha_fast + self.ema_fast * (1 - alpha_fast)
            self.ema_slow = price * alpha_slow + self.ema_slow * (1 - alpha_slow)
    
    def get_trend(self) -> str:
        """Get current trend based on EMA alignment"""
        if self.ema_fast is None or self.ema_slow is None:
            return 'NEUTRAL'
        
        if self.ema_fast > self.ema_slow * 1.001:  # 0.1% buffer
            return 'BULLISH'
        elif self.ema_fast < self.ema_slow * 0.999:
            return 'BEARISH'
        return 'NEUTRAL'
    
    def calculate_atr(self, period: int = 14) -> float:
        """Calculate Average True Range as percentage"""
        if len(self.price_history) < period + 1:
            return 0.01  # Default 1%
        
        tr_values = []
        for i in range(1, min(period + 1, len(self.price_history))):
            if i >= len(self.price_history):
                break
            high = max(self.price_history[-i], self.price_history[-i-1])
            low = min(self.price_history[-i], self.price_history[-i-1])
            prev_close = self.price_history[-i-1] if i < len(self.price_history) else self.price_history[-i]
            
            tr = high - low
            tr_values.append(tr)
        
        if not tr_values:
            return 0.01
        
        atr_abs = np.mean(tr_values)
        atr_pct = atr_abs / self.price_history[-1] if self.price_history[-1] > 0 else 0.01
        return atr_pct
    
    def calculate_volatile_range(self) -> Dict[str, Any]:
        """Calculate recent price range with volatility"""
        if len(self.price_history) < 20:
            return {
                'high_5': 0, 'low_5': 0,
                'high_10': 0, 'low_10': 0,
                'high_20': 0, 'low_20': 0,
                'range': 0, 'volatility': 0
            }
        
        recent_5 = self.price_history[-5:]
        recent_10 = self.price_history[-10:]
        recent_20 = self.price_history[-20:]
        
        high_5, low_5 = max(recent_5), min(recent_5)
        high_10, low_10 = max(recent_10), min(recent_10)
        high_20, low_20 = max(recent_20), min(recent_20)
        
        current = self.price_history[-1]
        range_pct = (high_10 - low_10) / current if current > 0 else 0
        
        return {
            'high_5': high_5, 'low_5': low_5,
            'high_10': high_10, 'low_10': low_10,
            'high_20': high_20, 'low_20': low_20,
            'range': range_pct,
            'volatility': self.calculate_atr()
        }
    
    def check_risk_limits(self, current_balance: float, position: Optional[Dict]) -> tuple[bool, str]:
        """Check if trading should continue"""
        if current_balance > self.peak_balance:
            self.peak_balance = current_balance
        
        # Check drawdown
        if self.peak_balance > 0:
            drawdown = (self.peak_balance - current_balance) / self.peak_balance
            if drawdown >= self.config.max_drawdown:
                return False, f"Max drawdown {drawdown:.1%} >= {self.config.max_drawdown:.0%}"
        
        # Check daily loss
        daily_loss_pct = abs(self.daily_pnl) / current_balance if current_balance > 0 else 0
        if self.daily_pnl < 0 and daily_loss_pct >= self.config.max_daily_loss:
            return False, f"Daily loss {daily_loss_pct:.1%} >= limit"
        
        # Check consecutive losses (circuit breaker)
        if self.consecutive_losses >= 3:
            return False, f"Circuit breaker: {self.consecutive_losses} consecutive losses"
        
        # Check cooldown
        if self.last_trade_time > 0:
            seconds_since = time.time() - self.last_trade_time
            if seconds_since < self.config.cooldown_minutes * 60:
                remaining = self.config.cooldown_minutes * 60 - seconds_since
                return False, f"Cooldown: {remaining:.0f}s remaining"
        
        return True, "OK"
    
    def calculate_position_size(self, balance: float, entry: float, stop: float, 
                                  confidence: float = 1.0) -> Dict[str, float]:
        """Calculate position size with confidence weighting"""
        if entry <= 0 or stop <= 0 or entry == stop:
            return {'size': 0, 'margin': 0, 'risk_amount': 0, 'leverage': 0}
        
        # Base risk adjusted by confidence
        risk_pct = self.config.risk_per_trade * min(confidence, 1.0)
        risk_amount = balance * risk_pct
        
        # Stop distance
        stop_dist = abs(entry - stop) / entry
        if stop_dist < 0.002:  # Minimum 0.2% stop
            stop_dist = 0.002
        
        # Position size with leverage
        position_value = risk_amount / stop_dist
        size = position_value / entry
        
        # Limit by leverage
        max_size = (balance * self.config.leverage) / entry
        size = min(size, max_size)
        
        return {
            'size': size,
            'margin': size * entry / self.config.leverage,
            'risk_amount': risk_amount,
            'leverage': self.config.leverage
        }
    
    def on_tick(self, tick_data: Dict[str, Any], balance: float,
                position: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main strategy logic called on each price tick.
        """
        price = tick_data.get('price', 0)
        volume = tick_data.get('volume', 0)
        self.update_price(price, volume)
        
        result = {
            'signal': Signal.HOLD,
            'size': 0,
            'entry_price': price,
            'stop_loss': 0,
            'take_profit': 0,
            'confidence': 0,
            'reason': ''
        }
        
        # Risk check
        can_trade, reason = self.check_risk_limits(balance, position)
        if not can_trade:
            result['reason'] = reason
            return result
        
        # If in position, manage it
        if position and position.get('size', 0) > 0:
            return self._manage_position(tick_data, position)
        
        # Look for entry
        return self._find_entry(tick_data, balance)
    
    def _find_entry(self, tick: Dict, balance: float) -> Dict:
        """Find high-conviction entry signals"""
        price = tick['price']
        result = {
            'signal': Signal.HOLD,
            'size': 0,
            'entry_price': price,
            'stop_loss': 0,
            'take_profit': 0,
            'confidence': 0,
            'reason': ''
        }
        
        # Need enough history
        if len(self.price_history) < 30:
            result['reason'] = f'Building history ({len(self.price_history)}/30)'
            return result
        
        # Calculate range EXCLUDING current price (use previous 5-10 bars)
        if len(self.price_history) < 10:
            result['reason'] = 'Not enough bars for range'
            return result
            
        prev_5 = self.price_history[-10:-5]  # 5 bars ago
        prev_10 = self.price_history[-20:-10] if len(self.price_history) >= 20 else prev_5
        
        high_5, low_5 = max(prev_5), min(prev_5)
        high_10, low_10 = max(prev_10), min(prev_10)
        
        trend = self.get_trend()
        atr_pct = self.calculate_atr()
        
        # Breakout levels (0.5% threshold)
        breakout_up = price > high_5 * (1 + self.config.breakout_threshold)
        breakout_down = price < low_5 * (1 - self.config.breakout_threshold)
        
        # Calculate range percentage for volatility check
        range_pct = (high_10 - low_10) / price if price > 0 else 0
        
        # Calculate confidence
        confidence = 0.0
        reasons = []
        
        # LONG setup
        if breakout_up:
            # Trend alignment
            if trend == 'BULLISH':
                confidence += 0.3
                reasons.append('trend=BULL')
            elif trend == 'NEUTRAL':
                confidence += 0.1
            
            # Volatility check
            if atr_pct > 0.005:  # Enough volatility
                confidence += 0.2
                reasons.append(f'ATR={atr_pct:.1%}')
            
            # Range expansion
            if range_pct > 0.01:  # 1%+ range
                confidence += 0.2
                reasons.append(f'range={range_pct:.1%}')
            
            # Distance from EMA
            if self.ema_slow and price > self.ema_slow:
                confidence += 0.2
                reasons.append('above_EMA')
            
            if confidence >= self.config.min_confidence:
                # Calculate ATR-based stop
                stop_dist = max(atr_pct * self.config.min_stop_atr, 0.005)
                stop = price * (1 - stop_dist)
                target = price * (1 + stop_dist * self.config.min_reward_ratio)
                
                pos = self.calculate_position_size(balance, price, stop, confidence)
                
                result.update({
                    'signal': Signal.BUY,
                    'size': pos['size'],
                    'entry_price': price,
                    'stop_loss': stop,
                    'take_profit': target,
                    'confidence': confidence,
                    'reason': f"LONG breakout {price:.0f} > {high_5:.0f} | {' | '.join(reasons)}"
                })
            else:
                result['reason'] = f"LONG breakout but low confidence: {confidence:.1%}"
        
        # SHORT setup
        elif breakout_down:
            # Trend alignment
            if trend == 'BEARISH':
                confidence += 0.3
                reasons.append('trend=BEAR')
            elif trend == 'NEUTRAL':
                confidence += 0.1
            
            # Volatility check
            if atr_pct > 0.005:
                confidence += 0.2
                reasons.append(f'ATR={atr_pct:.1%}')
            
            # Range expansion
            if range_pct > 0.01:
                confidence += 0.2
                reasons.append(f'range={range_pct:.1%}')
            
            # Distance from EMA
            if self.ema_slow and price < self.ema_slow:
                confidence += 0.2
                reasons.append('below_EMA')
            
            if confidence >= self.config.min_confidence:
                # Calculate ATR-based stop
                stop_dist = max(atr_pct * self.config.min_stop_atr, 0.005)
                stop = price * (1 + stop_dist)
                target = price * (1 - stop_dist * self.config.min_reward_ratio)
                
                pos = self.calculate_position_size(balance, price, stop, confidence)
                
                result.update({
                    'signal': Signal.SELL,
                    'size': pos['size'],
                    'entry_price': price,
                    'stop_loss': stop,
                    'take_profit': target,
                    'confidence': confidence,
                    'reason': f"SHORT breakout {price:.0f} < {low_5:.0f} | {' | '.join(reasons)}"
                })
            else:
                result['reason'] = f"SHORT breakout but low confidence: {confidence:.1%}"
        
        else:
            result['reason'] = f"No breakout | trend={trend} | 5H={high_5:.0f} 5L={low_5:.0f}"
        
        return result
    
    def _manage_position(self, tick: Dict, position: Dict) -> Dict:
        """Manage open position with trailing stops"""
        price = tick['price']
        entry = position.get('entry_price', 0)
        stop = position.get('stop_loss', 0)
        target = position.get('take_profit', 0)
        size = position.get('size', 0)
        side = position.get('side', 'LONG')
        
        result = {
            'signal': Signal.HOLD,
            'size': size,
            'entry_price': entry,
            'stop_loss': stop,
            'take_profit': target,
            'confidence': 1.0,
            'reason': ''
        }
        
        if size == 0 or entry == 0:
            return result
        
        # Calculate R-multiple
        if side == 'LONG':
            risk = entry - stop
            if risk <= 0:
                return result
            r_multiple = (price - entry) / risk
            
            # Stop loss hit
            if price <= stop:
                return {
                    'signal': Signal.SELL,
                    'size': size,
                    'entry_price': entry,
                    'stop_loss': stop,
                    'take_profit': target,
                    'confidence': 1.0,
                    'reason': f'STOP LOSS: {price:.0f} <= {stop:.0f}'
                }
            
            # Take profit hit
            if price >= target:
                return {
                    'signal': Signal.SELL,
                    'size': size,
                    'entry_price': entry,
                    'stop_loss': stop,
                    'take_profit': target,
                    'confidence': 1.0,
                    'reason': f'TAKE PROFIT: {price:.0f} >= {target:.0f} ({r_multiple:.1f}R)'
                }
            
            # Trailing stop
            if r_multiple >= self.config.trailing_activation:
                new_stop = entry + (price - entry) * self.config.trailing_percent
                if new_stop > stop:
                    result['stop_loss'] = new_stop
                    result['reason'] = f'Trailing stop: {stop:.0f} -> {new_stop:.0f} ({r_multiple:.1f}R)'
        
        else:  # SHORT
            risk = stop - entry
            if risk <= 0:
                return result
            r_multiple = (entry - price) / risk
            
            # Stop loss hit
            if price >= stop:
                return {
                    'signal': Signal.BUY,
                    'size': size,
                    'entry_price': entry,
                    'stop_loss': stop,
                    'take_profit': target,
                    'confidence': 1.0,
                    'reason': f'STOP LOSS: {price:.0f} >= {stop:.0f}'
                }
            
            # Take profit hit
            if price <= target:
                return {
                    'signal': Signal.BUY,
                    'size': size,
                    'entry_price': entry,
                    'stop_loss': stop,
                    'take_profit': target,
                    'confidence': 1.0,
                    'reason': f'TAKE PROFIT: {price:.0f} <= {target:.0f} ({r_multiple:.1f}R)'
                }
            
            # Trailing stop
            if r_multiple >= self.config.trailing_activation:
                new_stop = entry - (entry - price) * self.config.trailing_percent
                if new_stop < stop:
                    result['stop_loss'] = new_stop
                    result['reason'] = f'Trailing stop: {stop:.0f} -> {new_stop:.0f} ({r_multiple:.1f}R)'
        
        return result
    
    def record_trade(self, result: Dict):
        """Record trade result"""
        pnl = result.get('realized_pnl', 0)
        self.daily_pnl += pnl
        self.trades_today += 1
        
        if pnl > 0:
            self.wins_today += 1
            self.consecutive_losses = 0
        else:
            self.losses_today += 1
            self.consecutive_losses += 1
        
        self.last_trade_time = time.time()
    
    def reset_daily(self):
        """Reset daily stats at midnight"""
        self.trades_today = 0
        self.wins_today = 0
        self.losses_today = 0
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
    
    def get_stats(self) -> Dict:
        """Get strategy statistics"""
        win_rate = self.wins_today / self.trades_today if self.trades_today > 0 else 0
        return {
            'trades': self.trades_today,
            'wins': self.wins_today,
            'losses': self.losses_today,
            'win_rate': f'{win_rate:.0%}',
            'daily_pnl': f'${self.daily_pnl:.2f}',
            'consecutive_losses': self.consecutive_losses,
            'peak_balance': f'${self.peak_balance:.2f}',
            'trend': self.get_trend(),
            'ema_fast': f'{self.ema_fast:.2f}' if self.ema_fast else 'N/A',
            'ema_slow': f'{self.ema_slow:.2f}' if self.ema_slow else 'N/A'
        }


# Default instance
strategy = AggressiveStrategy()