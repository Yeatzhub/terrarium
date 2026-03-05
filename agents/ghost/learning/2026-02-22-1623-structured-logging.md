# Structured Logging Pattern
*Ghost Learning | 2026-02-22*

Logs you can query, parse, and analyze. Essential for trading systems audit trails.

## The Problem

```python
# Unstructured - hard to query
print(f"Order filled: BTC @ 50000 size=0.5 pnl=250")

# How many BTC orders failed yesterday?
# Can't grep reliably, no timestamps, no context
```

## The Solution: Structured Logs

```python
"""
Structured Logging Pattern
JSON logs for trading systems.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
import traceback


class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogEvent:
    """Structured log entry."""
    timestamp: str
    level: str
    message: str
    event_type: str  # "order", "trade", "risk", "system"
    
    # Context
    symbol: Optional[str] = None
    order_id: Optional[str] = None
    trade_id: Optional[str] = None
    strategy: Optional[str] = None
    
    # Data
    data: Optional[dict] = None
    
    # Error context
    error: Optional[str] = None
    stack_trace: Optional[str] = None
    
    # Metadata
    correlation_id: Optional[str] = None
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Flatten to dict, removing None values."""
        d = {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
            "event_type": self.event_type,
        }
        if self.symbol:
            d["symbol"] = self.symbol
        if self.order_id:
            d["order_id"] = self.order_id
        if self.trade_id:
            d["trade_id"] = self.trade_id
        if self.strategy:
            d["strategy"] = self.strategy
        if self.data:
            d["data"] = self.data
        if self.error:
            d["error"] = self.error
        if self.stack_trace:
            d["stack_trace"] = self.stack_trace
        if self.correlation_id:
            d["correlation_id"] = self.correlation_id
        if self.duration_ms is not None:
            d["duration_ms"] = self.duration_ms
        return d
    
    def to_json(self) -> str:
        """JSON string for logging."""
        return json.dumps(self.to_dict())


class StructuredLogger:
    """
    Structured logger for trading systems.
    
    Usage:
        log = StructuredLogger("trading")
        log.order("submitted", symbol="BTC", order_id="123", data={"size": 0.5})
        log.trade("filled", symbol="ETH", pnl=250)
    """
    
    def __init__(
        self,
        component: str,
        output: Any = None,
        min_level: LogLevel = LogLevel.DEBUG
    ):
        self.component = component
        self.output = output or sys.stdout
        self.min_level = min_level
        self._correlation_id: Optional[str] = None
    
    def _emit(self, event: LogEvent) -> None:
        """Write log event."""
        levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
        if levels.index(LogLevel(event.level)) < levels.index(self.min_level):
            return
        
        if self._correlation_id:
            event.correlation_id = self._correlation_id
        
        self.output.write(event.to_json() + "\n")
    
    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()
    
    # === Event Methods ===
    
    def debug(self, message: str, **kwargs) -> None:
        """Debug level log."""
        self._emit(LogEvent(
            timestamp=self._timestamp(),
            level=LogLevel.DEBUG.value,
            message=message,
            event_type=kwargs.pop("event_type", "system"),
            **kwargs
        ))
    
    def info(self, message: str, **kwargs) -> None:
        """Info level log."""
        self._emit(LogEvent(
            timestamp=self._timestamp(),
            level=LogLevel.INFO.value,
            message=message,
            event_type=kwargs.pop("event_type", "system"),
            **kwargs
        ))
    
    def warning(self, message: str, **kwargs) -> None:
        """Warning level log."""
        self._emit(LogEvent(
            timestamp=self._timestamp(),
            level=LogLevel.WARNING.value,
            message=message,
            event_type=kwargs.pop("event_type", "system"),
            **kwargs
        ))
    
    def error(self, message: str, error: Exception = None, **kwargs) -> None:
        """Error level log with optional exception."""
        event = LogEvent(
            timestamp=self._timestamp(),
            level=LogLevel.ERROR.value,
            message=message,
            event_type=kwargs.pop("event_type", "system"),
            **kwargs
        )
        if error:
            event.error = str(error)
            event.stack_trace = traceback.format_exc()
        self._emit(event)
    
    # === Domain-Specific Methods ===
    
    def order(self, action: str, symbol: str = None, order_id: str = None, **kwargs) -> None:
        """Log order event."""
        self.info(
            f"Order {action}",
            event_type="order",
            symbol=symbol,
            order_id=order_id,
            **kwargs
        )
    
    def trade(self, action: str, symbol: str = None, trade_id: str = None, **kwargs) -> None:
        """Log trade event."""
        self.info(
            f"Trade {action}",
            event_type="trade",
            symbol=symbol,
            trade_id=trade_id,
            **kwargs
        )
    
    def risk(self, event: str, **kwargs) -> None:
        """Log risk event."""
        self.warning(
            f"Risk: {event}",
            event_type="risk",
            **kwargs
        )
    
    def position(self, action: str, symbol: str = None, **kwargs) -> None:
        """Log position change."""
        self.info(
            f"Position {action}",
            event_type="position",
            symbol=symbol,
            **kwargs
        )
    
    def signal(self, strategy: str, action: str, symbol: str = None, **kwargs) -> None:
        """Log trading signal."""
        self.info(
            f"Signal: {action}",
            event_type="signal",
            strategy=strategy,
            symbol=symbol,
            **kwargs
        )
    
    # === Context Managers ===
    
    def with_correlation(self, correlation_id: str) -> "StructuredLogger":
        """Set correlation ID for all logs in context."""
        self._correlation_id = correlation_id
        return self
    
    def timed(self, operation: str, **kwargs) -> "TimedContext":
        """Time an operation."""
        return TimedContext(self, operation, **kwargs)


class TimedContext:
    """Context manager for timing operations."""
    
    def __init__(self, logger: StructuredLogger, operation: str, **kwargs):
        self.logger = logger
        self.operation = operation
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now(timezone.utc)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (datetime.now(timezone.utc) - self.start_time).total_seconds() * 1000
        
        if exc_type:
            self.logger.error(
                f"{self.operation} failed",
                error=exc_val,
                duration_ms=duration_ms,
                **self.kwargs
            )
        else:
            self.logger.info(
                f"{self.operation} completed",
                event_type="timing",
                duration_ms=round(duration_ms, 2),
                **self.kwargs
            )
        
        return False  # Don't suppress exceptions


def log_errors(logger: StructuredLogger):
    """Decorator to log exceptions."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"{func.__name__} failed",
                    error=e,
                    event_type="error"
                )
                raise
        return wrapper
    return decorator


# === Convenience Factory ===

def get_logger(name: str, min_level: LogLevel = LogLevel.INFO) -> StructuredLogger:
    """Get a structured logger."""
    return StructuredLogger(name, min_level=min_level)


# === Usage ===

if __name__ == "__main__":
    log = get_logger("trading-bot")
    
    # Basic logs
    log.info("Bot started", data={"version": "1.0", "paper": True})
    
    # Domain-specific
    log.order("submitted", symbol="BTC", order_id="ORD-123", data={
        "side": "buy",
        "price": 50000,
        "size": 0.5
    })
    
    log.order("filled", symbol="BTC", order_id="ORD-123", data={
        "fill_price": 50001,
        "fill_size": 0.5
    })
    
    log.trade("opened", symbol="BTC", trade_id="TRD-456", data={
        "entry": 50001,
        "size": 0.5,
        "stop": 48000,
        "target": 55000
    })
    
    # With timing
    with log.timed("market_data_fetch", symbol="ETH"):
        # Simulate work
        import time
        time.sleep(0.05)
    
    # Risk event
    log.risk("drawdown_limit", data={
        "current_dd": 0.15,
        "limit": 0.20
    })
    
    # Signal
    log.signal("breakout", action="long", symbol="SOL", data={
        "entry": 100,
        "atr": 5
    })
    
    # Error handling
    try:
        1 / 0
    except Exception as e:
        log.error("Calculation failed", error=e, data={"expression": "1/0"})
    
    # With correlation ID
    log.with_correlation("session-123")
    log.info("Processing session")
    
    print("\n=== Sample Query (grep equivalent) ===")
    print("All order events:")
    print("  jq 'select(.event_type == \"order\")' logs.jsonl")
    print("\nErrors only:")
    print("  jq 'select(.level == \"ERROR\")' logs.jsonl")
```

