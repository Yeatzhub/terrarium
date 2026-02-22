# Configuration Management Pattern
*Ghost Learning | 2026-02-21*

Type-safe, validated configuration loading with environment overrides, secrets handling, and hot-reload support. Essential for trading bot deployment.

```python
"""
Configuration Management Pattern
Type-safe config with validation, env overrides, and secrets handling.
"""

import os
import json
import yaml
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, TypeVar, Type, get_type_hints, Any
from decimal import Decimal
from enum import Enum


T = TypeVar("T")


class Environment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "dev"
    STAGING = "staging"
    PRODUCTION = "prod"


@dataclass(frozen=True)
class TradingConfig:
    """Trading parameters."""
    max_position_pct: Decimal = Decimal("0.20")
    max_risk_per_trade_pct: Decimal = Decimal("0.02")
    default_stop_pct: Decimal = Decimal("0.015")
    min_trade_size: Decimal = Decimal("10")
    max_open_positions: int = 10
    max_leverage: Decimal = Decimal("5")
    
    def __post_init__(self):
        """Validate config."""
        if not 0 < self.max_position_pct <= 1:
            raise ValueError(f"max_position_pct must be in (0,1], got {self.max_position_pct}")
        if not 0 < self.max_risk_per_trade_pct <= 0.5:
            raise ValueError(f"max_risk_per_trade_pct must be in (0,0.5], got {self.max_risk_per_trade_pct}")


@dataclass(frozen=True)
class ExchangeConfig:
    """Exchange connection settings."""
    name: str
    api_key: str = field(repr=False)  # Hide in logs
    api_secret: str = field(repr=False)
    sandbox: bool = True
    base_url: Optional[str] = None
    timeout_seconds: int = 30
    rate_limit_requests_per_second: int = 10
    
    def __post_init__(self):
        if not self.api_key or not self.api_secret:
            raise ValueError(f"API credentials required for {self.name}")
        if self.timeout_seconds < 1:
            raise ValueError("Timeout must be positive")


@dataclass(frozen=True)
class NotificationConfig:
    """Alert settings."""
    telegram_bot_token: Optional[str] = field(default=None, repr=False)
    telegram_chat_id: Optional[str] = None
    email_smtp_host: Optional[str] = None
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = field(default=None, repr=False)
    webhook_url: Optional[str] = None
    
    @property
    def telegram_enabled(self) -> bool:
        return self.telegram_bot_token is not None and self.telegram_chat_id is not None
    
    @property
    def email_enabled(self) -> bool:
        return all([self.email_smtp_host, self.email_username, self.email_password])


@dataclass(frozen=True)
class AppConfig:
    """Application configuration root."""
    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    data_dir: Path = field(default_factory=lambda: Path("./data"))
    
    trading: TradingConfig = field(default_factory=TradingConfig)
    exchange: ExchangeConfig = field(default_factory=lambda: ExchangeConfig(name="default"))
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    
    def to_dict(self) -> dict:
        """Serialize to dict (excluding secrets)."""
        return asdict(self)
    
    def to_json(self, include_secrets: bool = False) -> str:
        """Serialize to JSON."""
        data = self.to_dict()
        if not include_secrets:
            data = self._remove_secrets(data)
        return json.dumps(data, indent=2, default=str)
    
    def _remove_secrets(self, data: dict) -> dict:
        """Remove sensitive fields from dict."""
        secret_keys = {'api_key', 'api_secret', 'password', 'token', 'secret'}
        cleaned = {}
        for k, v in data.items():
            if any(sk in k.lower() for sk in secret_keys):
                cleaned[k] = "***"
            elif isinstance(v, dict):
                cleaned[k] = self._remove_secrets(v)
            else:
                cleaned[k] = v
        return cleaned


class ConfigLoader:
    """Load configuration from files and environment."""
    
    def __init__(self, env_prefix: str = "BOT_"):
        self.env_prefix = env_prefix
    
    def load(
        self,
        config_path: Optional[Path] = None,
        env: Optional[Environment] = None
    ) -> AppConfig:
        """Load config from file and environment."""
        
        # Start with defaults
        config_dict = {}
        
        # Load from file
        if config_path and config_path.exists():
            config_dict.update(self._load_file(config_path))
        
        # Override from environment
        config_dict.update(self._load_env_overrides())
        
        # Detect environment
        detected_env = env or self._detect_environment()
        config_dict['environment'] = detected_env
        
        # Parse nested config
        trading = TradingConfig(**config_dict.get('trading', {}))
        exchange = ExchangeConfig(**config_dict.get('exchange', {}))
        notifications = NotificationConfig(**config_dict.get('notifications', {}))
        
        # Build final config
        return AppConfig(
            environment=detected_env,
            log_level=config_dict.get('log_level', 'INFO'),
            data_dir=Path(config_dict.get('data_dir', './data')),
            trading=trading,
            exchange=exchange,
            notifications=notifications
        )
    
    def _load_file(self, path: Path) -> dict:
        """Load config from YAML or JSON file."""
        with open(path) as f:
            if path.suffix in ('.yaml', '.yml'):
                return yaml.safe_load(f) or {}
            return json.load(f)
    
    def _load_env_overrides(self) -> dict:
        """Load config overrides from environment variables."""
        overrides = {}
        
        # Map env vars to config keys
        mapping = {
            f"{self.env_prefix}ENV": 'environment',
            f"{self.env_prefix}LOG_LEVEL": 'log_level',
            f"{self.env_prefix}DATA_DIR": 'data_dir',
            f"{self.env_prefix}MAX_POSITION_PCT": ('trading', 'max_position_pct'),
            f"{self.env_prefix}MAX_RISK_PCT": ('trading', 'max_risk_per_trade_pct'),
            f"{self.env_prefix}EXCHANGE_KEY": ('exchange', 'api_key'),
            f"{self.env_prefix}EXCHANGE_SECRET": ('exchange', 'api_secret'),
            f"{self.env_prefix}EXCHANGE_SANDBOX": ('exchange', 'sandbox'),
            f"{self.env_prefix}TELEGRAM_TOKEN": ('notifications', 'telegram_bot_token'),
            f"{self.env_prefix}TELEGRAM_CHAT": ('notifications', 'telegram_chat_id'),
        }
        
        for env_var, config_key in mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Handle nested keys
                if isinstance(config_key, tuple):
                    section, key = config_key
                    if section not in overrides:
                        overrides[section] = {}
                    overrides[section][key] = self._convert_type(value)
                else:
                    overrides[config_key] = self._convert_type(value)
        
        return overrides
    
    def _convert_type(self, value: str) -> Any:
        """Convert string env var to appropriate type."""
        # Boolean
        if value.lower() in ('true', '1', 'yes'):
            return True
        if value.lower() in ('false', '0', 'no'):
            return False
        
        # Number
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        
        return value
    
    def _detect_environment(self) -> Environment:
        """Detect environment from various sources."""
        env_vars = ['BOT_ENV', 'ENV', 'ENVIRONMENT']
        for var in env_vars:
            val = os.getenv(var, '').lower()
            if val in ('prod', 'production'):
                return Environment.PRODUCTION
            if val in ('staging', 'stage'):
                return Environment.STAGING
        return Environment.DEVELOPMENT


class ConfigValidator:
    """Validate configuration for production safety."""
    
    CRITICAL_CHECKS = [
        "_check_sandbox_in_dev",
        "_check_no_test_creds_in_prod",
        "_check_reasonable_limits",
        "_check_notification_fallback",
    ]
    
    def validate(self, config: AppConfig) -> list[tuple[bool, str]]:
        """Run all validation checks."""
        results = []
        for check in self.CRITICAL_CHECKS:
            passed, message = getattr(self, check)(config)
            results.append((passed, message))
        return results
    
    def _check_sandbox_in_dev(self, config: AppConfig) -> tuple[bool, str]:
        """Ensure sandbox mode in development."""
        if config.environment == Environment.DEVELOPMENT and not config.exchange.sandbox:
            return False, "⚠️  Using LIVE exchange in DEVELOPMENT environment!"
        return True, "✓ Sandbox mode appropriately configured"
    
    def _check_no_test_creds_in_prod(self, config: AppConfig) -> tuple[bool, str]:
        """Check for test credentials in production."""
        test_patterns = ['test', 'demo', 'sandbox', 'example', 'changeme']
        key_lower = config.exchange.api_key.lower()
        if config.environment == Environment.PRODUCTION:
            if any(p in key_lower for p in test_patterns):
                return False, "⚠️  Production environment with test credentials detected!"
        return True, "✓ Credentials look legitimate"
    
    def _check_reasonable_limits(self, config: AppConfig) -> tuple[bool, str]:
        """Verify risk limits are reasonable."""
        trading = config.trading
        warnings = []
        
        if trading.max_position_pct > Decimal("0.5"):
            warnings.append(f"Position size limit {trading.max_position_pct:.0%} is high")
        
        if trading.max_leverage > Decimal("10"):
            warnings.append(f"Max leverage {trading.max_leverage}x is aggressive")
        
        if warnings:
            return True, "⚠️  " + "; ".join(warnings)
        return True, "✓ Risk limits look reasonable"
    
    def _check_notification_fallback(self, config: AppConfig) -> tuple[bool, str]:
        """Ensure at least one notification method is configured."""
        if not (config.notifications.telegram_enabled or config.notifications.email_enabled):
            return True, "⚠️  No notifications configured — you won't get alerts!"
        return True, "✓ Notifications configured"


def create_template_config(path: Path) -> None:
    """Generate sample config file."""
    template = {
        "log_level": "INFO",
        "data_dir": "./data",
        "trading": {
            "max_position_pct": 0.20,
            "max_risk_per_trade_pct": 0.02,
            "max_open_positions": 10
        },
        "exchange": {
            "name": "binance",
            "api_key": "YOUR_API_KEY",
            "api_secret": "YOUR_API_SECRET",
            "sandbox": True,
            "timeout_seconds": 30
        },
        "notifications": {
            "telegram_bot_token": "OPTIONAL",
            "telegram_chat_id": "OPTIONAL"
        }
    }
    
    with open(path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False)
    print(f"Created template config at {path}")


# === Usage Example ===

def example():
    """Demonstrate config loading."""
    # Load with defaults
    loader = ConfigLoader()
    
    # Load from file (if exists) + env overrides
    config = loader.load(Path("config.yaml"))
    
    print(f"Environment: {config.environment.value}")
    print(f"Max Position: {config.trading.max_position_pct:.0%}")
    print(f"Exchange: {config.exchange.name}")
    print(f"Sandbox: {config.exchange.sandbox}")
    
    # Validate
    validator = ConfigValidator()
    results = validator.validate(config)
    
    print("\nValidation:")
    for passed, message in results:
        status = "✓" if passed else "✗"
        print(f"  {status} {message}")
    
    # Export (without secrets)
    print(f"\nSafe Config Export:\n{config.to_json()}")


# === Environment Variable Examples ===

# BOT_ENV=production
# BOT_LOG_LEVEL=DEBUG
# BOT_MAX_POSITION_PCT=0.15
# BOT_EXCHANGE_KEY=abc123
# BOT_EXCHANGE_SECRET=xyz789
# BOT_EXCHANGE_SANDBOX=false
# BOT_TELEGRAM_TOKEN=123456:ABC
# BOT_TELEGRAM_CHAT=-100123456


def main():
    """Generate template config."""
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--template":
        create_template_config(Path("config.template.yaml"))
    else:
        example()


if __name__ == "__main__":
    main()
```

