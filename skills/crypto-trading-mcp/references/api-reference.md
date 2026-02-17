# API Reference

## Kraken API

### Public Endpoints (No Auth Required)

#### Get Server Time
```python
api.get_server_time()
# Returns: {'unixtime': 1234567890, 'rfc1123': 'Mon, 16 Feb 2026 12:00:00 GMT'}
```

#### Get Ticker
```python
api.get_ticker(['XXBTZUSD', 'XETHZUSD'])
# Returns: {
#   'XXBTZUSD': {
#     'a': ['65000.0', '1', '1.000'],  # ask
#     'b': ['64999.0', '1', '1.000'],  # bid
#     'c': ['65000.5', '0.5'],         # last trade
#     'v': ['1000', '5000'],           # volume
#     'p': ['64000', '64500'],         # vwap
#     't': [100, 500],                 # trades
#     'l': ['63000', '62000'],         # low
#     'h': ['66000', '67000'],         # high
#     'o': '64000'                     # open
#   }
# }
```

#### Get OHLC Data
```python
api.get_ohlc('XXBTZUSD', interval=60)  # 1-hour candles
# Returns: {
#   'XXBTZUSD': [
#     [time, open, high, low, close, vwap, volume, count],
#     ...
#   ],
#   'last': timestamp
# }
```

#### Get Order Book
```python
api.get_orderbook('XXBTZUSD', count=10)
# Returns: {
#   'XXBTZUSD': {
#     'bids': [[price, volume, timestamp], ...],
#     'asks': [[price, volume, timestamp], ...]
#   }
# }
```

### Private Endpoints (Requires API Key)

#### Get Balance
```python
api.get_balance()
# Returns: {'XXBT': '1.5', 'ZUSD': '10000.0', ...}
```

#### Place Order
```python
# Market order
api.place_order(
    pair='XXBTZUSD',
    type='buy',
    ordertype='market',
    volume=0.001
)

# Limit order
api.place_order(
    pair='XXBTZUSD',
    type='buy',
    ordertype='limit',
    volume=0.001,
    price=64000,
    time_in_force='GTC'
)
```

#### Cancel Order
```python
api.cancel_order(txid='O1234567890')
```

---

## Toobit API

**Status:** API incomplete - limited market data endpoints

### Public Endpoints

#### Exchange Info
```python
api.get_exchange_info()
# Returns: {'symbols': [...], 'timezone': 'UTC', ...}
```

### Private Endpoints

#### Place Order
```python
api.place_order(
    symbol='BTCUSDT',
    side='BUY',
    type='LIMIT',
    quantity=0.001,
    price=64000
)
```

**Note:** Toobit API lacks klines/depth endpoints. Use external price feeds for paper trading.

---

## Polymarket API

### Public Endpoints

#### Get Markets
```python
# Via requests
import requests
r = requests.get('https://clob.polymarket.com/markets', 
                 params={'active': 'true', 'limit': 100})
markets = r.json()['data']
```

#### Market Structure
```python
{
    'condition_id': '0x123...',
    'question': 'Will BTC reach $70k by March?',
    'tokens': [
        {'outcome': 'Yes', 'price': 0.65, 'token_id': '123'},
        {'outcome': 'No', 'price': 0.35, 'token_id '456'}
    ],
    'end_date_iso': '2026-03-01T00:00:00Z'
}
```

---

## Paper Trading API

### PaperAccount Methods

```python
from kraken_paper_trader import PaperAccount

# Initialize
paper = PaperAccount(initial_balance=10000.0)

# Place order
result = paper.place_paper_order(
    symbol='XXBTZUSD',
    side='buy',
    order_type='market',
    quantity=0.001,
    current_price=65000
)

# Get summary
summary = paper.get_summary(prices={'XXBTZUSD': 66000})
print(f"Balance: ${summary['balance']}")
print(f"P&L: ${summary['realized_pnl']}")

# Close position
paper.close_position('XXBTZUSD', current_price=67000)
```

---

## Strategy API

### Base Interface

```python
from kraken_strategies import MomentumStrategy

# Initialize
strategy = MomentumStrategy(
    rsi_period=14,
    rsi_overbought=70,
    rsi_oversold=30
)

# Analyze
signal = strategy.analyze(ohlc_data)
# Returns: Signal(action='buy', confidence=0.8, reason='RSI oversold')
```

### Signal Structure

```python
@dataclass
class Signal:
    action: str        # 'buy', 'sell', 'hold'
    confidence: float  # 0.0 to 1.0
    reason: str        # Human-readable explanation
    stop_loss: float   # Optional stop price
    take_profit: float # Optional target price
```

---

## Rate Limits

### Kraken
- Public API: 1 request/second
- Private API: 1 request/second
- Order placement: No explicit limit

### Toobit
- General: 1200 requests/minute
- WebSocket: 5 messages/second
- Order: 100 orders/10 seconds

### Best Practices
1. Implement exponential backoff
2. Cache data when possible
3. Use WebSocket for real-time data
4. Respect 429 responses

---

## Error Handling

All APIs raise custom exceptions:

```python
try:
    result = api.place_order(...)
except KrakenAPIError as e:
    print(f"Kraken error: {e}")
except ToobitAPIError as e:
    print(f"Toobit error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

Common errors:
- `EAPI:Invalid key` - Wrong API key
- `EAPI:Invalid signature` - Signature calculation error
- `EOrder:Insufficient funds` - Not enough balance
- `429` - Rate limited
