# Structured Logging with Context Pattern
*Ghost Learning | 2026-02-21*

Pattern for consistent, queryable logs across async trading components. Essential for debugging live systems.

```python
"""
Structured logging with context propagation.
Enables filtering: logger.info("Order placed", extra={"order_id": "abc123"})
Query: jq '. | select(.order_id == "abc123")' trades.log
"""

import logging
import json
import sys
from contextvars import ContextVar
from contextlib import contextmanager
from typing import Any, Optional
from datetime import datetime
from dataclasses import asdict, is_dataclass

# === 1. JSON Formatter ===

class JSONFormatter(logging.Formatter):
    """Output structured JSON for log aggregation."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "source": f"{record.filename}:{record.lineno}",
        }
        
        # Add extra fields from `extra={...}`
        if hasattr(record, "extra"):
            log_obj.update(record.extra)
        
        # Add exception info
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_obj, default=str)


# === 2. Context Propagation ===

# ContextVars survive async task switches
_request_ctx: ContextVar[dict[str, Any]] = ContextVar("request_ctx", default={})

@contextmanager
def log_context(**kwargs):
    """Inject context fields into all logs within scope."""
    token = _request_ctx.set(kwargs)
    try:
        yield
    finally:
        _request_ctx.reset(token)


class ContextualLogger:
    """Logger wrapper that auto-injects context fields."""
    
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)
    
    def _log(self, level: int, msg: str, extra: Optional[dict] = None, **kwargs):
        """Merge context vars with explicit extras."""
        merged = {**_request_ctx.get(), **(extra or {}), **kwargs}
        
        # Handle dataclass objects in extra
        for key, val in merged.items():
            if is_dataclass(val) and not isinstance(val, type):
                merged[key] = asdict(val)
        
        self._logger.log(level, msg, extra={"extra": merged})
    
    def debug(self, msg: str, **kwargs): self._log(logging.DEBUG, msg, **kwargs)
    def info(self, msg: str, **kwargs): self._log(logging.INFO, msg, **kwargs)
    def warning(self, msg: str, **kwargs): self._log(logging.WARNING, msg, **kwargs)
    def error(self, msg: str, **kwargs): self._log(logging.ERROR, msg, **kwargs)
    def critical(self, msg: str, **kwargs): self._log(logging.CRITICAL, msg, **kwargs)
    
    def exception(self, msg: str, **kwargs):
        """Log with exception info attached."""
        merged = {**_request_ctx.get(), **kwargs}
        self._logger.exception(msg, extra={"extra": merged})


# === 3. Setup Function ===

def setup_logging(level: int = logging.INFO, use_json: bool = True):
    """Configure root logger with JSON formatting."""
    handler = logging.StreamHandler(sys.stdout)
    
    if use_json:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        ))
    
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(handler)
    root.setLevel(level)


# === Usage Examples ===

# Setup
setup_logging()
logger = ContextualLogger("trading.engine")

# Simple log
logger.info("Engine started")
# {"timestamp": "2026-02-21T06:23:00Z", "level": "INFO", 
#  "logger": "trading.engine", "message": "Engine started", ...}

# With explicit extra fields
logger.info("Order received", order_id="ord_123", symbol="BTCUSD", side="buy")
# {"order_id": "ord_123", "symbol": "BTCUSD", "side": "buy", ...}

# With context propagation (survives async boundaries)
with log_context(strategy="momentum", session_id="sess_456"):
    logger.info("Processing signal")  # Auto-includes strategy+session_id
    
    # Nested contexts merge
    with log_context(position_id="pos_789"):
        logger.info("Position opened")  # Has all 3 context fields
    
    logger.info("Signal processed")  # Back to 2 context fields

# Exception logging
try:
    1 / 0
except ZeroDivisionError:
    logger.exception("Calculation failed", component="risk_engine")
# Includes "exception" field with stack trace


# === Async Example ===

import asyncio

async def place_order(symbol: str, logger: ContextualLogger):
    with log_context(symbol=symbol, action="place_order"):
        logger.info("Sending order to exchange")
        await asyncio.sleep(0.1)  # Async boundary
        logger.info("Order confirmed")  # Context preserved!

async def main():
    setup_logging()
    logger = ContextualLogger("trading")
    
    # Each task gets isolated context
    await asyncio.gather(
        place_order("BTCUSD", logger),
        place_order("ETHUSD", logger)
    )

# asyncio.run(main())


# === Querying Logs ===

"""
# Save to file: python trade.py >> trades.log 2>&1

# Filter by order ID:
jq 'select(.order_id == "ord_123")' trades.log

# Get all errors in session:
jq 'select(.level == "ERROR" and .session_id == "sess_456")' trades.log

# Count trades by symbol:
jq -r 'select(.message | contains("Order")) | .symbol' trades.log | sort | uniq -c

# View in human-readable (dev mode):
setup_logging(use_json=False)  # Switch to plain text
"""

# === Dataclass Support ===

from dataclasses import dataclass

@dataclass
class Order:
    id: str
    symbol: str
    size: float

order = Order("ord_123", "BTCUSD", 0.5)
logger.info("Order created", order=order)
# {"order": {"id": "ord_123", "symbol": "BTCUSD", "size": 0.5}, ...}
```

## Why This Pattern

| Problem | Solution |
|---------|----------|
| Parsing log lines with regex | JSON output, query with `jq` |
| Losing context in async code | `ContextVar` survives task switches |
| Inconsistent field naming | Centralized `ContextualLogger` wrapper |
| No traceability | Auto-injected request/session IDs |
| Dataclass objects in logs | Auto-serialization via `asdict` |

## Production Tips

1. **Always use context for request tracing**: `session_id`, `trace_id`, `user_id`
2. **Structured = queryable**: Log aggregators (Loki, CloudWatch) index JSON fields
3. **ContextVars are thread-safe** but **NOT** inherited by threads (use `copy_context()`)
4. **Switch to plain text in dev**: `setup_logging(use_json=False)` for readability
5. **Add correlation IDs at entry points**: HTTP handlers, WebSocket connections, queue consumers

## Dependencies
- Standard library only (`logging`, `contextvars`, `json`)

---
*Pattern: Structured logging + ContextVars for traceability*
