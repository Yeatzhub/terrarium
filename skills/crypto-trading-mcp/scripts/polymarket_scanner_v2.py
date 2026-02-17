#!/usr/bin/env python3
"""
Polymarket Arbitrage Scanner v2.0
- Finds TOP 5 best arbitrage opportunities
- Implied probability calculations
- Correlated market pair detection
- Timestamped JSON output
- Cron-ready for hourly execution

API: https://clob.polymarket.com/markets
"""

import requests
import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import re
from dataclasses import dataclass, asdict
import time


@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity"""
    rank: int
    type: str
    market: str
    condition_id: str
    strategy: str
    sum: float
    cost: float
    profit: float
    profit_pct: float
    implied_prob_yes: float
    implied_prob_no: float
    yes_price: float
    no_price: float
    market_probability: float
    liquidity: float
    volume: float
    end_date: str
    time_left_hours: float
    tokens: List[Dict]
    timestamp: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        return data


@dataclass
class CorrelatedPair:
    """Represents a correlated market pair"""
    rank: int
    primary_market: str
    primary_condition_id: str
    secondary_market: str
    secondary_condition_id: str
    relationship_type: str
    confidence: float
    primary_price: float
    secondary_price: float
    implied_correlation: float
    notes: str
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PolymarketArbitrageScannerV2:
    """
    Enhanced Polymarket Arbitrage Scanner
    Features:
    - Top 5 arbitrage opportunities ranking
    - Implied probability calculations
    - Correlated market detection
    - JSON output with timestamps
    """
    
    def __init__(self):
        self.base_url = "https://clob.polymarket.com"
        self.opportunities: List[ArbitrageOpportunity] = []
        self.correlated_pairs: List[CorrelatedPair] = []
        self.all_markets: List[Dict] = []
        self.timestamp = datetime.now().isoformat()
        
        # Configuration
        self.ARBITRAGE_THRESHOLD = 0.985  # Sum must be < this to be viable
        self.MAX_FETCH_LIMIT = 1000
        self.TOP_N = 5
        
    def fetch_active_markets(self, limit: int = 1000) -> List[Dict]:
        """Fetch active markets from CLOB API with pagination"""
        all_markets = []
        offset = 0
        
        print(f"🔄 Fetching markets from Polymarket CLOB API...")
        
        while len(all_markets) < limit:
            batch_size = min(500, limit - len(all_markets))
            
            try:
                url = f"{self.base_url}/markets"
                params = {
                    "active": "true",
                    "closed": "false",
                    "limit": batch_size,
                    "offset": offset
                }
                
                response = requests.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    markets = data.get("data", [])
                    
                    if not markets:
                        break
                    
                    all_markets.extend(markets)
                    offset += len(markets)
                    
                    print(f"   Fetched {len(markets)} markets (total: {len(all_markets)})")
                    
                else:
                    print(f"   ⚠️ API error: {response.status_code}")
                    break
                    
            except Exception as e:
                print(f"   ⚠️ Error: {e}")
                break
            
            time.sleep(0.1)  # Rate limiting
        
        print(f"✅ Total markets fetched: {len(all_markets)}")
        return all_markets
    
    def parse_end_date(self, end_date_iso: str) -> Tuple[datetime, float]:
        """Parse end date and calculate hours remaining"""
        try:
            if not end_date_iso:
                return datetime.now(), 0
            end_date = datetime.fromisoformat(end_date_iso.replace('Z', '+00:00'))
            now = datetime.now(end_date.tzinfo)
            hours_left = (end_date - now).total_seconds() / 3600
            return end_date, max(0, hours_left)
        except:
            return datetime.now(), 0
    
    def calculate_implied_probability(self, price: float) -> float:
        """
        Calculate implied probability from market price.
        In binary markets, price ≈ implied probability.
        """
        return round(price * 100, 2)  # Convert to percentage
    
    def calculate_market_probability(self, yes_price: float, no_price: float) -> float:
        """
        Calculate consensus probability from market prices.
        Weighted average of YES and NO prices.
        """
        if yes_price + no_price == 0:
            return 50.0
        return round((yes_price / (yes_price + no_price)) * 100, 2)
    
    def check_binary_arbitrage(self, market: Dict) -> Optional[ArbitrageOpportunity]:
        """
        Check if binary market has arbitrage opportunity.
        Returns ArbitrageOpportunity if found, None otherwise.
        """
        tokens = market.get("tokens", [])
        if len(tokens) != 2:
            return None
        
        yes_token = tokens[0]
        no_token = tokens[1]
        
        yes_price = yes_token.get("price", 0)
        no_price = no_token.get("price", 0)
        
        if yes_price <= 0 or no_price <= 0:
            return None
        
        # Calculate price sum (should be 1.00 in efficient market)
        price_sum = yes_price + no_price
        
        # Only consider obvious arbitrage (sum significantly < 1.00)
        if price_sum >= 0.995 or price_sum <= 0.85:
            return None
        
        # Calculate implied probabilities
        implied_prob_yes = self.calculate_implied_probability(yes_price)
        implied_prob_no = self.calculate_implied_probability(no_price)
        market_prob = self.calculate_market_probability(yes_price, no_price)
        
        # Profit calculation
        profit = round(1.00 - price_sum, 4)
        profit_pct = round(profit / price_sum * 100, 2)
        
        # Parse end date
        end_date_iso = market.get("end_date_iso", "")
        end_date, hours_left = self.parse_end_date(end_date_iso)
        
        # Liquidity and volume
        liquidity = market.get("liquidity", 0) or 0
        volume = market.get("volume", 0) or 0
        
        return ArbitrageOpportunity(
            rank=0,  # Will be assigned later
            type="arbitrage",
            market=market.get("question", "Unknown"),
            condition_id=market.get("condition_id", ""),
            strategy="DUTCH_BOOK",
            sum=round(price_sum, 4),
            cost=round(price_sum, 4),
            profit=profit,
            profit_pct=profit_pct,
            implied_prob_yes=implied_prob_yes,
            implied_prob_no=implied_prob_no,
            yes_price=round(yes_price, 4),
            no_price=round(no_price, 4),
            market_probability=market_prob,
            liquidity=round(liquidity, 2),
            volume=round(volume, 2),
            end_date=end_date_iso[:10] if end_date_iso else "unknown",
            time_left_hours=round(hours_left, 1),
            tokens=[
                {
                    "outcome": yes_token.get("outcome", ""),
                    "price": round(yes_price, 4),
                    "token_id": yes_token.get("token_id", "")
                },
                {
                    "outcome": no_token.get("outcome", ""),
                    "price": round(no_price, 4),
                    "token_id": no_token.get("token_id", "")
                }
            ],
            timestamp=self.timestamp
        )
    
    def extract_candidate_name(self, question: str) -> Optional[Tuple[str, str]]:
        """Extract candidate name and event type from question text"""
        question_lower = question.lower()
        
        # Common patterns for correlated markets
        patterns = [
            # Primary/Caucus patterns
            (r"will\s+(\w+(?:\s+\w+)?)\s+win.*(?:primary|caucus)", "primary"),
            (r"will\s+(\w+(?:\s+\w+)?)\s+win.*(?:presidential|presidency|election)", "election"),
            
            # Nomination patterns
            (r"will\s+(\w+(?:\s+\w+)?)\s+be.*nominated", "nomination"),
            (r"will\s+(\w+(?:\s+\w+)?)\s+be.*nominee", "nomination"),
            
            # Generic win patterns
            (r"will\s+(\w+(?:\s+\w+)?)\s+win", "generic"),
        ]
        
        for pattern, event_type in patterns:
            match = re.search(pattern, question_lower)
            if match:
                name = match.group(1).strip().title()
                return name, event_type
        
        return None
    
    def find_correlated_pairs(self, markets: List[Dict]):
        """Find correlated market pairs (e.g., primary vs election)"""
        print("\n🔗 Analyzing for correlated market pairs...")
        
        candidates = {}  # name -> list of (market, event_type)
        
        # Group markets by extracted candidate names
        for market in markets:
            question = market.get("question", "")
            if not question:
                continue
            
            result = self.extract_candidate_name(question)
            if result:
                name, event_type = result
                if name not in candidates:
                    candidates[name] = []
                candidates[name].append((market, event_type))
        
        correlated_pairs = []
        pair_id = 0
        
        # Find correlated pairs
        for name, markets_list in candidates.items():
            if len(markets_list) < 2:
                continue
            
            # Look for primary + election pairs
            primaries = [m for m, t in markets_list if "primary" in t]
            elections = [m for m, t in markets_list if "election" in t]
            nominations = [m for m, t in markets_list if "nomination" in t]
            
            # Primary -> Election correlation
            for primary in primaries:
                for election in elections:
                    primary_price = self.get_yes_price(primary)
                    election_price = self.get_yes_price(election)
                    
                    if primary_price is None or election_price is None:
                        continue
                    
                    # If P(win_primary) > P(win_election), that's suspicious
                    # P(win_election) should roughly = P(win_primary) * P(win_general|won_primary)
                    implied_correlation = election_price / primary_price if primary_price > 0 else 0
                    
                    confidence = round(primary_price * 100, 1)
                    
                    pair = CorrelatedPair(
                        rank=0,
                        primary_market=primary.get("question", ""),
                        primary_condition_id=primary.get("condition_id", ""),
                        secondary_market=election.get("question", ""),
                        secondary_condition_id=election.get("condition_id", ""),
                        relationship_type="PRIMARY_TO_ELECTION",
                        confidence=confidence,
                        primary_price=round(primary_price, 3),
                        secondary_price=round(election_price, 3),
                        implied_correlation=round(implied_correlation, 3),
                        notes=f"P({name}: Primary)={primary_price:.2f}, P({name}: Election)={election_price:.2f}",
                        timestamp=self.timestamp
                    )
                    correlated_pairs.append(pair)
            
            # Nomination -> Election correlation
            for nomination in nominations:
                for election in elections:
                    nom_price = self.get_yes_price(nomination)
                    election_price = self.get_yes_price(election)
                    
                    if nom_price is None or election_price is None:
                        continue
                    
                    implied_correlation = election_price / nom_price if nom_price > 0 else 0
                    confidence = round(nom_price * 100, 1)
                    
                    pair = CorrelatedPair(
                        rank=0,
                        primary_market=nomination.get("question", ""),
                        primary_condition_id=nomination.get("condition_id", ""),
                        secondary_market=election.get("question", ""),
                        secondary_condition_id=election.get("condition_id", ""),
                        relationship_type="NOMINATION_TO_ELECTION",
                        confidence=confidence,
                        primary_price=round(nom_price, 3),
                        secondary_price=round(election_price, 3),
                        implied_correlation=round(implied_correlation, 3),
                        notes=f"P({name}: Nomination)={nom_price:.2f}, P({name}: Election)={election_price:.2f}",
                        timestamp=self.timestamp
                    )
                    correlated_pairs.append(pair)
        
        # Sort by confidence and assign ranks
        correlated_pairs.sort(key=lambda x: x.confidence, reverse=True)
        for i, pair in enumerate(correlated_pairs, 1):
            correlated_pairs[i-1] = CorrelatedPair(
                rank=i,
                primary_market=pair.primary_market,
                primary_condition_id=pair.primary_condition_id,
                secondary_market=pair.secondary_market,
                secondary_condition_id=pair.secondary_condition_id,
                relationship_type=pair.relationship_type,
                confidence=pair.confidence,
                primary_price=pair.primary_price,
                secondary_price=pair.secondary_price,
                implied_correlation=pair.implied_correlation,
                notes=pair.notes,
                timestamp=pair.timestamp
            )
        
        self.correlated_pairs = correlated_pairs[:20]  # Keep top 20
        print(f"   Found {len(self.correlated_pairs)} correlated pairs")
    
    def get_yes_price(self, market: Dict) -> Optional[float]:
        """Extract YES token price from market"""
        tokens = market.get("tokens", [])
        if len(tokens) >= 1:
            return tokens[0].get("price", 0)
        return None
    
    def scan_for_arbitrage(self, markets: List[Dict]) -> List[ArbitrageOpportunity]:
        """Scan all markets and find TOP 5 best arbitrage opportunities"""
        print(f"\n🔍 Scanning {len(markets)} markets for arbitrage...")
        
        opportunities = []
        
        for market in markets:
            # Skip closed markets
            if market.get("closed", True):
                continue
            
            # Only binary markets
            tokens = market.get("tokens", [])
            if len(tokens) != 2:
                continue
            
            # Check for arbitrage
            opportunity = self.check_binary_arbitrage(market)
            if opportunity:
                opportunities.append(opportunity)
        
        # Sort by profit percentage (descending) to find BEST opportunities
        opportunities.sort(key=lambda x: x.profit_pct, reverse=True)
        
        # Assign ranks and take top N
        ranked_opportunities = []
        for i, opp in enumerate(opportunities[:self.TOP_N], 1):
            ranked_opp = ArbitrageOpportunity(
                rank=i,
                type=opp.type,
                market=opp.market,
                condition_id=opp.condition_id,
                strategy=opp.strategy,
                sum=opp.sum,
                cost=opp.cost,
                profit=opp.profit,
                profit_pct=opp.profit_pct,
                implied_prob_yes=opp.implied_prob_yes,
                implied_prob_no=opp.implied_prob_no,
                yes_price=opp.yes_price,
                no_price=opp.no_price,
                market_probability=opp.market_probability,
                liquidity=opp.liquidity,
                volume=opp.volume,
                end_date=opp.end_date,
                time_left_hours=opp.time_left_hours,
                tokens=opp.tokens,
                timestamp=opp.timestamp
            )
            ranked_opportunities.append(ranked_opp)
        
        return ranked_opportunities
    
    def display_opportunities(self, opportunities: List[ArbitrageOpportunity]):
        """Display formatted arbitrage opportunities"""
        if not opportunities:
            print("\n📊 No significant arbitrage opportunities found.")
            print("   Market prices sum close to $1.00 (efficient pricing)")
            return
        
        print(f"\n" + "="*90)
        print(f"🎯 TOP {len(opportunities)} ARBITRAGE OPPORTUNITIES")
        print("="*90)
        
        for opp in opportunities:
            print(f"\n📌 RANK #{opp.rank}")
            print(f"   Market: {opp.market[:70]}{'...' if len(opp.market) > 70 else ''}")
            print(f"   ├─ Strategy: {opp.strategy}")
            print(f"   ├─ Price Sum: ${opp.sum:.4f} (should be $1.00)")
            print(f"   ├─ 💰 Profit: ${opp.profit:.4f} ({opp.profit_pct}%)")
            print(f"   ├─ YES Token: ${opp.yes_price:.4f} → Implied: {opp.implied_prob_yes}%")
            print(f"   ├─ NO Token:  ${opp.no_price:.4f} → Implied: {opp.implied_prob_no}%")
            print(f"   ├─ Market Probability: {opp.market_probability}%")
            print(f"   ├─ Liquidity: ${opp.liquidity:,.2f} | Volume: ${opp.volume:,.2f}")
            print(f"   ├─ Time Left: {opp.time_left_hours} hours")
            print(f"   └─ End Date: {opp.end_date}")
            print(f"   📋 Token IDs:")
            for token in opp.tokens:
                print(f"      • {token['outcome']}: {token['token_id'][:20]}...")
        
        print("\n" + "="*90)
    
    def display_correlated_pairs(self):
        """Display correlated market pairs"""
        if not self.correlated_pairs:
            print("\n🔗 No significant correlated pairs found.")
            return
        
        print(f"\n" + "="*90)
        print(f"🔗 TOP {min(10, len(self.correlated_pairs))} CORRELATED MARKET PAIRS")
        print("="*90)
        
        for pair in self.correlated_pairs[:10]:
            print(f"\n🔄 RANK #{pair.rank} | {pair.relationship_type}")
            print(f"   Primary:   {pair.primary_market[:65]}")
            print(f"   Secondary: {pair.secondary_market[:65]}")
            print(f"   ├─ Confidence: {pair.confidence}%")
            print(f"   ├─ Primary Price: ${pair.primary_price:.3f}")
            print(f"   ├─ Secondary Price: ${pair.secondary_price:.3f}")
            print(f"   └─ Implied Correlation Ratio: {pair.implied_correlation:.3f}")
            print(f"   📝 {pair.notes}")
        
        print("\n" + "="*90)
    
    def save_results(self):
        """Save top opportunities to JSON with timestamp"""
        output_dir = "/home/yeatz/.openclaw/workspace/btc-trading-bot"
        os.makedirs(output_dir, exist_ok=True)
        
        # Main output file
        output_file = os.path.join(output_dir, "polymarket_arbitrage_v2.json")
        
        # Historical archive file
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_file = os.path.join(output_dir, f"arbitrage_history/polymarket_{timestamp_str}.json")
        os.makedirs(os.path.dirname(archive_file), exist_ok=True)
        
        # Build results dictionary
        results = {
            "metadata": {
                "version": "2.0",
                "timestamp": self.timestamp,
                "markets_scanned": len(self.all_markets),
                "opportunities_found": len(self.opportunities),
                "correlated_pairs_found": len(self.correlated_pairs)
            },
            "top_arbitrage_opportunities": [opp.to_dict() for opp in self.opportunities],
            "correlated_pairs": [pair.to_dict() for pair in self.correlated_pairs[:10]]
        }
        
        # Save to main file
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Save to archive
        with open(archive_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved:")
        print(f"   Main: {output_file}")
        print(f"   Archive: {archive_file}")
    
    def run_scan(self) -> Dict:
        """Execute full scan and return results"""
        print(f"\n{'='*90}")
        print(f"🚀 POLYMARKET ARBITRAGE SCANNER v2.0")
        print(f"📅 Scan Time: {self.timestamp}")
        print(f"{'='*90}\n")
        
        # Fetch markets
        self.all_markets = self.fetch_active_markets(limit=self.MAX_FETCH_LIMIT)
        
        if not self.all_markets:
            print("\n❌ No markets retrieved. API may be unreachable.")
            return {"error": "No markets retrieved"}
        
        # Scan for arbitrage opportunities
        self.opportunities = self.scan_for_arbitrage(self.all_markets)
        
        # Find correlated pairs
        self.find_correlated_pairs(self.all_markets)
        
        # Display results
        self.display_opportunities(self.opportunities)
        self.display_correlated_pairs()
        
        # Save results
        self.save_results()
        
        # Summary
        print(f"\n{'='*90}")
        print(f"📊 SCAN SUMMARY")
        print(f"{'='*90}")
        print(f"   Markets Scanned: {len(self.all_markets)}")
        print(f"   Arbitrage Opportunities: {len(self.opportunities)}")
        print(f"   Correlated Pairs: {len(self.correlated_pairs)}")
        print(f"   Timestamp: {self.timestamp}")
        print(f"{'='*90}\n")
        
        return {
            "timestamp": self.timestamp,
            "markets_scanned": len(self.all_markets),
            "opportunities": [opp.to_dict() for opp in self.opportunities],
            "correlated_pairs": [pair.to_dict() for pair in self.correlated_pairs[:10]]
        }


def main():
    """Main entry point"""
    scanner = PolymarketArbitrageScannerV2()
    results = scanner.run_scan()
    
    # Exit with appropriate code (0 = success, 1 = no opportunities)
    if results.get("error"):
        exit(1)
    
    exit(0)


if __name__ == "__main__":
    main()