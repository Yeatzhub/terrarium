# Polymarket Arbitrage Scanner
import requests
import json
from typing import Dict, List, Tuple
import time

class PolymarketArbitrageScanner:
    """Scan Polymarket markets for arbitrage opportunities"""
    
    def __init__(self):
        self.base_url = "https://clob.polymarket.com"
        self.opportunities = []
    
    def fetch_active_markets(self, limit: int = 100) -> List[Dict]:
        """Fetch active markets from CLOB API"""
        try:
            url = f"{self.base_url}/markets"
            params = {
                "active": "true",
                "closed": "false",
                "limit": limit
            }
            response = requests.get(url, params=params, timeout=30)
            if response.status_code == 200:
                data = response.json()
                markets = data.get("data", [])  # API returns data key
                print(f"✅ Fetched {len(markets)} active markets (count: {data.get('count', 0)})")
                return markets
            else:
                print(f"❌ API error: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Error fetching markets: {e}")
            return []
    
    def check_binary_arbitrage(self, market: Dict) -> Tuple[float, str, str]:
        """
        Check if binary market has arbitrage
        Returns: (sum, buy_opportunity, sell_opportunity)
        """
        tokens = market.get("tokens", [])
        if len(tokens) != 2:
            return None, None, None
        
        yes_price = tokens[0].get("price", 0)
        no_price = tokens[1].get("price", 0)
        
        # Prices should sum to 1.00
        price_sum = yes_price + no_price
        
        buy_opportunity = None
        sell_opportunity = None
        
        if price_sum < 0.995 and price_sum > 0:
            # Market is underpriced - buy both sides
            potential_profit = round(1.00 - price_sum, 4)
            buy_opportunity = f"💹 BUY BOTH: Cost ${price_sum:.4f} → Return $1.00 | Profit: +{potential_profit:.4f} ({potential_profit/price_sum*100:.2f}%)"
        
        if price_sum > 1.005:
            # Market is overpriced
            potential_profit = round(price_sum - 1.00, 4)
            sell_opportunity = f"📉 OVERPRICED: Sum ${price_sum:.4f} | Sell both would lose {potential_profit:.4f}"
        
        return price_sum, buy_opportunity, sell_opportunity
    
    def scan_for_arbitrage(self, markets: List[Dict]) -> List[Dict]:
        """Scan all markets for arbitrage"""
        opportunities = []
        
        for market in markets:
            question = market.get("question", "Unknown")
            market_id = market.get("condition_id", "")
            
            # Skip markets that are already closed
            if market.get("closed", True):
                continue
            
            # Check binary arbitrage
            price_sum, buy_opp, sell_opp = self.check_binary_arbitrage(market)
            
            if buy_opp:
                tokens = market.get("tokens", [])
                opp = {
                    "type": "arbitrage",
                    "market": question[:60] + "..." if len(question) > 60 else question,
                    "condition_id": market_id,
                    "strategy": "DUTCH_BOOK",  # Buy both outcomes
                    "sum": price_sum,
                    "cost": f"${price_sum:.4f}",
                    "return": "$1.00",
                    "profit": round(1.00 - price_sum, 4),
                    "profit_pct": round((1.00 - price_sum) / price_sum * 100, 2),
                    "details": buy_opp,
                    "tokens": [
                        {
                            "outcome": t.get("outcome", ""),
                            "price": t.get("price", 0),
                            "token_id": t.get("token_id", "")
                        } for t in tokens[:2]
                    ],
                    "time_left": market.get("end_date_iso", "unknown")
                }
                opportunities.append(opp)
                
        return opportunities
    
    def display_opportunities(self, opportunities: List[Dict]):
        """Display found opportunities"""
        if not opportunities:
            print("\n📊 No arbitrage opportunities found in current markets")
            print("   Prices are market-efficient (sum ≈ $1.00)")
            return
        
        print(f"\n🎯 FOUND {len(opportunities)} ARBITRAGE OPPORTUNITIES\n")
        print("="*80)
        
        for i, opp in enumerate(opportunities, 1):
            print(f"\n{i}. {opp['type'].upper()} OPPORTUNITY")
            print(f"   Market: {opp['market']}")
            print(f"   Strategy: {opp['strategy']}")
            print(f"   Cost: {opp['cost']}")
            print(f"   Return: {opp['return']}")
            print(f"   ⭐ Profit: ${opp['profit']:.4f} ({opp['profit_pct']}%)")
            print(f"   Resolution: {opp['time_left'][:10]}")
            print(f"   Token IDs:")
            for token in opp['tokens']:
                print(f"      - {token['outcome']}: ${token['price']:.4f}")
        
        print("\n" + "="*80)
        print("\n💡 TO EXECUTE:")
        print("   1. Buy YES token (Outcome 1)")
        print("   2. Buy NO token (Outcome 2)")
        print("   3. Wait for market to resolve")
        print("   4. One side wins $1.00, net profit = $1.00 - total_cost")
        print("\n⚠️  REQUIREMENTS:")
        print("   - USDC on Polygon/MATIC network")
        print("   - Gas fees reduce actual profit")
        print("   - Market must resolve within timeframe")
    
    def run_scan(self):
        """Full scan and report"""
        print("🚀 Starting Polymarket Arbitrage Scan\n")
        print("Fetching active markets...")
        
        markets = self.fetch_active_markets(limit=200)
        
        if not markets:
            print("\n❌ No markets returned. API may be rate-limited or unreachable.")
            return []
        
        print(f"Scanning {len(markets)} markets for arbitrage...")
        opportunities = self.scan_for_arbitrage(markets)
        self.display_opportunities(opportunities)
        
        return opportunities


def main():
    scanner = PolymarketArbitrageScanner()
    opportunities = scanner.run_scan()
    
    # Save results
    if opportunities:
        with open('/home/yeatz/.openclaw/workspace/btc-trading-bot/polymarket_arbitrage.json', 'w') as f:
            json.dump(opportunities, f, indent=2)
        print(f"\n💾 Saved {len(opportunities)} opportunities to polymarket_arbitrage.json")

if __name__ == "__main__":
    main()
