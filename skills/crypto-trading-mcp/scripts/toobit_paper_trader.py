"""
Toobit Paper Trading Simulation Engine
Realistic paper trading with fee simulation and slippage.
"""

import json
import time
import logging
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PaperPosition:
    """Represents a paper trading position"""
    symbol: str
    side: str  # 'LONG' or 'SHORT'
    entry_price: float
    quantity: float
    entry_time: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    
    @property
    def position_value(self) -> float:
        """Current position value in quote currency"""
        return self.quantity * self.entry_price
    
    def update_pnl(self, current_price: float):
        """Update unrealized P&L"""
        if self.side == 'LONG':
            self.unrealized_pnl = (current_price - self.entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.entry_price - current_price) * self.quantity
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'side': self.side,
            'entry_price': self.entry_price,
            'quantity': self.quantity,
            'entry_time': self.entry_time,
            'unrealized_pnl': self.unrealized_pnl,
            'realized_pnl': self.realized_pnl
        }


@dataclass
class PaperOrder:
    """Represents a paper trading order"""
    order_id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    type: str  # 'LIMIT' or 'MARKET'
    quantity: float
    price: Optional[float]
    status: str = 'OPEN'  # 'OPEN', 'FILLED', 'CANCELLED', 'PARTIAL'
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    created_at: float = 0.0
    filled_at: Optional[float] = None
    fee_paid: float = 0.0
    
    @property
    def is_filled(self) -> bool:
        return self.status == 'FILLED' and self.filled_quantity >= self.quantity
    
    @property
    def remaining_quantity(self) -> float:
        return self.quantity - self.filled_quantity
    
    def to_dict(self) -> Dict:
        return {
            'order_id': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'type': self.type,
            'quantity': self.quantity,
            'price': self.price,
            'status': self.status,
            'filled_quantity': self.filled_quantity,
            'filled_price': self.filled_price,
            'created_at': self.created_at,
            'filled_at': self.filled_at,
            'fee_paid': self.fee_paid
        }


