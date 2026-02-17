"""
Jupiter Trading Bot
High-frequency Solana DEX trading
"""

import os
import time
import json
import logging
from typing import Dict, Optional
from datetime import datetime

from jupiter_api import JupiterAPI, TOKENS, ArbitrageScanner
from strategies import DoublingPlan, RiskManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('jupiter_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('JupiterBot')


class JupiterTradingBot:
    """
    Main Jupiter trading bot
    
    Requires:
    - Solana wallet with private key
    - SOL for gas fees (~0.01 SOL per trade)
    - Trading capital
    """
    
    def __init__(
        self,
        private_key: Optional[str] = None,
        initial_capital_sol: float = 1.0,
        strategy: str = 'arbitrage',
        mode: str = 'paper'  # 'paper' or 'live'
    ):
        self.mode = mode
        self.strategy = strategy
        
        # Initialize API first (scanner needs it)
        self.api = JupiterAPI()
        self.scanner = ArbitrageScanner(self.api)
        self.risk = RiskManager(initial_capital_sol)
        
        # Paper trading state
        self.paper_balance = initial_capital_sol
        self.trade_count = 0
        
        # Wallet (live mode only)
        self.private_key = private_key
        self.wallet_address = None
        
        # Trade history for visual log
        self.trade_history = []
        self.trade_log_file = 'jupiter_trades.json'
        self._load_trade_history()
        
        if mode == 'live' and not private_key:
            raise ValueError("Live mode requires private key")
            
        logger.info(f"JupiterBot initialized: mode={mode}, strategy={strategy}, capital={initial_capital_sol} SOL")
        
    def _load_trade_history(self):
        """Load persisted trade history"""
        if os.path.exists(self.trade_log_file):
            try:
                with open(self.trade_log_file, 'r') as f:
                    self.trade_history = json.load(f)
                logger.info(f"Loaded {len(self.trade_history)} historical trades")
            except Exception as e:
                logger.warning(f"Could not load trade history: {e}")
                self.trade_history = []
        else:
            self.trade_history = []
    
    def _save_trade_history(self):
        """Persist trade history to file"""
        try:
            with open(self.trade_log_file, 'w') as f:
                json.dump(self.trade_history, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save trade history: {e}")
    
    def log_trade(self, trade: dict, console_print: bool = True):
        """
        Add trade to history and optionally print visual
        
        Trade format:
        {
            'timestamp': ISO timestamp,
            'trade_id': unique id,
            'route': str,
            'gross_profit_sol': float,
            'jupiter_fees_sol': float,
            'gas_fees_sol': float,
            'slippage_sol': float,
            'total_fees_sol': float,
            'net_profit_sol': float,
            'balance_before_sol': float,
            'balance_after_sol': float,
            'strategy': str,
            'mode': str,
            'is_simulation': bool
        }
        """
        trade['trade_id'] = len(self.trade_history) + 1
        self.trade_history.append(trade)
        self._save_trade_history()
        
        if console_print:
            self._print_trade_visual(trade)
    
    def _print_trade_visual(self, trade: dict):
        """Print a visually appealing trade log entry"""
        ts = datetime.fromisoformat(trade['timestamp']).strftime('%H:%M:%S')
        
        # Determine emoji based on profit
        if trade['net_profit_sol'] > 0:
            profit_emoji = '🟢'
        elif trade['net_profit_sol'] < 0:
            profit_emoji = '🔴'
        else:
            profit_emoji = '⚪'
            
        # Build visual output
        print(f"\n{'═' * 80}")
        print(f"{profit_emoji} TRADE #{trade['trade_id']:04d} | {ts}")
        print(f"{'─' * 80}")
        print(f"  Route:     {trade['route']}")
        print(f"  Strategy:  {trade['strategy'].upper()}")
        if trade.get('is_simulation'):
            print(f"  Mode:      [SIMULATION] Paper Trading")
        else:
            print(f"  Mode:      {'PAPER' if trade['mode'] == 'paper' else 'LIVE'}")
        print(f"{'─' * 80}")
        print(f"  {'Gross Profit:':<15} +{trade['gross_profit_sol']:.9f} SOL")
        print(f"  {'Jupiter Fees:':<15} -{trade['jupiter_fees_sol']:.9f} SOL")
        print(f"  {'Gas Fees:':<15} -{trade['gas_fees_sol']:.9f} SOL")
        print(f"  {'Slippage:':<15} -{trade['slippage_sol']:.9f} SOL")
        print(f"  {'─' * 50}")
        print(f"  {'Total Fees:':<15} -{trade['total_fees_sol']:.9f} SOL")
        print(f"  {'Net Profit:':<15} {trade['net_profit_sol']:+.9f} SOL")
        print(f"{'─' * 80}")
        print(f"  Balance:     {trade['balance_before_sol']:.6f} SOL → {trade['balance_after_sol']:.6f} SOL")
        print(f"{'═' * 80}")
    
    def print_trade_summary(self, last_n: int = 20):
        """Print summary table of recent trades"""
        if not self.trade_history:
            print("\nNo trades in history yet.")
            return
            
        recent = self.trade_history[-last_n:]
        
        print(f"\n{'═' * 100}")
        print(f"📊 TRADE HISTORY (Last {len(recent)} of {len(self.trade_history)} total)")
        print(f"{'═' * 100}")
        print(f"{'ID':<6} {'Time':<10} {'Route':<35} {'Gross':<12} {'Fees':<12} {'Net':<12}")
        print(f"{'─' * 100}")
        
        for t in recent:
            ts = datetime.fromisoformat(t['timestamp']).strftime('%H:%M:%S')
            gross = f"+{t['gross_profit_sol']:.6f}" if t['gross_profit_sol'] > 0 else f"{t['gross_profit_sol']:.6f}"
            fees = f"{t['total_fees_sol']:.6f}"
            net = f"{t['net_profit_sol']:+.6f}"
            status = 'SIM' if t.get('is_simulation') else t['mode'][:4].upper()
            
            print(f"{t['trade_id']:<6} {ts:<10} {t['route']:<35} {gross:<12} {fees:<12} {net:<12}")
            
        print(f"{'─' * 100}")
        
        # Calculate totals
        total_gross = sum(t['gross_profit_sol'] for t in recent)
        total_fees = sum(t['total_fees_sol'] for t in recent)
        total_net = sum(t['net_profit_sol'] for t in recent)
        wins = sum(1 for t in recent if t['net_profit_sol'] > 0)
        
        print(f"{'SUMMARY':<6} {'':<10} {'':<35} {total_gross:>+12.6f} {total_fees:>12.6f} {total_net:>+12.6f}")
        print(f"{'─' * 100}")
        print(f"Win Rate: {wins}/{len(recent)} ({wins/len(recent)*100:.1f}%) | Total Net: {total_net:+.9f} SOL")
        print(f"{'═' * 100}\n")
        
    def run_arbitrage_strategy(self):
        """
        Strategy: Triangular arbitrage
        Safest aggressive strategy
        Falls back to simulation mode if network fails
        """
        logger.info("Starting arbitrage scanner...")
        
        # Test network connectivity first
        network_available = False
        try:
            import socket
            socket.create_connection(("quote-api.jup.ag", 443), timeout=5)
            network_available = True
            logger.info("✅ Network connectivity confirmed")
        except:
            logger.warning("⚠️  Network unavailable - running in simulation mode")
            logger.info("Simulated opportunities will appear every ~30 seconds")
        
        if not network_available:
            self.run_simulation_mode()
            return
        
        while True:
            try:
                # Scan for opportunities
                quote_amount = int(self.paper_balance * 0.5 * 1e9)  # 50% of balance
                
                opportunities = self.scanner.find_triangular_arbitrage(
                    TOKENS['SOL'],
                    [TOKENS['USDC'], TOKENS['USDT'], TOKENS['JUP']],
                    quote_amount
                )
                
                if opportunities and opportunities[0]['profit_pct'] > 1.0:
                    opp = opportunities[0]
                    logger.info(f"🎯 ARBITRAGE FOUND: {opp['profit_pct']:.2f}% profit")
                    
                    if self.mode == 'live':
                        # Execute real trade
                        pass  # TODO: Implement wallet integration
                    else:
                        # Paper trade simulation
                        pnl = self.simulate_arbitrage(opp, is_simulation=False)
                        logger.info(f"Paper trade P&L: {pnl:.6f} SOL")
                        
                time.sleep(5)  # 5 second scan interval
                
            except Exception as e:
                logger.error(f"Strategy error: {e}")
                time.sleep(10)
    
    def simulate_arbitrage(self, opportunity: Dict, is_simulation: bool = False) -> float:
        """
        Simulate an arbitrage trade
        Includes realistic fees and slippage
        Returns net profit/loss
        """
        balance_before = self.paper_balance
        gross_profit = opportunity['profit'] / 1e9  # Convert lamports to SOL
        
        # Jupiter fees: ~0.2% per swap (two swaps in arbitrage = 0.4%)
        # For simulation, use consistent fee model
        jupiter_fee_rate = 0.004  # 0.4% total for the round-trip
        jupiter_fees = abs(gross_profit * jupiter_fee_rate)
        
        # Network/gas fees: ~0.00001 SOL per signature (typically 1-2 sigs per swap)
        gas_fees = 0.000015  # Conservative estimate for 2 swaps
        
        # Slippage simulation (0.1-0.5% of gross)
        slippage = abs(gross_profit * random.uniform(0.001, 0.005))
        
        total_fees = jupiter_fees + gas_fees + slippage
        net_pnl = gross_profit - total_fees
        
        # Update paper balance
        self.paper_balance += net_pnl
        self.trade_count += 1
        self.risk.record_trade(net_pnl)
        
        # Create detailed trade record
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'trade_id': 0,  # Will be set by log_trade
            'route': opportunity.get('route', 'SOL -> USDC -> SOL'),
            'gross_profit_sol': gross_profit,
            'jupiter_fees_sol': jupiter_fees,
            'gas_fees_sol': gas_fees,
            'slippage_sol': slippage,
            'total_fees_sol': total_fees,
            'net_profit_sol': net_pnl,
            'balance_before_sol': balance_before,
            'balance_after_sol': self.paper_balance,
            'strategy': self.strategy,
            'mode': self.mode,
            'is_simulation': is_simulation,
            'profit_pct': opportunity.get('profit_pct', 0)
        }
        
        self.log_trade(trade_record)
        self.save_state()
            
        return net_pnl
    
    def save_state(self):
        """Save bot state to file"""
        # Calculate fee statistics from trade history
        total_fees = 0
        total_gross = 0
        total_net = 0
        wins = 0
        losses = 0
        
        if self.trade_history:
            total_fees = sum(t['total_fees_sol'] for t in self.trade_history)
            total_gross = sum(t['gross_profit_sol'] for t in self.trade_history)
            total_net = sum(t['net_profit_sol'] for t in self.trade_history)
            wins = sum(1 for t in self.trade_history if t['net_profit_sol'] > 0)
            losses = len(self.trade_history) - wins
        
        state = {
            'balance_sol': self.paper_balance,
            'initial_balance': self.risk.initial_balance,
            'pnl_sol': self.paper_balance - self.risk.initial_balance,
            'pnl_pct': ((self.paper_balance / self.risk.initial_balance) - 1) * 100,
            'trades': self.trade_count,
            'strategy': self.strategy,
            'mode': self.mode,
            'status': 'active',
            'timestamp': datetime.now().timestamp(),
            'message': None,
            'fees': {
                'total_fees_sol': total_fees,
                'total_gross_profit_sol': total_gross,
                'total_net_profit_sol': total_net,
                'fee_efficiency_pct': round((total_fees / total_gross * 100), 4) if total_gross > 0 else 0
            },
            'performance': {
                'wins': wins,
                'losses': losses,
                'win_rate_pct': round((wins / len(self.trade_history) * 100), 2) if self.trade_history else 0,
                'avg_profit_sol': round((sum(t['net_profit_sol'] for t in self.trade_history) / len(self.trade_history)), 9) if self.trade_history else 0
            }
        }
        try:
            with open('jupiter_state.json', 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")
    
    def get_trade_stats(self) -> dict:
        """Get detailed trade statistics"""
        if not self.trade_history:
            return {'message': 'No trades in history'}
        
        total = len(self.trade_history)
        wins = sum(1 for t in self.trade_history if t['net_profit_sol'] > 0)
        losses = total - wins
        
        gross_profits = [t['gross_profit_sol'] for t in self.trade_history]
        net_profits = [t['net_profit_sol'] for t in self.trade_history]
        fees = [t['total_fees_sol'] for t in self.trade_history]
        
        return {
            'total_trades': total,
            'wins': wins,
            'losses': losses,
            'win_rate_pct': (wins / total * 100) if total > 0 else 0,
            'total_gross_sol': sum(gross_profits),
            'total_net_sol': sum(net_profits),
            'total_fees_sol': sum(fees),
            'avg_gross_sol': sum(gross_profits) / total,
            'avg_net_sol': sum(net_profits) / total,
            'avg_fees_sol': sum(fees) / total,
            'best_trade_sol': max(net_profits),
            'worst_trade_sol': min(net_profits),
            'jupiter_fees_total': sum(t['jupiter_fees_sol'] for t in self.trade_history),
            'gas_fees_total': sum(t['gas_fees_sol'] for t in self.trade_history),
            'slippage_total': sum(t['slippage_sol'] for t in self.trade_history)
        }
    
    def run_simulation_mode(self):
        """
        Simulation mode for offline/demo environments
        Generates fake arbitrage opportunities
        """
        logger.info("📊 SIMULATION MODE ACTIVE")
        logger.info("Generating simulated opportunities...")
        
        import random
        
        while True:
            try:
                # Simulate occasional opportunity (10% chance per scan)
                if random.random() < 0.1:
                    # Create fake opportunity
                    profit_pct = random.uniform(0.5, 2.0)
                    gross_profit_lamports = int(self.paper_balance * 0.5 * 1e9 * (profit_pct / 100))
                    
                    opp = {
                        'route': random.choice([
                            'SOL -> USDC -> SOL',
                            'SOL -> USDT -> SOL',
                            'SOL -> JUP -> USDC -> SOL',
                            'SOL -> BONK -> USDC -> SOL'
                        ]),
                        'profit_pct': profit_pct,
                        'profit': gross_profit_lamports,
                        'start_amount': int(self.paper_balance * 0.5 * 1e9),
                        'end_amount': int(self.paper_balance * 0.5 * 1e9) + gross_profit_lamports
                    }
                    
                    logger.info(f"🎯 [SIM] ARBITRAGE FOUND: {profit_pct:.2f}% profit")
                    logger.info(f"    Route: {opp['route']}")
                    
                    # Simulate trade
                    pnl = self.simulate_arbitrage(opp, is_simulation=True)
                    logger.info(f"💰 [SIM] Paper trade P&L: +{pnl:.6f} SOL")
                    logger.info(f"💼 New balance: {self.paper_balance:.4f} SOL")
                    
                else:
                    logger.debug("Scanning for opportunities...")
                    
                time.sleep(30)  # Slower scan in simulation
                
            except Exception as e:
                logger.error(f"Simulation error: {e}")
                time.sleep(30)
    
    def run_momentum_strategy(self):
        """
        Strategy: Momentum chasing
        Buy pumps, sell quickly
        """
        logger.info("Starting momentum strategy...")
        logger.warning("HIGH RISK: Momentum strategy can lose everything quickly")
        
        while True:
            try:
                # This would require price history tracking
                # Placeholder for implementation
                logger.info("Scanning for momentum...")
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Momentum error: {e}")
                time.sleep(10)
    
    def get_status(self) -> Dict:
        """Get current bot status"""
        risk_status = self.risk.get_status()
        
        return {
            'mode': self.mode,
            'strategy': self.strategy,
            'balance_sol': self.paper_balance if self.mode == 'paper' else 'N/A (live)',
            'trades_executed': self.trade_count,
            'risk_status': risk_status,
            'timestamp': datetime.now().isoformat()
        }
    
    def print_dashboard(self, show_recent_trades: int = 5):
        """Print live dashboard with optional trade history"""
        status = self.get_status()
        risk = status['risk_status']
        
        print("\n" + "="*80)
        print("🚀 JUPITER TRADING BOT - LIVE DASHBOARD")
        print("="*80)
        print(f"Mode: {status['mode'].upper()}")
        print(f"Strategy: {status['strategy'].upper()}")
        print()
        print(f"💰 Balance: {status['balance_sol']:.4f} SOL")
        print(f"📊 Total P&L: {risk['pnl']:+.9f} SOL ({risk['pnl_pct']:+.2f}%)")
        print(f"📈 Total Trades: {status['trades_executed']}")
        print(f"⚠️  Daily Loss: {risk['daily_loss']:.4f} / {self.risk.daily_loss_limit} SOL")
        print(f"🎯 Drawdown: {risk['drawdown_pct']:.2f}%")
        
        # Show total fees paid across all trades if history exists
        if self.trade_history:
            total_fees_paid = sum(t['total_fees_sol'] for t in self.trade_history)
            total_gross = sum(t['gross_profit_sol'] for t in self.trade_history)
            fee_efficiency = (total_fees_paid / total_gross * 100) if total_gross > 0 else 0
            print(f"💸 Total Fees Paid: {total_fees_paid:.9f} SOL ({fee_efficiency:.1f}% of gross)")
            
            # Win rate
            wins = sum(1 for t in self.trade_history if t['net_profit_sol'] > 0)
            if self.trade_history:
                print(f"🎯 Win Rate: {wins}/{len(self.trade_history)} ({wins/len(self.trade_history)*100:.1f}%)")
        
        print()
        print(f"Last Update: {status['timestamp']}")
        print("="*80)
        
        # Show recent trades summary
        if show_recent_trades > 0 and self.trade_history:
            recent = self.trade_history[-show_recent_trades:]
            print(f"\n📋 LAST {len(recent)} TRADES (type '!trades' for full log)")
            print("-"*80)
            for t in reversed(recent):
                ts = datetime.fromisoformat(t['timestamp']).strftime('%H:%M:%S')
                pnl = t['net_profit_sol']
                emoji = '🟢' if pnl > 0 else '🔴' if pnl < 0 else '⚪'
                sim = '[SIM]' if t.get('is_simulation') else ''
                print(f"  Trade #{t['trade_id']:04d} {emoji} {ts} {sim:6} | {t['route']:30} | Net: {pnl:+.6f} SOL")
            print("="*80)


def main():
    """
    CLI entry point
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Jupiter Trading Bot')
    parser.add_argument('--mode', choices=['paper', 'live'], default='paper',
                       help='Trading mode (default: paper)')
    parser.add_argument('--strategy', choices=['arbitrage', 'momentum', 'range'],
                       default='arbitrage', help='Trading strategy')
    parser.add_argument('--capital', type=float, default=1.0,
                       help='Initial capital in SOL')
    parser.add_argument('--private-key', help='Solana wallet private key (live mode only)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 JUPITER SOLANA TRADING BOT")
    print("=" * 60)
    print()
    print(f"Mode: {args.mode}")
    print(f"Strategy: {args.strategy}")
    print(f"Capital: {args.capital} SOL")
    print()
    
    if args.mode == 'live':
        print("⚠️  LIVE MODE - REAL FUNDS AT RISK")
        confirm = input("Type 'LIVE' to confirm: ")
        if confirm != 'LIVE':
            print("Aborted.")
            return
    
    # Initialize bot
    bot = JupiterTradingBot(
        private_key=args.private_key,
        initial_capital_sol=args.capital,
        strategy=args.strategy,
        mode=args.mode
    )
    
    # Run strategy
    if args.strategy == 'arbitrage':
        bot.run_arbitrage_strategy()
    elif args.strategy == 'momentum':
        bot.run_momentum_strategy()
    else:
        print(f"Strategy {args.strategy} not yet implemented")


if __name__ == '__main__':
    import random
    main()
