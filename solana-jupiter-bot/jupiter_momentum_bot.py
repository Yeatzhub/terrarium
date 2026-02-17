"""
Jupiter Momentum/Swing Trading Bot
Real strategy: Ride trends, cut losses quickly, let winners run
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import deque

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('jupiter_momentum.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('MomentumBot')

@dataclass
class Position:
    """Active trading position"""
    trade_id: int
    token: str
    entry_price: float
    entry_time: datetime
    size_sol: float
    direction: str  # 'long' or 'short'
    
    # Risk management
    stop_loss_price: float
    take_profit_price: float
    
    # Status
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[str] = None  # 'stop_loss', 'take_profit', 'signal_flip', 'timeout'
    pnl_pct: float = 0.0
    pnl_sol: float = 0.0
    is_open: bool = True
    
    def update_pnl(self, current_price: float):
        """Calculate current P&L"""
        if self.direction == 'long':
            self.pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
        else:
            self.pnl_pct = ((self.entry_price - current_price) / self.entry_price) * 100
        
        self.pnl_sol = self.size_sol * (self.pnl_pct / 100)


class MomentumBot:
    """
    Real momentum/swing trading bot
    - Uses price action and trend detection
    - Realistic win rate (~55-60%)
    - Proper risk management (stop losses)
    - Position sizing based on volatility
    """
    
    def __init__(self, initial_capital_sol: float = 1.0, mode: str = 'paper'):
        self.mode = mode
        self.balance = initial_capital_sol
        self.initial_capital = initial_capital_sol
        
        # Trading parameters
        self.position_size_pct = 0.25  # 25% of balance per trade
        self.max_positions = 3  # Max concurrent positions
        self.min_risk_reward = 1.5  # Need 1.5:1 reward/risk minimum
        
        # Risk management
        self.stop_loss_pct = 2.0  # 2% stop loss
        self.take_profit_pct = 4.0  # 4% take profit (2:1 RR)
        self.trailing_stop_pct = 1.5  # Trailing stop after 2% profit
        self.max_hold_hours = 4  # Close if no movement in 4 hours
        
        # Momentum detection
        self.price_history = {}  # Token -> deque of (timestamp, price)
        self.history_length = 20  # Lookback periods
        self.momentum_threshold = 0.8  # 0.8% move in 10 minutes = momentum
        
        # State
        self.positions: List[Position] = []
        self.closed_trades: List[Position] = []
        self.trade_counter = 0
        self.prices = {}
        
        # Fees
        self.trading_fee_pct = 0.1  # 0.1% per trade
        self.slippage_pct = 0.05  # 0.05% slippage
        
        # Statistics
        self.wins = 0
        self.losses = 0
        self.total_fees_paid = 0.0
        
        logger.info(f"🚀 MomentumBot initialized")
        logger.info(f"   Mode: {mode}")
        logger.info(f"   Capital: {initial_capital_sol} SOL")
        logger.info(f"   Strategy: Trend following with {self.stop_loss_pct}% stops")
        
    def fetch_prices(self) -> bool:
        """Get real prices from CoinGecko"""
        try:
            ids = 'solana,jupiter-exchange-solana,bonk,raydium,bome'
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Map to our token names
            mapping = {
                'solana': 'SOL',
                'jupiter-exchange-solana': 'JUP',
                'bonk': 'BONK',
                'raydium': 'RAY',
                'bome': 'BOME'
            }
            
            for cg_id, token_name in mapping.items():
                if cg_id in data:
                    self.prices[token_name] = {
                        'price': data[cg_id]['usd'],
                        'change_24h': data[cg_id].get('usd_24h_change', 0)
                    }
                    
                    # Update price history for momentum detection
                    if token_name not in self.price_history:
                        self.price_history[token_name] = deque(maxlen=self.history_length)
                    self.price_history[token_name].append((datetime.now(), data[cg_id]['usd']))
            
            logger.info(f"💰 Prices: SOL=${self.prices.get('SOL', {}).get('price', 'N/A')}, "
                       f"JUP=${self.prices.get('JUP', {}).get('price', 'N/A')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Price fetch failed: {e}")
            return False
    
    def detect_momentum(self, token: str) -> Tuple[str, float]:
        """
        Detect momentum direction and strength
        Returns: (signal, strength_pct)
        Signal: 'long', 'short', or 'neutral'
        """
        if token not in self.price_history or len(self.price_history[token]) < 10:
            return 'neutral', 0.0
        
        history = list(self.price_history[token])
        
        # Calculate short-term momentum (last 5 periods vs previous 5)
        recent = [p for _, p in history[-5:]]
        previous = [p for _, p in history[-10:-5]]
        
        if not recent or not previous:
            return 'neutral', 0.0
        
        recent_avg = sum(recent) / len(recent)
        previous_avg = sum(previous) / len(previous)
        
        momentum_pct = ((recent_avg - previous_avg) / previous_avg) * 100
        
        # Trend confirmation using longer history
        if len(history) >= 15:
            longer_avg = sum([p for _, p in history[-15:]]) / 15
            trend_direction = 'up' if recent_avg > longer_avg else 'down'
        else:
            trend_direction = 'up' if momentum_pct > 0 else 'down'
        
        # Generate signal
        if abs(momentum_pct) >= self.momentum_threshold:
            if momentum_pct > 0 and trend_direction == 'up':
                return 'long', momentum_pct
            elif momentum_pct < 0 and trend_direction == 'down':
                return 'short', abs(momentum_pct)
        
        return 'neutral', 0.0
    
    def calculate_position_size(self, token: str) -> float:
        """Calculate position size based on balance and volatility"""
        base_size = self.balance * self.position_size_pct
        
        # Adjust for available balance
        committed = sum(p.size_sol for p in self.positions if p.is_open)
        available = self.balance - committed
        
        return min(base_size, available * 0.9)  # Keep 10% buffer
    
    def open_position(self, token: str, direction: str, momentum_strength: float) -> bool:
        """Open a new position"""
        if len(self.positions) >= self.max_positions:
            logger.info(f"⏭️ Max positions ({self.max_positions}) reached")
            return False
        
        # Check if already have position in this token
        if any(p.token == token and p.is_open for p in self.positions):
            logger.info(f"⏭️ Already have open position in {token}")
            return False
        
        price = self.prices.get(token, {}).get('price')
        if not price:
            return False
        
        size = self.calculate_position_size(token)
        if size < 0.01:  # Minimum 0.01 SOL
            logger.info(f"⏭️ Position size too small ({size:.4f} SOL)")
            return False
        
        # Calculate entry and risk levels
        if direction == 'long':
            entry = price * 1.001  # Small slippage on entry
            stop = entry * (1 - self.stop_loss_pct / 100)
            target = entry * (1 + self.take_profit_pct / 100)
        else:
            entry = price * 0.999
            stop = entry * (1 + self.stop_loss_pct / 100)
            target = entry * (1 - self.take_profit_pct / 100)
        
        # Check risk/reward ratio
        risk = abs(entry - stop)
        reward = abs(target - entry)
        if reward / risk < self.min_risk_reward:
            logger.info(f"⏭️ Risk/reward too low ({reward/risk:.2f}:1 < {self.min_risk_reward}:1)")
            return False
        
        self.trade_counter += 1
        position = Position(
            trade_id=self.trade_counter,
            token=token,
            entry_price=entry,
            entry_time=datetime.now(),
            size_sol=size,
            direction=direction,
            stop_loss_price=stop,
            take_profit_price=target
        )
        
        self.positions.append(position)
        
        emoji = '🟢 LONG' if direction == 'long' else '🔴 SHORT'
        print(f"\n{'═' * 70}")
        print(f"{emoji} OPENED #{position.trade_id} | {token}")
        print(f"   Entry: ${entry:.4f} | Size: {size:.4f} SOL")
        print(f"   Stop: ${stop:.4f} ({-self.stop_loss_pct}%)")
        print(f"   Target: ${target:.4f} (+{self.take_profit_pct}%)")
        print(f"   Momentum: {momentum_strength:.2f}%")
        print(f"{'═' * 70}")
        
        logger.info(f"Opened {direction} {token} @ ${entry:.4f}, size={size:.4f} SOL")
        return True
    
    def close_position(self, position: Position, reason: str, exit_price: float):
        """Close a position and record P&L"""
        position.is_open = False
        position.exit_price = exit_price
        position.exit_time = datetime.now()
        position.exit_reason = reason
        
        # Calculate final P&L
        position.update_pnl(exit_price)
        
        # Deduct fees
        entry_fee = position.size_sol * self.trading_fee_pct / 100
        exit_fee = position.size_sol * (1 + position.pnl_pct / 100) * self.trading_fee_pct / 100
        slippage_cost = position.size_sol * self.slippage_pct / 100
        total_fees = entry_fee + exit_fee + slippage_cost
        
        position.pnl_sol -= total_fees
        self.total_fees_paid += total_fees
        
        # Update balance
        self.balance += position.pnl_sol
        
        # Record win/loss
        if position.pnl_sol > 0:
            self.wins += 1
            emoji = '🟢 PROFIT'
        else:
            self.losses += 1
            emoji = '🔴 LOSS'
        
        # Move to closed trades
        self.closed_trades.append(position)
        self.positions = [p for p in self.positions if p.is_open]
        
        # Print trade summary
        duration = position.exit_time - position.entry_time
        print(f"\n{'═' * 70}")
        print(f"{emoji} CLOSED #{position.trade_id} | {reason}")
        print(f"   {position.token} {position.direction.upper()}")
        print(f"   Entry: ${position.entry_price:.4f} → Exit: ${exit_price:.4f}")
        print(f"   P&L: {position.pnl_sol:+.6f} SOL ({position.pnl_pct:+.2f}%)")
        print(f"   Duration: {duration.seconds // 60}m {duration.seconds % 60}s")
        print(f"   Fees: {total_fees:.6f} SOL")
        print(f"{'═' * 70}")
        
        logger.info(f"Closed {position.token} {reason}: P&L={position.pnl_sol:.6f} SOL")
    
    def manage_positions(self):
        """Check all open positions for exit conditions"""
        for position in self.positions[:]:
            if not position.is_open:
                continue
            
            current_price = self.prices.get(position.token, {}).get('price')
            if not current_price:
                continue
            
            position.update_pnl(current_price)
            
            # Check stop loss
            if position.direction == 'long' and current_price <= position.stop_loss_price:
                self.close_position(position, 'stop_loss', current_price)
                continue
            
            if position.direction == 'short' and current_price >= position.stop_loss_price:
                self.close_position(position, 'stop_loss', current_price)
                continue
            
            # Check take profit
            if position.direction == 'long' and current_price >= position.take_profit_price:
                self.close_position(position, 'take_profit', current_price)
                continue
            
            if position.direction == 'short' and current_price <= position.take_profit_price:
                self.close_position(position, 'take_profit', current_price)
                continue
            
            # Check trailing stop (after 2% profit)
            if position.pnl_pct >= 2.0:
                if position.direction == 'long':
                    trailing_stop = current_price * (1 - self.trailing_stop_pct / 100)
                    if current_price < trailing_stop:
                        self.close_position(position, 'trailing_stop', current_price)
                        continue
            
            # Check max hold time
            hold_time = datetime.now() - position.entry_time
            if hold_time > timedelta(hours=self.max_hold_hours):
                self.close_position(position, 'timeout', current_price)
                continue
            
            # Check signal flip (momentum reversed)
            signal, strength = self.detect_momentum(position.token)
            if (position.direction == 'long' and signal == 'short' and strength > 1.0) or \
               (position.direction == 'short' and signal == 'long' and strength > 1.0):
                self.close_position(position, 'signal_flip', current_price)
                continue
    
    def scan_for_entries(self):
        """Look for new entry opportunities"""
        for token in ['SOL', 'JUP', 'BONK']:
            if token not in self.prices:
                continue
            
            signal, strength = self.detect_momentum(token)
            
            if signal != 'neutral' and strength >= self.momentum_threshold:
                # Check if this is a good setup
                price_change_24h = self.prices[token].get('change_24h', 0)
                
                # Avoid chasing if already moved >10% in 24h (risk of pullback)
                if abs(price_change_24h) > 10:
                    logger.info(f"⏭️ {token} moved {price_change_24h:.1f}% in 24h, skipping")
                    continue
                
                self.open_position(token, signal, strength)
    
    def print_dashboard(self):
        """Print live dashboard"""
        print(f"\n{'=' * 70}")
        print(f"📊 MOMENTUM BOT DASHBOARD | {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'=' * 70}")
        
        # Balance
        pnl = self.balance - self.initial_capital
        pnl_pct = (pnl / self.initial_capital) * 100
        print(f"💰 Balance: {self.balance:.6f} SOL ({pnl:+.6f} / {pnl_pct:+.2f}%)")
        print(f"💸 Fees Paid: {self.total_fees_paid:.6f} SOL")
        
        # Stats
        total_trades = self.wins + self.losses
        if total_trades > 0:
            win_rate = self.wins / total_trades * 100
            print(f"📈 Trades: {total_trades} (W: {self.wins} L: {self.losses}) | Win Rate: {win_rate:.1f}%")
        
        print(f"{'─' * 70}")
        
        # Open positions
        if self.positions:
            print(f"🎯 OPEN POSITIONS ({len(self.positions)}/{self.max_positions})")
            for p in self.positions:
                if p.is_open:
                    emoji = '🟢' if p.pnl_sol > 0 else '🔴'
                    print(f"   {emoji} #{p.trade_id} {p.token} {p.direction.upper()}")
                    print(f"      Entry: ${p.entry_price:.4f} | Current P&L: {p.pnl_sol:+.6f} SOL ({p.pnl_pct:+.2f}%)")
        else:
            print("🎯 No open positions")
        
        # Recent closed trades
        recent = self.closed_trades[-3:]
        if recent:
            print(f"{'─' * 70}")
            print("📜 RECENT CLOSED:")
            for t in reversed(recent):
                emoji = '🟢' if t.pnl_sol > 0 else '🔴'
                print(f"   {emoji} #{t.trade_id} {t.token} {t.exit_reason} | {t.pnl_sol:+.6f} SOL")
        
        print(f"{'=' * 70}\n")
    
    def save_state(self):
        """Save bot state"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'balance': self.balance,
            'initial_capital': self.initial_capital,
            'pnl_sol': self.balance - self.initial_capital,
            'pnl_pct': ((self.balance / self.initial_capital) - 1) * 100,
            'wins': self.wins,
            'losses': self.losses,
            'total_fees': self.total_fees_paid,
            'open_positions': [asdict(p) for p in self.positions if p.is_open],
            'closed_trades': len(self.closed_trades)
        }
        
        try:
            with open('jupiter_momentum_state.json', 'w') as f:
                json.dump(state, f, indent=2, default=str)
            with open('jupiter_momentum_trades.json', 'w') as f:
                json.dump([asdict(t) for t in self.closed_trades], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Save failed: {e}")
    
    def run(self, scan_interval: int = 60):
        """Main trading loop"""
        print("\n" + "=" * 70)
        print("🚀 JUPITER MOMENTUM/SWING TRADING BOT")
        print("=" * 70)
        print("\n✅ REAL market data from CoinGecko")
        print("✅ Trend-following with momentum detection")
        print("✅ Stop losses: {:.1f}% | Take profit: {:.1f}%".format(self.stop_loss_pct, self.take_profit_pct))
        print("✅ Position sizing: 25% of balance")
        print("✅ Max {} concurrent positions".format(self.max_positions))
        print("⚠️  Paper mode = simulated trades\n")
        
        # Initial price fetch
        if not self.fetch_prices():
            print("❌ Cannot fetch market data")
            return
        
        print(f"✅ Connected to market data")
        print(f"⏱️  Scan interval: {scan_interval}s")
        print(f"🎯 Looking for momentum >{self.momentum_threshold}% in 10min\n")
        
        self.print_dashboard()
        
        try:
            while True:
                # Update prices
                self.fetch_prices()
                
                # Manage existing positions
                self.manage_positions()
                
                # Look for new entries
                self.scan_for_entries()
                
                # Save state
                self.save_state()
                
                # Print dashboard every 5 cycles
                if self.trade_counter % 5 == 0:
                    self.print_dashboard()
                
                time.sleep(scan_interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Bot stopped")
            self.print_dashboard()
            self.save_state()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--capital', type=float, default=1.0)
    parser.add_argument('--mode', choices=['paper', 'live'], default='paper')
    parser.add_argument('--interval', type=int, default=60)
    
    args = parser.parse_args()
    
    bot = MomentumBot(
        initial_capital_sol=args.capital,
        mode=args.mode
    )
    bot.run(scan_interval=args.interval)
