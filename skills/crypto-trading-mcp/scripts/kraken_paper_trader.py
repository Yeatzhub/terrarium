"""
Kraken Paper Trading Engine
Simulates trading on Kraken without real money.
"""

import json
import time
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class PaperPosition:
    """Paper trading position"""
    symbol: str
    side: str
    size: float
    entry_price: float
    fees: float = 0.0
    opened_at: float = field(default_factory=time.time)
    
    def current_pnl(self, current_price: float) -> float:
        if self.side == 'long':
            return (current_price - self.entry_price) * self.size - self.fees
        return (self.entry_price - current_price) * self.size - self.fees


@dataclass
class PaperTrade:
    """Paper trade record"""
    symbol: str
    side: str
    type: str
    size: float
    price: float
    value: float
    fees: float
    pnl: float = 0.0
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'side': self.side,
            'type': self.type,
            'size': self.size,
            'price': self.price,
            'value': self.value,
            'fees': self.fees,
            'pnl': self.pnl,
            'timestamp': self.timestamp,
            'datetime': datetime.fromtimestamp(self.timestamp).isoformat()
        }


class PaperAccount:
    """Paper trading account"""
    
    MAKER_FEE = 0.0016  # 0.16%
    TAKER_FEE = 0.0026  # 0.26%
    SLIPPAGE_PCT = 0.001  # 0.1%
    
    def __init__(self, initial_balance: float = 10000.0, state_file: str = 'kraken_paper_state.json'):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.state_file = state_file
        self.positions: Dict[str, PaperPosition] = {}
        self.orders: List[Dict] = []
        self.trades: List[PaperTrade] = []
        self.total_fees = 0.0
        self.realized_pnl = 0.0
        self.load_state()
        logger.info(f"PaperAccount: ${self.balance:.2f}")
    
    def save_state(self):
        state = {
            'balance': self.balance,
            'initial_balance': self.initial_balance,
            'realized_pnl': self.realized_pnl,
            'total_fees': self.total_fees,
            'positions': {s: {'symbol': p.symbol, 'side': p.side, 'size': p.size,
                            'entry_price': p.entry_price, 'fees': p.fees, 'opened_at': p.opened_at}
                         for s, p in self.positions.items()},
            'orders': self.orders,
            'trades': [t.to_dict() for t in self.trades],
            'timestamp': time.time()
        }
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Save failed: {e}")
    
    def load_state(self):
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            self.balance = state.get('balance', self.initial_balance)
            self.realized_pnl = state.get('realized_pnl', 0.0)
            self.total_fees = state.get('total_fees', 0.0)
            for s, d in state.get('positions', {}).items():
                self.positions[s] = PaperPosition(**d)
            self.orders = state.get('orders', [])
        except FileNotFoundError:
            pass
    
    def place_paper_order(self, symbol: str, side: str, order_type: str,
                         quantity: float, price: Optional[float] = None,
                         current_price: float = None) -> Dict:
        if current_price is None and order_type == 'market':
            raise ValueError("current_price required")
        
        fill_price = current_price * (1 + self.SLIPPAGE_PCT) if side == 'buy' and order_type == 'market' else \
                     current_price * (1 - self.SLIPPAGE_PCT) if order_type == 'market' else price
        
        value = fill_price * quantity
        fee_rate = self.TAKER_FEE if order_type == 'market' else self.MAKER_FEE
        fees = value * fee_rate
        
        if side == 'buy':
            if value + fees > self.balance:
                return {'success': False, 'error': 'Insufficient balance', 'required': value + fees, 'available': self.balance}
            
            self.balance -= (value + fees)
            self.total_fees += fees
            
            if symbol in self.positions:
                p = self.positions[symbol]
                total = p.size + quantity
                p.entry_price = (p.entry_price * p.size + fill_price * quantity) / total
                p.size = total
                p.fees += fees
            else:
                self.positions[symbol] = PaperPosition(symbol, 'long', quantity, fill_price, fees)
            
            self.trades.append(PaperTrade(symbol, 'buy', order_type, quantity, fill_price, value, fees))
            logger.info(f"BUY {quantity} {symbol} @ {fill_price:.2f}")
        
        elif side == 'sell':
            if symbol not in self.positions:
                return {'success': False, 'error': 'No position'}
            
            p = self.positions[symbol]
            gross_pnl = (fill_price - p.entry_price) * min(quantity, p.size)
            self.total_fees += fees
            net_pnl = gross_pnl - fees
            self.realized_pnl += net_pnl
            self.balance += fill_price * quantity
            
            if quantity >= p.size:
                del self.positions[symbol]
            else:
                p.size -= quantity
            
            self.trades.append(PaperTrade(symbol, 'sell', order_type, quantity, fill_price, fill_price * quantity, fees, net_pnl))
            logger.info(f"SELL {quantity} {symbol} @ {fill_price:.2f} PnL: ${net_pnl:.2f}")
        
        self.save_state()
        return {'success': True, 'symbol': symbol, 'side': side, 'price': fill_price, 'value': value,
                'fees': fees, 'balance': self.balance, 'realized_pnl': self.realized_pnl}
    
    def get_summary(self, prices: Optional[Dict[str, float]] = None) -> Dict:
        unrealized = sum(p.current_pnl(prices[s]) for s, p in self.positions.items() if prices and s in prices)
        pos_value = sum(p.size * prices.get(s, 0) for s, p in self.positions.items())
        total_value = self.balance + pos_value
        total_return = ((total_value / self.initial_balance) - 1) * 100 if self.initial_balance > 0 else 0
        completed = [t for t in self.trades if t.side == 'sell' and t.pnl != 0]
        win_rate = len([t for t in completed if t.pnl > 0]) / len(completed) * 100 if completed else 0
        
        return {
            'balance': self.balance, 'initial_balance': self.initial_balance,
            'position_value': pos_value, 'total_value': total_value,
            'realized_pnl': self.realized_pnl, 'unrealized_pnl': unrealized,
            'total_return_pct': total_return, 'open_positions': len(self.positions),
            'trades_count': len(self.trades), 'win_rate': win_rate,
            'positions': {s: {'size': p.size, 'entry': p.entry_price, 'side': p.side} for s, p in self.positions.items()}
        }
