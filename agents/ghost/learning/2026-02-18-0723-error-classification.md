# Trading Error Classification & Recovery System

**Pattern:** Hierarchical exception classes + Automatic recovery decisions  
**Use Case:** Distinguish between retryable errors (rate limits, network blips) vs fatal errors (invalid API keys, insufficient funds) without messy string parsing.

## The Problem

```python
# ❌ What NOT to do - from kraken.py
try:
    return self.exchange.fetch_balance()
except Exception as e:  # Too broad!
    print(f"Error: {e}")
    return {}
# Is this a network blip (retry) or bad API key (alert)? Who knows.
```

## The Solution

```python
"""Structured exception hierarchy for trading operations.

Each error type knows:
- Should we retry?
- How long to wait?
- Is this an alert-worthy failure?
"""

from typing import Optional


class TradingError(Exception):
    """Base trading exception."""
    retryable: bool = False
    default_wait_seconds: float = 0.0
    alert_priority: str = "low"  # low, medium, high, critical


# ═══════════════════════════════════════════════════════════
# RETRYABLE ERRORS (transient, will likely resolve)
# ═══════════════════════════════════════════════════════════

class RetryableError(TradingError):
    """Errors that warrant automatic retry."""
    retryable: bool = True
    max_retries: int = 3


class RateLimitError(RetryableError):
    """Exchange rate limit hit."""
    default_wait_seconds: float = 1.0
    alert_priority: str = "low"
    
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class NetworkError(RetryableError):
    """Connection issues, timeouts, DNS failures."""
    default_wait_seconds: float = 2.0
    max_retries: int = 5
    alert_priority: str = "medium"


class ExchangeMaintenanceError(RetryableError):
    """Exchange is down for maintenance."""
    default_wait_seconds: float = 30.0
    max_retries: int = 10
    alert_priority: str = "medium"


# ═══════════════════════════════════════════════════════════
# FATAL ERRORS (don't retry, alert immediately)
# ═══════════════════════════════════════════════════════════

class FatalError(TradingError):
    """Errors that should NOT be retried."""
    retryable: bool = False
    max_retries: int = 0


class AuthenticationError(FatalError):
    """API keys invalid or revoked."""
    alert_priority: str = "critical"


class InsufficientFundsError(FatalError):
    """Account lacks balance for operation."""
    alert_priority: str = "high"


class InvalidSymbolError(FatalError):
    """Trading pair doesn't exist."""
    alert_priority: str = "high"


class OrderValidationError(FatalError):
    """Order parameters violate exchange rules."""
    alert_priority: str = "high"


# ═══════════════════════════════════════════════════════════
# CONVERTER: Map exchange errors to our hierarchy
# ═══════════════════════════════════════════════════════════

import ccxt

ERROR_MAP = {
    # Rate limits
    'RateLimitExceeded': RateLimitError,
    'DDoSProtection': RateLimitError,
    'TooManyRequests': RateLimitError,
    
    # Network
    'NetworkError': NetworkError,
    'RequestTimeout': NetworkError,
    'ConnectionError': NetworkError,
    
    # Auth
    'AuthenticationError': AuthenticationError,
    'PermissionDenied': AuthenticationError,
    'InvalidAPIKey': AuthenticationError,
    
    # Trading
    'InsufficientFunds': InsufficientFundsError,
    'InvalidOrder': OrderValidationError,
    'BadSymbol': InvalidSymbolError,
    'OrderNotFound': FatalError,  # Probably already filled/cancelled
}


def classify_exchange_error(error: Exception) -> TradingError:
    """Convert generic exchange error to classified TradingError.
    
    Args:
        error: The original exception from ccxt or exchange
        
    Returns:
        A TradingError subclass with retry/recovery metadata
    """
    error_name = type(error).__name__
    message = str(error).lower()
    
    # Direct class lookup
    if error_name in ERROR_MAP:
        exc_class = ERROR_MAP[error_name]
        
        # Extract retry-after if present
        if exc_class == RateLimitError:
            retry_after = getattr(error, 'retry_after', None)
            return exc_class(str(error), retry_after)
        
        return exc_class(str(error))
    
    # Pattern matching for messy exchange messages
    if any(x in message for x in ['rate limit', 'too many requests', 'throttled']):
        return RateLimitError(str(error))
    
    if any(x in message for x in ['maintenance', 'system upgrade', 'offline']):
        return ExchangeMaintenanceError(str(error))
    
    if any(x in message for x in ['insufficient', 'not enough', 'balance']):
        return InsufficientFundsError(str(error))
    
    if any(x in message for x in ['invalid key', 'unauthorized', 'api key']):
        return AuthenticationError(str(error))
    
    # Unknown errors default to retryable (network blip?)
    return NetworkError(str(error))


# ═══════════════════════════════════════════════════════════
# USAGE: Exchange wrapper with automatic handling
# ═══════════════════════════════════════════════════════════

class SmartExchangeWrapper:
    """Exchange wrapper with intelligent error handling."""
    
    def __init__(self, exchange_id: str, api_key: str, secret: str):
        self.exchange = getattr(ccxt, exchange_id)({
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
        })
        self.last_errors: list[TradingError] = []
    
    async def fetch_balance(self, max_retries: int = 3) -> dict:
        """Fetch balance with automatic retry logic."""
        for attempt in range(max_retries):
            try:
                return await self.exchange.fetch_balance()
            except Exception as e:
                classified = classify_exchange_error(e)
                self.last_errors.append(classified)
                
                if not classified.retryable:
                    raise classified  # Fatal - bubble up immediately
                
                if attempt >= min(classified.max_retries, max_retries - 1):
                    raise classified  # Exhausted retries
                
                # Wait with exponential backoff
                wait = classified.default_wait_seconds * (2 ** attempt)
                await asyncio.sleep(wait)
        
        return {}  # Should never reach here
    
    async def place_order(self, symbol: str, side: str, amount: float, price: float = None):
        """Place order with immediate fatal error detection."""
        try:
            if price:
                return await self.exchange.create_limit_order(symbol, side, amount, price)
            else:
                return await self.exchange.create_market_order(symbol, side, amount)
        except Exception as e:
            classified = classify_exchange_error(e)
            
            # Log with appropriate severity
            if classified.alert_priority == "critical":
                logger.critical(f"CRITICAL: {classified}")
                pagerduty_alert(str(classified))  # Page the human
            elif classified.alert_priority == "high":
                logger.error(f"HIGH: {classified}")
            
            raise classified


# ═══════════════════════════════════════════════════════════
# MONITORING: Alert routing
# ═══════════════════════════════════════════════════════════

def get_error_stats(errors: list[TradingError]) -> dict:
    """Summarize error patterns for monitoring dashboards."""
    from collections import Counter
    
    return {
        'total': len(errors),
        'by_type': Counter(type(e).__name__ for e in errors),
        'by_priority': Counter(e.alert_priority for e in errors),
        'retryable_pct': sum(1 for e in errors if e.retryable) / len(errors) * 100
        if errors else 0
    }


# Example stats output:
# {
#     'total': 47,
#     'by_type': {'RateLimitError': 35, 'NetworkError': 10, 'InsufficientFundsError': 2},
#     'by_priority': {'low': 35, 'medium': 10, 'high': 2},
#     'retryable_pct': 95.7
# }
```

## Why This Pattern Wins

| Approach | Retryable Detection | Alert Priorities | Actionable Metrics |
|----------|-------------------|------------------|-------------------|
| `except Exception` | Manual string parsing | None | None |
| This pattern | `error.retryable` property | Built-in priority | Automatic stats |

## Integration Example

Replace the simple catch-all in your exchange wrappers:

```python
# Before
except Exception as e:
    print(f"Error: {e}")
    return {}

# After  
except TradingError as e:
    if not e.retryable:
        alert_ops(f"Fatal trading error: {e}")
        raise
    # Automatic retry handled upstream
```

## Files in this learning series:
- `2026-02-18-0423-async-context-managers.md` - Resource cleanup patterns
- `2026-02-18-0523-trading-retry-handler.md` - Circuit breaker implementation  
- `2026-02-18-0623-position-sizing.md` - Risk management math
- `2026-02-18-0723-error-classification.md` - This file
