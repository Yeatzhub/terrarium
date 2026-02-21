#!/usr/bin/env python3
"""
Long Backtest for XRP Mean Reversion Strategy
Verify pricing and performance over extended period
"""

from decimal import Decimal
from backtester import Backtester

def run_long_backtest():
    """Run extended backtest with verified pricing"""
    
    print("="*70)
    print("🔬 LONG BACKTEST - Mean Reversion Strategy")
    print("="*70)
    print("Strategy: Mean Reversion")
    print("Parameters: lookback=15, entry_z=2.5, exit_z=0.7")
    print("Data: 5000 candles (≈ 7 months)")
    print("="*70)
    
    # Initialize backtester with winning strategy
    backtester = Backtester(
        strategy_name='mean_reversion',
        initial_xrp=Decimal('100'),
        initial_usdt=Decimal('1000'),
        lookback=15,
        entry_z=2.5,
        exit_z=0.7
    )
    
    # Fetch 5000 candles (longer period)
    candles = backtester.fetch_historical_data(
        symbol="XRP_USDT",
        interval="1h",
        limit=5000
    )
    
    # Verify pricing
    if candles:
        closes = [c['close'] for c in candles]
        print(f"\n📊 PRICE VERIFICATION:")
        print(f"  Candles: {len(candles)}")
        print(f"  First price: ${candles[0]['close']:.4f}")
        print(f"  Last price: ${candles[-1]['close']:.4f}")
        print(f"  Min: ${min(closes):.4f}")
        print(f"  Max: ${max(closes):.4f}")
        print(f"  Average: ${sum(closes)/len(closes):.4f}")
        print(f"  Price change: {((closes[-1] - closes[0]) / closes[0] * 100):.2f}%")
        
        # Check if price is realistic (XRP should be around $0.50-$3.00)
        avg_price = sum(closes) / len(closes)
        if avg_price < 0.5 or avg_price > 3.0:
            print(f"\n⚠️  WARNING: Price seems unrealistic!")
            print(f"   Expected: ~$1.44 (current market)")
            print(f"   Simulated avg: ${avg_price:.4f}")
        else:
            print(f"\n✅ Price range looks realistic")
    
    # Run backtest
    print("\n🚀 Running backtest...")
    result = backtester.run_backtest(candles)
    
    if result:
        print("\n" + "="*70)
        print("📊 LONG BACKTEST RESULTS")
        print("="*70)
        print(f"Total Trades: {result.total_trades}")
        print(f"Winning Trades: {result.winning_trades}")
        print(f"Losing Trades: {result.losing_trades}")
        print(f"Win Rate: {result.win_rate:.2f}%")
        print(f"Total P&L: ${result.total_pnl:.2f}")
        print(f"Profit: {result.profit_percent:.2f}%")
        print(f"Max Drawdown: {result.max_drawdown:.2f}%")
        print(f"Final XRP: {result.final_xrp:.4f}")
        print(f"Final USDT: ${result.final_usdt:.2f}")
        
        if result.win_rate >= 50:
            print("\n✅ WIN RATE GOAL ACHIEVED: 50%+")
        else:
            print(f"\n❌ Win rate below goal: {result.win_rate:.1f}% < 50%")
        
        if result.final_xrp >= 200:
            print("🎯 DOUBLING GOAL ACHIEVED!")
        else:
            print(f"🎯 Need {200 - result.final_xrp:.2f} more XRP to double")
        
        # Calculate expected trades per month
        trades_per_month = result.total_trades / (len(candles) / 720)
        print(f"\n📈 Trades per month: {trades_per_month:.1f}")
    
    return result

if __name__ == "__main__":
    run_long_backtest()