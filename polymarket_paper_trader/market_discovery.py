#!/usr/bin/env python3
"""
Phase 1: Market Discovery Module
Queries Polymarket API for active crypto "Up or Down" markets.
"""

import json
import requests
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass

BASE_API_URL = "https://gamma-api.polymarket.com"


@dataclass
class Market:
    """Represents a Polymarket prediction market."""
    market_id: str
    condition_id: str
    question: str
    slug: str
    yes_price: float
    no_price: float
    end_date: str
    active: bool
    closed: bool
    outcomes: List[str]
    volume: float
    
    def __repr__(self):
        return f"Market({self.market_id}: {self.question[:50]}...)"


class PolymarketAPI:
    """Client for Polymarket Gamma API."""
    
    def __init__(self, base_url: str = BASE_API_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'PolymarketPaperTrader/1.0',
            'Accept': 'application/json'
        })
    
    def get_markets(
        self, 
        active: bool = True, 
        closed: bool = False, 
        limit: int = 500,
        category: Optional[str] = None
    ) -> List[Dict]:
        """Fetch markets from the API."""
        url = f"{self.base_url}/markets"
        params = {
            "active": str(active).lower(),
            "closed": str(closed).lower(),
            "limit": limit
        }
        if category:
            params["category"] = category
            
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API Error: {e}")
            return []
    
    def parse_market(self, data: Dict) -> Optional[Market]:
        """Parse raw API data into Market object."""
        try:
            market_id = str(data.get('id', ''))
            condition_id = data.get('conditionId', '')
            question = data.get('question', '')
            slug = data.get('slug', '')
            end_date = data.get('endDate', '')
            active = data.get('active', False)
            closed = data.get('closed', True)
            volume = float(data.get('volumeNum', 0))
            
            # Parse outcomes and prices
            outcomes_raw = data.get('outcomes', '["Yes", "No"]')
            if isinstance(outcomes_raw, str):
                outcomes = json.loads(outcomes_raw)
            else:
                outcomes = outcomes_raw
            
            prices_raw = data.get('outcomePrices', '["0.5", "0.5"]')
            if isinstance(prices_raw, str):
                prices = json.loads(prices_raw)
            else:
                prices = [0.5, 0.5]
            
            yes_price = float(prices[0]) if len(prices) > 0 else 0.5
            no_price = float(prices[1]) if len(prices) > 1 else 0.5
            
            return Market(
                market_id=market_id,
                condition_id=condition_id,
                question=question,
                slug=slug,
                yes_price=yes_price,
                no_price=no_price,
                end_date=end_date,
                active=active,
                closed=closed,
                outcom es=outcomes,
                volume=volume
            )
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            print(f"Error parsing market {data.get('id')}: {e}")
            return None


class MarketDiscovery:
    """Discovers and filters crypto Up/Down markets."""
    
    # Crypto keywords to match
    CRYPTO_KEYWORDS = ['bitcoin', 'ethereum', 'solana', 'btc', 'eth', 'sol']
    
    # Direction keywords for Up/Down markets
    DIRECTION_KEYWORDS = [
        'up', 'down', 'above', 'below', 'higher', 'lower',
        'go up', 'going up', 'go down', 'going down',
        'close above', 'close below', 'end above', 'end below'
    ]
    
    def __init__(self, api: Optional[PolymarketAPI] = None):
        self.api = api or PolymarketAPI()
    
    def is_crypto_market(self, market: Market) -> bool:
        """Check if market is crypto-related."""
        question_lower = market.question.lower()
        return any(kw in question_lower for kw in self.CRYPTO_KEYWORDS)
    
    def is_up_down_market(self, market: Market) -> bool:
        """Check if market is an Up/Down prediction."""
        question_lower = market.question.lower()
        return any(kw in question_lower for kw in self.DIRECTION_KEYWORDS)
    
    def get_all_active_markets(self, limit: int = 500) -> List[Market]:
        """Get all active markets from the API."""
        raw_markets = self.api.get_markets(active=True, closed=False, limit=limit)
        markets = []
        for data in raw_markets:
            market = self.api.parse_market(data)
            if market:
                markets.append(market)
        return markets
    
    def get_crypto_markets(self, limit: int = 500) -> List[Market]:
        """Get all active crypto markets."""
        all_markets = self.get_all_active_markets(limit)
        return [m for m in all_markets if self.is_crypto_market(m)]
    
    def get_crypto_up_down_markets(self, limit: int = 500) -> List[Market]:
        """Get crypto Up/Down markets."""
        crypto_markets = self.get_crypto_markets(limit)
        return [m for m in crypto_markets if self.is_up_down_market(m)]
    
    def get_market_by_id(self, market_id: str) -> Optional[Market]:
        """Get a specific market by ID."""
        markets = self.get_all_active_markets(limit=500)
        for m in markets:
            if m.market_id == market_id:
                return m
        return None


def main():
    """Run market discovery and print results."""
    print("=" * 70)
    print("POLYMARKET CRYPTO MARKET DISCOVERY")
    print("=" * 70)
    
    discovery = MarketDiscovery()
    
    print("\nFetching active markets...")
    
    # Get all crypto markets
    crypto_markets = discovery.get_crypto_markets(limit=500)
    print(f"\nFound {len(crypto_markets)} active crypto markets")
    
    # Get Up/Down specific markets
    up_down_markets = discovery.get_crypto_up_down_markets(limit=500)
    print(f"Found {len(up_down_markets)} crypto Up/Down markets")
    
    print("\n" + "-" * 70)
    print("CRYPTO UP/DOWN MARKETS:")
    print("-" * 70)
    
    for market in up_down_markets:
        print(f"\nID: {market.market_id}")
        print(f"Question: {market.question}")
        print(f"Slug: {market.slug}")
        print(f"YES Price: ${market.yes_price:.4f}")
        print(f" NO Price: ${market.no_price:.4f}")
        print(f"Resolution Date: {market.end_date}")
        print(f"Condition ID: {market.condition_id}")
    
    # Also show some general crypto markets if Up/Down is sparse
    if len(up_down_markets) < 3 and crypto_markets:
        print("\n" + "-" * 70)
        print("OTHER ACTIVE CRYPTO MARKETS AVAILABLE FOR TRADING:")
        print("-" * 70)
        for market in crypto_markets[:10]:
            if market not in up_down_markets:
                print(f"\nID: {market.market_id}")
                print(f"Question: {market.question}")
                print(f"YES Price: ${market.yes_price:.4f}")
                print(f" NO Price: ${market.no_price:.4f}")
    
    print("\n" + "=" * 70)
    print("Discovery Complete!")
    print("=" * 70)
    
    return up_down_markets or crypto_markets[:10]


if __name__ == "__main__":
    main()
