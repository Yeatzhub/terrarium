"""
Toobit Trading Strategies
Grid, Momentum, and Arbitrage strategies for fast growth.
"""

import time
import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
from collections import deque

logger = logging.getLogger(__name__)


class StrategySignal:
    """Trading signal from strategy analysis"""
    BUY = 'BUY'
    SELL = 'SELL'
    HOLD = 'HOLD'
    
    def __init__(self, action: str, symbol: str, price: float,
                 confidence: float = 1.0, metadata: Optional[Dict] = None):
        self.action = action
        self.symbol = symbol
        self.price = price
        self.confidence = confidence  # 0.0 to 1.0
        self.metadata = metadata or {}
        self.timestamp = time.time()
    
    def __repr__(self):
        return f"Signal({self.action} {self.symbol} @ {self.price:.2f}, conf={self.confidence:.2f})"


class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
        self.is_active = True
        self.last_analysis_time = 0
        self.analysis_interval = config.get('update_interval', 10)
        self.min_confidence = config.get('min_confidence', 0.5)
    
    @abstractmethod
    def analyze(self, market_data: Dict[str, Any]) -> List[StrategySignal]:
        """Analyze market data and return trading signals"""
        pass
    
    @abstractmethod
    def execute(self, signal: StrategySignal, 
                executor: Any) -> bool:
        """Execute a trading signal"""
        pass
    
    def should_analyze(self) -> bool:
        """Check if enough time has passed since last analysis"""
        if time.time() - self.last_analysis_time >= self.analysis_interval:
            return True
        return False
    
    def _calculate_rsi(self, closes: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(closes) < period + 1:
            return 50.0
        
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [abs(d) if d < 0 else 0 for d in deltas[-period:]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_sma(self, data: List[float], period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(data) < period:
            return sum(data) / len(data) if data else 0
        return sum(data[-period:]) / period
    
    def _calculate_ema(self, data: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(data) < period:
            return self._calculate_sma(data, len(data))
        
        multiplier = 2 / (period + 1)
        ema = self._calculate_sma(data[:period], period)
        
        for price in data[period:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def _calculate_macd(self, closes: List[float], 
                       fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float, float]:
        """Calculate MACD indicator"""
        if len(closes) < slow + signal:
            return 0, 0, 0
        
        ema_fast = self._calculate_ema(closes, fast)
        ema_slow = self._calculate_ema(closes, slow)
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema(closes[-signal:], signal) if len(closes) >= signal else 0
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _calculate_bollinger_bands(self, closes: List[float], 
                                    period: int = 20, std: float = 2.0) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands"""
        if len(closes) < period:
            return closes[-1] if closes else 0, 0, 0
        
        sma = self._calculate_sma(closes, period)
        std_dev = np.std(closes[-period:])
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        return upper, sma, lower
    
    def _calculate_atr(self, highs: List[float], lows: List[float], 
                       closes: List[float], period: int = 14) -> float:
        """Calculate Average True Range"""
        if len(closes) < period + 1:
            return 0
        
        tr_list = []
        for i in range(1, len(closes)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            tr_list.append(max(tr1, tr2, tr3))
        
        return sum(tr_list[-period:]) / period
    
    def _calculate_volume_profile(self, volumes: List[float], 
                                   closes: List[float], levels: int = 10) -> Dict[float, float]:
        """Calculate volume profile"""
        if len(volumes) != len(closes) or not closes:
            return {}
        
        min_price = min(closes)
        max_price = max(closes)
        price_range = max_price - min_price
        
        if price_range == 0:
            return {closes[0]: sum(volumes)}
        
        level_size = price_range / levels
        profile = {}
        
        for price, vol in zip(closes, volumes):
            level = int((price - min_price) / level_size)
            level_price = min_price + (level + 0.5) * level_size
            profile[level_price] = profile.get(level_price, 0) + vol
        
        return profile


class GridStrategy(BaseStrategy):
    """
    Grid Trading Strategy
    Places buy/sell orders at regular intervals around current price.
    Optimized for volatile, ranging markets.
    
    Features:
    - Volatility-adjusted grid spacing
    - Trend-following grid repositioning
    - Dynamic profit taking
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.grid_levels = config.get('grid_levels', 10)
        self.grid_spacing_pct = config.get('grid_spacing_pct', 0.005)
        self.order_size = config.get('order_size', 100.0)
        self.max_grids = config.get('max_grids', 20)
        self.rebalance_threshold = config.get('rebalance_threshold', 0.02)
        
        # Fast growth features
        self.volatility_adjust = config.get('volatility_adjust', True)
        self.trend_following = config.get('trend_following', True)
        self.pyramiding = config.get('pyramiding', False)
        
        # State
        self.grids: Dict[str, Dict] = {}  # symbol -> grid state
        self.price_history: Dict[str, deque] = {}
    
    def analyze(self, market_data: Dict[str, Any]) -> List[StrategySignal]:
        """Analyze and generate grid trading signals"""
        signals = []
        
        for symbol, data in market_data.items():
            ticker = data.get('ticker', {})
            orderbook = data.get('orderbook', {})
            klines = data.get('klines', [])
            
            if not ticker or not klines:
                continue
            
            current_price = float(ticker.get('lastPrice', 0))
            if current_price == 0:
                continue
            
            # Initialize or update price history
            if symbol not in self.price_history:
                self.price_history[symbol] = deque(maxlen=100)
            self.price_history[symbol].append(current_price)
            
            # Calculate adjusted grid spacing based on volatility
            spacing = self._calculate_grid_spacing(symbol, current_price)
            
            # Get or create grid state
            if symbol not in self.grids:
                self.grids[symbol] = {
                    'center_price': current_price,
                    'last_rebalance': time.time(),
                    'buy_grids': [],
                    'sell_grids': []
                }
            
            grid = self.grids[symbol]
            
            # Check if grids need rebalancing (trend following)
            if self.trend_following:
                price_movement = abs(current_price - grid['center_price']) / grid['center_price']
                if price_movement > self.rebalance_threshold:
                    logger.info(f"[GRID] Rebalancing {symbol}: {price_movement:.2%} move")
                    grid['center_price'] = current_price
                    grid['buy_grids'] = []
                    grid['sell_grids'] = []
            
            # Generate grid levels
            buy_levels, sell_levels = self._calculate_grid_levels(
                grid['center_price'], spacing, self.grid_levels
            )
            
            # Check current price against grid levels
            for level in buy_levels:
                if current_price <= level and level not in grid['buy_grids']:
                    # Price hit buy grid
                    if len(grid['buy_grids']) < self.max_grids // 2:
                        signals.append(StrategySignal(
                            action=StrategySignal.BUY,
                            symbol=symbol,
                            price=current_price,
                            confidence=0.8,
                            metadata={
                                'grid_level': level,
                                'strategy': 'grid',
                                'size': self.order_size
                            }
                        ))
                        grid['buy_grids'].append(level)
                        break
            
            for level in sell_levels:
                if current_price >= level and level not in grid['sell_grids']:
                    # Price hit sell grid
                    if len(grid['sell_grids']) < self.max_grids // 2:
                        signals.append(StrategySignal(
                            action=StrategySignal.SELL,
                            symbol=symbol,
                            price=current_price,
                            confidence=0.8,
                            metadata={
                                'grid_level': level,
                                'strategy': 'grid',
                                'size': self.order_size
                            }
                        ))
                        grid['sell_grids'].append(level)
                        break
        
        self.last_analysis_time = time.time()
        return signals
    
    def execute(self, signal: StrategySignal, executor: Any) -> bool:
        """Execute grid trading signal"""
        try:
            size = signal.metadata.get('size', self.order_size)
            
            if signal.action == StrategySignal.BUY:
                if hasattr(executor, 'paper_buy'):
                    qty = size / signal.price
                    order, _ = executor.paper_buy(signal.symbol, qty)
                    return True
                else:
                    qty = size / signal.price
                    executor.place_order(signal.symbol, 'BUY', 'MARKET', qty)
                    return True
            
            elif signal.action == StrategySignal.SELL:
                # Check if we have position
                if hasattr(executor, 'get_position'):
                    position = executor.get_position(signal.symbol)
                    if position and position.quantity > 0:
                        qty = min(size / signal.price, position.quantity)
                        if hasattr(executor, 'paper_sell'):
                            order, _, _ = executor.paper_sell(signal.symbol, qty)
                        else:
                            executor.place_order(signal.symbol, 'SELL', 'MARKET', qty)
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"[GRID] Execution failed: {e}")
            return False
    
    def _calculate_grid_spacing(self, symbol: str, current_price: float) -> float:
        """Calculate dynamic grid spacing based on volatility"""
        base_spacing = self.grid_spacing_pct
        
        if not self.volatility_adjust or symbol not in self.price_history:
            return base_spacing
        
        prices = list(self.price_history[symbol])
        if len(prices) < 20:
            return base_spacing
        
        # Calculate recent volatility
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = np.std(returns)
        
        # Adjust spacing: wider in high volatility, tighter in low
        adjusted = base_spacing * (1 + volatility * 10)
        return max(adjusted, 0.002)  # Minimum 0.2% spacing
    
    def _calculate_grid_levels(self, center: float, spacing: float, levels: int) -> Tuple[List[float], List[float]]:
        """Calculate buy and sell grid levels"""
        buy_levels = [center * (1 - spacing * (i + 1)) for i in range(levels)]
        sell_levels = [center * (1 + spacing * (i + 1)) for i in range(levels)]
        return buy_levels, sell_levels


class MomentumStrategy(BaseStrategy):
    """
    Momentum Strategy
    Uses RSI, MACD, Bollinger Bands, and volume for signal generation.
    Optimized for trend-following and breakout capture.
    
    Features:
    - Multi-indicator confirmation
    - Volume-weighted signals
    - Adaptive thresholds
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rsi_period = config.get('rsi_period', 14)
        self.rsi_overbought = config.get('rsi_overbought', 70)
        self.rsi_oversold = config.get('rsi_oversold', 30)
        self.volume_threshold = config.get('volume_threshold', 1.5)
        self.price_change_threshold = config.get('price_change_threshold', 0.02)
        
        # MACD settings
        self.use_macd = config.get('use_macd', True)
        self.macd_fast = config.get('macd_fast', 12)
        self.macd_slow = config.get('macd_slow', 26)
        self.macd_signal = config.get('macd_signal', 9)
        
        # Bollinger settings
        self.use_bollinger = config.get('use_bollinger', True)
        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2.0)
        
        # Signal confirmation
        self.entry_confirmation = config.get('entry_confirmation', 2)
        
        # State
        self.pending_signals: Dict[str, List[StrategySignal]] = {}
        self.position_sizes: Dict[str, float] = {}
    
    def analyze(self, market_data: Dict[str, Any]) -> List[StrategySignal]:
        """Analyze and generate momentum signals"""
        signals = []
        
        for symbol, data in market_data.items():
            ticker = data.get('ticker', {})
            klines = data.get('klines', [])
            
            if not ticker or len(klines) < 30:
                continue
            
            # Parse klines
            opens = [float(k[1]) for k in klines]
            highs = [float(k[2]) for k in klines]
            lows = [float(k[3]) for k in klines]
            closes = [float(k[4]) for k in klines]
            volumes = [float(k[5]) for k in klines]
            
            current_price = float(ticker.get('lastPrice', closes[-1]))
            
            # Calculate indicators
            rsi = self._calculate_rsi(closes, self.rsi_period)
            macd_line, signal_line, histogram = self._calculate_macd(
                closes, self.macd_fast, self.macd_slow, self.macd_signal
            )
            bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
                closes, self.bb_period, self.bb_std
            )
            
            # Volume analysis
            avg_volume = np.mean(volumes[-20:])
            current_volume = volumes[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Price momentum
            price_change = (closes[-1] - closes[-5]) / closes[-5] if len(closes) > 5 else 0
            
            # Generate score for signal strength
            buy_score = 0
            sell_score = 0
            
            # RSI signals
            if rsi < self.rsi_oversold:
                buy_score += 2
            elif rsi > self.rsi_overbought:
                sell_score += 2
            
            # MACD signals
            if self.use_macd:
                if macd_line > signal_line and histogram > 0:
                    buy_score += 1
                elif macd_line < signal_line and histogram < 0:
                    sell_score += 1
            
            # Bollinger signals
            if self.use_bollinger:
                if current_price < bb_lower:
                    buy_score += 1
                elif current_price > bb_upper:
                    sell_score += 1
            
            # Volume confirmation
            if volume_ratio > self.volume_threshold:
                if price_change > 0:
                    buy_score += 1
                else:
                    sell_score += 1
            
            # Price momentum
            if abs(price_change) > self.price_change_threshold:
                if price_change > 0:
                    buy_score += 1
                else:
                    sell_score += 1
            
            # Generate signals based on score
            if buy_score >= self.entry_confirmation:
                confidence = min(buy_score / 5, 1.0)
                signal = StrategySignal(
                    action=StrategySignal.BUY,
                    symbol=symbol,
                    price=current_price,
                    confidence=confidence,
                    metadata={
                        'strategy': 'momentum',
                        'rsi': rsi,
                        'macd_hist': histogram,
                        'volume_ratio': volume_ratio,
                        'score': buy_score,
                        'bb_position': (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
                    }
                )
                
                # Handle confirmation requirement
                if self._confirm_signal(symbol, signal):
                    signals.append(signal)
            
            elif sell_score >= self.entry_confirmation:
                confidence = min(sell_score / 5, 1.0)
                signal = StrategySignal(
                    action=StrategySignal.SELL,
                    symbol=symbol,
                    price=current_price,
                    confidence=confidence,
                    metadata={
                        'strategy': 'momentum',
                        'rsi': rsi,
                        'macd_hist': histogram,
                        'volume_ratio': volume_ratio,
                        'score': sell_score,
                        'bb_position': (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
                    }
                )
                
                if self._confirm_signal(symbol, signal):
                    signals.append(signal)
        
        self.last_analysis_time = time.time()
        return signals
    
    def execute(self, signal: StrategySignal, executor: Any) -> bool:
        """Execute momentum signal"""
        try:
            # Calculate position size based on confidence
            base_size = 500.0  # Base position in USDT
            size = base_size * signal.confidence
            qty = size / signal.price
            
            if signal.action == StrategySignal.BUY:
                if hasattr(executor, 'paper_buy'):
                    order, _ = executor.paper_buy(signal.symbol, qty)
                else:
                    executor.place_order(signal.symbol, 'BUY', 'MARKET', qty)
                
                self.position_sizes[signal.symbol] = qty
                logger.info(f"[MOMENTUM BUY] {signal.symbol}: {qty:.6f} @ {signal.price:.2f} (conf: {signal.confidence:.2f})")
                return True
            
            elif signal.action == StrategySignal.SELL:
                # Get position size
                if hasattr(executor, 'get_position'):
                    position = executor.get_position(signal.symbol)
                    if position and position.quantity > 0:
                        qty = min(qty, position.quantity)
                        if hasattr(executor, 'paper_sell'):
                            order, _, pnl = executor.paper_sell(signal.symbol, qty)
                        else:
                            executor.place_order(signal.symbol, 'SELL', 'MARKET', qty)
                        
                        logger.info(f"[MOMENTUM SELL] {signal.symbol}: {qty:.6f} @ {signal.price:.2f}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"[MOMENTUM] Execution failed: {e}")
            return False
    
    def _confirm_signal(self, symbol: str, signal: StrategySignal) -> bool:
        """Confirm signal with multiple candle requirement"""
        if self.entry_confirmation <= 1:
            return True
        
        if symbol not in self.pending_signals:
            self.pending_signals[symbol] = []
        
        self.pending_signals[symbol].append(signal)
        
        # Keep only recent signals
        cutoff = time.time() - 300  # 5 minute window
        self.pending_signals[symbol] = [
            s for s in self.pending_signals[symbol] 
            if s.timestamp > cutoff
        ]
        
        # Count similar signals
        similar = sum(1 for s in self.pending_signals[symbol] 
                     if s.action == signal.action)
        
        return similar >= self.entry_confirmation


class ArbitrageStrategy(BaseStrategy):
    """
    Cross-Exchange Arbitrage Strategy
    Compares Toobit prices with other exchanges for arbitrage opportunities.
    
    Features:
    - Multi-exchange price monitoring
    - Fee-adjusted profit calculation
    - Slippage estimation
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.min_profit_pct = config.get('min_profit_pct', 0.001)
        self.max_trade_size = config.get('max_trade_size', 5000.0)
        self.exchanges = config.get('exchanges', ['binance', 'bybit', 'okx'])
        self.update_interval = config.get('update_interval', 5)
        
        # Simulated external prices (in production, fetch from other APIs)
        self.external_prices: Dict[str, Dict[str, float]] = {}
        self.last_external_update = 0
    
    def analyze(self, market_data: Dict[str, Any]) -> List[StrategySignal]:
        """Analyze for arbitrage opportunities"""
        signals = []
        
        # Update external prices periodically
        if time.time() - self.last_external_update > self.update_interval:
            self._update_external_prices(market_data)
        
        for symbol, data in market_data.items():
            ticker = data.get('ticker', {})
            if not ticker:
                continue
            
            toobit_price = float(ticker.get('lastPrice', 0))
            if toobit_price == 0:
                continue
            
            # Compare with other exchanges
            for exchange, prices in self.external_prices.items():
                if symbol not in prices:
                    continue
                
                external_price = prices[symbol]
                price_diff = (toobit_price - external_price) / external_price
                
                # Account for fees (0.1% each way + spread)
                estimated_fees = 0.002  # 0.2% round trip
                net_profit = abs(price_diff) - estimated_fees
                
                if net_profit > self.min_profit_pct:
                    if price_diff > 0:
                        # Toobit higher - sell on Toobit, buy elsewhere
                        signal = StrategySignal(
                            action=StrategySignal.SELL,
                            symbol=symbol,
                            price=toobit_price,
                            confidence=net_profit * 10,  # Scale confidence by profit
                            metadata={
                                'strategy': 'arbitrage',
                                'arbitrage_type': 'sell_toobit',
                                'exchange': exchange,
                                'external_price': external_price,
                                'price_diff_pct': price_diff * 100,
                                'net_profit_pct': net_profit * 100,
                                'max_size': self.max_trade_size
                            }
                        )
                    else:
                        # Toobit lower - buy on Toobit, sell elsewhere
                        signal = StrategySignal(
                            action=StrategySignal.BUY,
                            symbol=symbol,
                            price=toobit_price,
                            confidence=net_profit * 10,
                            metadata={
                                'strategy': 'arbitrage',
                                'arbitrage_type': 'buy_toobit',
                                'exchange': exchange,
                                'external_price': external_price,
                                'price_diff_pct': abs(price_diff) * 100,
                                'net_profit_pct': net_profit * 100,
                                'max_size': self.max_trade_size
                            }
                        )
                    
                    signals.append(signal)
        
        self.last_analysis_time = time.time()
        return signals
    
    def execute(self, signal: StrategySignal, executor: Any) -> bool:
        """Execute arbitrage signal"""
        try:
            max_size = signal.metadata.get('max_size', self.max_trade_size)
            qty = max_size / signal.price
            
            if signal.action == StrategySignal.BUY:
                if hasattr(executor, 'paper_buy'):
                    order, _ = executor.paper_buy(signal.symbol, qty)
                else:
                    executor.place_order(signal.symbol, 'BUY', 'MARKET', qty)
                
                profit_pct = signal.metadata.get('net_profit_pct', 0)
                logger.info(f"[ARBITRAGE BUY] {signal.symbol}: {qty:.6f} @ {signal.price:.2f} "
                           f"(expected profit: {profit_pct:.3f}%)")
                return True
            
            elif signal.action == StrategySignal.SELL:
                if hasattr(executor, 'get_position'):
                    position = executor.get_position(signal.symbol)
                    if position and position.quantity > 0:
                        qty = min(qty, position.quantity)
                        if hasattr(executor, 'paper_sell'):
                            order, _, _ = executor.paper_sell(signal.symbol, qty)
                        else:
                            executor.place_order(signal.symbol, 'SELL', 'MARKET', qty)
                        
                        profit_pct = signal.metadata.get('net_profit_pct', 0)
                        logger.info(f"[ARBITRAGE SELL] {signal.symbol}: {qty:.6f} @ {signal.price:.2f} "
                                   f"(expected profit: {profit_pct:.3f}%)")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"[ARBITRAGE] Execution failed: {e}")
            return False
    
    def _update_external_prices(self, market_data: Dict[str, Any]):
        """Update prices from external exchanges (simulated)"""
        # In production, this would fetch real prices from:
        # - Binance API
        # - Bybit API
        # - OKX API
        # - etc.
        
        # For simulation, add small random variations
        for symbol, data in market_data.items():
            ticker = data.get('ticker', {})
            base_price = float(ticker.get('lastPrice', 0))
            
            if base_price == 0:
                continue
            
            for exchange in self.exchanges:
                if exchange not in self.external_prices:
                    self.external_prices[exchange] = {}
                
                # Simulate price variation (-0.5% to +0.5%)
                variation = random.uniform(-0.005, 0.005)
                self.external_prices[exchange][symbol] = base_price * (1 + variation)
        
        self.last_external_update = time.time()


class MultiStrategy(BaseStrategy):
    """
    Multi-Strategy Wrapper
    Combines multiple strategies with weighting and conflict resolution.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Initialize sub-strategies
        self.strategies: Dict[str, BaseStrategy] = {}
        
        strategy_weights = config.get('strategy_weights', {
            'grid': 0.4,
            'momentum': 0.6
        })
        
        if strategy_weights.get('grid', 0) > 0:
            grid_config = config.get('grid_config', {})
            grid_config.update({'min_confidence': 0.6})
            self.strategies['grid'] = GridStrategy(grid_config)
        
        if strategy_weights.get('momentum', 0) > 0:
            momentum_config = config.get('momentum_config', {})
            momentum_config.update({'min_confidence': 0.7})
            self.strategies['momentum'] = MomentumStrategy(momentum_config)
        
        self.weights = strategy_weights
    
    def analyze(self, market_data: Dict[str, Any]) -> List[StrategySignal]:
        """Analyze using all strategies and combine signals"""
        all_signals = []
        
        # Collect signals from all strategies
        for name, strategy in self.strategies.items():
            if strategy.should_analyze():
                try:
                    signals = strategy.analyze(market_data)
                    for sig in signals:
                        sig.confidence *= self.weights.get(name, 1.0)
                    all_signals.extend(signals)
                except Exception as e:
                    logger.error(f"Strategy {name} failed: {e}")
        
        # Resolve conflicts (if buy and sell for same symbol)
        symbol_signals: Dict[str, List[StrategySignal]] = {}
        for sig in all_signals:
            if sig.symbol not in symbol_signals:
                symbol_signals[sig.symbol] = []
            symbol_signals[sig.symbol].append(sig)
        
        final_signals = []
        for symbol, sigs in symbol_signals.items():
            buys = [s for s in sigs if s.action == StrategySignal.BUY]
            sells = [s for s in sigs if s.action == StrategySignal.SELL]
            
            if buys and sells:
                # Conflict - choose by higher total confidence
                buy_conf = sum(s.confidence for s in buys)
                sell_conf = sum(s.confidence for s in sells)
                
                if buy_conf > sell_conf:
                    final_signals.append(max(buys, key=lambda s: s.confidence))
                else:
                    final_signals.append(max(sells, key=lambda s: s.confidence))
            elif buys:
                final_signals.append(max(buys, key=lambda s: s.confidence))
            elif sells:
                final_signals.append(max(sells, key=lambda s: s.confidence))
        
        return final_signals
    
    def execute(self, signal: StrategySignal, executor: Any) -> bool:
        """Route execution to appropriate strategy"""
        strategy_name = signal.metadata.get('strategy', 'momentum')
        
        if strategy_name in self.strategies:
            return self.strategies[strategy_name].execute(signal, executor)
        
        # Fallback to momentum execution
        return MomentumStrategy({}).execute(signal, executor)


# Strategy factory
def create_strategy(name: str, config: Dict[str, Any]) -> BaseStrategy:
    """Factory function to create strategy by name"""
    strategies = {
        'grid': GridStrategy,
        'momentum': MomentumStrategy,
        'arbitrage': ArbitrageStrategy,
        'multi': MultiStrategy
    }
    
    if name not in strategies:
        raise ValueError(f"Unknown strategy: {name}. Available: {list(strategies.keys())}")
    
    return strategies[name](config)
