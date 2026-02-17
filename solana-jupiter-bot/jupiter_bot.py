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

from jupiter_api import JupiterAPI, TOKENS
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
        self.api = JupiterAPI()
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
        """
        logger.info("Starting arbitrage scanner...")
        
        while True:
            try:
                # Scan for opportunities
                quote_amount = int(self.paper_balance * 0.5 * 1e9)  # 50% of balance
                
                opportunities = self.api.find_triangular_arbitrage(
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
            
        return net_pnl
    
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