## Output

```json
{"timestamp": "2026-02-22T16:23:00.123456+00:00", "level": "INFO", "message": "Bot started", "event_type": "system", "data": {"version": "1.0", "paper": true}}
{"timestamp": "2026-02-22T16:23:00.123789+00:00", "level": "INFO", "message": "Order submitted", "event_type": "order", "symbol": "BTC", "order_id": "ORD-123", "data": {"side": "buy", "price": 50000, "size": 0.5}}
{"timestamp": "2026-02-22T16:23:00.124012+00:00", "level": "INFO", "message": "Order filled", "event_type": "order", "symbol": "BTC", "order_id": "ORD-123", "data": {"fill_price": 50001, "fill_size": 0.5}}
{"timestamp": "2026-02-22T16:23:00.124234+00:00", "level": "INFO", "message": "Trade opened", "event_type": "trade", "symbol": "BTC", "trade_id": "TRD-456", "data": {"entry": 50001, "size": 0.5, "stop": 48000, "target": 55000}}
{"timestamp": "2026-02-22T16:23:00.175123+00:00", "level": "INFO", "message": "market_data_fetch completed", "event_type": "timing", "duration_ms": 50.12, "symbol": "ETH"}
{"timestamp": "2026-02-22T16:23:00.175456+00:00", "level": "WARNING", "message": "Risk: drawdown_limit", "event_type": "risk", "data": {"current_dd": 0.15, "limit": 0.2}}
{"timestamp": "2026-02-22T16:23:00.175789+00:00", "level": "INFO", "message": "Signal: long", "event_type": "signal", "strategy": "breakout", "symbol": "SOL", "data": {"entry": 100, "atr": 5}}
{"timestamp": "2026-02-22T16:23:00.176012+00:00", "level": "ERROR", "message": "Calculation failed", "event_type": "system", "error": "division by zero", "stack_trace": "...", "data": {"expression": "1/0"}}
```

