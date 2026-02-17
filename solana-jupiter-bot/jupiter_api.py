"""
Jupiter API Client for Solana DEX Trading
Docs: https://station.jup.ag/docs/
"""

import requests
import json
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Token addresses (Solana mainnet)
TOKENS = {
    'SOL': 'So11111111111111111111111111111111111111112',
    'USDC': 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    'USDT': 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',
    'BONK': 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263',
    'JUP': 'JUPyiwrYJFskUPiHa7hkeRQoUfXh2pQ5rM9N9XzC5T7',
    'WIF': 'EKpQGSJtjMFqKZ9KQbRd8y9jvGjM6C3dA1rX1mU4gJYH',
    'PYTH': 'HZ1JovNiQvRDn2C6wG7C2z3P4yQG6NfX5mQ8bF8D8kL5',
}

@dataclass
class SwapQuote:
    input_mint: str
    output_mint: str
    in_amount: int
    out_amount: int
    price_impact_pct: float
    market_infos: List[Dict]
    route: Dict
    
    @property
    def price(self) -> float:
        """Price ratio (output/input)"""
        if self.in_amount == 0:
            return 0
        return self.out_amount / self.in_amount


class JupiterAPI:
    """Jupiter API client for Solana DEX trading"""
    
    BASE_URL = "https://quote-api.jup.ag/v6"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session = requests.Session()
        
    def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,  # 0.5% default
        fee_bps: Optional[int] = None,
        only_direct_routes: bool = False
    ) -> Optional[SwapQuote]:
        """
        Get swap quote from Jupiter
        
        Args:
            input_mint: Input token address
            output_mint: Output token address
            amount: Amount in lamports/smallest unit
            slippage_bps: Slippage in basis points (100 = 1%)
        """
        params = {
            'inputMint': input_mint,
            'outputMint': output_mint,
            'amount': str(amount),
            'slippageBps': slippage_bps,
        }
        
        if fee_bps:
            params['feeBps'] = fee_bps
        if only_direct_routes:
            params['onlyDirectRoutes'] = 'true'
            
        try:
            response = self.session.get(
                f"{self.BASE_URL}/quote",
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return SwapQuote(
                input_mint=input_mint,
                output_mint=output_mint,
                in_amount=int(data.get('inAmount', 0)),
                out_amount=int(data.get('outAmount', 0)),
                price_impact_pct=float(data.get('priceImpactPct', 0)),
                market_infos=data.get('marketInfos', []),
                route=data
            )
        except Exception as e:
            logger.error(f"Quote failed: {e}")
            return None
    
    def get_swap_transaction(
        self,
        quote: SwapQuote,
        user_public_key: str,
        wrap_unwrap_sol: bool = True,
        prioritization_fee_lamports: Optional[int] = None
    ) -> Optional[Dict]:
        """
        Get swap transaction for execution
        Requires wallet to sign and send
        """
        payload = {
            'quoteResponse': quote.route,
            'userPublicKey': user_public_key,
            'wrapUnwrapSOL': wrap_unwrap_sol,
        }
        
        if prioritization_fee_lamports:
            payload['prioritizationFeeLamports'] = prioritization_fee_lamports
            
        try:
            response = self.session.post(
                f"{self.BASE_URL}/swap",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Swap transaction failed: {e}")
            return None
    
    def get_token_list(self) -> List[Dict]:
        """Get list of tradable tokens"""
        try:
            response = self.session.get(
                "https://token.jup.ag/all",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Token list failed: {e}")
            return []
    
    def get_price(self, token_address: str) -> Optional[float]:
        """Get current price in USD"""
        try:
            response = self.session.get(
                f"https://price.jup.ag/v4/price?ids={token_address}",
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data.get('data', {}).get(token_address, {}).get('price')
        except Exception as e:
            logger.error(f"Price fetch failed: {e}")
            return None


class ArbitrageScanner:
    """Scan for arbitrage opportunities across Jupiter routes"""
    
    def __init__(self, api: JupiterAPI):
        self.api = api
        
    def find_triangular_arbitrage(
        self,
        start_token: str,
        intermediate_tokens: List[str],
        amount: int
    ) -> List[Dict]:
        """
        Find triangular arbitrage opportunities
        A -> B -> C -> A
        """
        opportunities = []
        
        for mid in intermediate_tokens:
            # Route 1: Start -> Mid
            quote1 = self.api.get_quote(start_token, mid, amount)
            if not quote1:
                continue
                
            # Route 2: Mid -> Start
            quote2 = self.api.get_quote(mid, start_token, quote1.out_amount)
            if not quote2:
                continue
                
            profit = quote2.out_amount - amount
            profit_pct = (profit / amount) * 100 if amount > 0 else 0
            
            if profit > 0:
                opportunities.append({
                    'route': f"{start_token[:4]} -> {mid[:4]} -> {start_token[:4]}",
                    'start_amount': amount,
                    'end_amount': quote2.out_amount,
                    'profit': profit,
                    'profit_pct': profit_pct,
                    'path': [start_token, mid, start_token]
                })
                
        return sorted(opportunities, key=lambda x: x['profit_pct'], reverse=True)
    
    def scan_new_tokens(self, min_volume_24h: float = 10000) -> List[Dict]:
        """
        Scan for new/unknown tokens with momentum
        High risk - for aggressive strategies only
        """
        tokens = self.api.get_token_list()
        
        # Filter for tokens with tags like 'new', 'trending'
        interesting = []
        for token in tokens:
            tags = token.get('tags', [])
            if any(tag in tags for tag in ['new', 'trending', 'community']):
                interesting.append(token)
                
        return interesting[:20]  # Top 20 candidates


if __name__ == '__main__':
    # Test
    api = JupiterAPI()
    
    # Get SOL price
    sol_price = api.get_price(TOKENS['SOL'])
    print(f"SOL Price: ${sol_price}")
    
    # Get quote: 0.1 SOL -> USDC
    amount = int(0.1 * 1e9)  # 0.1 SOL in lamports
    quote = api.get_quote(TOKENS['SOL'], TOKENS['USDC'], amount)
    if quote:
        print(f"Quote: {amount/1e9} SOL -> {quote.out_amount/1e6} USDC")
        print(f"Price impact: {quote.price_impact_pct}%")
