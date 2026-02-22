"""
XRP Pionex Trading Bot
Main orchestrator for backtesting and paper trading
"""

import os
import sys
import time
import argparse
from decimal import Decimal
from typing import Optional

from backtester import Backtester, optimize_strategy
from paper_trader import PaperTrader
from strategies import get_strategy
from pionex_api import PionexAPI

class XRPPionexBot:
    """
    Main trading bot for XRP on Pionex
    Supports backtesting, paper trading, and (eventually) live trading
    """
    
    def __init__(self, mode: str = 'paper'):
        self.mode = mode
        self.pionex_api = PionexAPI()
        self.paper_trader = None
        self.strategy = None
        
    def run_backtest(self, strategy_name: str = 'momentum', 
                     optimize: bool = False, **strategy_params) -> dict:
        """
        Run backtest for a strategy
        """
        print(f"\n🧪 BACKTEST MODE: {strategy_name}")
        print(f"{'='*60}")
        
        # Initialize backtester
        backtester = Backtester(
            strategy_name=strategy_name,
            initial_xrp=Decimal('100'),
            initial_usdt=Decimal('1000'),
            **strategy_params
        )
        
        # Fetch candle data
        candles = backtester.fetch_historical_data(
            symbol="XRP_USDT",
            interval="1h",
            limit=720  # 30 days of hourly data
        )
        
        if optimize:
            # Run parameter optimization
            print(f"\n🔧 Running parameter optimization for {strategy_name}...")
            
            if strategy_name == 'momentum':
                param_ranges = {
                    'rsi_period': [10, 14, 20],
                    'rsi_oversold': [20, 25, 30],
                    'rsi_overbought': [70, 75, 80]
                }
            elif strategy_name == 'mean_reversion':
                param_ranges = {
                    'lookback': [10, 15, 20, 25],
                    'entry_z': [1.5, 2.0, 2.5],
                    'exit_z': [0.3, 0.5, 0.7]
                }
            else:
                param_ranges = strategy_params
            
            opt_results = optimize_strategy(strategy_name, candles, param_ranges)
            return opt_results
        else:
            # Run single backtest
            result = backtester.run_backtest(candles)
            return {'result': result}
    
    def run_multiple_strategy_backtests(self) -> dict:
        """
        Test all strategies to find best performer
        """
        print("\n" + "="*70)
        print("🚀 COMPREHENSIVE STRATEGY TESTING")
        print("="*70)
        print("Testing 4 strategies to find best performer...")
        print(f"Goal: {'='*70}")
        print("  - Minimum 50% win rate")
        print("  - Positive returns")
        print("  - Double 100 XRP starting balance")
        print("="*70)
        
        # Test momentum strategy with variations
        strategies = [
            ('momentum', {'rsi_period': 14, 'rsi_oversold': 30, 'rsi_overbought': 70}),
            ('momentum', {'rsi_period': 10, 'rsi_oversold': 25, 'rsi_overbought': 75}),
            ('bollinger', {'period': 20, 'squeeze_threshold': 0.02}),
            ('mean_reversion', {'lookback': 20, 'entry_z': 2.0, 'exit_z': 0.5}),
            ('trend_following', {'fast_ema': 9, 'slow_ema': 21}),
            ('trend_following', {'fast_ema': 5, 'slow_ema': 20}),
        ]
        
        results = []
        
        for strategy_name, params in strategies:
            print(f"\n{'='*70}")
            print(f"📊 Testing: {strategy_name} with {params}")
            print(f"{'='*70}")
            
            backtester = Backtester(strategy_name, Decimal('100'), Decimal('1000'), **params)
            candles = backtester.fetch_historical_data()
            result = backtester.run_backtest(candles)
            
            if result:
                results.append({
                    'strategy': strategy_name,
                    'params': params,
                    'result': result
                })
        
        # Find best strategy
        if results:
            # Filter for strategies with at least 5 trades
            valid_results = [r for r in results if r['result'].total_trades >= 5]
            
            if valid_results:
                # First, prioritize win rate >= 50%
                good_win_rates = [r for r in valid_results if r['result'].win_rate >= 50]
                
                if good_win_rates:
                    # Among good win rates, pick highest profit
                    best = max(good_win_rates, key=lambda r: r['result'].profit_percent)
                else:
                    # If no 50% win rate, pick best win rate
                    best = max(valid_results, key=lambda r: r['result'].win_rate)
                
                print("\n" + "="*70)
                print("🏆 BEST PERFORMING STRATEGY")
                print("="*70)
                print(f"Strategy: {best['strategy']}")
                print(f"Parameters: {best['params']}")
                print(f"Win Rate: {best['result'].win_rate:.2f}%")
                print(f"Profit: {best['result'].profit_percent:.2f}%")
                print(f"Final XRP: {best['result'].final_xrp:.4f}")
                
                if best['result'].win_rate >= 50:
                    print("✅ GOAL ACHIEVED: Win rate >= 50%")
                
                if best['result'].final_xrp >= 200:
                    print("🎯 GOAL ACHIEVED: Doubled XRP!")
                
                return {
                    'best_strategy': best['strategy'],
                    'best_params': best['params'],
                    'best_result': best['result'],
                    'all_results': results
                }
        
        print("\n❌ No valid results from any strategy")
        return {'all_results': results}
    
    def run_paper_trading(self, strategy_name: str = 'momentum', 
                         interval_minutes: int = 5, **strategy_params):
        """
        Run paper trading with selected strategy
        """
        print(f"\n💰 PAPER TRADING MODE: {strategy_name}")
        print(f"{'='*60}")
        print("⚠️  PAPER TRADING ONLY - NO REAL FUNDS AT RISK")
        print(f"{'='*60}")
        print(f"Starting balance: 100 XRP | $1000 USDT")
        print(f"Check interval: {interval_minutes} minutes")
        print(f"Strategy: {strategy_name}")
        print(f"{'='*60}")
        print("\nPress Ctrl+C to stop\n")
        
        # Initialize components
        self.paper_trader = PaperTrader(
            initial_xrp=Decimal('100'),
            initial_usdt=Decimal('1000'),
            state_file='live_paper_state.json'
        )
        
        self.strategy = get_strategy(strategy_name, **strategy_params)
        
        try:
            while True:
                # Get current price
                ticker = self.pionex_api.get_ticker("XRP_USDT")
                current_price = Decimal(str(ticker['last_price']))
                
                # Get recent candles for signal
                candles = self.pionex_api.get_klines("XRP_USDT", "5m", 30)
                
                # Check position
                has_position = 'XRP' in self.paper_trader.positions
                
                # Generate signal
                signal = self.strategy.generate_signal(candles, has_position)
                
                timestamp = datetime.now().isoformat()
                
                # Execute based on signal
                if signal.action == 'buy' and not has_position:
                    # Use 50% of USDT for buying
                    usdt_to_use = self.paper_trader.usdt_balance * Decimal('0.5')
                    amount = usdt_to_use / current_price
                    amount = amount.quantize(Decimal('0.0001'), rounding='ROUND_DOWN')
                    
                    if amount > 0:
                        self.paper_trader.buy(amount, current_price, timestamp)
                        
                elif signal.action == 'sell' and has_position:
                    position = self.paper_trader.positions.get('XRP')
                    if position:
                        self.paper_trader.sell(position.amount, current_price, timestamp)
                
                # Print status
                balance = self.paper_trader.get_balance()
                print(f"[{timestamp}] Price: ${float(current_price):.4f} | "
                      f"XRP: {balance['xrp']:.4f} | USDT: ${balance['usdt']:.2f} | "
                      f"Signal: {signal.action}")
                
                # Save state after each check (even if no trade)
                self.paper_trader._save_state()
                
                # Check if goal reached
                if balance['xrp'] >= 200:
                    print("\n🎯 GOAL ACHIEVED: Doubled XRP!")
                    self.paper_trader.print_performance()
                    break
                
                # Wait for next check
                time.sleep(interval_minutes * 60)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping paper trading...")
            self.paper_trader.print_performance()
            print("💾 State saved for next session")
    
    def iterate_and_improve(self, target_win_rate: float = 50.0):
        """
        Iterate through strategies and parameters to achieve target win rate
        """
        print("\n" + "="*70)
        print("🔁 ITERATIVE IMPROVEMENT PROCESS")
        print("="*70)
        print(f"Target: {target_win_rate}% win rate")
        print(f"Starting: 100 XRP")
        print(f"Goal: Double to 200 XRP")
        print("="*70)
        
        iteration = 0
        best_result = None
        
        # Phase 1: Test all base strategies
        print("\n📌 Phase 1: Testing all base strategies...")
        phase1_results = self.run_multiple_strategy_backtests()
        
        if 'best_result' in phase1_results:
            best = phase1_results['best_result']
            iteration += 1
            
            if best.win_rate >= target_win_rate and best.final_xrp >= 200:
                print(f"\n🎉 ITERATION {iteration}: GOALS ACHIEVED!")
                return phase1_results
            
            best_result = best
        
        # Phase 2: Optimize best strategy
        if best_result:
            print(f"\n📌 Phase 2: Optimizing {best_result.strategy_name}...")
            best_strategy = 'momentum'  # Simplified for demo
            
            opt_results = self.run_backtest(
                strategy_name=best_strategy,
                optimize=True
            )
            
            if 'best_result' in opt_results:
                iteration += 1
                opt_result = opt_results['best_result']
                
                if opt_result and opt_result.win_rate >= target_win_rate:
                    print(f"\n🎉 ITERATION {iteration}: OPTIMIZED TO TARGET!")
                    return {
                        'strategy': best_strategy,
                        'params': opt_results['best_params'],
                        'result': opt_result
                    }
                elif opt_result and (not best_result or opt_result.win_rate > best_result.win_rate):
                    best_result = opt_result
        
        # Phase 3: Test variations
        print(f"\n📌 Phase 3: Testing strategy variations...")
        
        variations = [
            ('momentum', {'rsi_period': 7, 'rsi_oversold': 20, 'rsi_overbought': 80}),
            ('momentum', {'rsi_period': 21, 'rsi_oversold': 35, 'rsi_overbought': 65}),
            ('mean_reversion', {'lookback': 10, 'entry_z': 1.5, 'exit_z': 0.3}),
            ('mean_reversion', {'lookback': 30, 'entry_z': 2.5, 'exit_z': 1.0}),
        ]
        
        for strategy_name, params in variations:
            iteration += 1
            print(f"\n📊 ITERATION {iteration}: {strategy_name} with {params}")
            
            result_dict = self.run_backtest(strategy_name, **params)
            result = result_dict.get('result')
            
            if result and result.win_rate >= target_win_rate:
                print(f"🎉 ITERATION {iteration}: TARGET ACHIEVED!")
                return {
                    'strategy': strategy_name,
                    'params': params,
                    'result': result
                }
            elif result and (not best_result or result.win_rate > best_result.win_rate):
                best_result = result
                print(f"  New best win rate: {result.win_rate:.2f}%")
        
        # Summary
        print("\n" + "="*70)
        print("🔚 ITERATION COMPLETE")
        print("="*70)
        
        if best_result:
            print(f"Best Strategy: {best_result.strategy_name}")
            print(f"Best Win Rate: {best_result.win_rate:.2f}%")
            print(f"Best Profit: {best_result.profit_percent:.2f}%")
            
            if best_result.win_rate >= target_win_rate:
                print("✅ Win rate goal achieved!")
            else:
                print(f"❌ Could not reach {target_win_rate}% win rate")
                print(f"   Best achieved: {best_result.win_rate:.2f}%")
            
            if best_result.final_xrp >= 200:
                print("✅ Doubling goal achieved!")
        
        return {'best_result': best_result}

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='XRP Pionex Trading Bot')
    parser.add_argument('mode', choices=['backtest', 'paper', 'iterate'],
                       help='Bot mode: backtest, paper trading, or iterate')
    parser.add_argument('--strategy', default='momentum',
                       choices=['momentum', 'bollinger', 'mean_reversion', 'trend_following'],
                       help='Trading strategy to use')
    parser.add_argument('--optimize', action='store_true',
                       help='Optimize strategy parameters')
    parser.add_argument('--interval', type=int, default=5,
                       help='Check interval in minutes (paper mode)')
    
    args = parser.parse_args()
    
    # Create bot
    bot = XRPPionexBot(mode=args.mode)
    
    if args.mode == 'backtest':
        # Run single backtest
        result = bot.run_backtest(
            strategy_name=args.strategy,
            optimize=args.optimize
        )
        print("\n" + "="*60)
        print("Backtest complete!")
        
    elif args.mode == 'iterate':
        # Run iterative improvement
        results = bot.iterate_and_improve(target_win_rate=50.0)
        print("\n" + "="*60)
        print("Iteration complete!")
        
    elif args.mode == 'paper':
        # Run paper trading
        bot.run_paper_trading(
            strategy_name=args.strategy,
            interval_minutes=args.interval
        )
        print("\n" + "="*60)
        print("Paper trading complete!")

if __name__ == "__main__":
    from datetime import datetime
    main()