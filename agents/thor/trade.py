#!/usr/bin/env python3
"""
Thor Trading Executor
Runs inside Docker with VPN network (Surfshark Dubai)
"""

import os
import sys
import json
import time
import hmac
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# Configuration
API_KEY = os.environ.get('PIONEX_API_KEY', '')
API_SECRET = os.environ.get('PIONEX_SECRET', '')
PAPER_MODE = os.environ.get('PAPER_MODE', 'true').lower() == 'true'
BALANCE = float(os.environ.get('BALANCE', '100'))
BASE_URL = 'https://api.pionex.com'

# Signal file path (mounted from host)
SIGNAL_FILE = Path('/app/SIGNAL.md')
STATE_FILE = Path('/app/TRADE_STATE.md')
LOG_FILE = Path('/app/TRADE_LOG.md')


class PionexAPI:
    """Pionex API client"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = BASE_URL
    
    def _sign(self, query_string: str) -> str:
        """Generate HMAC signature"""
        return hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _request(self, method: str, endpoint: str, params: dict = None) -> dict:
        """Make authenticated request"""
        timestamp = str(int(time.time() * 1000))
        
        if params:
            query = '&'.join(f'{k}={v}' for k, v in params.items())
            query_string = f'{query}&timestamp={timestamp}'
        else:
            query_string = f'timestamp={timestamp}'
        
        signature = self._sign(query_string)
        
        headers = {
            'PIONEX-KEY': self.api_key,
            'PIONEX-SIGNATURE': signature,
            'PIONEX-TIMESTAMP': timestamp,
            'Content-Type': 'application/json'
        }
        
        url = f'{self.base_url}{endpoint}?{query_string}'
        
        try:
            req = urllib.request.Request(url, headers=headers)
            if method == 'POST':
                req = urllib.request.Request(url, headers=headers, method='POST')
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return {'error': f'HTTP {e.code}: {e.read().decode()}'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_balance(self) -> dict:
        """Get account balance"""
        return self._request('GET', '/api/v1/account/balances')
    
    def get_ticker(self, symbol: str) -> dict:
        """Get ticker price"""
        return self._request('GET', '/api/v1/ticker', {'symbol': symbol})
    
    def place_order(self, symbol: str, side: str, size: float, price: float = None) -> dict:
        """Place order (requires trading API permissions)"""
        params = {
            'symbol': symbol,
            'side': side.upper(),
            'size': str(size)
        }
        if price:
            params['type'] = 'LIMIT'
            params['price'] = str(price)
        else:
            params['type'] = 'MARKET'
        
        return self._request('POST', '/api/v1/order', params)


class ThorExecutor:
    """Thor trading executor"""
    
    def __init__(self, paper_mode: bool = True, balance: float = 100):
        self.paper_mode = paper_mode
        self.balance = balance
        self.position = None
        self.api = PionexAPI(API_KEY, API_SECRET) if API_KEY and API_SECRET else None
        
    def parse_signal(self) -> dict:
        """Parse signal from SIGNAL.md"""
        if not SIGNAL_FILE.exists():
            return None
        
        content = SIGNAL_FILE.read_text()
        
        # Parse signal from markdown
        signal = {}
        
        # Extract fields
        import re
        action_match = re.search(r'\|\s*Action\s*\|\s*(\w+)\s*\|', content)
        if action_match:
            signal['action'] = action_match.group(1).lower()
        
        symbol_match = re.search(r'\|\s*Symbol\s*\|\s*([\w/]+)\s*\|', content)
        if symbol_match:
            signal['symbol'] = symbol_match.group(1)
        
        price_match = re.search(r'\|\s*Price\s*\|\s*([\d.]+)\s*\|', content)
        if price_match:
            signal['price'] = float(price_match.group(1))
        
        strategy_match = re.search(r'\|\s*Strategy\s*\|\s*(\w[\w-]*)\s*\|', content)
        if strategy_match:
            signal['strategy'] = strategy_match.group(1)
        
        # Parse raw JSON
        json_match = re.search(r'```json\n([\s\S]*?)\n```', content)
        if json_match:
            try:
                signal['raw'] = json.loads(json_match.group(1))
            except:
                pass
        
        return signal if signal else None
    
    def update_state(self, status: str, position: dict = None, pnl: float = 0):
        """Update TRADE_STATE.md"""
        state = f"""# Thor - Current Trade State

