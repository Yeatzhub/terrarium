"""
XRP Strategy Backtester
Test strategies on historical data to find 50%+ win rate
"""

import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from decimal import Decimal
from dataclasses import dataclass, asdict

from paper_trader import PaperTrader
from strategies import get_strategy
from pionex_api import PionexAPI

@dataclass
class BacktestResult:
    """Backtest results summary"""
    strategy_name: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_pnl: float
    max_drawdown: float
    final_xrp: float
    final_usdt: float
    profit_percent: float
    start_date: str
    end_date: str
    parameters: Dict

class Backtester:
    """
    Backtesting engine for XRP strategies
    """
    
    def __init__(self, strategy_name: str, initial_xrp: Decimal = Decimal('100'),
                 initial_usdt: Decimal = Decimal('1000'), **strategy_params):
        self.strategy_name = strategy_name
        self.strategy = get_strategy(strategy_name, **strategy_params)
        self.initial_xrp = initial_xrp
        self.initial_usdt = initial_usdt
        self.strategy_params = strategy_params
        self.pionex_api = PionexAPI()
        
    def fetch_historical_data(self, symbol: str = "XRP_USDT", 
                              interval: str = "1h", limit: int = 720) -> List[Dict]:
        """Fetch historical candle data for backtesting"""
        print(f"📊 Fetching {limit} candles of {symbol} ({interval}) for backtesting...")
        candles = self.pionex_api.get_klines(symbol, interval, limit)
        print(f"✅ Fetched {len(candles)} candles")
        return candles
    
    def run_backtest(self, candles: List[Dict] = None, 
                     symbol: str = "XRP_USDT") -> BacktestResult:
        """
        Run strategy backtest
        """
        # Fetch data if not provided
        if candles is None:
            candles = self.fetch_historical_data(symbol)
        
        if len(candles) < 50:
            print("❌ Insufficient data for backtesting")
            return None
        
        # Initialize paper trader
        trader = PaperTrader(self.initial_xrp, self.initial_usdt,
                           state_file=f'backtest_{self.strategy_name}.json')
        trader.reset()  # Start fresh
        
        # Track equity curve
        equity_history = []
        max_equity = float(self.initial_xrp * Decimal('2.0') + self.initial_usdt)
        max_drawdown = 0.0
        
        print(f"\n🚀 Starting backtest: {self.strategy.name}")
        print(f"📊 Testing on {len(candles)} candles")
        print(f"💰 Starting balance: {float(self.initial_xrp)} XRP | ${float(self.initial_usdt)} USDT")
        print("="*60)
        
        # Run through each candle
        for i in range(20, len(candles)):
            # Get window of candles for indicator calculation
            window = candles[max(0, i-50):i+1]
            current_candle = candles[i]
            timestamp = datetime.fromtimestamp(current_candle['timestamp'] / 1000).isoformat()
            
            # Check if we have position
            has_position = 'XRP' in trader.positions
            
            # Generate signal
            signal = self.strategy.generate_signal(window, has_position)
            current_price = Decimal(str(current_candle['close']))
            
            # Execute trades
            if signal.action == 'buy' and not has_position:
                # Calculate position size (use 50% of USDT for each trade)
                usdt_to_use = trader.usdt_balance * Decimal('0.5')
                amount = usdt_to_use / current_price
                amount = amount.quantize(Decimal('0.0001'), rounding='ROUND_DOWN')
                
                if amount > 0:
                    trader.buy(amount, current_price, timestamp)
                    print(f"  📈 BUY signal @ ${float(current_price):.4f} | Confidence: {signal.confidence:.2f}")
                    print(f"     Reason: {signal.reason}")
                    
            elif signal.action == 'sell' and has_position:
                # Sell all XRP
                position = trader.positions.get('XRP')
                if position:
                    trader.sell(position.amount, current_price, timestamp)
                    print(f"  📉 SELL signal @ ${float(current_price):.4f} | Confidence: {signal.confidence:.2f}")
                    print(f"     Reason: {signal.reason}")
            
            # Track equity and drawdown
            current_equity = float(trader._get_total_equity_usd())
            equity_history.append({
                'timestamp': timestamp,
                'equity': current_equity,
                'price': float(current_price)
            })
            
            if current_equity > max_equity:
                max_equity = current_equity
            
            drawdown = (max_equity - current_equity) / max_equity * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # Close any open positions at end of backtest
        if 'XRP' in trader.positions:
            print("\n📉 Closing open position at end of backtest...")
            position = trader.positions['XRP']
            final_price = Decimal(str(candles[-1]['close']))
            trader.sell(position.amount, final_price, equity_history[-1]['timestamp'])
        
        # Calculate results
        stats = trader.get_performance_stats()
        
        result = BacktestResult(
            strategy_name=self.strategy.name,
            total_trades=stats['total_trades'],
            winning_trades=stats['winning_trades'],
            losing_trades=stats['losing_trades'],
            win_rate=stats['win_rate'],
            total_pnl=stats['total_pnl'],
            avg_pnl=stats['avg_pnl'],
            max_drawdown=max_drawdown,
            final_xrp=stats['current_xrp'],
            final_usdt=stats['current_usdt'],
            profit_percent=stats['profit_percent'],
            start_date=equity_history[0]['timestamp'] if equity_history else "",
            end_date=equity_history[-1]['timestamp'] if equity_history else "",
            parameters=self.strategy_params
        )
        
        # Print results
        self._print_backtest_results(result)
        
        # Save results
        self.save_result(result)
        
        return result
    
    def _print_backtest_results(self, result: BacktestResult):
        """Print backtest results"""
        print("\n" + "="*60)
        print(f"📊 BACKTEST RESULTS: {result.strategy_name}")
        print("="*60)
        print(f"Total Trades: {result.total_trades}")
        print(f"Winning Trades: {result.winning_trades}")
        print(f"Losing Trades: {result.losing_trades}")
        print(f"Win Rate: {result.win_rate:.2f}%")
        print(f"Total P&L: ${result.total_pnl:.2f}")
        print(f"Average P&L: ${result.avg_pnl:.2f}")
        print(f"Max Drawdown: {result.max_drawdown:.2f}%")
        print(f"Final XRP: {result.final_xrp:.4f}")
        print(f"Final USDT: ${result.final_usdt:.2f}")
        print(f"Profit: {result.profit_percent:.2f}%")
        
        # Goal assessment
        if result.win_rate >= 50:
            print("✅ WIN RATE GOAL ACHIEVED: 50%+")
        else:
            print(f"❌ Win rate below goal: {result.win_rate:.1f}% < 50%")
        
        if result.final_xrp >= 200:
            print("🎯 DOUBLING GOAL ACHIEVED!")
        else:
            remaining = 200 - result.final_xrp
            print(f"🎯 Need {remaining:.2f} more XRP to double")
        
        print("="*60)
    
    def save_result(self, result: BacktestResult, filename: str = 'backtest_results.json'):
        """Save backtest results"""
        results_data = {
            'backtest_date': datetime.now().isoformat(),
            'strategy': result.strategy_name,
            'parameters': result.parameters,
            'results': asdict(result)
        }
        
        # Load existing results
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                all_results = json.load(f)
        else:
            all_results = {'backtests': []}
        
        all_results['backtests'].append(results_data)
        
        with open(filename, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        print(f"💾 Results saved to {filename}")
    
    def test_multiple_strategies(self, candles: List[Dict] = None) -> List[BacktestResult]:
        """Test multiple strategies and return best performer"""
        strategies_to_test = [
            ('momentum', {}),
            ('bollinger', {'period': 20}),
            ('mean_reversion', {'lookback': 20}),
            ('trend_following', {'fast_ema': 9, 'slow_ema': 21}),
        ]
        
        results = []
        
        print("\n" + "="*70)
        print("🧪 TESTING MULTIPLE STRATEGIES")
        print("="*70)
        
        for strategy_name, params in strategies_to_test:
            print(f"\n{'='*70}")
            print(f"Testing: {strategy_name}")
            print(f"{'='*70}")
            
            # Fresh candles for each test
            if candles is None:
                test_candles = self.fetch_historical_data()
            else:
                test_candles = candles
            
            backtester = Backtester(strategy_name, self.initial_xrp, 
                                   self.initial_usdt, **params)
            result = backtester.run_backtest(test_candles)
            
            if result:
                results.append(result)
        
        # Find best strategy
        if results:
            best = max(results, key=lambda r: r.win_rate if r.total_trades > 5 else 0)
            print("\n" + "="*70)
            print(f"🏆 BEST STRATEGY: {best.strategy_name}")
            print(f"   Win Rate: {best.win_rate:.2f}%")
            print(f"   Total P&L: ${best.total_pnl:.2f}")
            print("="*70)
        
        return results

def optimize_strategy(strategy_name: str, candles: List[Dict],
                     param_ranges: Dict) -> Dict:
    """
    Optimize strategy parameters using grid search
    """
    print(f"\n🔧 Optimizing {strategy_name} parameters...")
    print(f"Parameter ranges: {param_ranges}")
    
    best_result = None
    best_params = None
    best_score = 0
    
    # Simple grid search (can be expanded)
    from itertools import product
    
    keys = list(param_ranges.keys())
    values = [param_ranges[k] for k in keys]
    
    for combo in product(*values):
        params = dict(zip(keys, combo))
        backtester = Backtester(strategy_name, Decimal('100'), Decimal('1000'), **params)
        result = backtester.run_backtest(candles)
        
        if result and result.total_trades > 5:
            # Score = win rate * profit (weighted)
            score = result.win_rate * (1 + result.profit_percent / 100)
            
            if score > best_score:
                best_score = score
                best_result = result
                best_params = params
                print(f"  New best: {params} -> Win rate: {result.win_rate:.2f}%")
    
    if best_params:
        print(f"\n🏆 OPTIMAL PARAMETERS: {best_params}")
        print(f"   Win Rate: {best_result.win_rate:.2f}%")
        print(f"   Profit: {best_result.profit_percent:.2f}%")
    
    return {
        'best_params': best_params,
        'best_result': best_result,
        'score': best_score
    }

# Example usage
if __name__ == "__main__":
    # Test single strategy
    backtester = Backtester('momentum', initial_xrp=Decimal('100'))
    result = backtester.run_backtest()
    
    if result and result.win_rate < 50:
        print("\n⚠️ Win rate below 50%, trying other strategies...")
        backtester.test_multiple_strategies()