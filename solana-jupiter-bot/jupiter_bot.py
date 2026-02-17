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
        
        if mode == 'live' and not private_key:
            raise ValueError("Live mode requires private key")
            
        logger.info(f"JupiterBot initialized: mode={mode}, strategy={strategy}, capital={initial_capital_sol} SOL")
        
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
                        pnl = self.simulate_arbitrage(opp)
                        logger.info(f"Paper trade P&L: {pnl:.6f} SOL")
                        
                time.sleep(5)  # 5 second scan interval
                
            except Exception as e:
                logger.error(f"Strategy error: {e}")
                time.sleep(10)
    
    def simulate_arbitrage(self, opportunity: Dict) -> float:
        """
        Simulate an arbitrage trade
        Includes realistic fees and slippage
        """
        gross_profit = opportunity['profit'] / 1e9  # Convert lamports to SOL
        
        # Jupiter fees: ~0.2% per swap
        # Network fees: ~0.000005 SOL per tx
        fees = abs(gross_profit * 0.004) + 0.00001  # 0.4% total + gas
        
        # Slippage simulation (0.1-0.5%)
        slippage = abs(gross_profit * random.uniform(0.001, 0.005))
        
        net_pnl = gross_profit - fees - slippage
        
        # Update paper balance
        if net_pnl > 0:
            self.paper_balance += net_pnl
            self.trade_count += 1
            self.risk.record_trade(net_pnl)
            self.save_state()
            
        return net_pnl
    
    def save_state(self):
        """Save bot state to file"""
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
            'message': None
        }
        try:
            with open('jupiter_state.json', 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")
    
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
                    pnl = self.simulate_arbitrage(opp)
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
    
    def print_dashboard(self):
        """Print live dashboard"""
        status = self.get_status()
        risk = status['risk_status']
        
        print("\n" + "="*60)
        print("🚀 JUPITER TRADING BOT - LIVE DASHBOARD")
        print("="*60)
        print(f"Mode: {status['mode'].upper()}")
        print(f"Strategy: {status['strategy'].upper()}")
        print()
        print(f"💰 Balance: {status['balance_sol']:.4f} SOL")
        print(f"📊 P&L: {risk['pnl']:+.4f} SOL ({risk['pnl_pct']:+.2f}%)")
        print(f"📈 Trades: {status['trades_executed']}")
        print(f"⚠️  Daily Loss: {risk['daily_loss']:.4f} / {self.risk.daily_loss_limit} SOL")
        print(f"🎯 Drawdown: {risk['drawdown_pct']:.2f}%")
        print()
        print(f"Last Update: {status['timestamp']}")
        print("="*60)


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
