import requests
import json

# Get real prices
ids = 'solana,usd-coin,tether,bonk,jupiter-exchange-solana'
url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd"
r = requests.get(url, timeout=15)
prices = r.json()

print("🪐 REAL MARKET DATA")
print("=" * 50)
print(f"SOL:  ${prices['solana']['usd']:.2f}")
print(f"USDC: ${prices['usd-coin']['usd']:.4f}")
print(f"USDT: ${prices['tether']['usd']:.4f}")
print(f"BONK: ${prices['bonk']['usd']:.6f}")
print(f"JUP:  ${prices['jupiter-exchange-solana']['usd']:.4f}")
print("=" * 50)

# Model arbitrage SOL -> USDC -> SOL
sol_price = prices['solana']['usd']
usdc_price = prices['usd-coin']['usd']

# DEX spread model (0.1% each way)
trade_sol = 0.5  # 0.5 SOL
value_usd = trade_sol * sol_price

# Buy USDC (pay 0.1% spread)
usdc_received = value_usd / usdc_price * 0.999
# Sell USDC back to SOL (pay 0.1% spread)
sol_back = usdc_received * usdc_price / sol_price * 0.999

# Fees
jupiter_fee = trade_sol * 0.001  # 0.1%
gas_fee = 0.00002  # 2 tx

net_profit = sol_back - trade_sol - jupiter_fee - gas_fee
net_profit_pct = (net_profit / trade_sol) * 100

print(f"\n📊 ARBITRAGE MODEL: 0.5 SOL -> USDC -> SOL")
print(f"   Start: {trade_sol:.4f} SOL (${value_usd:.2f})")
print(f"   After round-trip: {sol_back:.6f} SOL")
print(f"   Gross P&L: {sol_back - trade_sol:+.6f} SOL")
print(f"   Jupiter fees: -{jupiter_fee:.6f} SOL")
print(f"   Gas fees: -{gas_fee:.6f} SOL")
print(f"   NET P&L: {net_profit:+.6f} SOL ({net_profit_pct:.3f}%)")
print(f"\n   ⚠️  Negative = No arbitrage (market efficient)")

# What profit do we need?
min_profit_for_fees = jupiter_fee + gas_fee
min_price_discrepancy = (min_profit_for_fees / trade_sol) + 0.002  # 0.2% spread
print(f"\n💡 To profit, need price discrepancy > {min_price_discrepancy*100:.2f}%")
