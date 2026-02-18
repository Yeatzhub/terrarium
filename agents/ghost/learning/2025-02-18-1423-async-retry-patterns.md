# Async Context Manager + Retry Pattern for Trading APIs

Date: 2025-02-18  
Agent: Ghost (👻)  
Topic: Resilient async API calls with exponential backoff

## The Problem

Trading bots hit APIs thousands of times. Networks flake, exchanges rate-limit, connections reset. Your bot dies mid-trade or worse — hangs forever.

**What we need:**
- Automatic retry with exponential backoff
- Proper timeout handling
- Rate limit awareness (429 detection)
- Clean connection lifecycle
- Circuit breaker for repeated failures

## The Pattern: `AsyncRetryClient`

```python
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum, auto
import aiohttp
from typing import Optional, Callable


class CircuitState(Enum):
    CLOSED = auto()   # Normal operation
    OPEN = auto()     # Failing fast
    HALF_OPEN = auto()  # Testing recovery


@dataclass
class RetryConfig:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    timeout: float = 30.0
    circuit_threshold: int = 5  # failures before opening
    circuit_timeout: float = 60.0  # seconds before half-open


class CircuitBreaker:
    """Prevents cascade failures. Open circuit = fail fast."""
    
    def __init__(self, threshold: int = 5, timeout: float = 60.0):
        self.threshold = threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure: Optional[float] = None
        self.state = CircuitState.CLOSED
    
    def record_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self) -> CircuitState:
        self.failures += 1
        self.last_failure = asyncio.get_event_loop().time()
        
        if self.failures >= self.threshold:
            self.state = CircuitState.OPEN
        return self.state
    
    def can_attempt(self) -> bool:
        now = asyncio.get_event_loop().time()
        
        if self.state == CircuitState.OPEN:
            if now - (self.last_failure or 0) > self.timeout:
                self.state = CircuitState.HALF_OPEN
                return True
            return False
        return True


@asynccontextmanager
async def retry_client(
    session: aiohttp.ClientSession,
    config: RetryConfig = None,
    on_rate_limit: Optional[Callable[[float], None]] = None
):
    """
    Context manager for resilient API calls.
    
    Usage:
        async with retry_client(session) as fetch:
            data = await fetch("GET", "https://api.exchange.com/ticker")
    """
    cfg = config or RetryConfig()
    circuit = CircuitBreaker(cfg.circuit_threshold, cfg.circuit_timeout)
    
    async def fetch_with_retry(method: str, url: str, **kwargs) -> dict:
        if not circuit.can_attempt():
            raise Exception("Circuit breaker OPEN - too many failures")
        
        for attempt in range(cfg.max_retries + 1):
            try:
                timeout = aiohttp.ClientTimeout(total=cfg.timeout)
                async with session.request(
                    method, url, timeout=timeout, **kwargs
                ) as response:
                    
                    if response.status == 429:
                        retry_after = float(
                            response.headers.get("Retry-After", cfg.base_delay * 2 ** attempt)
                        )
                        if on_rate_limit:
                            on_rate_limit(retry_after)
                        await asyncio.sleep(min(retry_after, cfg.max_delay))
                        continue  # Retry after rate limit
                    
                    response.raise_for_status()
                    data = await response.json()
                    circuit.record_success()
                    return data
                    
            except aiohttp.ClientError as e:
                circuit.record_failure()
                if attempt == cfg.max_retries:
                    raise
                
                delay = min(cfg.base_delay * (2 ** attempt), cfg.max_delay)
                await asyncio.sleep(delay)
                
            except asyncio.TimeoutError:
                circuit.record_failure()
                if attempt == cfg.max_retries:
                    raise
                await asyncio.sleep(cfg.base_delay)
        
        raise Exception("Max retries exceeded")
    
    try:
        yield fetch_with_retry
    finally:
        # Cleanup if needed
        pass


# --- Practical Example: Exchange API Wrapper ---

class ResilientExchangeClient:
    """Drop-in replacement for raw aiohttp calls in trading bots."""
    
    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limit_hits = 0
    
    async def __aenter__(self):
        self._session = aiohttp.ClientSession(
            headers={"User-Agent": "TradingBot/1.0"}
        )
        return self
    
    async def __aexit__(self, *args):
        if self._session:
            await self._session.close()
    
    async def get_ticker(self, symbol: str) -> dict:
        config = RetryConfig(
            max_retries=3,
            base_delay=0.5,  # Fast markets need quick retries
            timeout=10.0     # Don't hang on stale data
        )
        
        def log_rate_limit(wait: float):
            self._rate_limit_hits += 1
            print(f"⚠️  Rate limited. Waiting {wait:.1f}s (hit #{self._rate_limit_hits})")
        
        async with retry_client(self._session, config, log_rate_limit) as fetch:
            return await fetch("GET", f"{self.base_url}/ticker/{symbol}")
    
    async def place_order(self, symbol: str, side: str, amount: float) -> dict:
        # Orders need higher reliability - more retries, longer timeouts
        config = RetryConfig(
            max_retries=5,
            base_delay=1.0,
            timeout=45.0
        )
        
        async with retry_client(self._session, config) as fetch:
            return await fetch(
                "POST",
                f"{self.base_url}/order",
                json={"symbol": symbol, "side": side, "amount": amount}
            )


# --- Quick Test ---

async def demo():
    client = ResilientExchangeClient("https://api.exchange.com")
    
    async with client:
        try:
            ticker = await client.get_ticker("BTCUSD")
            print(f"Price: {ticker.get('price')}")
        except Exception as e:
            print(f"Failed after all retries: {e}")


if __name__ == "__main__":
    asyncio.run(demo())
```

## Why This Pattern

| Feature | Why It Matters |
|---------|---------------|
| **Exponential backoff** | Avoids hammering a struggling server |
| **Different retry configs** | Market data can fail fast; orders must succeed |
| **Circuit breaker** | Prevents cascade failures when exchange is down |
| **429 detection** | Respects rate limits automatically |
| **Async context mgr** | Clean resource lifecycle, no connection leaks |

## Integration in Trading Bot

Replace direct `aiohttp` calls in `exchange/` modules:

```python
# Before:
async with session.get(url) as r:
    return await r.json()

# After:
async with retry_client(session, trading_config) as fetch:
    return await fetch("GET", url)
```

**Result:** Bot survives network blips, respects limits, fails gracefully when needed.