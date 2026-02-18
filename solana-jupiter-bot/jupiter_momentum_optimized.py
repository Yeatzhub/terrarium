"""
Jupiter Momentum/Swing Trading Bot - OPTIMIZED VERSION
Targets low-volatility market conditions with tighter parameters
Real strategy: Quick scalps on micro-momentum, tight risk management
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
    exit_reason: Optional[str] = None
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
    OPTIMIZED momentum/swing trading bot for low-volatility markets
    - Faster signal detection (reduced thresholds)
    - Tighter risk management (quicker exits)
    - More frequent, smaller scalps
    """
    
    def __init__(self, initial_capital_sol: float = 1.0, mode: str = 'paper'):
        self.mode = mode
        self.balance = initial_capital_sol
        self.initial_capital = initial_capital_sol
        
        # OPTIMIZED Trading parameters
        self.position_size_pct = 0.30  # Increased: 30% of balance per trade (was 25%)
        self.max_positions = 3  # Max concurrent positions
        self.min_risk_reward = 1.3  # Reduced: 1.3:1 minimum (was 1.5:1)
        
        # OPTIMIZED Risk management - tighter for scalping
        self.stop_loss_pct = 1.2  # Reduced: 1.2% stop loss (was 2.0%)
        self.take_profit_pct = 2.0  # Reduced: 2.0% take profit (was 4.0%)
        self.trailing_stop_pct = 0.8  # Reduced: 0.8% trailing (was 1.5%)
        self.max_hold_hours = 1  # Reduced: 1 hour max hold (was 4 hours)
        
        # OPTIMIZED Momentum detection - more sensitive
        self.price_history = {}  # Token -> deque of (timestamp, price)
        self.history_length = 10  # Reduced: 10 lookback periods (was 20)
        self.momentum_threshold = 0.3  # Reduced: 0.3% move = momentum (was 0.8%)
        self.chop_filter_threshold = 0.15  # NEW: Filter out sub-0.15% noise
        
        # State
        self.positions: List[Position] = []
        self.closed_trades: List[Position] = []
        self.trade_counter = 0
        self.prices = {}
        self.last_scan_time = datetime.now()
        
        # Fees (slightly higher to account for more frequent trading)
        self.trading_fee_pct = 0.1  # 0.1% per trade
        self.slippage_pct = 0.05  # 0.05% slippage
        
        # Statistics
        self.wins = 0
        self.losses = 0
        self.total_fees_paid = 0.0
        self.scans_without_trade = 0  # NEW: Track scan frequency
        
        logger.info(f"🚀 MomentumBot OPTIMIZED initialized")
        logger.info(f"   Mode: {mode}")
        logger.info(f"   Capital: {initial_capital_sol} SOL")
        logger.info(f"   ⚡ OPTIMIZED: {self.momentum_threshold}% threshold, {self.stop_loss_pct}% stops")
        
    def fetch_prices(self) -> bool:
        """Get real prices from CoinGecko - EXPANDED token list"""
        try:
            # EXPANDED: More tokens for better opportunity detection
            ids = ('solana,jupiter-exchange-solana,bonk,raydium,bome,'
                   'wif,dogwifcoin,pengu,popcat,ai16z,arthur Hayes')
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            # Map to our token names - EXPANDED
            mapping = {
                'solana': 'SOL',
                'jupiter-exchange-solana': 'JUP',
                'bonk': 'BONK',
                'raydium': 'RAY',
                'bome': 'BOME',
                'wif': 'WIF',
                'dogwifcoin': 'WIF2',
                'pengu': 'PENGU',
                'popcat': 'POPCAT',
                'ai16z': 'AI16Z'
            }
            
            prices_fetched = 0
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
                    prices_fetched += 1
            
            if prices_fetched > 0:
                logger.debug(f"💰 Fetched {prices_fetched} token prices")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Price fetch failed: {e}")
            return False
    
    def detect_momentum(self, token: str) -> Tuple[str, float]:
        """
        OPTIMIZED momentum detection for low-volatility markets
        Returns: (signal, strength_pct)
        """
        if token not in self.price_history:
            return 'neutral', 0.0
        
        history = list(self.price_history[token])
        
        # Need at least 5 periods for short-term momentum
        if len(history) < 5:
            return 'neutral', 0.0
        
        # Calculate recent prices
        recent_prices = [p for _, p in history[-5:]]
        
        if len(history) >= 8:
            # Compare recent vs slightly older
            recent_avg = sum(recent_prices) / len(recent_prices)
            older_prices = [p for _, p in history[-8:-3]]
            older_avg = sum(older_prices) / len(older_prices)
            
            momentum_pct = ((recent_avg - older_avg) / older_avg) * 100
        else:
            # Compare last price to average of period
            latest = recent_prices[-1]
            avg = sum(recent_prices) / len(recent_prices)
            momentum_pct = ((latest - avg) / avg) * 100
        
        # OPTIMIZED: Lower threshold + chop filter
        if abs(momentum_pct) < self.chop_filter_threshold:
            return 'neutral', 0.0  # Filter out noise
        
        if abs(momentum_pct) >= self.momentum_threshold:
            # Trend confirmation - check if consistent
            if len(history) >= self.history_length:
                longer_avg = sum([p for _, p in history]) / len(history)
                if momentum_pct > 0:
                    return ('long', momentum_pct) if recent_prices[-1] > longer_avg else ('neutral', 0.0)
                else:
                    return ('short', abs(momentum_pct)) if recent_prices[-1] < longer_avg else ('neutral', 0.0)
            else:
                # Not enough history yet - be more lenient
                return ('long', momentum_pct) if momentum_pct > 0 else ('short', abs(momentum_pct))
        
        return 'neutral', 0.0
    
    def calculate_position_size(self, token: str) -> float:
        """Calculate position size based on balance and volatility"""
        base_size = self.balance * self.position_size_pct
        
        # Adjust for available balance
        committed = sum(p.size_sol for p in self.positions if p.is_open)
        available = self.balance - committed
        
        return min(base_size, available * 0.9)  # Keep 10% buffer
    
    def open_position(self, token: str, direction: str, momentum_strength: float) -> bool:
        """Open a new position - OPTIMIZED for faster entries"""
        if len(self.positions) >= self.max_positions:
            logger.debug(f"⏭️ Max positions ({self.max_positions}) reached")
            return False
        
        # Check if already have position in this token
        if any(p.token == token and p.is_open for p in self.positions):
            logger.debug(f"⏭️ Already have open position in {token}")
            return False
        
        price = self.prices.get(token, {}).get('price')
        if not price:
            return False
        
        size = self.calculate_position_size(token)
        if size < 0.01:  # Minimum 0.01 SOL
            logger.debug(f"⏭️ Position size too small ({size:.4f} SOL)")
            return False
        
        # OPTIMIZED: Calculate entry with minimal slippage assumption
        if direction == 'long':
            entry = price * 1.0005  # Reduced slippage (was 1.001)
            stop = entry * (1 - self.stop_loss_pct / 100)
            target = entry * (1 + self.take_profit_pct / 100)
        else:
            entry = price * 0.9995  # Reduced slippage
            stop = entry * (1 + self.stop_loss_pct / 100)
            target = entry * (1 - self.take_profit_pct / 100)
        
        # Check risk/reward ratio - still essential
        risk = abs(entry - stop)
        reward = abs(target - entry)
        if reward / risk < self.min_risk_reward:
            logger.debug(f"⏭️ Risk/reward too low ({reward/risk:.2f}:1 < {self.min_risk_reward}:1)")
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
        self.scans_without_trade = 0  # Reset counter
        
        emoji = '🟢 LONG' if direction == 'long' else '🔴 SHORT'
        print(f"\n{'═' * 70}")
        print(f"{emoji} OPENED #{position.trade_id} | {token}")
        print(f"   Entry: ${entry:.4f} | Size: {size:.4f} SOL")
        print(f"   Stop: ${stop:.4f} ({-self.stop_loss_pct}%)")
        print(f"   Target: ${target:.4f} (+{self.take_profit_pct}%)")
        print(f"   Momentum: {momentum_strength:.2f}%")
        print(f"{'═' * 70}")
        
        logger.info(f"Opened {direction} {token} @ ${entry:.4f}, size={size:.4f} SOL, mom={momentum_strength:.2f}%")
        return True
    
    def close_position(self, position: Position, reason: str, exit_price: float):
        """Close a position and record P&L"""
        position.is_open = False
        position.exit_price = exit_price
        position.exit_time = datetime.now()
        position.exit_reason = reason
        
        # Calculate final P&L
        position.update_pnl(exit_price)
        
        # Deduct fees (both entry and exit)
        entry_fee = position.size_sol * self.trading_fee_pct / 100
        exit_fee = position.size_sol * (1 + position.pnl_pct / 100) * self.trading_fee_pct / 100
        slippage_cost = position.size_sol * self.slippage_pct / 100 * 2  # Entry + exit
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
        duration_mins = duration.seconds // 60
        print(f"\n{'═' * 70}")
        print(f"{emoji} CLOSED #{position.trade_id} | {reason}")
        print(f"   {position.token} {position.direction.upper()}")
        print(f"   Entry: ${position.entry_price:.4f} → Exit: ${exit_price:.4f}")
        print(f"   P&L: {position.pnl_sol:+.6f} SOL ({position.pnl_pct:+.2f}%)")
        print(f"   Duration: {duration_mins}m {duration.seconds % 60}s")
        print(f"   Fees: {total_fees:.6f} SOL")
        print(f"{'═' * 70}")
        
        logger.info(f"Closed {position.token} {reason}: P&L={position.pnl_sol:.6f} SOL, time={duration_mins}m")
    
    def manage_positions(self):
        """OPTIMIZED: Check all open positions for exit conditions"""
        for position in self.positions[:]:
            if not position.is_open:
                continue
            
            current_price = self.prices.get(position.token, {}).get('price')
            if not current_price:
                continue
            
            position.update_pnl(current_price)
            hold_time = datetime.now() - position.entry_time
            
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
            
            # OPTIMIZED: Lower trailing stop trigger (1.0% instead of 2.0%)
            if position.pnl_pct >= 1.0:
                if position.direction == 'long':
                    trailing_stop = current_price * (1 - self.trailing_stop_pct / 100)
                    if current_price < trailing_stop:
                        self.close_position(position, 'trailing_stop', current_price)
                        continue
                else:
                    trailing_stop = current_price * (1 + self.trailing_stop_pct / 100)
                    if current_price > trailing_stop:
                        self.close_position(position, 'trailing_stop', current_price)
                        continue
            
            # OPTIMIZED: Reduced max hold time (1 hour)
            if hold_time > timedelta(hours=self.max_hold_hours):
                self.close_position(position, 'timeout', current_price)
                continue
            
            # OPTIMIZED: Earlier signal flip detection
            signal, strength = self.detect_momentum(position.token)
            if hold_time > timedelta(minutes=10):  # Only flip after 10 min
                if (position.direction == 'long' and signal == 'short' and strength > self.momentum_threshold * 1.5) or \
                   (position.direction == 'short' and signal == 'long' and strength > self.momentum_threshold * 1.5):
                    self.close_position(position, 'signal_flip', current_price)
                    continue
    
    def scan_for_entries(self):
        """OPTIMIZED: Look for new entry opportunities"""
        # Scan all tracked tokens
        for token in self.prices.keys():
            # Skip if already in position
            if any(p.token == token and p.is_open for p in self.positions):
                continue
            
            signal, strength = self.detect_momentum(token)
            
            if signal != 'neutral' and strength >= self.momentum_threshold:
                # Get 24h change for context
                price_change_24h = self.prices[token].get('change_24h', 0)
                
                # OPTIMIZED: Relaxed skip condition (was >10%, now >15%)
                if abs(price_change_24h) > 15:
                    logger.debug(f"⏭️ {token} moved {price_change_24h:.1f}% in 24h, skipping")
                    continue
                
                # OPTIMIZED: Directional bias - prefer longs in up moves, shorts in down
                # but don't require it (allows counter-trend scalps)
                success = self.open_position(token, signal, strength)
                if success:
                    return True  # Only one entry per scan cycle
        
        self.scans_without_trade += 1
        return False
    
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
        else:
            print(f"📈 No trades yet | Scans without trade: {self.scans_without_trade}")
        
        # OPTIMIZED parameters display
        print(f"⚡ Config: {self.momentum_threshold}% threshold | {self.stop_loss_pct}% SL | {self.take_profit_pct}% TP")
        print(f"{'─' * 70}")
        
        # Open positions
        if self.positions:
            print(f"🎯 OPEN POSITIONS ({len(self.positions)}/{self.max_positions})")
            for p in self.positions:
                if p.is_open:
                    emoji = '🟢' if p.pnl_sol > 0 else '🔴'
                    hold_time = datetime.now() - p.entry_time
                    print(f"   {emoji} #{p.trade_id} {p.token} {p.direction.upper()} ({hold_time.seconds//60}m)")
                    print(f"      Entry: ${p.entry_price:.4f} | P&L: {p.pnl_sol:+.6f} SOL ({p.pnl_pct:+.2f}%)")
        else:
            print("🎯 No open positions")
        
        # Recent closed trades
        recent = self.closed_trades[-5:]
        if recent:
            print(f"{'─' * 70}")
            print("📜 RECENT CLOSED:")
            for t in reversed(recent):
                emoji = '🟢' if t.pnl_sol > 0 else '🔴'
                dur = (t.exit_time - t.entry_time).seconds // 60
                print(f"   {emoji} #{t.trade_id} {t.token} {t.exit_reason} | {t.pnl_sol:+.6f} SOL ({dur}m)")
        
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
            'scans_without_trade': self.scans_without_trade,
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
    
    def run(self, scan_interval: int = 30):
        """Main trading loop - OPTIMIZED with 30s default interval"""
        print("\n" + "=" * 70)
        print("🚀 JUPITER MOMENTUM BOT - OPTIMIZED VERSION")
        print("=" * 70)
        print("\n✅ REAL market data from CoinGecko")
        print("✅ EXPANDED token list (SOL, JUP, BONK, RAY, BOME, WIF, PENGU, POPCAT)")
        print(f"⚡ OPTIMIZED: {self.momentum_threshold}% momentum | {self.stop_loss_pct}% SL | {self.take_profit_pct}% TP")
        print(f"⚡ Faster entries: {self.history_length} periods | More trades expected")
        print(f"✅ Position sizing: 30% of balance")
        print(f"✅ Max {self.max_positions} concurrent positions")
        print("⚠️  Paper mode = simulated trades\n")
        
        # Initial price fetch
        if not self.fetch_prices():
            print("❌ Cannot fetch market data")
            return
        
        print(f"✅ Connected to market data")
        print(f"⏱️  Scan interval: {scan_interval}s (OPTIMIZED from 60s)")
        print(f"🎯 Looking for momentum >{self.momentum_threshold}%")
        print(f"⚠️  Filtering noise below {self.chop_filter_threshold}%\n")
        
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
                
                # Print dashboard every 10 cycles (~5 min at 30s interval)
                if self.scans_without_trade % 10 == 0:
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
    parser.add_argument('--interval', type=int, default=30)
    
    args = parser.parse_args()
    
    bot = MomentumBot(
        initial_capital_sol=args.capital,
        mode=args.mode
    )
    bot.run(scan_interval=args.interval)
