"""
Kraken Exchange API Wrapper
Complete REST API client for Kraken exchange.
"""

import time
import hmac
import hashlib
import base64
import requests
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class KrakenAPIError(Exception):
    """Kraken API specific errors"""
    pass


class RateLimiter:
    """Rate limiter for API calls"""
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = []
    
    def can_request(self) -> bool:
        now = time.time()
        self.requests = [t for t in self.requests if now - t < self.window]
        return len(self.requests) < self.max_requests
    
    def wait_if_needed(self):
        if not self.can_request():
            now = time.time()
            oldest = self.requests[0] if self.requests else now
            wait_time = self.window - (now - oldest) + 0.1
            if wait_time > 0:
                logger.debug(f"Rate limit hit, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
        self.requests.append(time.time())


class KrakenAPI:
    """Kraken REST API Client"""
    
    def __init__(self, api_key: Optional[str] = None, 
                 api_secret: Optional[str] = None,
                 timeout: int = 30):
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        
        # Kraken uses different base URLs for public vs private
        self.public_url = "https://api.kraken.com/0/public"
        self.private_url = "https://api.kraken.com/0/private"
        
        # Rate limiters
        self.public_limiter = RateLimiter(60, 60)   # 60/min for public
        self.private_limiter = RateLimiter(60, 60)  # 60/min for private
        
        self.session = requests.Session()
        
        logger.info(f"KrakenAPI initialized (has_credentials={bool(api_key)})")
    
    def _generate_signature(self, urlpath: str, data: Dict) -> str:
        """Generate Kraken API signature"""
        if not self.api_secret:
            raise KrakenAPIError("API secret required for private requests")
        
        # Kraken signature: HMAC-SHA256 of (nonce + POST data)
        # base64 decoded secret key used as HMAC key
        postdata = urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode('utf-8')
        message = urlpath.encode('utf-8') + hashlib.sha256(encoded).digest()
        signature = hmac.new(
            base64.b64decode(self.api_secret),
            message,
            hashlib.sha512
        ).hexdigest()
        return signature
    
    def _make_public_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make public API request"""
        self.public_limiter.wait_if_needed()
        
        url = f"{self.public_url}/{endpoint}"
        
        try:
            if params:
                response = self.session.get(url, params=params, timeout=self.timeout)
            else:
                response = self.session.get(url, timeout=self.timeout)
            
            response.raise_for_status()
            data = response.json()
            
            # Kraken returns errors in response
            if data.get('error'):
                raise KrakenAPIError(f"API Error: {data['error']}")
            
            return data.get('result', {})
            
        except requests.exceptions.Timeout:
            raise KrakenAPIError(f"Request timeout for {endpoint}")
        except requests.exceptions.ConnectionError:
            raise KrakenAPIError(f"Connection error for {endpoint}")
        except Exception as e:
            raise KrakenAPIError(f"Request failed: {str(e)}")
    
    def _make_private_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make private API request (requires authentication)"""
        if not self.api_key:
            raise KrakenAPIError("API key required for private requests")
        
        self.private_limiter.wait_if_needed()
        
        url = f"{self.private_url}/{endpoint}"
        urlpath = f"/0/private/{endpoint}"
        
        params = params or {}
        params['nonce'] = int(time.time() * 1000)
        
        headers = {
            'API-Key': self.api_key,
            'API-Sign': self._generate_signature(urlpath, params),
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = self.session.post(url, headers=headers, data=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if data.get('error'):
                raise KrakenAPIError(f"API Error: {data['error']}")
            
            return data.get('result', {})
            
        except Exception as e:
            raise KrakenAPIError(f"Private request failed: {str(e)}")
    
    # ==================== PUBLIC ENDPOINTS ====================
    
    def get_server_time(self) -> Dict:
        """Get server time"""
        return self._make_public_request('Time')
    
    def get_system_status(self) -> Dict:
        """Get system status"""
        return self._make_public_request('SystemStatus')
    
    def get_assets(self, assets: Optional[List[str]] = None) -> Dict:
        """Get asset info"""
        params = {}
        if assets:
            params['asset'] = ','.join(assets)
        return self._make_public_request('Assets', params)
    
    def get_asset_pairs(self, pairs: Optional[List[str]] = None) -> Dict:
        """Get tradable asset pairs"""
        params = {}
        if pairs:
            params['pair'] = ','.join(pairs)
        return self._make_public_request('AssetPairs', params)
    
    def get_ticker(self, pairs: List[str]) -> Dict:
        """
        Get ticker information
        
        Args:
            pairs: List of asset pairs (e.g., ['XXBTZUSD', 'XETHZUSD'])
        
        Returns: {
            'XXBTZUSD': {
                'a': [ask_price, ask_whole_lot_volume, ask_lot_volume],
                'b': [bid_price, bid_whole_lot_volume, bid_lot_volume],
                'c': [last_trade_price, last_trade_lot_volume],
                'v': [volume_today, volume_last_24h],
                'p': [vwap_today, vwap_last_24h],
                't': [number_of_trades_today, number_of_trades_last_24h],
                'l': [low_today, low_last_24h],
                'h': [high_today, high_last_24h],
                'o': opening_price
            }
        }
        """
        params = {'pair': ','.join(pairs)}
        return self._make_public_request('Ticker', params)
    
    def get_ohlc(self, pair: str, interval: int = 60, since: Optional[int] = None) -> Dict:
        """
        Get OHLC (candlestick) data
        
        Args:
            pair: Asset pair (e.g., 'XXBTZUSD')
            interval: Candle interval in minutes (1, 5, 15, 30, 60, 240, 1440, 10080, 21600)
            since: Return data since given timestamp
        
        Returns: {
            'XXBTZUSD': [
                [time, open, high, low, close, vwap, volume, count],
                ...
            ],
            'last': last_timestamp
        }
        """
        params = {'pair': pair, 'interval': interval}
        if since:
            params['since'] = since
        return self._make_public_request('OHLC', params)
    
    def get_orderbook(self, pair: str, count: int = 100) -> Dict:
        """
        Get order book
        
        Args:
            pair: Asset pair
            count: Number of entries (max 1000)
        
        Returns: {
            'XXBTZUSD': {
                'bids': [[price, volume, timestamp], ...],
                'asks': [[price, volume, timestamp], ...]
            }
        }
        """
        params = {'pair': pair, 'count': count}
        return self._make_public_request('Depth', params)
    
    def get_recent_trades(self, pair: str, since: Optional[int] = None) -> Dict:
        """Get recent trades"""
        params = {'pair': pair}
        if since:
            params['since'] = since
        return self._make_public_request('Trades', params)
    
    def get_spread(self, pair: str) -> Dict:
        """Get recent spreads"""
        return self._make_public_request('Spread', {'pair': pair})
    
    # ==================== PRIVATE ENDPOINTS ====================
    
    def get_balance(self) -> Dict:
        """Get account balance"""
        return self._make_private_request('Balance')
    
    def get_trade_balance(self, asset: str = 'ZUSD') -> Dict:
        """Get trade balance"""
        return self._make_private_request('TradeBalance', {'asset': asset})
    
    def get_open_orders(self, trades: bool = False) -> Dict:
        """Get open orders"""
        return self._make_private_request('OpenOrders', {'trades': trades})
    
    def get_closed_orders(self, trades: bool = False) -> Dict:
        """Get closed orders"""
        return self._make_private_request('ClosedOrders', {'trades': trades})
    
    def place_order(self, pair: str, type: str, ordertype: str,
                   volume: float, price: Optional[float] = None,
                   price2: Optional[float] = None,
                   leverage: Optional[str] = None,
                   oflags: Optional[str] = None) -> Dict:
        """
        Place an order
        
        Args:
            pair: Asset pair (e.g., 'XXBTZUSD')
            type: 'buy' or 'sell'
            ordertype: 'market', 'limit', 'stop-loss', 'take-profit', etc.
            volume: Order volume
            price: Price (required for limit orders)
            price2: Secondary price (for stop-loss-limit, etc.)
            leverage: Amount of leverage desired (optional)
            oflags: Order flags (optional, comma delimited list)
        
        Returns:
            {'txid': ['transaction_id'], 'descr': {'order': 'description'}}
        """
        params = {
            'pair': pair,
            'type': type,
            'ordertype': ordertype,
            'volume': str(volume)
        }
        
        if price:
            params['price'] = str(price)
        if price2:
            params['price2'] = str(price2)
        if leverage:
            params['leverage'] = leverage
        if oflags:
            params['oflags'] = oflags
        
        return self._make_private_request('AddOrder', params)
    
    def cancel_order(self, txid: str) -> Dict:
        """Cancel an order"""
        return self._make_private_request('CancelOrder', {'txid': txid})
    
    def cancel_all_orders(self) -> Dict:
        """Cancel all orders"""
        return self._make_private_request('CancelAll')
    
    def query_orders(self, txid: str) -> Dict:
        """Query orders"""
        return self._make_private_request('QueryOrders', {'txid': txid})