@dataclass
class PaperTrade:
    """Represents a completed paper trade"""
    trade_id: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    fee: float
    pnl: float
    timestamp: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PaperAccount:
    """
    Paper Trading Account Simulation
    
    Features:
    - Realistic fee simulation (0.1% maker/taker)
    - Slippage simulation for market orders
    - Position tracking
    - Order management
    - Trade history
    - P&L calculation
    - State persistence to JSON
    """
    
    # Trading fees (Toobit-like)
    MAKER_FEE = 0.001  # 0.1%
    TAKER_FEE = 0.001  # 0.1%
    
    # Slippage parameters
    SLIPPAGE_BASE = 0.0005  # 0.05% base slippage
    SLIPPAGE_VOLATILITY = 0.001  # 0.1% volatility-based
    
    def __init__(self, initial_balance: float = 10000.0,
                 state_file: str = 'toobit_paper_state.json',
                 base_currency: str = 'USDT'):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.base_currency = base_currency
        self.state_file = Path(state_file)
        
        # Account state
        self.positions: Dict[str, PaperPosition] = {}
        self.orders: Dict[str, PaperOrder] = {}
        self.trade_history: List[PaperTrade] = []
        
        # Order ID counter
        self._order_counter = 0
        self._trade_counter = 0
        
        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.total_fees_paid = 0.0
        self.total_pnl = 0.0
        
        # Load state if exists
        self._load_state()
        
        logger.info(f"PaperAccount initialized: {self.balance:.2f} {base_currency}")
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID"""
        self._order_counter += 1
        return f"PAPER_{int(time.time())}_{self._order_counter}"
    
    def _generate_trade_id(self) -> str:
        """Generate unique trade ID"""
        self._trade_counter += 1
        return f"TRADE_{int(time.time())}_{self._trade_counter}"
    
    def _calculate_slippage(self, side: str, orderbook: Optional[Dict] = None) -> float:
        """Calculate realistic slippage for market orders"""
        base_slippage = self.SLIPPAGE_BASE
        
        # Add random component based on volatility
        random_slippage = random.uniform(0, self.SLIPPAGE_VOLATILITY)
        
        # Direction based on side
        if side == 'BUY':
            slippage = base_slippage + random_slippage
        else:
            slippage = -(base_slippage + random_slippage)
        
        return slippage
    
    def _calculate_fee(self, quantity: float, price: float, is_maker: bool = False) -> float:
        """Calculate trading fee"""
        fee_rate = self.MAKER_FEE if is_maker else self.TAKER_FEE
        trade_value = quantity * price
        return trade_value * fee_rate
    
    def paper_buy(self, symbol: str, quantity: float, 
                  price: Optional[float] = None,
                  orderbook: Optional[Dict] = None) -> Tuple[PaperOrder, float]:
        """
        Execute paper buy order
        
        Args:
            symbol: Trading pair
            quantity: Amount to buy
            price: Limit price (None for market order)
            orderbook: Current orderbook for slippage calc
        
        Returns:
            (order, execution_price)
        """
        order_type = 'LIMIT' if price else 'MARKET'
        
        # Calculate execution price
        if price:
            # Limit order - executes at limit price or better
            execution_price = price
            is_maker = True
        else:
            # Market order - apply slippage
            slippage = self._calculate_slippage('BUY', orderbook)
            
            # Get reference price from orderbook or simulate
            if orderbook and 'asks' in orderbook and orderbook['asks']:
                ref_price = float(orderbook['asks'][0][0])
            else:
                ref_price = 50000.0  # Fallback
            
            execution_price = ref_price * (1 + abs(slippage))
            is_maker = False
        
        # Check balance
        total_cost = quantity * execution_price
        fee = self._calculate_fee(quantity, execution_price, is_maker)
        total_required = total_cost + fee
        
        if total_required > self.balance:
            raise ValueError(f"Insufficient balance: {self.balance:.2f} < {total_required:.2f}")
        
        # Create order
        order = PaperOrder(
            order_id=self._generate_order_id(),
            symbol=symbol,
            side='BUY',
            type=order_type,
            quantity=quantity,
            price=price,
            status='FILLED',
            filled_quantity=quantity,
            filled_price=execution_price,
            created_at=time.time(),
            filled_at=time.time(),
            fee_paid=fee
        )
        
        # Update balance
        self.balance -= total_required
        
        # Update or create position
        if symbol in self.positions:
            pos = self.positions[symbol]
            # Average down
            total_qty = pos.quantity + quantity
            pos.entry_price = (pos.quantity * pos.entry_price + quantity * execution_price) / total_qty
            pos.quantity = total_qty
            pos.entry_time = time.time()
        else:
            self.positions[symbol] = PaperPosition(
                symbol=symbol,
                side='LONG',
                entry_price=execution_price,
                quantity=quantity,
                entry_time=time.time()
            )
        
        # Record trade
        trade = PaperTrade(
            trade_id=self._generate_trade_id(),
            order_id=order.order_id,
            symbol=symbol,
            side='BUY',
            quantity=quantity,
            price=execution_price,
            fee=fee,
            pnl=0.0,
            timestamp=time.time()
        )
        self.trade_history.append(trade)
        
        # Update stats
        self.total_trades += 1
        self.total_fees_paid += fee
        self.orders[order.order_id] = order
        
        logger.info(f"[PAPER BUY] {symbol}: {quantity} @ {execution_price:.2f} (fee: {fee:.4f})")
        
        self._save_state()
        return order, execution_price
    
    def paper_sell(self, symbol: str, quantity: float,
                   price: Optional[float] = None,
                   orderbook: Optional[Dict] = None) -> Tuple[PaperOrder, float, float]:
        """
        Execute paper sell order
        
        Args:
            symbol: Trading pair
            quantity: Amount to sell
            price: Limit price (None for market order)
            orderbook: Current orderbook for slippage calc
        
        Returns:
            (order, execution_price, realized_pnl)
        """
        order_type = 'LIMIT' if price else 'MARKET'
        
        # Check position
        if symbol not in self.positions:
            raise ValueError(f"No position in {symbol} to sell")
        
        position = self.positions[symbol]
        if quantity > position.quantity:
            raise ValueError(f"Insufficient position: {position.quantity:.6f} < {quantity:.6f}")
        
        # Calculate execution price
        if price:
            execution_price = price
            is_maker = True
        else:
            slippage = self._calculate_slippage('SELL', orderbook)
            
            if orderbook and 'bids' in orderbook and orderbook['bids']:
                ref_price = float(orderbook['bids'][0][0])
            else:
                ref_price = position.entry_price
            
            execution_price = ref_price * (1 - abs(slippage))
            is_maker = False
        
        # Calculate P&L
        cost_basis = quantity * position.entry_price
        proceeds = quantity * execution_price
        fee = self._calculate_fee(quantity, execution_price, is_maker)
        net_proceeds = proceeds - fee
        
        realized_pnl = net_proceeds - cost_basis
        
        # Create order
        order = PaperOrder(
            order_id=self._generate_order_id(),
            symbol=symbol,
            side='SELL',
            type=order_type,
            quantity=quantity,
            price=price,
            status='FILLED',
            filled_quantity=quantity,
            filled_price=execution_price,
            created_at=time.time(),
            filled_at=time.time(),
            fee_paid=fee
        )
        
        # Update balance
        self.balance += net_proceeds
        
        # Update position
        position.quantity -= quantity
        position.realized_pnl += realized_pnl
        
        if position.quantity <= 0.00001:  # Close position if negligible
            del self.positions[symbol]
        
        # Record trade
        trade = PaperTrade(
            trade_id=self._generate_trade_id(),
            order_id=order.order_id,
            symbol=symbol,
            side='SELL',
            quantity=quantity,
            price=execution_price,
            fee=fee,
            pnl=realized_pnl,
            timestamp=time.time()
        )
        self.trade_history.append(trade)
        
        # Update stats
        self.total_trades += 1
        if realized_pnl > 0:
            self.winning_trades += 1
        self.total_fees_paid += fee
        self.total_pnl += realized_pnl
        self.orders[order.order_id] = order
        
        logger.info(f"[PAPER SELL] {symbol}: {quantity} @ {execution_price:.2f} (PNL: {realized_pnl:.2f}, fee: {fee:.4f})")
        
        self._save_state()
        return order, execution_price, realized_pnl
    
    def get_pnl(self, current_prices: Optional[Dict[str, float]] = None) -> Dict:
        """Get comprehensive P&L statistics"""
        realized_pnl = self.total_pnl
        unrealized_pnl = 0.0
        
        if current_prices:
            for symbol, position in self.positions.items():
                if symbol in current_prices:
                    position.update_pnl(current_prices[symbol])
                    unrealized_pnl += position.unrealized_pnl
        
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        return {
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unrealized_pnl,
            'total_pnl': realized_pnl + unrealized_pnl,
            'total_fees': self.total_fees_paid,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'win_rate': win_rate,
            'current_balance': self.balance,
            'initial_balance': self.initial_balance,
            'return_pct': ((self.balance + unrealized_pnl - self.initial_balance) / self.initial_balance * 100)
        }
    
    def get_positions(self) -> Dict[str, Dict]:
        """Get all current positions"""
        return {symbol: pos.to_dict() for symbol, pos in self.positions.items()}
    
    def get_position(self, symbol: str) -> Optional[PaperPosition]:
        """Get specific position"""
        return self.positions.get(symbol)
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order"""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status == 'OPEN':
                order.status = 'CANCELLED'
                self._save_state()
                logger.info(f"[PAPER CANCEL] Order {order_id} cancelled")
                return True
        return False
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[PaperOrder]:
        """Get open orders"""
        orders = [o for o in self.orders.values() if o.status == 'OPEN']
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders
    
    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """Get recent trade history"""
        return [t.to_dict() for t in self.trade_history[-limit:]]
    
    def reset(self):
        """Reset account to initial state"""
        self.balance = self.initial_balance
        self.positions = {}
        self.orders = {}
        self.trade_history = []
        self.total_trades = 0
        self.winning_trades = 0
        self.total_fees_paid = 0.0
        self.total_pnl = 0.0
        self._order_counter = 0
        self._trade_counter = 0
        
        # Delete state file
        if self.state_file.exists():
            self.state_file.unlink()
        
        logger.info("Paper account reset")
    
    def _save_state(self):
        """Persist state to JSON file"""
        state = {
            'balance': self.balance,
            'initial_balance': self.initial_balance,
            'base_currency': self.base_currency,
            'positions': {s: p.to_dict() for s, p in self.positions.items()},
            'orders': {oid: o.to_dict() for oid, o in self.orders.items()},
            'trade_history': [t.to_dict() for t in self.trade_history[-1000:]],  # Keep last 1000
            'stats': {
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'total_fees_paid': self.total_fees_paid,
                'total_pnl': self.total_pnl
            },
            'saved_at': datetime.now().isoformat()
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def _load_state(self):
        """Load state from JSON file"""
        if not self.state_file.exists():
            return
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            self.balance = state.get('balance', self.initial_balance)
            self.initial_balance = state.get('initial_balance', self.initial_balance)
            self.base_currency = state.get('base_currency', self.base_currency)
            
            # Load positions
            self.positions = {}
            for symbol, pos_data in state.get('positions', {}).items():
                self.positions[symbol] = PaperPosition(**pos_data)
            
            # Load orders
            self.orders = {}
            for oid, order_data in state.get('orders', {}).items():
                self.orders[oid] = PaperOrder(**order_data)
            
            # Load trade history
            self.trade_history = [
                PaperTrade(**t) for t in state.get('trade_history', [])
            ]
            
            # Load stats
            stats = state.get('stats', {})
            self.total_trades = stats.get('total_trades', 0)
            self.winning_trades = stats.get('winning_trades', 0)
            self.total_fees_paid = stats.get('total_fees_paid', 0.0)
            self.total_pnl = stats.get('total_pnl', 0.0)
            
            logger.info(f"Loaded state: {self.balance:.2f} {self.base_currency}, "
                       f"{len(self.positions)} positions, {len(self.orders)} orders")
            
        except Exception as e:
            logger.error(f"Failed to load state: {e}. Starting fresh.")
    
    def get_summary(self) -> str:
        """Get formatted account summary"""
        pnl = self.get_pnl()
        
        summary = f"""
╔════════════════════════════════════════════════════════╗
║           PAPER TRADING ACCOUNT SUMMARY                ║
╠════════════════════════════════════════════════════════╣
║ Balance: {self.balance:>12.2f} {self.base_currency:<10}           ║
║ Initial: {self.initial_balance:>12.2f} {self.base_currency:<10}           ║
╠════════════════════════════════════════════════════════╣
║ Realized PnL:   {pnl['realized_pnl']:>10.2f} ({pnl['return_pct']:+.2f}%)       ║
║ Total Fees:     {pnl['total_fees']:>10.4f}                      ║
║ Win Rate:       {pnl['win_rate']:>10.1f}%                      ║
╠════════════════════════════════════════════════════════╣
║ Positions: {len(self.positions):>3} | Trades: {pnl['total_trades']:>4} | Wins: {pnl['winning_trades']:>4}        ║
╚════════════════════════════════════════════════════════╝
"""
        return summary


# Convenience function
def create_paper_account(initial_balance: float = 10000.0,
                         state_file: str = 'toobit_paper_state.json') -> PaperAccount:
    """Factory function to create PaperAccount"""
    return PaperAccount(initial_balance, state_file)
