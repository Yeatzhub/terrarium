# Position Risk Validator

**Purpose:** Instant pre-trade risk check. Validates if a proposed trade fits within risk limits.

**Use case:** Run before executing any trade to avoid oversized positions or excessive risk.

## The Code

```python
#!/usr/bin/env python3
"""Position Risk Validator - Pre-trade risk check utility."""
from dataclasses import dataclass
from typing import Optional, List, Tuple
from decimal import Decimal, ROUND_DOWN
import json


@dataclass(frozen=True)
class RiskProfile:
    """Trader's risk parameters."""
    max_position_pct: Decimal = Decimal("0.25")      # Max 25% in single position
    max_portfolio_risk_pct: Decimal = Decimal("0.02") # Max 2% risk per trade
    max_leverage: Decimal = Decimal("3.0")           # Max 3x leverage
    min_risk_reward: Decimal = Decimal("1.5")        # Min 1.5:1 R/R
    max_concentration: int = 3                        # Max 3 positions per sector


@dataclass
class Position:
    """Proposed position to validate."""
    symbol: str
    entry: Decimal
    stop_loss: Decimal
    take_profit: Decimal
    position_size: Decimal
    portfolio_value: Decimal
    leverage: Decimal = Decimal("1.0")
    sector: str = "general"


@dataclass
class ValidationResult:
    """Result of risk validation."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    risk_amount: Decimal
    risk_pct: Decimal
    position_value: Decimal
    risk_reward: Decimal


class PositionRiskValidator:
    """Validates positions against risk profile before execution."""
    
    def __init__(self, profile: RiskProfile, current_positions: Optional[List[Position]] = None):
        self.profile = profile
        self.current_positions = current_positions or []
    
    def validate(self, position: Position) -> ValidationResult:
        """Validate a proposed position against risk rules."""
        errors = []
        warnings = []
        
        # Calculate position metrics
        position_value = position.position_size * position.entry * position.leverage
        risk_per_unit = abs(position.entry - position.stop_loss)
        risk_amount = position.position_size * risk_per_unit
        risk_pct = risk_amount / position.portfolio_value
        
        # Risk/Reward calculation
        reward_per_unit = abs(position.take_profit - position.entry)
        risk_reward = reward_per_unit / risk_per_unit if risk_per_unit > 0 else Decimal("0")
        
        # === HARD RULES (errors) ===
        
        # 1. Stop loss must be set and valid
        if position.stop_loss <= 0:
            errors.append("❌ Stop loss required")
        elif position.entry > position.stop_loss and position.take_profit < position.entry:
            # Long position with valid stop below entry
            pass
        elif position.entry < position.stop_loss and position.take_profit > position.entry:
            # Short position with valid stop above entry
            pass
        else:
            errors.append("❌ Invalid stop/target configuration")
        
        # 2. Portfolio risk limit
        if risk_pct > self.profile.max_portfolio_risk_pct:
            errors.append(
                f"❌ Risk {risk_pct:.2%} exceeds max {self.profile.max_portfolio_risk_pct:.2%}"
            )
        
        # 3. Position size limit
        position_pct = position_value / position.portfolio_value
        if position_pct > self.profile.max_position_pct:
            errors.append(
                f"❌ Position {position_pct:.1%} exceeds max {self.profile.max_position_pct:.1%}"
            )
        
        # 4. Leverage limit
        if position.leverage > self.profile.max_leverage:
            errors.append(
                f"❌ Leverage {position.leverage}x exceeds max {self.profile.max_leverage}x"
            )
        
        # 5. Minimum risk/reward
        if risk_reward < self.profile.min_risk_reward:
            errors.append(
                f"❌ R/R {risk_reward:.2f} below minimum {self.profile.min_risk_reward}"
            )
        
        # === WARNINGS (soft rules) ===
        
        # 6. Position concentration
        sector_positions = sum(
            1 for p in self.current_positions if p.sector == position.sector
        )
        if sector_positions >= self.profile.max_concentration:
            warnings.append(
                f"⚠️ Sector concentration: {sector_positions} in {position.sector}"
            )
        
        # 7. Stop distance check (suspiciously tight or wide)
        stop_pct = risk_per_unit / position.entry
        if stop_pct < Decimal("0.005"):  # < 0.5%
            warnings.append(f"⚠️ Tight stop: {stop_pct:.2%} - risk of noise")
        elif stop_pct > Decimal("0.10"):  # > 10%
            warnings.append(f"⚠️ Wide stop: {stop_pct:.1%} - large loss if hit")
        
        # 8. Risk/Reward sweet spot
        if risk_reward > Decimal("5.0"):
            warnings.append(f"⚠️ Aggressive target: {risk_reward:.1f}:1 R/R - check feasibility")
        
        # 9. Portfolio heat check (total at-risk capital)
        total_risk = sum(
            (p.position_size * abs(p.entry - p.stop_loss)) / p.portfolio_value
            for p in self.current_positions
        ) + risk_pct
        if total_risk > Decimal("0.06"):  # > 6% total portfolio risk
            warnings.append(f"⚠️ Portfolio heat: {total_risk:.1%} at risk")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            risk_amount=risk_amount,
            risk_pct=risk_pct,
            position_value=position_value,
            risk_reward=risk_reward
        )
    
    def format_result(self, result: ValidationResult, position: Position) -> str:
        """Format validation result for display."""
        lines = [
            f"\n{'='*50}",
            f"RISK CHECK: {position.symbol}",
            f"{'='*50}",
            f"Position Value: ${result.position_value:,.2f}",
            f"Risk Amount:    ${result.risk_amount:,.2f} ({result.risk_pct:.2%})",
            f"Risk/Reward:    {result.risk_reward:.2f}:1",
            f"{'-'*50}",
        ]
        
        if result.valid:
            lines.append("✅ VALID - Meets all risk criteria")
        else:
            lines.append("❌ REJECTED - Fix errors before executing")
        
        if result.errors:
            lines.append("\nERRORS:")
            for error in result.errors:
                lines.append(f"  {error}")
        
        if result.warnings:
            lines.append("\nWARNINGS:")
            for warning in result.warnings:
                lines.append(f"  {warning}")
        
        lines.append(f"{'='*50}\n")
        return "\n".join(lines)


# === QUICK ENTRY FUNCTIONS ===

def quick_check(
    symbol: str,
    entry: float,
    stop: float,
    target: float,
    size: float,
    portfolio: float,
    leverage: float = 1.0,
    sector: str = "general"
) -> bool:
    """One-liner risk check. Returns True if valid, False otherwise."""
    profile = RiskProfile()
    validator = PositionRiskValidator(profile)
    
    position = Position(
        symbol=symbol,
        entry=Decimal(str(entry)),
        stop_loss=Decimal(str(stop)),
        take_profit=Decimal(str(target)),
        position_size=Decimal(str(size)),
        portfolio_value=Decimal(str(portfolio)),
        leverage=Decimal(str(leverage)),
        sector=sector
    )
    
    result = validator.validate(position)
    print(validator.format_result(result, position))
    return result.valid


def calculate_size(
    entry: float,
    stop: float,
    portfolio: float,
    risk_pct: float = 0.01,
    max_position_pct: float = 0.25
) -> Tuple[float, str]:
    """Calculate max position size for given risk parameters.
    
    Returns: (size, reasoning)
    """
    entry_d = Decimal(str(entry))
    stop_d = Decimal(str(stop))
    portfolio_d = Decimal(str(portfolio))
    risk_pct_d = Decimal(str(risk_pct))
    max_pos_d = Decimal(str(max_position_pct))
    
    risk_per_unit = abs(entry_d - stop_d)
    risk_amount = portfolio_d * risk_pct_d
    
    if risk_per_unit == 0:
        return 0, "❌ Stop must differ from entry"
    
    # Size based on risk
    size_by_risk = risk_amount / risk_per_unit
    
    # Max size by position limit
    max_size = (portfolio_d * max_pos_d) / entry_d
    
    # Take the smaller
    size = min(size_by_risk, max_size)
    
    if size_by_risk > max_size:
        reason = f"Position limit caps size (risk would allow {float(size_by_risk):.4f})"
    else:
        reason = f"Risk-based sizing ({risk_pct:.1%} risk)"
    
    return float(size), reason


# === EXAMPLE USAGE ===

if __name__ == "__main__":
    print("\n🔍 POSITION RISK VALIDATOR - Examples\n")
    
    # Example 1: Valid long position
    print("Example 1: Good trade setup")
    quick_check(
        symbol="BTC-PERP",
        entry=50000,
        stop=48500,      # 3% stop
        target=54000,    # 8% target = 2.67 R/R
        size=0.1,
        portfolio=100000,
        leverage=2.0
    )
    
    # Example 2: Oversized position
    print("Example 2: Oversized position (rejected)")
    quick_check(
        symbol="ETH-PERP",
        entry=3000,
        stop=2800,
        target=3600,
        size=15,         # Too big for $100k portfolio
        portfolio=100000,
        leverage=1.0
    )
    
    # Example 3: Poor R/R
    print("Example 3: Poor risk/reward (rejected)")
    quick_check(
        symbol="SOL-PERP",
        entry=100,
        stop=95,         # $5 risk
        target=102,      # $2 reward = 0.4 R/R
        size=50,
        portfolio=100000
    )
    
    # Example 4: Calculate optimal size
    print("\n📐 SIZE CALCULATOR")
    size, reason = calculate_size(
        entry=50000,
        stop=48500,
        portfolio=100000,
        risk_pct=0.015   # 1.5% risk
    )
    print(f"  Entry: $50,000 | Stop: $48,500 | Risk: 1.5%")
    print(f"  Recommended size: {size:.4f} BTC")
    print(f"  Reason: {reason}\n")