## Query Examples

```bash
# All orders for BTC
jq 'select(.event_type == "order" and .symbol == "BTC")' logs.jsonl

# Errors with stack traces
jq 'select(.level == "ERROR") | {timestamp, message, error}' logs.jsonl

# Slow operations (>100ms)
jq 'select(.duration_ms > 100)' logs.jsonl

# Trade P&L summary
jq 'select(.event_type == "trade") | .data.pnl' logs.jsonl | jq -s 'add'

# Orders by hour
jq -R 'fromjson? | select(.event_type=="order") | .timestamp[:13]' logs.jsonl | sort | uniq -c
```

## Event Types

| Type | Use Case |
|------|----------|
| `order` | Order submission, fills, cancels |
| `trade` | Trade opens, closes, P&L |
| `position` | Position changes |
| `signal` | Strategy signals |
| `risk` | Risk limit warnings |
| `system` | Startup, errors, config |
| `timing` | Operation duration |

## Quick Reference

```python
log = get_logger("bot")

log.order("submitted", symbol="BTC", order_id="123")
log.trade("filled", symbol="ETH", data={"pnl": 250})
log.risk("limit_approaching", data={"usage": 0.18})
log.error("API failed", error=exception)

with log.timed("fetch_data"):
    data = fetch()

@log_errors(log)
def risky_function():
    ...
```

---
*Pattern: Structured Logging | JSON logs, domain methods, timing context, queryable*