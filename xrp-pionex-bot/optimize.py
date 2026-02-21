#!/usr/bin/env python3
"""
Comprehensive XRP Trading Strategy Optimization
Run extensive parameter sweeps to find 50%+ win rate strategy
"""

import json
import os
from decimal import Decimal
from itertools import product
import numpy as np

from backtester import Backtester
from strategies import get_strategy

def run_optimization():
    """Run comprehensive parameter optimization"""
    
    print("="*70)
    print("🔬 COMPREHENSIVE STRATEGY OPTIMIZATION")
    print("="*70)
    print("Testing 50+ parameter combinations...")
    print("="*70)
    
    # Parameter sweeps
    momentum_params = {
        'name': 'momentum',
        'ranges': {
            'rsi_period': [10, 14, 21],
            'rsi_oversold': [20, 25, 30, 35],
            'rsi_overbought': [65, 70, 75, 80]
        }
    }
    
    mean_rev_params = {
        'name': 'mean_reversion',
        'ranges': {
            'lookback': [10, 15, 20, 30],
            'entry_z': [1.5, 2.0, 2.5, 3.0],
            'exit_z': [0.3, 0.5, 0.7]
        }
    }
    
    trend_params = {
        'name': 'trend_following',
        'ranges': {
            'fast_ema': [5, 9, 12],
            'slow_ema': [20, 21, 26]
        }
    }
    
    all_results = []
    test_count = 0
    
    # Generate all combinations for each strategy
    for strategy_config in [momentum_params, mean_rev_params, trend_params]:
        strategy_name = strategy_config['name']
        ranges = strategy_config['ranges']
        
        # Generate parameter combinations
        keys = list(ranges.keys())
        values = [ranges[k] for k in keys]
        combinations = list(product(*values))
        
        print(f"\n{'='*70}")
        print(f"🧪 Testing {strategy_name}: {len(combinations)} combinations")
        print(f"{'='*70}")
        
        for combo in combinations:
            test_count += 1
            params = dict(zip(keys, combo))
            
            print(f"\n[{test_count}] {strategy_name}: {params}")
            
            try:
                # Run backtest
                backtester = Backtester(
                    strategy_name=strategy_name,
                    initial_xrp=Decimal('100'),
                    initial_usdt=Decimal('1000'),
                    **params
                )
                
                # Fetch longer data (more candles = more signals)
                candles = backtester.fetch_historical_data(
                    symbol="XRP_USDT",
                    interval="1h",
                    limit=1000  # Longer period for more trades
                )
                
                # Run backtest
                result = backtester.run_backtest(candles)
                
                if result and result.total_trades >= 5:
                    all_results.append({
                        'strategy': strategy_name,
                        'params': params,
                        'win_rate': result.win_rate,
                        'total_pnl': result.total_pnl,
                        'profit_percent': result.profit_percent,
                        'total_trades': result.total_trades,
                        'final_xrp': result.final_xrp,
                        'max_drawdown': result.max_drawdown
                    })
                    
                    # Check for target
                    if result.win_rate >= 50.0 and result.final_xrp >= 200:
                        print(f"\n🎯 TARGET ACHIEVED!")
                        print(f"   Strategy: {strategy_name}")
                        print(f"   Params: {params}")
                        print(f"   Win Rate: {result.win_rate:.2f}%")
                        print(f"   Final XRP: {result.final_xrp:.4f}")
                        return {
                            'best': {
                                'strategy': strategy_name,
                                'params': params,
                                'result': result
                            },
                            'all_results': all_results
                        }
                        
            except Exception as e:
                print(f"   Error: {e}")
                continue
    
    # Find best result
    if all_results:
        print("\n" + "="*70)
        print("🏆 ALL RESULTS SUMMARY")
        print("="*70)
        
        # Filter for strategies with at least 5 trades
        valid = [r for r in all_results if r['total_trades'] >= 5]
        
        if valid:
            # Best by win rate
            best_wr = max(valid, key=lambda x: x['win_rate'])
            print(f"\nBest Win Rate: {best_wr['win_rate']:.2f}%")
            print(f"  Strategy: {best_wr['strategy']}")
            print(f"  Params: {best_wr['params']}")
            print(f"  Total Trades: {best_wr['total_trades']}")
            print(f"  Final XRP: {best_wr['final_xrp']:.4f}")
            
            # Best by profit
            best_profit = max(valid, key=lambda x: x['profit_percent'])
            print(f"\nBest Profit: {best_profit['profit_percent']:.2f}%")
            print(f"  Strategy: {best_profit['strategy']}")
            print(f"  Params: {best_profit['params']}")
            
            # Best by final XRP amount
            best_xrp = max(valid, key=lambda x: x['final_xrp'])
            print(f"\nBest Final XRP: {best_xrp['final_xrp']:.4f}")
            print(f"  Strategy: {best_xrp['strategy']}")
            print(f"  Params: {best_xrp['params']}")
            
            # Check if any met target
            winners = [r for r in valid if r['win_rate'] >= 50]
            if winners:
                print(f"\n✅ {len(winners)} strategies achieved 50%+ win rate")
            else:
                print(f"\n❌ No strategy achieved 50%+ win rate")
                print(f"   Best: {best_wr['win_rate']:.2f}% win rate")
        else:
            print("No valid results found")
    
    # Save all results
    with open('optimization_results.json', 'w') as f:
        json.dump({
            'total_tests': test_count,
            'results': all_results
        }, f, indent=2)
    print(f"\n💾 Saved {len(all_results)} results to optimization_results.json")
    
    return {'results': all_results}

if __name__ == "__main__":
    run_optimization()