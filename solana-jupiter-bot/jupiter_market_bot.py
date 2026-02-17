"""
Jupiter Bot with Real Market Data
Uses CoinGecko for price reference + realistic DEX modeling
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('jupiter_real.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('RealMarketBot')

# Token info with typical DEX spreads
TOKENS = {
    'SOL': {'coingecko_id': 'solana', 'decimals': 9, 'spread_bps': 10},  # 0.1% spread
    'USDC': {'coingecko_id': 'usd-coin', 'decimals': 6, 'spread_bps': 5},
    'USDT': {'coingecko_id': 'tether', 'decimals': 6, 'spread_bps': 5},
    'BONK': {'coingecko_id': 'bonk', 'decimals': 5, 'spread_bps': 50},  # 0.5% for memecoins
    'JUP': {'coingecko_id': 'jupiter-exchange-solana', 'decimals': 6, 'spread_bps': 15},
}

class RealMarketBot:
    """
    Bot using real market data from CoinGecko
    Models realistic DEX spreads and arbitrage
    """
    
    def __init__(self, initial_capital_sol: float = 1.0, mode: str = 'paper'):
        self.mode = mode
        self.paper_balance = initial_capital_sol
        self.initial_capital = initial_capital_sol
        self.trade_count = 0
        self.trade_history = []
        self.wins = 0
        self.losses = 0
        
        self.min_profit_pct = 0.3  # 0.3% min profit
        self.trade_size_pct = 0.5  # 50% of balance per trade
        self.jupiter_fee_bps = 10  # 0.1%
        self.sol_gas_fee = 0.00001
        
        self.prices = {}  # Real prices from CoinGecko
        self.last_price_update = 0
        
        logger.info(f"🚀 RealMarketBot initialized")
        logger.info(f"   Mode: {mode}")
        logger.info(f"   Capital: {initial_capital_sol} SOL")
        
    def fetch_real_prices(self) -> bool:
        """Get real prices from CoinGecko"""
        try:
            ids = ','.join([t['coingecko_id'] for t in TOKENS.values()])
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
            
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            for token, info in TOKENS.items():
                cg_id = info['coingecko_id']
                if cg_id in data:
                    self.prices[token] = data[cg_id]['usd']
            
            self.last_price_update = time.time()
            logger.info(f"✅ Prices updated: SOL=${self.prices.get('SOL', 'N/A')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Price fetch failed: {e}")
            return False
    
    def get_dex_quote(self, from_token: str, to_token: str, amount_from: float) -> Dict:
        """
        Simulate realistic DEX quote based on real market data
        Models: spread, slippage, price impact
        """
        if not self.prices:
            return None
        
        price_from = self.prices.get(from_token)
        price_to = self.prices.get(to_token)
        
        if not price_from or not price_to:
            return None
        
        # Base exchange rate
        base_rate = price_from / price_to
        
        # DEX spread (buy slightly higher, sell slightly lower)
        spread_from = TOKENS[from_token]['spread_bps'] / 10000
        spread_to = TOKENS[to_token]['spread_bps'] / 10000
        total_spread = spread_from + spread_to
        
        # Slippage based on trade size (larger = more slippage)
        # Assume $10k depth for small tokens, $100k for SOL/USDC
        depth_usd = 100000 if from_token in ['SOL', 'USDC', 'USDT'] else 10000
        trade_value_usd = amount_from * price_from
        slippage = min(trade_value_usd / depth_usd * 0.01, 0.005)  # Max 0.5%
        
        # Effective rate (worse for trader due to spread + slippage)
        effective_rate = base_rate * (1 - total_spread - slippage)
        
        # Amount out
        amount_to = amount_from * effective_rate
        
        # Price impact
        price_impact_pct = (total_spread + slippage) * 100
        
        return {
            'amount_in': amount_from,
            'amount_out': amount_to,
            'exchange_rate': effective_rate,
            'base_rate': base_rate,
            'spread_pct': total_spread * 100,
            'slippage_pct': slippage * 100,
            'price_impact_pct': price_impact_pct
        }
    
    def find_arbitrage(self, amount_sol: float) -> List[Dict]:
        """Find arbitrage using real price data"""
        opportunities = []
        
        # Update prices if stale (>60 seconds)
        if time.time() - self.last_price_update > 60:
            if not self.fetch_real_prices():
                return []
        
        # Test routes
        routes = [
            ('SOL', 'USDC', 'SOL'),
            ('SOL', 'USDT', 'SOL'),
            ('SOL', 'JUP', 'SOL'),
            ('SOL', 'USDC', 'USDT', 'SOL'),
        ]
        
        for route in routes:
            if len(route) == 3:
                # Step 1: SOL -> Token
                q1 = self.get_dex_quote(route[0], route[1], amount_sol)
                if not q1:
                    continue
                
                # Step 2: Token -> SOL
                q2 = self.get_dex_quote(route[1], route[2], q1['amount_out'])
                if not q2:
                    continue
                
                # Calculate
                final_amount = q2['amount_out']
                gross_profit = final_amount - amount_sol
                gross_profit_pct = (gross_profit / amount_sol) * 100
                
                # Fees
                jupiter_fees = amount_sol * (self.jupiter_fee_bps / 10000) * 2
                gas_fees = self.sol_gas_fee * 2
                
                net_profit = gross_profit - jupiter_fees - gas_fees
                net_profit_pct = (net_profit / amount_sol) * 100
                
                if net_profit > 0:
                    opportunities.append({
                        'route': f"{route[0]} -> {route[1]} -> {route[2]}",
                        'amount_in': amount_sol,
                        'amount_out': final_amount,
                        'gross_profit_sol': gross_profit,
                        'gross_profit_pct': gross_profit_pct,
                        'jupiter_fees_sol': jupiter_fees,
                        'gas_fees_sol': gas_fees,
                        'net_profit_sol': net_profit,
                        'net_profit_pct': net_profit_pct,
                        'price_impact_1': q1['price_impact_pct'],
                        'price_impact_2': q2['price_impact_pct'],
                        'base_prices': {k: self.prices.get(k) for k in route}
                    })
            
            elif len(route) == 4:
                # Triple hop: A -> B -> C -> A
                q1 = self.get_dex_quote(route[0], route[1], amount_sol)
                if not q1:
                    continue
                q2 = self.get_dex_quote(route[1], route[2], q1['amount_out'])
                if not q2:
                    continue
                q3 = self.get_dex_quote(route[2], route[3], q2['amount_out'])
                if not q3:
                    continue
                
                final_amount = q3['amount_out']
                gross_profit = final_amount - amount_sol
                jupiter_fees = amount_sol * (self.jupiter_fee_bps / 10000) * 3
                gas_fees = self.sol_gas_fee * 3
                
                net_profit = gross_profit - jupiter_fees - gas_fees
                
                if net_profit > 0:
                    opportunities.append({
                        'route': f"{route[0]} -> {route[1]} -> {route[2]} -> {route[3]}",
                        'amount_in': amount_sol,
                        'net_profit_sol': net_profit,
                        'net_profit_pct': (net_profit / amount_sol) * 100,
                        'price_impact_1': q1['price_impact_pct'],
                        'price_impact_2': q2['price_impact_pct'],
                        'price_impact_3': q3['price_impact_pct'],
                    })
        
        opportunities.sort(key=lambda x: x['net_profit_pct'], reverse=True)
        return opportunities
    
    def execute_trade(self, opp: Dict) -> bool:
        """Execute paper trade"""
        balance_before = self.paper_balance
        trade_amount = self.paper_balance * self.trade_size_pct
        
        # Scale profit
        scale = trade_amount / opp['amount_in']
        net_profit = opp['net_profit_sol'] * scale
        
        self.paper_balance += net_profit
        self.trade_count += 1
        
        if net_profit > 0:
            self.wins += 1
        else:
            self.losses += 1
        
        trade_record = {
            'timestamp': datetime.now().isoformat(),
            'trade_id': self.trade_count,
            'route': opp['route'],
            'amount_in_sol': trade_amount,
            'net_profit_sol': net_profit,
            'balance_before': balance_before,
            'balance_after': self.paper_balance,
            'mode': self.mode,
            'real_prices': self.prices.copy(),
            'opportunity': opp
        }
        
        self.trade_history.append(trade_record)
        self._log_trade(trade_record)
        self._save_state()
        
        return True
    
    def _log_trade(self, trade: Dict):
        """Log trade to console"""
        ts = datetime.fromisoformat(trade['timestamp']).strftime('%H:%M:%S')
        emoji = '🟢' if trade['net_profit_sol'] > 0 else '🔴'
        
        print(f"\n{'═' * 70}")
        print(f"{emoji} TRADE #{trade['trade_id']} | {ts}")
        print(f"   Route: {trade['route']}")
        print(f"   Amount: {trade['amount_in_sol']:.4f} SOL")
        print(f"   Net P&L: {trade['net_profit_sol']:+.6f} SOL")
        print(f"   Balance: {trade['balance_before']:.6f} → {trade['balance_after']:.6f}")
        print(f"   Prices: SOL=${trade['real_prices'].get('SOL', 'N/A')}, USDC=$1.00")
        print(f"{'═' * 70}")
        
        logger.info(f"Trade: {trade['route']} | P&L: {trade['net_profit_sol']:.6f} SOL")
    
    def _save_state(self):
        """Save state"""
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
            'win_rate': (self.wins / self.trade_count * 100) if self.trade_count > 0 else 0,
            'last_prices': self.prices
        }
        
        try:
            with open('jupiter_market_state.json', 'w') as f:
                json.dump(state, f, indent=2)
            with open('jupiter_market_trades.json', 'w') as f:
                json.dump(self.trade_history, f, indent=2)
        except Exception as e:
            logger.error(f"Save failed: {e}")
    
    def print_status(self):
        """Print status"""
        pnl = self.paper_balance - self.initial_capital
        pnl_pct = ((self.paper_balance / self.initial_capital) - 1) * 100
        
        print(f"\n{'=' * 70}")
        print(f"🪐 REAL MARKET BOT STATUS")
        print(f"{'=' * 70}")
        print(f"Mode: {self.mode.upper()} (Real CoinGecko Prices)")
        print(f"Current SOL Price: ${self.prices.get('SOL', 'N/A')}")
        print(f"Balance: {self.paper_balance:.6f} SOL (${self.paper_balance * self.prices.get('SOL', 0):.2f})")
        print(f"P&L: {pnl:+.6f} SOL ({pnl_pct:+.2f}%)")
        print(f"Trades: {self.trade_count} (W: {self.wins} | L: {self.losses})")
        if self.trade_count > 0:
            print(f"Win Rate: {self.wins/self.trade_count*100:.1f}%")
        print(f"{'=' * 70}\n")
    
    def run(self, scan_interval: int = 30):
        """Main loop"""
        print("\n" + "=" * 70)
        print("🪐 REAL MARKET ARBITRAGE BOT")
        print("=" * 70)
        print("\n✅ Uses REAL prices from CoinGecko")
        print("✅ Models realistic DEX spreads")
        print("✅ Realistic Jupiter fees (0.1%)")
        print("✅ Realistic gas fees (0.00001 SOL)")
        print("⚠️  Paper mode = no real money at risk\n")
        
        # Get initial prices
        if not self.fetch_real_prices():
            print("❌ Cannot fetch market data")
            return
        
        print(f"✅ Connected to CoinGecko")
        print(f"⏱️  Scan interval: {scan_interval}s")
        print(f"💰 Trade size: {self.trade_size_pct*100}% of balance")
        print(f"🎯 Min profit: {self.min_profit_pct}%\n")
        
        self.print_status()
        
        try:
            while True:
                trade_amount = self.paper_balance * self.trade_size_pct
                
                logger.info(f"Scanning for arbitrage... SOL=${self.prices.get('SOL', 'N/A')}")
                
                opportunities = self.find_arbitrage(trade_amount)
                
                if opportunities:
                    best = opportunities[0]
                    logger.info(f"🎯 Found {len(opportunities)} opportunities!")
                    logger.info(f"   Best: {best['route']} | Net: {best['net_profit_pct']:.3f}%")
                    logger.info(f"   Gross: {best['gross_profit_pct']:.3f}% | After fees: {best['net_profit_pct']:.3f}%")
                    
                    if best['net_profit_pct'] >= self.min_profit_pct:
                        logger.info("✅ Executing trade!")
                        self.execute_trade(best)
                    else:
                        logger.info(f"⏭️  Below threshold ({best['net_profit_pct']:.3f}% < {self.min_profit_pct}%)")
                else:
                    logger.info("⏭️  No profitable opportunities")
                
                time.sleep(scan_interval)
                
        except KeyboardInterrupt:
            print("\n\n👋 Bot stopped")
            self.print_status()
            self._save_state()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--capital', type=float, default=1.0)
    parser.add_argument('--mode', choices=['paper', 'live'], default='paper')
    parser.add_argument('--interval', type=int, default=30)
    
    args = parser.parse_args()
    
    bot = RealMarketBot(
        initial_capital_sol=args.capital,
        mode=args.mode
    )
    bot.run(scan_interval=args.interval)
