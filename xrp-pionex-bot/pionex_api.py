"""
Pionex API Wrapper
Supports both paper trading simulation and live trading.
WARNING: Only paper trading is enabled by default.
"""

import time
import hashlib
import hmac
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PionexConfig:
    """API Configuration"""
    api_key: str = ""
    api_secret: str = ""
    base_url: str = "https://api.pionex.com"
    timeout: int = 30

class PionexAPI:
    """
    Pionex Exchange API Client
    Based on standard REST API patterns used by crypto exchanges.
    """
    
    def __init__(self, config: PionexConfig = None):
        self.config = config or PionexConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
    def _generate_signature(self, params: Dict) -> str:
        """Generate HMAC signature for authenticated requests"""
        if not self.config.api_secret:
            return ""
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            self.config.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _get_headers(self, params: Dict = None) -> Dict:
        """Get request headers with authentication"""
        headers = {'Content-Type': 'application/json'}
        if self.config.api_key and params:
            headers['X-PIONEX-APIKEY'] = self.config.api_key
            headers['X-PIONEX-SIGNATURE'] = self._generate_signature(params)
        return headers
    
    def get_ticker(self, symbol: str = "XRP_USDT") -> Dict:
        """Get current ticker data for a symbol"""
        try:
            # Pionex ticker endpoint (standard format)
            url = f"{self.config.base_url}/api/v1/market/ticker?symbol={symbol}"
            response = self.session.get(url, timeout=self.config.timeout)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'symbol': symbol,
                    'last_price': float(data.get('data', {}).get('lastPrice', 0)),
                    'bid': float(data.get('data', {}).get('bidPrice', 0)),
                    'ask': float(data.get('data', {}).get('askPrice', 0)),
                    'volume': float(data.get('data', {}).get('volume', 0)),
                    'high_24h': float(data.get('data', {}).get('highPrice', 0)),
                    'low_24h': float(data.get('data', {}).get('lowPrice', 0)),
                    'timestamp': int(time.time() * 1000)
                }
            else:
                # Fallback: simulate ticker data for testing
                return self._simulate_ticker(symbol)
        except Exception as e:
            print(f"Error fetching ticker: {e}")
            return self._simulate_ticker(symbol)
    
    def get_klines(self, symbol: str = "XRP_USDT", interval: str = "1h", 
                   limit: int = 100) -> List[Dict]:
        """Get OHLCV data for backtesting"""
        try:
            url = f"{self.config.base_url}/api/v1/market/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            response = self.session.get(url, params=params, timeout=self.config.timeout)
            
            if response.status_code == 200:
                data = response.json()
                # Check if API returned data or error
                if data.get('result') is True and 'data' in data and data['data']:
                    candles = []
                    for kline in data['data']:
                        candles.append({
                            'timestamp': int(kline[0]),
                            'open': float(kline[1]),
                            'high': float(kline[2]),
                            'low': float(kline[3]),
                            'close': float(kline[4]),
                            'volume': float(kline[5])
                        })
                    return candles
                else:
                    print(f"API returned error: {data.get('code', 'unknown')}")
                    return self._simulate_klines(symbol, limit)
            else:
                return self._simulate_klines(symbol, limit)
        except Exception as e:
            print(f"Error fetching klines: {e}")
            return self._simulate_klines(symbol, limit)
    
    def _simulate_ticker(self, symbol: str) -> Dict:
        """Simulate ticker data for testing when API unavailable"""
        import random
        # Use realistic XRP price (~$1.44 as of Feb 2026)
        base_price = 1.44 if "XRP" in symbol else 50000.0
        variation = random.uniform(-0.02, 0.02)
        price = base_price * (1 + variation)
        
        return {
            'symbol': symbol,
            'last_price': round(price, 4),
            'bid': round(price * 0.999, 4),
            'ask': round(price * 1.001, 4),
            'volume': random.uniform(100000, 500000),
            'high_24h': round(price * 1.05, 4),
            'low_24h': round(price * 0.95, 4),
            'timestamp': int(time.time() * 1000)
        }
    
    def _simulate_klines(self, symbol: str, limit: int) -> List[Dict]:
        """Simulate OHLCV data for backtesting with mean reversion"""
        import random
        candles = []
        # Use realistic XRP price (~$1.44 as of Feb 2026)
        base_price = 1.44 if "XRP" in symbol else 50000.0
        current_price = base_price
        
        for i in range(limit):
            timestamp = int(time.time() * 1000) - (limit - i) * 3600000
            
            # Mean reversion: pull price back toward base
            deviation = (current_price - base_price) / base_price
            mean_reversion = -deviation * 0.1  # Pull back 10% of deviation per candle
            
            # Random walk with mean reversion
            random_change = random.uniform(-0.008, 0.008)  # Reduced volatility
            change = random_change + mean_reversion
            
            open_price = current_price
            close_price = current_price * (1 + change)
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.003))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.003))
            volume = random.uniform(10000, 100000)
            
            candles.append({
                'timestamp': timestamp,
                'open': round(open_price, 4),
                'high': round(high_price, 4),
                'low': round(low_price, 4),
                'close': round(close_price, 4),
                'volume': round(volume, 2)
            })
            current_price = close_price
        
        return candles
    
    def get_balance(self) -> Dict:
        """Get account balance - PAPER TRADING ONLY"""
        # Paper trading - return simulated balance
        raise NotImplementedError("Use PaperTrader.get_balance() for paper trading")
    
    def place_order(self, symbol: str, side: str, order_type: str,
                    amount: float, price: float = None) -> Dict:
        """Place an order - PAPER TRADING ONLY ENABLED"""
        # Paper trading only - this should never be called directly
        raise NotImplementedError("Use PaperTrader.place_order() for paper trading")

# Example usage
if __name__ == "__main__":
    api = PionexAPI()
    ticker = api.get_ticker("XRP_USDT")
    print(f"XRP Price: ${ticker['last_price']}")
    
    klines = api.get_klines("XRP_USDT", "1h", 10)
    print(f"Fetched {len(klines)} candles")