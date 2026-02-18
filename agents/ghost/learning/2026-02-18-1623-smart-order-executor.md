# Smart Order Executor - Trading Utility

**Created:** 2026-02-18 16:23 (America/Chicago)  
**Purpose:** Async order execution with retry logic, fill tracking, and notification hooks  
**Use Immediately:** Drop into `btc-trading-bot/utils/smart_executor.py`

---

## File: `smart_executor.py`

```python
"""
Smart Order Executor
- Retry with exponential backoff
- Order fill tracking
- Position reconciliation
- Async/await pattern
"""

import asyncio
import json
import hashlib
import time
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Dict, List, Callable, Any
from datetime import datetime
import aiohttp


class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL_FILL = "partial_fill"
    FILLED = "filled"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RetryPolicy:
    """Configurable retry behavior"""
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        retryable_errors: tuple = (ConnectionError, asyncio.TimeoutError)
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_errors = retryable_errors

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for attempt N (0-indexed)"""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


@dataclass
class Fill:
    """Individual fill record"""
    amount: float
    price: float
    fee: float
    timestamp: datetime
    order_id: str


@dataclass  
class Order:
    """Order with lifecycle tracking"""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    order_type: str  # 'market' or 'limit'
    amount: float
    price: Optional[float]
    status: OrderStatus
    fills: List[Fill]
    created_at: datetime
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    error_msg: Optional[str] = None
    exchange_id: Optional[str] = None

    @property
    def filled_amount(self) -> float:
        return sum(f.amount for f in self.fills)

    @property
    def average_price(self) -> float:
        if not self.fills:
            return 0.0
        total_value = sum(f.amount * f.price for f in self.fills)
        return total_value / self.filled_amount

    @property
    def remaining(self) -> float:
        return self.amount - self.filled_amount

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'status': self.status.value,
            'filled_amount': self.filled_amount,
            'average_price': self.average_price,
            'remaining': self.remaining
        }


class OrderNotificator:
    """Webhook/SMS/notification dispatcher"""
    def __init__(self):
        self.callbacks: List[Callable] = []

    def register(self, callback: Callable):
        """Register notification callback"""
        self.callbacks.append(callback)

    async def notify(self, order: Order, event: str):
        """Send notifications to all registered callbacks"""
        payload = {
            'event': event,  # 'submitted', 'filled', 'partial_fill', 'failed'
            'order': order.to_dict(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        for cb in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(payload)
                else:
                    cb(payload)
            except Exception as e:
                print(f"Notification failed: {e}")


class SmartOrderExecutor:
    """
    Async order executor with:
    - Smart retry logic
    - Fill tracking 
    - Position reconciliation
    - Webhook notifications
    """
    
    def __init__(
        self,
        exchange,
        retry_policy: Optional[RetryPolicy] = None,
        notifier: Optional[OrderNotificator] = None
    ):
        self.exchange = exchange
        self.retry_policy = retry_policy or RetryPolicy()
        self.notifier = notifier or OrderNotificator()
        self._active_orders: Dict[str, Order] = {}
        self._order_history: List[Order] = []

    def _generate_id(self, symbol: str, side: str) -> str:
        """Generate unique order ID"""
        entropy = f"{symbol}:{side}:{time.time()}:{id(self)}"
        return f"ord_{hashlib.sha256(entropy.encode()).hexdigest()[:16]}"

    async def submit_order(
        self,
        symbol: str,
        side: str,
        amount: float,
        order_type: str = 'market',
        price: Optional[float] = None,
        **kwargs
    ) -> Order:
        """
        Submit order with retry logic and full tracking
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: Order quantity
            order_type: 'market' or 'limit'
            price: Limit price (required for limit orders)
        
        Returns:
            Order object with full lifecycle tracking
        """
        # Create order record
        order = Order(
            id=self._generate_id(symbol, side),
            symbol=symbol,
            side=side.lower(),
            order_type=order_type,
            amount=abs(amount),
            price=price,
            status=OrderStatus.PENDING,
            fills=[],
            created_at=datetime.utcnow()
        )
        
        self._active_orders[order.id] = order
        
        # Attempt submission with retries
        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                order.status = OrderStatus.SUBMITTED
                order.submitted_at = datetime.utcnow()
                
                # Execute on exchange
                if order_type == 'market':
                    if side.lower() == 'buy':
                        result = await self._create_market_buy(symbol, amount)
                    else:
                        result = await self._create_market_sell(symbol, amount)
                else:
                    result = await self._create_limit_order(
                        symbol, side, amount, price, **kwargs
                    )
                
                if result:
                    order.exchange_id = result.get('id')
                    
                    # Handle immediate fills (market orders)
                    if 'filled' in result:
                        fill = Fill(
                            amount=result.get('filled', amount),
                            price=result.get('price', 0),
                            fee=result.get('fee', {}).get('cost', 0),
                            timestamp=datetime.utcnow(),
                            order_id=order.exchange_id
                        )
                        order.fills.append(fill)
                        order.filled_at = datetime.utcnow()
                        
                        if order.remaining <= 0.001:  # Fully filled
                            order.status = OrderStatus.FILLED
                            await self.notifier.notify(order, 'filled')
                        else:
                            order.status = OrderStatus.PARTIAL_FILL
                            await self.notifier.notify(order, 'partial_fill')
                    
                    break  # Success - exit retry loop
                    
            except self.retry_policy.retryable_errors as e:
                if attempt < self.retry_policy.max_retries:
                    delay = self.retry_policy.get_delay(attempt)
                    print(f"Order failed (attempt {attempt + 1}), retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    order.status = OrderStatus.FAILED
                    order.error_msg = str(e)
                    await self.notifier.notify(order, 'failed')
                    
        self._order_history.append(order)
        return order

    async def _create_market_buy(self, symbol: str, amount: float) -> Dict:
        """Override with exchange-specific implementation"""
        if hasattr(self.exchange, 'create_market_buy_order'):
            return await asyncio.to_thread(self.exchange.create_market_buy_order, symbol, amount)
        raise NotImplementedError("Exchange integration required")

    async def _create_market_sell(self, symbol: str, amount: float) -> Dict:
        """Override with exchange-specific implementation"""
        if hasattr(self.exchange, 'create_market_sell_order'):
            return await asyncio.to_thread(self.exchange.create_market_sell_order, symbol, amount)
        raise NotImplementedError("Exchange integration required")

    async def _create_limit_order(
        self, symbol: str, side: str, amount: float, price: float, **kwargs
    ) -> Dict:
        """Override with exchange-specific implementation"""
        raise NotImplementedError("Limit order implementation required")

    async def poll_order_fills(self, order: Order) -> Order:
        """
        Poll exchange for order fills (for limit orders)
        Run this periodically for active limit orders
        """
        if order.status not in [OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILL]:
            return order
            
        try:
            if hasattr(self.exchange, 'fetch_order'):
                result = await asyncio.to_thread(
                    self.exchange.fetch_order, order.exchange_id, order.symbol
                )
                
                # Update fills if new trades occurred
                filled = result.get('filled', 0)
                if filled > order.filled_amount:
                    new_fill = Fill(
                        amount=filled - order.filled_amount,
                        price=result.get('average', result.get('price', 0)),
                        fee=result.get('fee', {}).get('cost', 0),
                        timestamp=datetime.utcnow(),
                        order_id=order.exchange_id
                    )
                    order.fills.append(new_fill)
                    
                    if order.remaining <= 0.001:
                        order.status = OrderStatus.FILLED
                        order.filled_at = datetime.utcnow()
                        await self.notifier.notify(order, 'filled')
                    else:
                        order.status = OrderStatus.PARTIAL_FILL
                        await self.notifier.notify(order, 'partial_fill')
                        
        except Exception as e:
            print(f"Error polling order {order.id}: {e}")
            
        return order

    async def reconcile_position(
        self, symbol: str, expected_amount: float
    ) -> Dict[str, Any]:
        """
        Compare expected position with exchange-reported position.
        Returns discrepancy info for investigation.
        """
        try:
            if hasattr(self.exchange, 'fetch_balance'):
                balance = await asyncio.to_thread(self.exchange.fetch_balance)
                actual = balance.get(symbol.split('/')[0], {}).get('free', 0)
                
                discrepancy = actual - expected_amount
                
                return {
                    'symbol': symbol,
                    'expected': expected_amount,
                    'actual': actual,
                    'discrepancy': discrepancy,
                    'reconciled': abs(discrepancy) < 0.0001,
                    'timestamp': datetime.utcnow().isoformat()
                }
        except Exception as e:
            return {
                'symbol': symbol,
                'error': str(e),
                'reconciled': False
            }
        
        return {'symbol': symbol, 'error': 'Method not available'}

    def get_order_history(self, symbol: Optional[str] = None) -> List[Order]:
        """Get order history, optionally filtered by symbol"""
        if symbol:
            return [o for o in self._order_history if o.symbol == symbol]
        return self._order_history.copy()

    def get_active_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get orders awaiting fills"""
        active = [o for o in self._active_orders.values() 
                  if o.status in [OrderStatus.SUBMITTED, OrderStatus.PARTIAL_FILL]]
        if symbol:
            return [o for o in active if o.symbol == symbol]
        return active


# ───────────────────────────────────────────────
# USAGE EXAMPLE
# ───────────────────────────────────────────────

async def main():
    """Quick usage demo"""
    from btc_trading_bot.exchange.kraken import KrakenExchange
    
    # Initialize
    api = KrakenExchange(paper=True)
    executor = SmartOrderExecutor(api)
    
    # Add webhook notification
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
    
    async def notify_slack(payload: dict):
        """Send fill notifications to Slack"""
        order = payload['order']
        if payload['event'] == 'filled':
            async with aiohttp.ClientSession() as session:
                await session.post(webhook_url, json={
                    "text": f"✅ Order Filled: {order['side'].upper()} {order['amount']} {order['symbol']} @ {order['average_price']:.2f}"
                })
    
    executor.notifier.register(notify_slack)
    
    # Submit order with auto-retry
    order = await executor.submit_order(
        symbol="BTC/USDT",
        side="buy",
        amount=0.001,
        order_type="market"
    )
    
    print(f"Order submitted: {order.id}")
    print(f"Status: {order.status.value}")
    print(f"Filled: {order.filled_amount}/{order.amount}")
    print(f"Avg Price: {order.average_price}")
    
    # Check position matches expectations
    reconciliation = await executor.reconcile_position(
        symbol="BTC/USDT",
        expected_amount=order.filled_amount
    )
    print(f"Position reconciled: {reconciliation['reconciled']}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Why This Pattern Works

| Feature | Benefit |
|---------|---------|
| **Retry with backoff** | Survives transient exchange issues without hammering the API |
| **Order state machine** | Clear lifecycle: pending → submitted → partial_fill → filled/failed |
| **Fill tracking** | Handles partial fills transparently; shows true avg price |
| **Async/await** | Non-blocking; can manage many orders concurrently |
| **Webhook notifications** | Instant alerts on fills/slippage/failures |
| **Position reconciliation** | Catches exchange sync issues before they compound |

## Drop Into Existing Bot

```python
# In your strategy file
from utils.smart_executor import SmartOrderExecutor, OrderNotificator

executor = SmartOrderExecutor(exchange_api)

# Add notification
async def on_fill(payload):
    await send_telegram(f"Filled: {payload['order']['filled_amount']}")
    
executor.notifier.register(on_fill)

# Fire and track
order = await executor.submit_order("BTC/USDT", "buy", 0.01)
```

---

**Immediate Use:** Copy `SmartOrderExecutor` + `Order` classes into `utils/smart_executor.py`, wire up to existing exchange class.
