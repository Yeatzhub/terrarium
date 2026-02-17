"""
Toobit API Wrapper
Binance-compatible REST API client for Toobit exchange.
"""

import time
import hmac
import hashlib
import requests
import logging
from typing import Dict, List, Optional, Any
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class ToobitAPIError(Exception):
    """Toobit API specific errors"""
    pass


class RateLimiter:
    """Simple rate limiter for API calls"""
    def __init__(self, max_requests: int = 1200, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = []
    
    def can_request(self) -> bool:
        now = time.time()
        # Remove old requests outside window
        self.requests = [t for t in self.requests if now - t < self.window]
        return len(self.requests) < self.max_requests
    
    def wait_if_needed(self):
        if not self.can_request():
            # Wait until we can make a request
            now = time.time()
            oldest = self.requests[0] if self.requests else now
            wait_time = self.window - (now - oldest) + 0.1
            if wait_time > 0:
                logger.debug(f"Rate limit hit, waiting {wait_time:.2f}s")
                time.sleep(wait_time)
        self.requests.append(time.time())


class ToobitAPI:
    """
    Toobit REST API Client
    
    Public endpoints: No authentication needed
    Private endpoints: Requires API key + signature
    """
    
    def __init__(self, api_key: Optional[str] = None, 
                 api_secret: Optional[str] = None,
                 testnet: bool = False,
                 timeout: int = 30):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.timeout = timeout
        
        # Base URL
        if testnet:
            self.base_url = "https://api-testnet.toobit.com"
        else:
            self.base_url = "https://api.toobit.com"
        
        # Rate limiters for different endpoints
        self.public_limiter = RateLimiter(1200, 60)  # 1200/min for public
        self.private_limiter = RateLimiter(60, 60)   # 60/min for private
        self.order_limiter = RateLimiter(100, 10)    # 100/10s for orders
        
        self.session = requests.Session()
        
        logger.info(f"ToobitAPI initialized (testnet={testnet}, has_credentials={bool(api_key)})")
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Generate HMAC SHA256 signature for private endpoints"""
        if not self.api_secret:
            raise ToobitAPIError("API secret required for signed requests")
        
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method: str, endpoint: str, 
                      params: Optional[Dict] = None,
                      signed: bool = False) -> Dict:
        """Make HTTP request with error handling and rate limiting"""
        
        # Apply rate limiting
        if signed:
            if 'order' in endpoint or 'trade' in endpoint:
                self.order_limiter.wait_if_needed()
            else:
                self.private_limiter.wait_if_needed()
        else:
            self.public_limiter.wait_if_needed()
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if signed:
            if not self.api_key:
                raise ToobitAPIError("API key required for signed requests")
            
            headers['X-MBX-APIKEY'] = self.api_key
            
            # Add timestamp for signed requests
            params = params or {}
            params['timestamp'] = int(time.time() * 1000)
            params['signature'] = self._generate_signature(params)
        
        try:
            if method == 'GET':
                if params:
                    url = f"{url}?{urlencode(params)}"
                response = self.session.get(url, headers=headers, timeout=self.timeout)
            elif method == 'POST':
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
                response = self.session.post(
                    url, 
                    headers=headers, 
                    data=params if signed else urlencode(params or {}),
                    timeout=self.timeout
                )
            elif method == 'DELETE':
                if params:
                    url = f"{url}?{urlencode(params)}"
                response = self.session.delete(url, headers=headers, timeout=self.timeout)
            else:
                raise ToobitAPIError(f"Unsupported HTTP method: {method}")
            
            # Handle response
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Retry after {retry_after}s")
                time.sleep(retry_after)
                return self._make_request(method, endpoint, params, signed)
            
            response.raise_for_status()
            data = response.json()
            
            # Check for API-level errors
            if isinstance(data, dict) and 'code' in data and data['code'] != 200:
                raise ToobitAPIError(f"API Error {data['code']}: {data.get('msg', 'Unknown error')}")
            
            return data
            
        except requests.exceptions.Timeout:
            raise ToobitAPIError(f"Request timeout for {endpoint}")
        except requests.exceptions.ConnectionError:
            raise ToobitAPIError(f"Connection error for {endpoint}")
        except requests.exceptions.HTTPError as e:
            raise ToobitAPIError(f"HTTP error {response.status_code}: {e}")
        except Exception as e:
            raise ToobitAPIError(f"Request failed: {str(e)}")
    
    # ==================== PUBLIC ENDPOINTS ====================
    
    def ping(self) -> bool:
        """Test connectivity"""
        try:
            result = self._make_request('GET', '/api/v1/ping')
            return result == {}
        except:
            return False
    
    def get_server_time(self) -> int:
        """Get server time in milliseconds"""
        result = self._make_request('GET', '/api/v1/time')
        return result.get('serverTime', 0)
    
    def get_exchange_info(self) -> Dict:
        """Get exchange trading rules and symbol information"""
        return self._make_request('GET', '/api/v1/exchangeInfo')
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get 24hr ticker price change statistics
        
        Returns: {
            'symbol': str,
            'priceChange': str,
            'priceChangePercent': str,
            'weightedAvgPrice': str,
            'lastPrice': str,
            'lastQty': str,
            'bidPrice': str,
            'bidQty': str,
            'askPrice': str,
            'askQty': str,
            'openPrice': str,
            'highPrice': str,
            'lowPrice': str,
            'volume': str,
            'quoteVolume': str,
            'openTime': int,
            'closeTime': int,
            'firstId': int,
            'lastId': int,
            'count': int
        }
        """
        return self._make_request('GET', '/api/v1/ticker/24hr', {'symbol': symbol})
    
    def get_orderbook(self, symbol: str, limit: int = 5) -> Dict:
        """
        Get order book (bids/asks)
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            limit: Number of bids/asks (5, 10, 20, 50, 100, 500, 1000)
        
        Returns: {
            'lastUpdateId': int,
            'bids': [[price, qty], ...],
            'asks': [[price, qty], ...]
        }
        """
        valid_limits = [5, 10, 20, 50, 100, 500, 1000]
        if limit not in valid_limits:
            limit = min(valid_limits, key=lambda x: abs(x - limit))
        
        return self._make_request('GET', '/api/v1/depth', {
            'symbol': symbol,
            'limit': limit
        })
    
    def get_klines(self, symbol: str, interval: str, limit: int = 100) -> List:
        """
        Get OHLCV kline/candlestick data
        
        Args:
            symbol: Trading pair
            interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            limit: Number of candles (max 1000)
        
        Returns: List of [open_time, open, high, low, close, volume, close_time, ...]
        """
        valid_intervals = ['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w', '1M']
        if interval not in valid_intervals:
            raise ToobitAPIError(f"Invalid interval: {interval}. Use: {valid_intervals}")
        
        limit = min(limit, 1000)
        
        return self._make_request('GET', '/api/v1/klines', {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        })
    
    def get_recent_trades(self, symbol: str, limit: int = 100) -> List:
        """Get recent trades"""
        return self._make_request('GET', '/api/v1/trades', {
            'symbol': symbol,
            'limit': min(limit, 1000)
        })
    
    # ==================== PRIVATE ENDPOINTS ====================
    
    def get_balance(self) -> Dict:
        """
        Get account balance (requires API key)
        
        Returns: {
            'makerCommission': int,
            'takerCommission': int,
            'buyerCommission': int,
            'sellerCommission': int,
            'canTrade': bool,
            'canWithdraw': bool,
            'canDeposit': bool,
            'updateTime': int,
            'accountType': str,
            'balances': [
                {'asset': str, 'free': str, 'locked': str},
                ...
            ]
        }
        """
        return self._make_request('GET', '/api/v1/account', signed=True)
    
    def place_order(self, symbol: str, side: str, type: str, 
                    quantity: float, price: Optional[float] = None,
                    time_in_force: str = 'GTC', 
                    client_order_id: Optional[str] = None) -> Dict:
        """
        Place a new order (LIVE - real money!)
        
        Args:
            symbol: Trading pair
            side: BUY or SELL
            type: LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT
            quantity: Order quantity
            price: Required for LIMIT orders
            time_in_force: GTC (Good Till Cancel), IOC (Immediate Or Cancel), FOK (Fill Or Kill)
            client_order_id: Optional custom order ID
        
        Returns: Order details
        """
        if side not in ['BUY', 'SELL']:
            raise ToobitAPIError(f"Invalid side: {side}")
        
        if type not in ['LIMIT', 'MARKET', 'STOP_LOSS', 'STOP_LOSS_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT']:
            raise ToobitAPIError(f"Invalid order type: {type}")
        
        params = {
            'symbol': symbol,
            'side': side,
            'type': type,
            'quantity': quantity,
            'timeInForce': time_in_force
        }
        
        if type == 'LIMIT' and price is None:
            raise ToobitAPIError("Price required for LIMIT orders")
        
        if price:
            params['price'] = price
        
        if client_order_id:
            params['newClientOrderId'] = client_order_id
        
        logger.warning(f"PLACE ORDER: {side} {quantity} {symbol} @ {price or 'MARKET'}")
        
        return self._make_request('POST', '/api/v1/order', params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: Optional[str] = None,
                     client_order_id: Optional[str] = None) -> Dict:
        """
        Cancel an active order
        
        Args:
            symbol: Trading pair
            order_id: Order ID (from Toobit)
            client_order_id: Your custom order ID
        """
        if not order_id and not client_order_id:
            raise ToobitAPIError("Either order_id or client_order_id required")
        
        params = {'symbol': symbol}
        if order_id:
            params['orderId'] = order_id
        if client_order_id:
            params['origClientOrderId'] = client_order_id
        
        logger.warning(f"CANCEL ORDER: {symbol} - ID: {order_id or client_order_id}")
        
        return self._make_request('DELETE', '/api/v1/order', params, signed=True)
    
    def get_order_status(self, symbol: str, order_id: Optional[str] = None,
                         client_order_id: Optional[str] = None) -> Dict:
        """Get order status"""
        if not order_id and not client_order_id:
            raise ToobitAPIError("Either order_id or client_order_id required")
        
        params = {'symbol': symbol}
        if order_id:
            params['orderId'] = order_id
        if client_order_id:
            params['origClientOrderId'] = client_order_id
        
        return self._make_request('GET', '/api/v1/order', params, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List:
        """Get all open orders"""
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._make_request('GET', '/api/v1/openOrders', params, signed=True)
    
    def cancel_all_orders(self, symbol: str) -> List:
        """Cancel all open orders for a symbol"""
        return self._make_request('DELETE', '/api/v1/openOrders', 
                                   {'symbol': symbol}, signed=True)
    
    def get_trade_history(self, symbol: str, limit: int = 500) -> List:
        """Get account trade history"""
        return self._make_request('GET', '/api/v1/myTrades', {
            'symbol': symbol,
            'limit': min(limit, 1000)
        }, signed=True)


# Convenience function
def create_api(api_key: Optional[str] = None, 
               api_secret: Optional[str] = None,
               testnet: bool = False) -> ToobitAPI:
    """Factory function to create ToobitAPI instance"""
    return ToobitAPI(api_key, api_secret, testnet)
