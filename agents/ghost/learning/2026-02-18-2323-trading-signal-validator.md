# Trading Signal Validator
*2026-02-18 23:23* - Practical utility for pre-execution signal validation

## Purpose
Validate trading signals before execution to catch errors early, prevent over-leverage, and enforce risk rules. Acts as a gatekeeper between signal generators and order execution.

## Code

```python
"""
Trading Signal Validator
Pre-execution validation for trading signals.
"""
from dataclasses import dataclass
from typing import Optional, List, Callable
from enum import Enum, auto
import re

class ValidationSeverity(Enum):
    ERROR = auto()    # Block execution
    WARNING = auto()  # Log but allow

@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    errors: List[str]
    warnings: List[str]
    
    @property
    def can_execute(self) -> bool:
        return self.passed and not self.errors

@dataclass
class TradingSignal:
    symbol: str
    side: str  # 'BUY' or 'SELL'
    size: float
    price: Optional[float] = None  # None for market orders
    order_type: str = 'LIMIT'
    time_in_force: str = 'GTC'
    
class SignalValidator:
    """Composable signal validator with built-in and custom rules."""
    
    def __init__(
        self,
        max_position_size: float = 100.0,
        max_order_value: float = 100000.0,
        allowed_symbols: Optional[List[str]] = None,
        price_deviation_pct: float = 5.0,
        reference_prices: Optional[dict] = None
    ):
        self.max_position_size = max_position_size
        self.max_order_value = max_order_value
        self.allowed_symbols = allowed_symbols
        self.price_deviation_pct = price_deviation_pct
        self.reference_prices = reference_prices or {}
        self.custom_rules: List[Callable[[TradingSignal], ValidationResult]] = []
    
    def add_rule(self, rule: Callable[[TradingSignal], ValidationResult]):
        """Add custom validation rule."""
        self.custom_rules.append(rule)
        return self  # Fluent interface
    
    def validate(self, signal: TradingSignal) -> ValidationResult:
        """Run all validation rules."""
        errors, warnings = [], []
        
        # 1. Symbol validation
        if not self._is_valid_symbol(signal.symbol):
            errors.append(f"Invalid symbol format: {signal.symbol}")
        elif self.allowed_symbols and signal.symbol not in self.allowed_symbols:
            errors.append(f"Symbol not in whitelist: {signal.symbol}")
        
        # 2. Side validation
        if signal.side not in ('BUY', 'SELL'):
            errors.append(f"Invalid side: {signal.side}")
        
        # 3. Size validation
        if signal.size <= 0:
            errors.append(f"Size must be positive: {signal.size}")
        elif signal.size > self.max_position_size:
            errors.append(f"Size {signal.size} exceeds max {self.max_position_size}")
        
        # 4. Price validation for limit orders
        if signal.order_type == 'LIMIT':
            if signal.price is None or signal.price <= 0:
                errors.append("Limit orders require positive price")
            else:
                order_value = signal.size * signal.price
                if order_value > self.max_order_value:
                    errors.append(f"Order value ${order_value:,.2f} exceeds max")
                
                # Price sanity check vs reference
                ref = self.reference_prices.get(signal.symbol)
                if ref:
                    deviation = abs(signal.price - ref) / ref * 100
                    if deviation > self.price_deviation_pct:
                        warnings.append(
                            f"Price {signal.price} deviates {deviation:.1f}% from ref {ref}"
                        )
        
        # 5. Run custom rules
        for rule in self.custom_rules:
            result = rule(signal)
            errors.extend(result.errors)
            warnings.extend(result.warnings)
        
        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _is_valid_symbol(self, symbol: str) -> bool:
        """Basic symbol format check."""
        return bool(re.match(r'^[A-Z0-9\-]{2,20}$', symbol))


# === PRACTICAL EXAMPLES ===

def example_basic_usage():
    """Basic validation setup."""
    validator = SignalValidator(
        max_position_size=10.0,
        max_order_value=50000.0,
        allowed_symbols=['BTC-USD', 'ETH-USD', 'SOL-USD'],
        reference_prices={'BTC-USD': 50000.0, 'ETH-USD': 3000.0}
    )
    
    # Valid signal
    signal = TradingSignal(
        symbol='BTC-USD',
        side='BUY',
        size=0.5,
        price=49500.0,
        order_type='LIMIT'
    )
    
    result = validator.validate(signal)
    print(f"Can execute: {result.can_execute}")
    if result.warnings:
        print(f"Warnings: {result.warnings}")
    
    return result

def example_with_custom_rule():
    """Add custom risk rules."""
    
    # Rule: No trading in first/last 30 min of session
    def session_timing_rule(signal: TradingSignal) -> ValidationResult:
        from datetime import datetime
        now = datetime.now()
        minute = now.hour * 60 + now.minute
        
        # Assume 9:30-16:00 session (EST)
        market_open = 9 * 60 + 30  # 570
        market_close = 16 * 60      # 960
        
        if minute < market_open + 30 or minute > market_close - 30:
            return ValidationResult(
                passed=False,
                errors=["Trading disabled: too close to session open/close"],
                warnings=[]
            )
        return ValidationResult(passed=True, errors=[], warnings=[])
    
    validator = SignalValidator()
    validator.add_rule(session_timing_rule)
    
    return validator

def example_batch_validation():
    """Validate multiple signals efficiently."""
    validator = SignalValidator(
        max_position_size=100.0,
        allowed_symbols=['AAPL', 'MSFT', 'GOOGL']
    )
    
    signals = [
        TradingSignal('AAPL', 'BUY', 10, 175.0),
        TradingSignal('MSFT', 'SELL', 5, 330.0),
        TradingSignal('INVALID', 'BUY', 1000, 1.0),  # Will fail
    ]
    
    results = [(s, validator.validate(s)) for s in signals]
    valid = [s for s, r in results if r.can_execute]
    rejected = [(s, r.errors) for s, r in results if not r.can_execute]
    
    return valid, rejected

def example_integration_with_executor():
    """How to integrate with SmartOrderExecutor."""
    
    class ValidatedExecutor:
        def __init__(self, validator: SignalValidator, executor):
            self.validator = validator
            self.executor = executor
            self.stats = {'validated': 0, 'rejected': 0}
        
        async def submit(self, signal: TradingSignal):
            # Validate first
            result = self.validator.validate(signal)
            self.stats['validated'] += 1
            
            if not result.can_execute:
                self.stats['rejected'] += 1
                raise ValueError(f"Signal rejected: {result.errors}")
            
            if result.warnings:
                print(f"Warning (proceeding): {result.warnings}")
            
            # Pass to actual executor
            return await self.executor.execute(signal)


# === QUICK REFERENCE ===

"""
Common Custom Rules:

# Rule: Maximum daily loss limit
@dataclass
class DailyLimitRule:
    max_loss_pct: float
    daily_pnl: float
    starting_equity: float
    
    def __call__(self, signal: TradingSignal) -> ValidationResult:
        loss_pct = abs(self.daily_pnl) / self.starting_equity * 100
        if loss_pct >= self.max_loss_pct:
            return ValidationResult(
                passed=False,
                errors=[f"Daily loss limit hit: {loss_pct:.2f}%"],
                warnings=[]
            )
        return ValidationResult(passed=True, errors=[], warnings=[])

# Rule: Correlation check (don't add to crowded position)
class CorrelationRule:
    def __init__(self, positions: dict, max_correlated_exposure: float):
        self.positions = positions  # symbol -> size
        self.max_correlated = max_correlated_exposure
        self.correlation_matrix = {...}  # Load your correlations
    
    def __call__(self, signal: TradingSignal) -> ValidationResult:
        # Check if new position increases correlated exposure too much
        pass  # Implementation depends on your correlation data

Usage Pattern:

validator = SignalValidator(
    max_position_size=config['max_single_position'],
    max_order_value=config['max_order_value'],
    allowed_symbols=load_tradable_symbols(),
    reference_prices=cache.get_latest_prices()
)

# Add dynamic rules
validator.add_rule(DailyLimitRule(2.0, portfolio.daily_pnl, portfolio.equity))
validator.add_rule(CorrelationRule(portfolio.positions, 0.5))

# In your signal handler
result = validator.validate(incoming_signal)
if result.can_execute:
    await executor.submit(incoming_signal)
else:
    logger.error(f"Rejected: {result.errors}")
    alert_risk_team(incoming_signal, result.errors)
"""

if __name__ == "__main__":
    # Run examples
    print("=== Basic Usage ===")
    example_basic_usage()
    
    print("\n=== Batch Validation ===")
    valid, rejected = example_batch_validation()
    print(f"Valid: {len(valid)}, Rejected: {len(rejected)}")
    for sig, errs in rejected:
        print(f"  {sig.symbol}: {errs}")
