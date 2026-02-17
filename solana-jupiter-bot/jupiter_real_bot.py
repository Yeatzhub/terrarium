"""
Real Jupiter DEX Trading Bot
Queries live Jupiter API for actual arbitrage opportunities
"""

import os
import sys
import time
import json
import random
import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal, ROUND_DOWN

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('jupiter_real.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RealJupiterBot')

# Token addresses (Solana mainnet)
TOKENS = {
    'SOL': 'So11111111111111111111111111111111111111112',
    'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    'USDT': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
    'BONK': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
    'JUP': 'JUPyiwrYJFskUPiHa7hkeRQoUfXh2pQ5rM9N9XzC5T7',
}

class RealJupiterBot:
    """
    Real Jupiter DEX bot using live API quotes
    NO SIMULATION - only real market data
    """
    
    BASE_URL = "https://quote-api.jup.ag/v6"
    
    def __init__(self, initial_capital_sol: float = 1.0, mode: str = 'paper'):
        self.mode = mode  # 'paper' or 'live'
        self.session = requests.Session()
        self.paper_balance = initial_capital_sol
        self.initial_capital = initial_capital_sol
        self.trade_count = 0
        self.trade_history = []
        self.wins = 0
        self.losses = 0
        
        # Trading parameters
        self.min_profit_pct = 0.3  # Minimum 0.3% profit to trade
        self.max_slippage_bps = 50  # 0.5% max slippage
        self.trade_size_pct = 0.5  # Use 50% of balance per trade
        
        # Fee structure (real Jupiter fees)
        self.jupiter_fee_bps = 10  # 0.1% platform fee
        self.sol_gas_fee = 0.00001  # ~0.00001 SOL per signature
        
        logger.info(f"🚀 RealJupiterBot initialized")
        logger.info(f"   Mode: {mode}")
        logger.info(f"   Capital: {initial_capital_sol} SOL")
        logger.info(f"   Min Profit: {self.min_profit_pct}%")
        
    def test_connectivity(self) -> bool:
        """Test if Jupiter API is reachable"""
        try:
            # Try to get SOL price as connectivity test
            response = self.session.get(
                "https://price.jup.ag/v4/price?ids=So11111111111111111111111111111111111111112",
                timeout=5
            )
            response.raise_for_status()
            data = response.json()
            sol_price = data.get('data', {}).get(TOKENS['SOL'], {}).get('price')
            if sol_price:
                logger.info(f"✅ Jupiter API connected (SOL: ${sol_price:.2f})")
                return True
        except Exception as e:
            logger.error(f"❌ Cannot reach Jupiter API: {e}")
            return False
        return False
    
    def get_quote(self, input_mint: str, output_mint: str, amount_lamports: int) -> Optional[Dict]:
        """Get real quote from Jupiter DEX"""
        params = {
            'inputMint': input_mint,
            'outputMint': output_mint,
            'amount': str(amount_lamports),
            'slippageBps': self.max_slippage_bps,
        }
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}/quote",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Quote failed: {e}")
            return None
    
    def find_arbitrage_opportunities(self, amount_sol: float) -> List[Dict]:
        """
        Scan for REAL arbitrage opportunities
        A -> B -> A (triangular arbitrage)
        """
        opportunities = []
        amount_lamports = int(amount_sol * 1e9)
        
        # Routes to check
        routes = [
            ('SOL', 'USDC', 'SOL'),
            ('SOL', 'USDT', 'SOL'),
            ('SOL', 'JUP', 'SOL'),
            ('SOL', 'USDC', 'USDT', 'SOL'),  # Double hop
            ('SOL', 'BONK', 'USDC', 'SOL'),
        ]
        
        for route in routes:
            if len(route) == 3:  # Simple round trip
                token_a = TOKENS[route[0]]
                token_b = TOKENS[route[1]]
                
                # Step 1: A -> B
                quote1 = self.get_quote(token_a, token_b, amount_lamports)
                if not quote1:
                    continue
                    
                out_amount_1 = int(quote1.get('outAmount', 0))
                if out_amount_1 == 0:
                    continue
                
                # Step 2: B -> A
                quote2 = self.get_quote(token_b, token_a, out_amount_1)
                if not quote2:
                    continue
                    
                out_amount_2 = int(quote2.get('outAmount', 0))
                if out_amount_2 == 0:
                    continue
                
                # Calculate profit
                profit_lamports = out_amount_2 - amount_lamports
                profit_pct = (profit_lamports / amount_lamports) * 100
                
                # Calculate real fees
                jupiter_fees = amount_lamports * (self.jupiter_fee_bps / 10000) * 2  # 2 swaps
                gas_fees = self.sol_gas_fee * 2 * 1e9  # 2 transactions
                
                net_profit = profit_lamports - jupiter_fees - gas_fees
                net_profit_pct = (net_profit / amount_lamports) * 100
                
                if net_profit > 0:  # Only positive net profit
                    opportunities.append({
                        'route': f"{route[0]} -> {route[1]} -> {route[2]}",
                        'amount_in': amount_sol,
                        'gross_profit_sol': profit_lamports / 1e9,
                        'jupiter_fees_sol': jupiter_fees / 1e9,
                        'gas_fees_sol': (gas_fees / 1e9),
                        'net_profit_sol': net_profit / 1e9,
                        'net_profit_pct': net_profit_pct,
                        'price_impact_1': float(quote1.get('priceImpactPct', 0)),
                        'price_impact_2': float(quote2.get('priceImpactPct', 0)),
                        'raw_quotes': [quote1, quote2]
                    })
                    
            elif len(route) == 4:  # Double hop
                token_a = TOKENS[route[0]]
                token_b = TOKENS[route[1]]
                token_c = TOKENS[route[2]]
                
                quote1 = self.get_quote(token_a, token_b, amount_lamports)
                if not quote1:
                    continue
                out_1 = int(quote1.get('outAmount', 0))
                
                quote2 = self.get_quote(token_b, token_c, out_1)
                if not quote2:
                    continue
                out_2 = int(quote2.get('outAmount', 0))
                
                quote3 = self.get_quote(token_c, token_a, out_2)
                if not quote3:
                    continue
                out_3 = int(quote3.get('outAmount', 0))
                
                profit_lamports = out_3 - amount_lamports
                jupiter_fees = amount_lamports * (self.jupiter_fee_bps / 10000) * 3
                gas_fees = self.sol_gas_fee * 3 * 1e9
                
                net_profit = profit_lamports - jupiter_fees - gas_fees
                net_profit_pct = (net_profit / amount_lamports) * 100
                
                if net_profit > 0:
                    opportunities.append({
                        'route': f"{route[0]} -> {route[1]} -> {route[2]} -> {route[3]}",
                        'amount_in': amount_sol,
                        'gross_profit_sol': profit_lamports / 1e9,
                        'jupiter_fees_sol': jupiter_fees / 1e9,
                        'gas_fees_sol': (gas_fees / 1e9),
                        'net_profit_sol': net_profit / 1e9,
                        'net_profit_pct': net_profit_pct,
                        'price_impact_1': float(quote1.get('priceImpactPct', 0)),
                        'price_impact_2': float(quote2.get('priceImpactPct', 0)),
                        'price_impact_3': float(quote3.get('priceImpactPct', 0)),
                        'raw_quotes': [quote1, quote2, quote3]
                    })
        
        # Sort by net profit
        opportunities.sort(key=lambda x: x['net_profit_pct'], reverse=True)
        return opportunities
    
    def execute_trade(self, opportunity: Dict) -> bool:
        """
        Execute a paper trade based on real opportunity
        In live mode, this would submit transactions
        """
        balance_before = self.paper_balance
        
        # Calculate trade size
        trade_amount = self.paper_balance * self.trade_size_pct
        
        # Scale opportunity to actual trade size
        scale_factor = trade_amount / opportunity['amount_in']
        net_profit = opportunity['net_profit_sol'] * scale_factor
        
        # Execute (paper trade)
        self.paper_balance += net_profit
        self.trade_count += 1
        
        if net_profit > 0:
            self.wins += 1
        else:
            self.losses += 1
        
        # Log trade
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'trade_id': self.trade_count,
            'route': opportunity['route'],
            'amount_in_sol': trade_amount,
            'net_profit_sol': net_profit,
            'balance_before': balance_before,
            'balance_after': self.paper_balance,
            'mode': self.mode,
            'opportunity': opportunity
        }
        
        self.trade_history.append(trade_record)
        self._log_trade(trade_record)
        self._save_state()
        
        return True
    
    def _log_trade(self, trade: Dict):
        """Print trade to console"""
        ts = datetime.fromisoformat(trade['timestamp']).strftime('%H:%M:%S')
        emoji = '🟢' if trade['net_profit_sol'] > 0 else '🔴'
        
        print(f"\n{'═' * 70}")
        print(f"{emoji} TRADE #{trade['trade_id']} | {ts} | {trade['route']}")
        print(f"   Amount: {trade['amount_in_sol']:.4f} SOL")
        print(f"   Net P&L: {trade['net_profit_sol']:+.6f} SOL")
        print(f"   Balance: {trade['balance_before']:.6f} → {trade['balance_after']:.6f}")
        print(f"{'═' * 70}")
        
        logger.info(f"Trade executed: {trade['route']} | P&L: {trade['net_profit_sol']:.6f} SOL")
    
    def _save_state(self):
        """Save bot state"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'mode': self.mode,
            'balance_sol': self.paper_balance,
            'initial_capital': self.initial_capital,
            'total_pnl_sol': self.paper_balance - self.initial_capital,
            'total_pnl_pct': ((self.paper_balance / self.initial_capital) - 1) * 100,
            'trade_count': self.trade_count,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': (self.wins / self.trade_count * 100) if self.trade_count > 0 else 0
        }
        
        try:
            with open('jupiter_real_state.json', 'w') as f:
                json.dump(state, f, indent=2)
            with open('jupiter_real_trades.json', 'w') as f:
                json.dump(self.trade_history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def print_status(self):
        """Print current status"""
        pnl = self.paper_balance - self.initial_capital
        pnl_pct = ((self.paper_balance / self.initial_capital) - 1) * 100
        
        print(f"\n{'=' * 70}")
        print(f"🚀 REAL JUPITER BOT STATUS")
        print(f"{'=' * 70}")
        print(f"Mode: {self.mode.upper()} (Real Jupiter DEX Quotes)")
        print(f"Balance: {self.paper_balance:.6f} SOL")
        print(f"P&L: {pnl:+.6f} SOL ({pnl_pct:+.2f}%)")
        print(f"Trades: {self.trade_count} (W: {self.wins} | L: {self.losses})")
        if self.trade_count > 0:
            print(f"Win Rate: {self.wins/self.trade_count*100:.1f}%")
        print(f"{'=' * 70}\n")
    
    def run(self, scan_interval: int = 30):
        """
        Main bot loop - scans for real arbitrage opportunities
        """
        print("\n" + "=" * 70)
        print("🪐 REAL JUPITER DEX ARBITRAGE BOT")
        print("=" * 70)
        print("\n⚠️  Using REAL market data from Jupiter DEX")
        print("⚠️  Trades only execute when profitable opportunities found")
        print("⚠️  Paper mode = no real money at risk\n")
        
        # Test connectivity
        if not self.test_connectivity():
            print("❌ Cannot reach Jupiter API. Check internet connection.")
            print("The bot requires active internet to query live DEX prices.")
            return
        
        print(f"✅ Connected to Jupiter DEX")
        print(f"⏱️  Scan interval: {scan_interval}s")
        print(f"💰 Trade size: {self.trade_size_pct*100}% of balance")
        print(f"🎯 Min profit: {self.min_profit_pct}%\n")
        
        self.print_status()
        
        try:
            while True:
                # Calculate trade amount
                trade_amount = self.paper_balance * self.trade_size_pct
                
                logger.info(f"Scanning for arbitrage with {trade_amount:.4f} SOL...")
                
                # Find real opportunities
                opportunities = self.find_arbitrage_opportunities(trade_amount)
                
                if opportunities:
                    best = opportunities[0]
                    logger.info(f"🎯 Found {len(opportunities)} opportunities!")
                    logger.info(f"   Best: {best['route']} | Net: {best['net_profit_pct']:.3f}%")
                    
                    if best['net_profit_pct'] >= self.min_profit_pct:
                        logger.info("✅ Profit above threshold - executing!")
                        self.execute_trade(best)
                    else:
                        logger.info(f"⏭️  Best opportunity ({best['net_profit_pct']:.3f}%) below threshold")
                else:
                    logger.info("⏭️  No profitable opportunities found")
                
                time.sleep(scan_interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Bot stopped by user")
            self.print_status()
            self._save_state()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--capital', type=float, default=1.0, help='Initial capital in SOL')
    parser.add_argument('--mode', choices=['paper', 'live'], default='paper')
    parser.add_argument('--interval', type=int, default=30, help='Scan interval in seconds')
    
    args = parser.parse_args()
    
    bot = RealJupiterBot(
        initial_capital_sol=args.capital,
        mode=args.mode
    )
    bot.run(scan_interval=args.interval)
