#!/usr/bin/env python3
"""
Phase 2: Paper Trading Engine
Mean-reversion strategy for Polymarket crypto markets.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum

from market_discovery import Market, MarketDiscovery


class TradeDirection(Enum):
    """Trade direction."""
    YES = "yes"
    NO = "no"


class TradeStatus(Enum):
    """Trade status."""
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class Trade:
    """Represents a paper trade."""
    trade_id: str
    timestamp: str
    market_id: str
    question: str
    direction: str  # "yes" or "no"
    entry_price: float
    exit_price: Optional[float] = None
    position_size: float = 10.0  # $10 max per trade
    pnl: float = 0.0
    status: str = "open"  # "open" or "closed"
    is_winner: Optional[bool] = None
    
    def close(self, exit_price: float, is_winner: bool):
        """Close the trade and calculate P/L."""
        self.exit_price = exit_price
        self.status = "closed"
        self.is_winner = is_winner
        
        # Calculate P/L
        if self.direction == "yes":
            # If bought YES at entry, profit if exit > entry
            self.pnl = (exit_price - self.entry_price) * self.position_size
        else:
            # If bought NO at entry, profit if exit > entry (NO going up)
            self.pnl = (exit_price - self.entry_price) * self.position_size


@dataclass
class Position:
    """Represents an open position."""
    market_id: str
    question: str
    direction: str
    entry_price: float
    entry_time: str
    size: float = 10.0


class Portfolio:
    """Manages paper trading portfolio state."""
    
    PORTFOLIO_FILE = "polymarket_paper_trader/portfolio.json"
    
    def __init__(self, initial_balance: float = 1000.0):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions: Dict[str, Position] = {}  # market_id -> Position
        self.trade_history: List[Trade] = []
        self.consecutive_losses = 0
        self.total_pnl = 0.0
        self.circuit_breaker_triggered = False
        
        self.load()
    
    def load(self):
        """Load portfolio from JSON file."""
        if os.path.exists(self.PORTFOLIO_FILE):
            try:
                with open(self.PORTFOLIO_FILE, 'r') as f:
                    data = json.load(f)
                self.balance = data.get('balance', self.initial_balance)
                self.positions = {
                    k: Position(**v) for k, v in data.get('positions', {}).items()
                }
                self.consecutive_losses = data.get('consecutive_losses', 0)
                self.total_pnl = data.get('total_pnl', 0.0)
                self.circuit_breaker_triggered = data.get('circuit_breaker_triggered', False)
                
                # Reconstruct trade history
                self.trade_history = [
                    Trade(**t) for t in data.get('trade_history', [])
                ]
            except Exception as e:
                print(f"Error loading portfolio: {e}. Starting fresh.")
                self.reset()
    
    def save(self):
        """Save portfolio to JSON file."""
        data = {
            'balance': self.balance,
            'initial_balance': self.initial_balance,
            'positions': {
                k: {
                    'market_id': v.market_id,
                    'question': v.question,
                    'direction': v.direction,
                    'entry_price': v.entry_price,
                    'entry_time': v.entry_time,
                    'size': v.size
                } for k, v in self.positions.items()
            },
            'trade_history': [
                {
                    'trade_id': t.trade_id,
                    'timestamp': t.timestamp,
                    'market_id': t.market_id,
                    'question': t.question,
                    'direction': t.direction,
                    'entry_price': t.entry_price,
                    'exit_price': t.exit_price,
                    'position_size': t.position_size,
                    'pnl': t.pnl,
                    'status': t.status,
                    'is_winner': t.is_winner
                } for t in self.trade_history
            ],
            'consecutive_losses': self.consecutive_losses,
            'total_pnl': self.total_pnl,
            'circuit_breaker_triggered': self.circuit_breaker_triggered
        }
        os.makedirs(os.path.dirname(self.PORTFOLIO_FILE), exist_ok=True)
        with open(self.PORTFOLIO_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    def reset(self):
        """Reset portfolio to initial state."""
        self.balance = self.initial_balance
        self.positions.clear()
        self.trade_history.clear()
        self.consecutive_losses = 0
        self.total_pnl = 0.0
        self.circuit_breaker_triggered = False
        self.save()
    
    def get_win_rate(self) -> float:
        """Calculate win rate percentage."""
        closed_trades = [t for t in self.trade_history if t.status == "closed"]
        if not closed_trades:
            return 0.0
        winners = [t for t in closed_trades if t.is_winner]
        return len(winners) / len(closed_trades) * 100
    
    def get_recent_trades(self, n: int = 10) -> List[Trade]:
        """Get N most recent trades."""
        return sorted(self.trade_history, key=lambda x: x.timestamp, reverse=True)[:n]


class TrendAnalyzer:
    """Analyzes market trends for entry/exit signals."""
    
    def __init__(self, price_history: Dict[str, List[float]] = None):
        self.price_history = price_history or {}
    
    def update_price(self, market_id: str, price: float):
        """Record a price update."""
        if market_id not in self.price_history:
            self.price_history[market_id] = []
        self.price_history[market_id].append(price)
        # Keep only last 50 prices
        self.price_history[market_id] = self.price_history[market_id][-50:]
    
    def is_uptrend(self, market_id: str, period: int = 5) -> bool:
        """Check if market is in uptrend over last N prices."""
        prices = self.price_history.get(market_id, [])
        if len(prices) < period:
            return prices[-1] > prices[0] if len(prices) >= 2 else True
        
        recent = prices[-period:]
        return sum(recent) / len(recent) > prices[-period]
    
    def is_downtrend(self, market_id: str, period: int = 5) -> bool:
        """Check if market is in downtrend over last N prices."""
        prices = self.price_history.get(market_id, [])
        if len(prices) < period:
            return prices[-1] < prices[0] if len(prices) >= 2 else False
        
        recent = prices[-period:]
        return sum(recent) / len(recent) < prices[-period]


class MeanReversionTrader:
    """
    Mean-reversion trading strategy.
    
    Strategy rules:
    - For "Will X go Up" markets:
      * BUY YES when price < 0.40 AND in uptrend
      * SELL when YES price > 0.60
    - Position size: $10 max per trade
    - Circuit breaker: Stop after 3 consecutive losses
    """
    
    # Strategy parameters
    BUY_THRESHOLD = 0.40  # Buy YES when below this
    SELL_THRESHOLD = 0.60  # Sell when YES above this
    POSITION_SIZE = 10.0  # Max $10 per trade
    MAX_CONSECUTIVE_LOSSES = 3
    
    def __init__(self, portfolio: Optional[Portfolio] = None):
        self.portfolio = portfolio or Portfolio()
        self.trend_analyzer = TrendAnalyzer()
        self.price_tracking: Dict[str, float] = {}
    
    def should_buy(self, market: Market, direction: str = "yes") -> Tuple[bool, str]:
        """
        Check if we should buy.
        Returns (should_buy, reason)
        """
        # Check circuit breaker
        if self.portfolio.consecutive_losses >= self.MAX_CONSECUTIVE_LOSSES:
            return False, "Circuit breaker triggered"
        
        # Check if already have position
        if market.market_id in self.portfolio.positions:
            return False, "Already have position"
        
        # Check balance
        if self.portfolio.balance < self.POSITION_SIZE:
            return False, "Insufficient balance"
        
        # Mean-reversion: buy YES when cheap and trending up
        if market.yes_price < self.BUY_THRESHOLD:
            self.trend_analyzer.update_price(market.market_id, market.yes_price)
            if self.trend_analyzer.is_uptrend(market.market_id):
                return True, f"YES price {market.yes_price:.4f} < {self.BUY_THRESHOLD} + uptrend"
            return False, f"YES price {market.yes_price:.4f} < threshold but no uptrend"
        
        return False, f"YES price {market.yes_price:.4f} >= threshold {self.BUY_THRESHOLD}"
    
    def should_sell(self, market: Market, direction: str = "yes") -> Tuple[bool, str]:
        """
        Check if we should sell/exit position.
        Returns (should_sell, reason)
        """
        # Check if we have a position
        position = self.portfolio.positions.get(market.market_id)
        if not position:
            return False, "No position to sell"
        
        # Mean-reversion: sell YES when expensive
        if market.yes_price > self.SELL_THRESHOLD:
            return True, f"YES price {market.yes_price:.4f} > {self.SELL_THRESHOLD}"
        
        return False, f"Holding position, YES price {market.yes_price:.4f}"
    
    def execute_buy(self, market: Market, direction: str = "yes") -> Optional[Trade]:
        """Execute a paper buy order."""
        should_buy, reason = self.should_buy(market, direction)
        if not should_buy:
            return None
        
        trade_id = f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{market.market_id}"
        timestamp = datetime.now().isoformat()
        
        trade = Trade(
            trade_id=trade_id,
            timestamp=timestamp,
            market_id=market.market_id,
            question=market.question,
            direction=direction,
            entry_price=market.yes_price if direction == "yes" else market.no_price,
            position_size=self.POSITION_SIZE,
            status="open"
        )
        
        position = Position(
            market_id=market.market_id,
            question=market.question,
            direction=direction,
            entry_price=market.yes_price if direction == "yes" else market.no_price,
            entry_time=timestamp,
            size=self.POSITION_SIZE
        )
        
        # Update portfolio
        self.portfolio.positions[market.market_id] = position
        self.portfolio.balance -= self.POSITION_SIZE
        self.portfolio.trade_history.append(trade)
        self.portfolio.save()
        
        return trade
    
    def execute_sell(self, market: Market) -> Optional[Trade]:
        """Execute a paper sell order."""
        should_sell, reason = self.should_sell(market)
        if not should_sell:
            return None
        
        position = self.portfolio.positions.get(market.market_id)
        if not position:
            return None
        
        # Find the open trade
        open_trade = None
        for trade in reversed(self.portfolio.trade_history):
            if trade.market_id == market.market_id and trade.status == "open":
                open_trade = trade
                break
        
        if not open_trade:
            return None
        
        # Calculate exit
        exit_price = market.yes_price if position.direction == "yes" else market.no_price
        
        # Determine if winner (simplified: profit > 0)
        if position.direction == "yes":
            pnl = (exit_price - position.entry_price) * position.size
        else:
            pnl = (exit_price - position.entry_price) * position.size
        
        is_winner = pnl > 0
        
        # Close the trade
        open_trade.close(exit_price, is_winner)
        
        # Update portfolio
        del self.portfolio.positions[market.market_id]
        self.portfolio.balance += position.size + pnl
        self.portfolio.total_pnl += pnl
        
        if is_winner:
            self.portfolio.consecutive_losses = 0
        else:
            self.portfolio.consecutive_losses += 1
        
        if self.portfolio.consecutive_losses >= self.MAX_CONSECUTIVE_LOSSES:
            self.portfolio.circuit_breaker_triggered = True
        
        self.portfolio.save()
        
        return open_trade
    
    def get_status(self) -> Dict:
        """Get trader status summary."""
        return {
            'balance': self.portfolio.balance,
            'initial_balance': self.portfolio.initial_balance,
            'total_pnl': self.portfolio.total_pnl,
            'open_positions': len(self.portfolio.positions),
            'total_trades': len(self.portfolio.trade_history),
            'win_rate': self.portfolio.get_win_rate(),
            'consecutive_losses': self.portfolio.consecutive_losses,
            'circuit_breaker': self.portfolio.circuit_breaker_triggered,
            'positions': [
                {
                    'market_id': p.market_id,
                    'question': p.question,
                    'direction': p.direction,
                    'entry_price': p.entry_price
                }
                for p in self.portfolio.positions.values()
            ]
        }


def main():
    """Test the trading engine."""
    print("=" * 70)
    print("PAPER TRADING ENGINE TEST")
    print("=" * 70)
    
    # Initialize trader
    trader = MeanReversionTrader()
    
    # Get current status
    print("\nInitial Portfolio Status:")
    status = trader.get_status()
    print(f"Balance: ${status['balance']:.2f}")
    print(f"Open Positions: {status['open_positions']}")
    print(f"Total P/L: ${status['total_pnl']:.2f}")
    print(f"Consecutive Losses: {status['consecutive_losses']}")
    print(f"Circuit Breaker: {'TRIGGERED' if status['circuit_breaker'] else 'OFF'}")
    
    # Discover markets
    print("\n" + "-" * 70)
    print("DISCOVERING MARKETS...")
    "-" * 70
    discovery = MarketDiscovery()
    markets = discovery.get_crypto_up_down_markets(limit=100)
    
    if not markets:
        print("No crypto Up/Down markets found, checking general crypto markets...")
        markets = discovery.get_crypto_markets(limit=100)
    
    print(f"\nFound {len(markets)} tradable markets")
    
    # Evaluate each for trading signals
    print("\n" + "-" * 70)
    print("EVALUATING TRADING SIGNALS")
    print("-" * 70)
    
    for market in markets[:5]:
        print(f"\n{market.question[:60]}...")
        print(f"  YES: ${market.yes_price:.4f} | NO: ${market.no_price:.4f}")
        
        # Track price
        trader.trend_analyzer.update_price(market.market_id, market.yes_price)
        
        # Check buy signal
        should_buy, buy_reason = trader.should_buy(market)
        print(f"  BUY Signal: {'YES' if should_buy else 'NO'} - {buy_reason}")
        
        # Check sell signal (if we had a position)
        should_sell, sell_reason = trader.should_sell(market)
        print(f"  SELL Signal: {'YES' if should_sell else 'NO'} - {sell_reason}")
    
    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
