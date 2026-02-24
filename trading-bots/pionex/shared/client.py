"""
Pionex API Client for XRP COIN-M PERP
Handles authentication, market data, and order execution
"""

import requests
import hmac
import hashlib
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PionexCredentials:
    api_key: str
    api_secret: str

class PionexClient:
    """Pionex API Client for COIN-M Futures"""
    
    BASE_URL = "https://api.pionex.com"
    
    def __init__(self, credentials: PionexCredentials, paper: bool = True):
        self.credentials = credentials
        self.paper = paper
        self.session = requests.Session()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
    def _generate_signature(self, params: Dict) -> str:
        """Generate HMAC SHA256 signature"""
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            self.credentials.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make authenticated request with rate limiting"""
        # Rate limit
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
        
        url = f"{self.BASE_URL}{endpoint}"
        
        # Add timestamp and signature
        params = params or {}
        params['timestamp'] = int(time.time() * 1000)
        params['signature'] = self._generate_signature(params)
        
        headers = {
            'X-API-KEY': self.credentials.api_key,
            'Content-Type': 'application/json'
        }
        
        try:
            if method == 'GET':
                response = self.session.get(url, params=params, headers=headers, timeout=10)
            else:
                response = self.session.post(url, json=params, headers=headers, timeout=10)
            
            self.last_request_time = time.time()
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {'error': str(e), 'success': False}
    
    def get_ticker(self, symbol: str = "XRP-USDT") -> Dict:
        """Get current price and 24h stats"""
        return self._request('GET', '/api/v1/market/ticker', {'symbol': symbol})
    
    def get_klines(self, symbol: str, interval: str = "1m", limit: int = 100) -> List[Dict]:
        """Get candlestick/OHLCV data"""
        """
        Intervals: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        return self._request('GET', '/api/v1/market/klines', params)
    
    def get_orderbook(self, symbol: str, limit: int = 10) -> Dict:
        """Get current order book"""
        return self._request('GET', '/api/v1/market/depth', {
            'symbol': symbol,
            'limit': limit
        })
    
    def get_account(self) -> Dict:
        """Get account balance"""
        return self._request('GET', '/api/v1/account/balance', {})
    
    def get_positions(self, symbol: Optional[str] = None) -> Dict:
        """Get current positions (COIN-M)"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/api/v1/futures/position', params)
    
    def place_order(self, symbol: str, side: str, size: float, 
                    order_type: str = "MARKET", price: Optional[float] = None,
                    stop_price: Optional[float] = None) -> Dict:
        """Place an order (COIN-M futures)"""
        """
        side: BUY/SELL for perps
        order_type: MARKET, LIMIT, STOP_MARKET, STOP_LIMIT
        size: in contracts (XRP contracts)
        """
        if self.paper:
            return self._simulate_order(symbol, side, size, order_type, price)
        
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'size': size
        }
        
        if order_type in ['LIMIT', 'STOP_LIMIT'] and price:
            params['price'] = price
        if stop_price:
            params['stopPrice'] = stop_price
            
        return self._request('POST', '/api/v1/futures/order', params)
    
    def close_position(self, symbol: str) -> Dict:
        """Close position at market price"""
        return self._request('POST', '/api/v1/futures/position/close', {
            'symbol': symbol,
            'type': 'MARKET'
        })
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """Set leverage for symbol (1-100x)"""
        return self._request('POST', '/api/v1/futures/leverage', {
            'symbol': symbol,
            'leverage': leverage
        })
    
    def _simulate_order(self, symbol: str, side: str, size: float, 
                       order_type: str, price: Optional[float]) -> Dict:
        """Simulate order in paper trading mode"""
        return {
            'success': True,
            'paper_trade': True,
            'symbol': symbol,
            'side': side,
            'size': size,
            'order_type': order_type,
            'price': price or self.get_ticker(symbol).get('price', 0),
            'order_id': f'paper_{int(time.time()*1000)}',
            'timestamp': int(time.time() * 1000)
        }

# Example usage
if __name__ == '__main__':
    import os
    
    # Load credentials from environment
    api_key = os.getenv('PIONEX_API_KEY', '')
    api_secret = os.getenv('PIONEX_API_SECRET', '')
    
    if not api_key or not api_secret:
        print("Error: Set PIONEX_API_KEY and PIONEX_API_SECRET environment variables")
        exit(1)
    
    client = PionexClient(
        PionexCredentials(api_key, api_secret),
        paper=True  # Start in paper mode
    )
    
    # Test connection
    print("Testing Pionex connection...")
    ticker = client.get_ticker('XRP-USDT')
    print(f"XRP Price: {ticker.get('price', 'N/A')}")
    
    account = client.get_account()
    print(f"Account: {account}")