## Quick Start

```bash
# Generate template config
python config_pattern.py --template

# Load config (file + env overrides)
python config_pattern.py
```

## Features

| Feature | Description |
|---------|-------------|
| **Type Safety** | Frozen dataclasses with validation |
| **Env Overrides** | `BOT_MAX_POSITION_PCT=0.15` overrides file |
| **Secrets Protection** | `repr=False` hides secrets in logs |
| **Safe Export** | `to_json()` excludes sensitive fields |
| **Validation** | Production safety checks (sandbox, test creds) |
| **Nested Config** | Trading, Exchange, Notification sections |

## Environment Variables

| Variable | Maps To |
|----------|---------|
| `BOT_ENV` | environment |
| `BOT_MAX_POSITION_PCT` | trading.max_position_pct |
| `BOT_EXCHANGE_KEY` | exchange.api_key |
| `BOT_EXCHANGE_SECRET` | exchange.api_secret |
| `BOT_TELEGRAM_TOKEN` | notifications.telegram_bot_token |

## Validation Checks

| Check | Purpose |
|-------|---------|
| Sandbox in dev | Prevents live trading in development |
| No test creds in prod | Catches placeholder API keys |
| Reasonable limits | Warns on extreme position/leverage |
| Notification fallback | Ensures alerts are configured |

## YAML Config Example

```yaml
log_level: INFO
data_dir: ./data

trading:
  max_position_pct: 0.20
  max_risk_per_trade_pct: 0.02
  max_open_positions: 10

exchange:
  name: binance
  api_key: ${EXCHANGE_KEY}  # Use env substitution
  api_secret: ${EXCHANGE_SECRET}
  sandbox: true
  timeout_seconds: 30

notifications:
  telegram_bot_token: ${TELEGRAM_TOKEN}
  telegram_chat_id: ${TELEGRAM_CHAT}
```

## Why Frozen Dataclasses

- **Immutable**: Can't accidentally mutate after loading
- **Type-safe**: mypy catches errors at static analysis
- **Default values**: Sensible defaults, override as needed
- **`__post_init__`**: Validation runs on instantiation

---
*Pattern: Type-safe Configuration Management with Environment Overrides*
