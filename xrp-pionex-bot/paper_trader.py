"""
XRP Paper Trading Engine
Realistic simulation with fees, slippage, and P&L tracking.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_DOWN

@dataclass
class Position:
    """Open position tracking"""
    symbol: str
    side: str  # 'long' or 'short'
    entry_price: Decimal
    amount: Decimal
    timestamp: str
    unrealized_pnl: Decimal = Decimal('0')
    
@dataclass
class Trade:
    """Completed trade record"""
    id: str
    symbol: str
    side: str
    entry_price: Decimal
    exit_price: Optional[Decimal]
    amount: Decimal
    entry_time: str
    exit_time: Optional[str]
    pnl: Decimal = Decimal('0')
    pnl_percent: Decimal = Decimal('0')
    status: str = 'open'  # 'open', 'closed'

class PaperTrader:
    """
    Paper trading engine for XRP
    Start with 100 XRP, goal: double it
    """
    
    # Trading fees (Pionex spot trading fees)
    MAKER_FEE = Decimal('0.0005')  # 0.05%
    TAKER_FEE = Decimal('0.0005')  # 0.05%
    
    # Slippage simulation
    SLIPPAGE = Decimal('0.001')  # 0.1%
    
    def __init__(self, initial_xrp: Decimal = Decimal('100'), 
                 initial_usdt: Decimal = Decimal('1000'),
                 state_file: str = 'paper_state.json'):
        self.initial_xrp = initial_xrp
        self.initial_usdt = initial_usdt
        self.state_file = state_file
        
        # Portfolio tracking
        self.xrp_balance = initial_xrp
        self.usdt_balance = initial_usdt
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.trade_id_counter = 0
        
        # Performance tracking
        self.peak_xrp_value = initial_xrp  # Track peak for drawdown calculation
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # Load state if exists
        self._load_state()
        
    def _generate_trade_id(self) -> str:
        """Generate unique trade ID"""
        self.trade_id_counter += 1
        return f"trade_{self.trade_id_counter}_{int(datetime.now().timestamp())}"
    
    def get_balance(self) -> Dict:
        """Get current balance"""
        return {
            'xrp': float(self.xrp_balance),
            'usdt': float(self.usdt_balance),
            'xrp_value_usd': self._get_position_value_usd(),
            'total_equity_usd': self._get_total_equity_usd()
        }
    
    def _get_position_value_usd(self) -> float:
        """Calculate current position value in USD (simulated)"""
        # For backtesting, we'll estimate XRP value at $2
        xrp_price = Decimal('2.0')
        return float(self.xrp_balance * xrp_price)
    
    def _get_total_equity_usd(self) -> float:
        """Total equity in USD"""
        return float(self.usdt_balance + (self.xrp_balance * Decimal('2.0')))
    
    def buy(self, amount: Decimal, price: Decimal, timestamp: str = None) -> Trade:
        """
        Buy XRP with USDT
        Returns the trade record
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
            
        # Apply slippage (price goes up when buying)
        executed_price = price * (Decimal('1') + self.SLIPPAGE)
        
        # Calculate cost including fees
        cost = amount * executed_price
        fee = cost * self.TAKER_FEE
        total_cost = cost + fee
        
        # Check if we have enough USDT
        if total_cost > self.usdt_balance:
            print(f"Insufficient USDT. Need {float(total_cost):.2f}, have {float(self.usdt_balance):.2f}")
            return None
        
        # Execute trade
        self.usdt_balance -= total_cost
        self.xrp_balance += amount
        
        # Create trade record
        trade = Trade(
            id=self._generate_trade_id(),
            symbol='XRP_USDT',
            side='buy',
            entry_price=executed_price,
            exit_price=None,
            amount=amount,
            entry_time=timestamp,
            exit_time=None,
            status='open'
        )
        
        self.trades.append(trade)
        self.positions['XRP'] = Position(
            symbol='XRP_USDT',
            side='long',
            entry_price=executed_price,
            amount=amount,
            timestamp=timestamp
        )
        
        self.total_trades += 1
        self._save_state()
        
        print(f"🟢 BUY: {float(amount):.4f} XRP @ ${float(executed_price):.4f} | Fee: ${float(fee):.4f}")
        print(f"💰 Balance: {float(self.xrp_balance):.4f} XRP | ${float(self.usdt_balance):.2f} USDT")
        
        return trade
    
    def sell(self, amount: Decimal, price: Decimal, timestamp: str = None) -> Trade:
        """
        Sell XRP for USDT
        Returns the trade record with P&L
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
            
        # Apply slippage (price goes down when selling)
        executed_price = price * (Decimal('1') - self.SLIPPAGE)
        
        # Check if we have enough XRP
        if amount > self.xrp_balance:
            print(f"Insufficient XRP. Need {float(amount):.4f}, have {float(self.xrp_balance):.4f}")
            return None
        
        # Calculate proceeds minus fees
        proceeds = amount * executed_price
        fee = proceeds * self.TAKER_FEE
        net_proceeds = proceeds - fee
        
        # Calculate P&L
        position = self.positions.get('XRP')
        if position:
            entry_value = amount * position.entry_price
            pnl = net_proceeds - entry_value
            pnl_percent = (pnl / entry_value) * 100
            
            if pnl > 0:
                self.winning_trades += 1
                emoji = "✅"
            else:
                self.losing_trades += 1
                emoji = "❌"
        else:
            pnl = Decimal('0')
            pnl_percent = Decimal('0')
            emoji = "⚪"
        
        # Execute trade
        self.xrp_balance -= amount
        self.usdt_balance += net_proceeds
        
        # Update trade record
        open_trade = None
        for trade in reversed(self.trades):
            if trade.status == 'open' and trade.side == 'buy':
                open_trade = trade
                break
        
        if open_trade:
            open_trade.exit_price = executed_price
            open_trade.exit_time = timestamp
            open_trade.pnl = pnl
            open_trade.pnl_percent = pnl_percent
            open_trade.status = 'closed'
        
        # Clear position
        if 'XRP' in self.positions:
            del self.positions['XRP']
        
        self.total_trades += 1
        self._save_state()
        
        print(f"🔴 SELL: {float(amount):.4f} XRP @ ${float(executed_price):.4f} | Fee: ${float(fee):.4f}")
        print(f"{emoji} P&L: ${float(pnl):.4f} ({float(pnl_percent):.2f}%)")
        print(f"💰 Balance: {float(self.xrp_balance):.4f} XRP | ${float(self.usdt_balance):.2f} USDT")
        
        return open_trade
    
    def calculate_win_rate(self) -> float:
        """Calculate win rate percentage"""
        closed_trades = [t for t in self.trades if t.status == 'closed']
        if not closed_trades:
            return 0.0
        winners = sum(1 for t in closed_trades if t.pnl > 0)
        return (winners / len(closed_trades)) * 100
    
    def get_performance_stats(self) -> Dict:
        """Get trading performance statistics"""
        closed_trades = [t for t in self.trades if t.status == 'closed']
        
        if not closed_trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'total_pnl': 0.0,
                'avg_pnl': 0.0,
                'current_xrp': float(self.xrp_balance),
                'current_usdt': float(self.usdt_balance),
                'profit_xrp': float(self.xrp_balance - self.initial_xrp),
                'profit_percent': 0.0
            }
        
        total_pnl = sum(t.pnl for t in closed_trades)
        avg_pnl = total_pnl / len(closed_trades)
        
        # Calculate profit in terms of XRP equivalent
        current_equity_usd = self._get_total_equity_usd()
        initial_equity_usd = float(self.initial_xrp * Decimal('2.0') + self.initial_usdt)
        profit_percent = ((current_equity_usd - initial_equity_usd) / initial_equity_usd) * 100
        
        return {
            'total_trades': len(closed_trades),
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.calculate_win_rate(),
            'total_pnl': float(total_pnl),
            'avg_pnl': float(avg_pnl),
            'current_xrp': float(self.xrp_balance),
            'current_usdt': float(self.usdt_balance),
            'profit_percent': profit_percent,
            'goal_doubled': self.xrp_balance >= self.initial_xrp * 2
        }
    
    def print_performance(self):
        """Print current performance"""
        stats = self.get_performance_stats()
        print("\n" + "="*50)
        print("📊 PERFORMANCE SUMMARY")
        print("="*50)
        print(f"Total Trades: {stats['total_trades']}")
        print(f"Winning Trades: {stats['winning_trades']}")
        print(f"Losing Trades: {stats['losing_trades']}")
        print(f"Win Rate: {stats['win_rate']:.2f}%")
        print(f"Total P&L: ${stats['total_pnl']:.2f} USDT")
        print(f"Current XRP: {stats['current_xrp']:.4f}")
        print(f"Current USDT: ${stats['current_usdt']:.2f}")
        print(f"Profit: {stats['profit_percent']:.2f}%")
        if stats['goal_doubled']:
            print("🎯 GOAL ACHIEVED: Doubled the 100 XRP!")
        print("="*50 + "\n")
    
    def _save_state(self):
        """Save trading state to file"""
        state = {
            'xrp_balance': str(self.xrp_balance),
            'usdt_balance': str(self.usdt_balance),
            'positions': {k: asdict(v) for k, v in self.positions.items()},
            'trades': [asdict(t) for t in self.trades],
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_trades': self.total_trades,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_state(self):
        """Load trading state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                self.xrp_balance = Decimal(state.get('xrp_balance', self.initial_xrp))
                self.usdt_balance = Decimal(state.get('usdt_balance', self.initial_usdt))
                self.winning_trades = state.get('winning_trades', 0)
                self.losing_trades = state.get('losing_trades', 0)
                self.total_trades = state.get('total_trades', 0)
                
                # Load trades - convert string values back to Decimal
                for trade_data in state.get('trades', []):
                    trade = Trade(
                        id=trade_data['id'],
                        symbol=trade_data['symbol'],
                        side=trade_data['side'],
                        entry_price=Decimal(trade_data['entry_price']),
                        exit_price=Decimal(trade_data['exit_price']) if trade_data.get('exit_price') else None,
                        amount=Decimal(trade_data['amount']),
                        entry_time=trade_data['entry_time'],
                        exit_time=trade_data.get('exit_time'),
                        pnl=Decimal(trade_data.get('pnl', '0')),
                        pnl_percent=Decimal(trade_data.get('pnl_percent', '0')),
                        status=trade_data.get('status', 'open')
                    )
                    self.trades.append(trade)
                
                # Load positions - convert string values back to Decimal
                for symbol, pos_data in state.get('positions', {}).items():
                    self.positions[symbol] = Position(
                        symbol=pos_data['symbol'],
                        side=pos_data['side'],
                        entry_price=Decimal(pos_data['entry_price']),
                        amount=Decimal(pos_data['amount']),
                        timestamp=pos_data['timestamp'],
                        unrealized_pnl=Decimal(pos_data.get('unrealized_pnl', '0'))
                    )
                
                print(f"📂 Loaded previous state: {self.total_trades} trades, {len(self.positions)} positions")
            except Exception as e:
                print(f"Error loading state: {e}")
    
    def reset(self):
        """Reset to initial state"""
        self.xrp_balance = self.initial_xrp
        self.usdt_balance = self.initial_usdt
        self.positions = {}
        self.trades = []
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_trades = 0
        self._save_state()
        print("🔄 Paper trading state reset")

# Example usage
if __name__ == "__main__":
    trader = PaperTrader()
    print("Starting with:", trader.get_balance())
    
    # Simulate some trades
    trader.buy(Decimal('10'), Decimal('2.0'))
    trader.sell(Decimal('5'), Decimal('2.2'))
    trader.print_performance()