## Position
**{position['side'] if position else 'None'}**

---

## Balance
- **Account:** {self.balance:.2f} USDT ({'Paper' if self.paper_mode else 'Live'})
- **Status:** {status}

---

## Daily Stats
- **P&L:** {pnl:.2f} USDT
- **Time:** {datetime.utcnow().isoformat()}Z

---

*Last updated: {datetime.utcnow().isoformat()}Z*
"""
        STATE_FILE.write_text(state)
    
    def log_trade(self, trade: dict):
        """Log trade to TRADE_LOG.md"""
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        log_entry = f"| {timestamp} | {trade['side']} | ${trade['entry']:.4f} | ${trade.get('exit', 'N/A')} | {trade['pnl']:.2f} USDT | {trade['status']} |\n"
        
        if not LOG_FILE.exists():
            LOG_FILE.write_text("# Thor - Trade Log\n\n| Time | Side | Entry | Exit | P&L | Status |\n|------|------|-------|------|-----|--------|\n")
        
        with LOG_FILE.open('a') as f:
            f.write(log_entry)
    
    def execute_signal(self, signal: dict):
        """Execute trading signal"""
        if not signal:
            return
        
        action = signal.get('action', '')
        symbol = signal.get('symbol', 'XRPUSDT')
        price = signal.get('price', 0)
        
        print(f"[{datetime.utcnow().isoformat()}] Signal: {action.upper()} {symbol} @ ${price:.4f}")
        
        if self.paper_mode:
            # Paper trading - simulate execution
            if action == 'long':
                self.position = {
                    'side': 'LONG',
                    'size': self.balance * 0.2 / price,  # 20% of balance
                    'entry': price,
                    'entry_time': datetime.utcnow().isoformat()
                }
                self.update_state('running', self.position)
                print(f"  → OPENED LONG {self.position['size']:.4f} @ ${price:.4f}")
                
            elif action == 'short':
                self.position = {
                    'side': 'SHORT',
                    'size': self.balance * 0.2 / price,
                    'entry': price,
                    'entry_time': datetime.utcnow().isoformat()
                }
                self.update_state('running', self.position)
                print(f"  → OPENED SHORT {self.position['size']:.4f} @ ${price:.4f}")
                
            elif action == 'close' and self.position:
                pnl = (price - self.position['entry']) * self.position['size']
                if self.position['side'] == 'SHORT':
                    pnl = -pnl
                
                trade = {
                    'side': self.position['side'],
                    'entry': self.position['entry'],
                    'exit': price,
                    'pnl': pnl,
                    'status': 'closed'
                }
                self.log_trade(trade)
                
                self.balance += pnl
                self.position = None
                self.update_state('waiting', pnl=pnl)
                print(f"  → CLOSED: P&L = {pnl:+.2f} USDT | Balance = {self.balance:.2f} USDT")
        else:
            # Live trading - use Pionex API
            if not self.api:
                print("  → ERROR: No API configured for live trading")
                return
            
            # TODO: Implement live trading
            print(f"  → Live trading not implemented yet")
    
    def run(self):
        """Main loop - watch for signals"""
        print(f"Thor started ({'PAPER' if self.paper_mode else 'LIVE'} mode, balance: {self.balance} USDT)")
        
        last_signal = None
        
        while True:
            try:
                signal = self.parse_signal()
                
                if signal and signal != last_signal:
                    self.execute_signal(signal)
                    last_signal = signal.copy()
                
                time.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                print("\nThor stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(30)


if __name__ == '__main__':
    executor = ThorExecutor(paper_mode=PAPER_MODE, balance=BALANCE)
    executor.run()