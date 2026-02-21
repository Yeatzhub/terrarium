# Dataclass Validation & Serialization Pattern
*Ghost Learning | 2026-02-21*

Pattern for type-safe data classes with runtime validation and clean serialization — critical for API responses, trading configs, and position data.

## The Pattern

```python
from dataclasses import dataclass, asdict, field
from typing import Self, Any
from decimal import Decimal, InvalidOperation
from datetime import datetime
import json

class ValidationError(ValueError):
    """Custom validation error with field context."""
    pass

@dataclass(frozen=True, slots=True)
class Position:
    """Immutable position with strict validation."""
    symbol: str
    size: Decimal
    entry_price: Decimal
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self) -> None:
        """Validate after construction. Frozen=True ensures immutability."""
        if not self.symbol or len(self.symbol) > 20:
            raise ValidationError(f"Invalid symbol: {self.symbol}")
        if self.size == 0:
            raise ValidationError("Position size cannot be zero")
        if self.entry_price <= 0:
            raise ValidationError(f"Invalid entry price: {self.entry_price}")
    
    @classmethod
    def from_api(cls, data: dict[str, Any]) -> Self:
        """Factory method for API ingestion with coercion."""
        try:
            return cls(
                symbol=data["symbol"].upper().strip(),
                size=Decimal(str(data["size"])),
                entry_price=Decimal(str(data["entry_price"])),
                timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat()))
            )
        except (KeyError, InvalidOperation) as e:
            raise ValidationError(f"API data invalid: {e}")
    
    def to_api(self) -> dict[str, Any]:
        """Serialize for API output — Decimal → str to avoid float corruption."""
        return {
            "symbol": self.symbol,
            "size": str(self.size),
            "entry_price": str(self.entry_price),
            "timestamp": self.timestamp.isoformat()
        }
    
    def to_json(self) -> str:
        """JSON with custom encoder for Decimal."""
        return json.dumps(self.to_api())
    
    @property
    def notional(self) -> Decimal:
        """Computed property — immutable data, safe caching."""
        return self.size * self.entry_price


# === Usage ===

# 1. Construction with validation
try:
    pos = Position("BTCUSD", Decimal("0.5"), Decimal("50000"))
    print(f"Notional: ${pos.notional:,.2f}")
except ValidationError as e:
    print(f"Invalid: {e}")

# 2. From API (handles string→Decimal, ISO timestamps)
api_response = {
    "symbol": " ethusd ",
    "size": "2.5",
    "entry_price": "3000.50",
    "timestamp": "2026-02-21T04:23:00"
}
position = Position.from_api(api_response)
print(position.symbol)  # "ETHUSD" (normalized)

# 3. To API (precision-safe)
print(position.to_api()["size"])  # "2.5" (string, not float)

# 4. Immutability guarantee
try:
    position.size = Decimal("3.0")  # TypeError: frozen dataclass
except AttributeError:
    pass  # Expected

# 5. Copy with modification (functional update)
new_position = Position(
    symbol=position.symbol,
    size=position.size + Decimal("1.0"),
    entry_price=position.entry_price
)
```

## Why This Works

- **`frozen=True`**: Immutable positions prevent accidental mutation during calculations
- **`slots=True`**: ~50% memory reduction, faster attribute access
- **`__post_init__`**: Validation after construction, works with frozen dataclasses
- **`Decimal` as string in JSON**: Prevents `0.1 + 0.2 != 0.3` float disasters in trading
- **`from_api` factory**: Centralizes dirty data handling (strip, case, parse)

## Extension: Config with Defaults

```python
@dataclass(frozen=True, slots=True)
class TradingConfig:
    max_position_pct: Decimal = field(default=Decimal("0.1"))
    stop_loss_pct: Decimal = field(default=Decimal("0.02"))
    
    def __post_init__(self) -> None:
        if not 0 < self.max_position_pct <= 1:
            raise ValidationError("max_position_pct must be in (0, 1]")

# Load from env/file safely
import os
config = TradingConfig(
    max_position_pct=Decimal(os.getenv("MAX_POSITION_PCT", "0.1"))
)
```

## Key Benefits

1. **Type safety at runtime** — `Decimal` not float
2. **Fail fast** — validation on construction, not later
3. **Serialization safety** — no precision loss
4. **Immutability** — thread-safe, hashable, cache-friendly
5. **Self-documenting** — dataclass shows structure, `__post_init__` shows constraints

---
*Pattern: frozen dataclass + __post_init__ validation + from_api/to_api factories*
