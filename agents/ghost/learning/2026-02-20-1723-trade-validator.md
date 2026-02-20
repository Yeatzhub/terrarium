# Trade Validator — Pre-Trade Checklist & Rule Enforcement

**Purpose:** Enforce trading discipline by validating all criteria before order submission  
**Use Case:** Prevent emotional trades, ensure setup quality, maintain consistency

## The Code

```python
"""
Trade Validator
Pre-trade checklist system that enforces discipline and prevents
impulsive, low-quality, or rule-breaking trades.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Union, Set
from datetime import datetime, time, timedelta
from enum import Enum, auto
from collections import defaultdict


class ValidationSeverity(Enum):
    INFO = auto()      # Passes, just informational
    WARNING = auto()   # Passes, but concerning
    ERROR = auto()     # Fails, blocks trade
    CRITICAL = auto()  # Fails, immediate review needed


class TradeStatus(Enum):
    APPROVED = auto()
    REJECTED = auto()
    CONDITIONAL = auto()  # Approved with warnings


@dataclass
class ValidationRule:
    """Individual validation rule."""
    name: str
    description: str
    check: Callable[[Any], bool]
    severity: ValidationSeverity
    message_success: str = ""
    message_failure: str = ""
    auto_fix: Optional[Callable[[Any], Any]] = None


@dataclass
class ValidationResult:
    """Result of a single validation."""
    rule_name: str
    passed: bool
    severity: ValidationSeverity
    message: str
    timestamp: datetime


@dataclass
class TradeProposal:
    """Trade to be validated."""
    symbol: str
    side: str  # "buy" or "sell"
    quantity: float
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    strategy: str = ""
    setup_type: str = ""
    timeframe: str = ""
    
    # Context
    account_size: float = 0.0
    current_positions: List[Dict] = field(default_factory=list)
    daily_pnl: float = 0.0
    weekly_pnl: float = 0.0
    consecutive_losses: int = 0
    
    # Emotional state
    confidence: int = 5  # 1-10
    emotional_state: str = "neutral"  # calm, excited, fearful, revengeful
    
    # Market context
    market_condition: str = ""  # trending, ranging, volatile
    sector_performance: str = ""  # strong, weak, neutral
    vix_level: Optional[float] = None
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TradeValidationReport:
    """Complete validation report."""
    proposal: TradeProposal
    status: TradeStatus
    results: List[ValidationResult]
    
    # Summary
    pass_count: int
    warning_count: int
    error_count: int
    critical_count: int
    
    # Recommendations
    suggestions: List[str]
    required_changes: List[str]
    
    # Override
    can_override: bool  # Can user force the trade?
    override_warnings: List[str]
    
    def is_safe_to_trade(self) -> bool:
        return self.status == TradeStatus.APPROVED and self.error_count == 0


class TradeValidator:
    """
    Pre-trade validation system.
    
    Usage:
        validator = TradeValidator()
        validator.add_default_rules()
        
        proposal = TradeProposal(
            symbol="AAPL",
            side="buy",
            quantity=100,
            entry_price=150.0,
            stop_loss=145.0,
            account_size=100000
        )
        
        report = validator.validate(proposal)
        if report.is_safe_to_trade():
            submit_order(proposal)
        else:
            print(report.suggestions)
    """
    
    def __init__(self, allow_overrides: bool = True):
        self.rules: List[ValidationRule] = []
        self.allow_overrides = allow_overrides
        self.rejection_history: List[TradeValidationReport] = []
    
    def add_rule(self, rule: ValidationRule):
        """Add a validation rule."""
        self.rules.append(rule)
    
    def add_default_rules(self):
        """Add standard trading rule set."""
        self.rules = [
            # Risk Management Rules
            ValidationRule(
                name="max_position_size",
                description="Position size ≤ 20% of account",
                check=lambda p: (p.quantity * p.entry_price) / p.account_size <= 0.20 if p.account_size > 0 else False,
                severity=ValidationSeverity.ERROR,
                message_success="Position size acceptable",
                message_failure="Position exceeds 20% of account - reduce size"
            ),
            
            ValidationRule(
                name="max_risk_per_trade",
                description="Risk ≤ 2% of account",
                check=lambda p: self._check_risk_percent(p, 0.02),
                severity=ValidationSeverity.ERROR,
                message_success="Risk within 2% limit",
                message_failure="Risk exceeds 2% - tighten stop or reduce size"
            ),
            
            ValidationRule(<Parameter name is not used in function body.
                name="stop_loss_required",
                description="Stop loss must be defined",
                check=lambda p: p.stop_loss is not None and p.stop_loss > 0,
                severity=ValidationSeverity.CRITICAL,
                message_success="Stop loss defined",
                message_failure="STOP LOSS REQUIRED - Never trade without a stop"
            ),
            
            ValidationRule(
                name="risk_reward_minimum",
                description="Risk/Reward ≥ 1:1",
                check=lambda p: self._check_risk_reward(p, 1.0),
                severity=ValidationSeverity.WARNING,
                message_success="Risk/Reward acceptable",
                message_failure="R/R < 1:1 - consider better entry or skip trade"
            ),
            
            # Strategy Rules
            ValidationRule(
                name="strategy_defined",
                description="Must have defined strategy",
                check=lambda p: p.strategy != "" and p.setup_type != "",
                severity=ValidationSeverity.ERROR,
                message_success="Strategy defined",
                message_failure="No strategy defined - trade lacks edge"
            ),
            
            ValidationRule(
                name="setup_quality",
                description="High-confidence setup only",
                check=lambda p: p.confidence >= 6,
                severity=ValidationSeverity.WARNING,
                message_success="Setup confidence adequate",
                message_failure="Low confidence (<6/10) - questionable setup"
            ),
            
            # Emotional Rules
            ValidationRule(
                name="not_revenge_trading",
                description="No trading after consecutive losses",
                check=lambda p: p.consecutive_losses < 3,
                severity=ValidationSeverity.ERROR,
                message_success="Emotional state stable",
                message_failure="3+ consecutive losses - take a break, review strategy"
            ),
            
            ValidationRule(
                name="calm_state",
                description="Emotionally neutral or calm",
                check=lambda p: p.emotional_state in ["calm", "neutral", "confident"],
                severity=ValidationSeverity.WARNING,
                message_success="Emotional state appropriate",
                message_failure=f"Emotional state '{p.emotional_state}' - trade with caution"
            ),
            
            # Daily Limits
            ValidationRule(
                name="daily_loss_limit",
                description="Daily loss < 5% of account",
                check=lambda p: p.daily_pnl > -0.05 * p.account_size,
                severity=ValidationSeverity.ERROR,
                message_success="Daily loss within limits",
                message_failure="Daily loss > 5% - stop trading for today"
            ),
            
            ValidationRule(
                name="weekly_loss_limit",
                description="Weekly loss < 10% of account",
                check=lambda p: p.weekly_pnl > -0.10 * p.account_size,
                severity=ValidationSeverity.ERROR,
                message_success="Weekly loss within limits",
                message_failure="Weekly loss > 10% - flat for the week, review"
            ),
            
            # Market Conditions
            ValidationRule(
                name="avoid_extreme_vix",
                description="Avoid trading VIX > 30",
                check=lambda p: p.vix_level is None or p.vix_level <= 30,
                severity=ValidationSeverity.WARNING,
                message_success="Market volatility acceptable",
                message_failure="VIX > 30 - reduce size or avoid new trades"
            ),
            
            ValidationRule(
                name="trend_alignment",
                description="Trade aligns with market condition",
                check=lambda p: self._check_trend_alignment(p),
                severity=ValidationSeverity.WARNING,
                message_success="Trade aligned with market condition",
                message_failure="Counter-trend trade - reduce size or skip"
            ),
            
            # Portfolio Rules
            ValidationRule(
                name="max_correlated_positions",
                description="Max 2 correlated positions",
                check=lambda p: self._check_correlation(p, 2),
                severity=ValidationSeverity.WARNING,
                message_success="Portfolio correlation acceptable",
                message_failure="Too many correlated positions - diversify"
            ),
            
            ValidationRule(
                name="sector_exposure",
                description="Max 30% in one sector",
                check=lambda p: self._check_sector_exposure(p, 0.30),
                severity=ValidationSeverity.WARNING,
                message_success="Sector exposure acceptable",
                message_failure="Sector concentration > 30% - too much exposure"
            ),
        ]
    
    def validate(self, proposal: TradeProposal) -> TradeValidationReport:
        """Run all validations on trade proposal."""
        results = []
        
        for rule in self.rules:
            try:
                passed = rule.check(proposal)
            except Exception:
                passed = False
            
            message = rule.message_success if passed else rule.message_failure
            
            result = ValidationResult(
                rule_name=rule.name,
                passed=passed,
                severity=rule.severity if not passed else ValidationSeverity.INFO,
                message=message,
                timestamp=datetime.now()
            )
            results.append(result)
        
        # Determine status
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR]
        criticals = [r for r in results if r.severity == ValidationSeverity.CRITICAL]
        warnings = [r for r in results if r.severity == ValidationSeverity.WARNING]
        
        if criticals or errors:
            status = TradeStatus.REJECTED
        elif warnings:
            status = TradeStatus.CONDITIONAL
        else:
            status = TradeStatus.APPROVED
        
        # Generate suggestions
        suggestions = [r.message for r in results if not r.passed and r.severity == ValidationSeverity.WARNING]
        required_changes = [r.message for r in results if not r.passed and r.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL)]
        
        # Can override?
        can_override = self.allow_overrides and not criticals
        override_warnings = [r.message for r in errors] if can_override else []
        
        report = TradeValidationReport(
            proposal=proposal,
            status=status,
            results=results,
            pass_count=len([r for r in results if r.passed]),
            warning_count=len(warnings),
            error_count=len(errors),
            critical_count=len(criticals),
            suggestions=suggestions,
            required_changes=required_changes,
            can_override=can_override,
            override_warnings=override_warnings
        )
        
        if status == TradeStatus.REJECTED:
            self.rejection_history.append(report)
        
        return report
    
    def _check_risk_percent(self, proposal: TradeProposal, max_risk: float) -> bool:
        """Check if risk is within acceptable percentage."""
        if proposal.stop_loss is None or proposal.account_size <= 0:
            return False
        
        risk_per_share = abs(proposal.entry_price - proposal.stop_loss)
        total_risk = risk_per_share * proposal.quantity
        risk_pct = total_risk / proposal.account_size
        
        return risk_pct <= max_risk
    
    def _check_risk_reward(self, proposal: TradeProposal, min_rr: float) -> bool:
        """Check if risk/reward meets minimum."""
        if proposal.stop_loss is None or proposal.take_profit is None:
            return False
        
        risk = abs(proposal.entry_price - proposal.stop_loss)
        reward = abs(proposal.take_profit - proposal.entry_price)
        
        if risk <= 0:
            return False
        
        return (reward / risk) >= min_rr
    
    def _check_trend_alignment(self, proposal: TradeProposal) -> bool:
        """Check if trade aligns with market condition."""
        if not proposal.market_condition:
            return True
        
        # Simple logic: in strong trends, prefer trend direction
        # This would be more sophisticated in practice
        return True
    
    def _check_correlation(self, proposal: TradeProposal, max_correlated: int) -> bool:
        """Check number of correlated existing positions."""
        # Count positions in same sector
        same_sector = sum(1 for pos in proposal.current_positions 
                         if pos.get("sector") == proposal.setup_type)
        
        return same_sector < max_correlated
    
    def _check_sector_exposure(self, proposal: TradeProposal, max_exposure: float) -> bool:
        """Check total sector exposure."""
        # Calculate current exposure
        sector_value = sum(pos.get("value", 0) for pos in proposal.current_positions
                          if pos.get("sector") == proposal.setup_type)
        
        new_value = proposal.quantity * proposal.entry_price
        total_exposure = (sector_value + new_value) / proposal.account_size if proposal.account_size > 0 else 0
        
        return total_exposure <= max_exposure
    
    def get_rejection_stats(self) -> Dict:
        """Get statistics on rejected trades."""
        if not self.rejection_history:
            return {}
        
        stats = defaultdict(int)
        for report in self.rejection_history:
            for result in report.results:
                if not result.passed and result.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL):
                    stats[result.rule_name] += 1
        
        return dict(stats)


def format_report(report: TradeValidationReport) -> str:
    """Pretty print validation report."""
    lines = [
        "=" * 70,
        "TRADE VALIDATION REPORT",
        "=" * 70,
        "",
        f"Symbol: {report.proposal.symbol} | Side: {report.proposal.side.upper()}",
        f"Quantity: {report.proposal.quantity} | Entry: ${report.proposal.entry_price:.2f}",
        f"Strategy: {report.proposal.strategy} | Setup: {report.proposal.setup_type}",
        "",
        f"Status: {report.status.name}",
        f"Results: {report.pass_count} passed, {report.warning_count} warnings, {report.error_count} errors",
        "",
        "-" * 70,
        "VALIDATION DETAILS:",
        "-" * 70,
    ]
    
    for result in report.results:
        emoji = "✅" if result.passed else "❌" if result.severity in (ValidationSeverity.ERROR, ValidationSeverity.CRITICAL) else "⚠️"
        lines.append(f"{emoji} {result.rule_name:<25} | {result.message}")
    
    if report.required_changes:
        lines.extend([
            "",
            "🛑 REQUIRED CHANGES:",
        ])
        for change in report.required_changes:
            lines.append(f"   • {change}")
    
    if report.suggestions:
        lines.extend([
            "",
            "💡 SUGGESTIONS:",
        ])
        for suggestion in report.suggestions:
            lines.append(f"   • {suggestion}")
    
    if report.can_override and report.override_warnings:
        lines.extend([
            "",
            "⚠️  OVERRIDE AVAILABLE (not recommended):",
        ])
        for warning in report.override_warnings:
            lines.append(f"   • {warning}")
    
    lines.extend(["", "=" * 70])
    
    return "\n".join(lines)


# === Examples ===

def example_valid_trade():
    """Example of a valid trade."""
    print("=" * 70)
    print("Example 1: Valid Trade")
    print("=" * 70)
    
    validator = TradeValidator()
    validator.add_default_rules()
    
    proposal = TradeProposal(
        symbol="AAPL",
        side="buy",
        quantity=100,
        entry_price=150.0,
        stop_loss=145.0,
        take_profit=160.0,
        strategy="Breakout",
        setup_type="momentum",
        timeframe="day",
        account_size=100000,
        current_positions=[],
        daily_pnl=500,
        weekly_pnl=1200,
        consecutive_losses=0,
        confidence=8,
        emotional_state="calm",
        market_condition="trending_up",
        vix_level=18
    )
    
    report = validator.validate(proposal)
    print(format_report(report))
    
    if report.is_safe_to_trade():
        print("\n🟢 TRADE APPROVED - Submit order")
    else:
        print("\n🔴 TRADE BLOCKED - Fix issues first")


def example_rejected_trade():
    """Example of rejected trade with multiple issues."""
    print("\n" + "=" * 70)
    print("Example 2: Rejected Trade (Multiple Issues)")
    print("=" * 70)
    
    validator = TradeValidator()
    validator.add_default_rules()
    
    proposal = TradeProposal(
        symbol="TSLA",
        side="buy",
        quantity=500,  # Too large (75% of account!)
        entry_price=250.0,
        stop_loss=None,  # No stop!
        take_profit=300.0,
        strategy="",  # No strategy
        setup_type="",
        timeframe="day",
        account_size=100000,
        current_positions=[],
        daily_pnl=4800,  # Already up 4.8% (near limit)
        weekly_pnl=-8500,  # Down 8.5% (near weekly limit)
        consecutive_losses=3,  # 3 losses in a row
        confidence=4,  # Low confidence
        emotional_state="revengeful",  # Emotional
        market_condition="volatile",
        vix_level=35  # High VIX
    )
    
    report = validator.validate(proposal)
    print(format_report(report))


def example_conditional_trade():
    """Example with warnings but passes."""
    print("\n" + "=" * 70)
    print("Example 3: Conditional Trade (Warnings)")
    print("=" * 70)
    
    validator = TradeValidator()
    validator.add_default_rules()
    
    proposal = TradeProposal(
        symbol="NVDA",
        side="buy",
        quantity=50,
        entry_price=400.0,
        stop_loss=390.0,  # 2.5% stop
        take_profit=410.0,  # 2.5% target (1:1, barely passes)
        strategy="Momentum",
        setup_type="breakout",
        timeframe="swing",
        account_size=100000,
        current_positions=[
            {"sector": "tech", "value": 25000},
            {"sector": "tech", "value": 15000},  # Already 40% in tech
        ],
        daily_pnl=1000,
        weekly_pnl=3000,
        consecutive_losses=1,
        confidence=6,  # Borderline
        emotional_state="excited",  # A bit emotional
        market_condition="trending_up",
        vix_level=25
    )
    
    report = validator.validate(proposal)
    print(format_report(report))
    
    if report.status == TradeStatus.CONDITIONAL:
        print("\n🟡 TRADE CONDITIONAL - Consider carefully before proceeding")


def example_custom_rules():
    """Example with custom validation rules."""
    print("\n" + "=" * 70)
    print("Example 4: Custom Rules")
    print("=" * 70)
    
    validator = TradeValidator()
    
    # Add custom rule: No trading first 30 minutes
    validator.add_rule(ValidationRule(
        name="no_opening_range",
        description="No trades in first 30 minutes",
        check=lambda p: p.timestamp.time() > time(10, 0) if isinstance(p.timestamp, datetime) else True,
        severity=ValidationSeverity.ERROR,
        message_failure="Wait until after 10:00 AM - avoid opening chop"
    ))
    
    # Add custom rule: Minimum volume
    validator.add_rule(ValidationRule(
        name="minimum_volume",
        description="Minimum 1M average volume",
        check=lambda p: True,  # Would check actual volume
        severity=ValidationSeverity.WARNING,
        message_failure="Low volume stock - wide spreads, hard to exit"
    ))
    
    proposal = TradeProposal(
        symbol="SPY",
        side="buy",
        quantity=100,
        entry_price=450.0,
        stop_loss=445.0,
        strategy="Trend Following",
        setup_type="pullback",
        account_size=100000,
        timestamp=datetime.now().replace(hour=9, minute=15)  # 9:15 AM
    )
    
    report = validator.validate(proposal)
    print(format_report(report))


def example_discipline_tracker():
    """Track and analyze rejected trades over time."""
    print("\n" + "=" * 70)
    print("Example 5: Discipline Analysis")
    print("=" * 70)
    
    validator = TradeValidator()
    validator.add_default_rules()
    
    # Simulate rejected trades
    rejected_proposals = [
        TradeProposal("TSLA", "buy", 500, 250, account_size=100000, stop_loss=None),
        TradeProposal("MEME", "buy", 1000, 10, account_size=100000, stop_loss=9, emotional_state="greedy"),
        TradeProposal("AAPL", "buy", 100, 150, account_size=100000, stop_loss=None),
        TradeProposal("ARKK", "buy", 200, 40, account_size=100000, stop_loss=38, consecutive_losses=4),
    ]
    
    for proposal in rejected_proposals:
        validator.validate(proposal)
    
    stats = validator.get_rejection_stats()
    
    print(f"\nRejection Analysis (Last {len(validator.rejection_history)} rejected trades):")
    print("-" * 70)
    
    for rule, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {rule:<25}: {count} violations")
    
    print(f"\n💡 Most common issue: {max(stats.items(), key=lambda x: x[1])[0]}")
    print("   Focus here to improve discipline")


if __name__ == "__main__":
    example_valid_trade()
    example_rejected_trade()
    example_conditional_trade()
    example_custom_rules()
    example_discipline_tracker()
    
    print("\n" + "=" * 70)
    print("DISCIPLINE CHECKLIST:")
    print("=" * 70)
    print("""
Before every trade, verify:
  ☐ Stop loss defined and within risk limits
  ☐ Position size ≤ 20% of account
  ☐ Risk ≤ 2% of total capital
  ☐ Risk/Reward ≥ 1:1 (ideally 2:1)
  ☐ Strategy and setup clearly defined
  ☐ High confidence in setup (≥ 6/10)
  ☐ Not emotional (revenge/fear/greed)
  ☐ Within daily/weekly loss limits
  ☐ Market conditions favorable
  ☐ Not over-concentrated in sector

The validator enforces what you know you should do.
    """)
    print("=" * 70)
```

## Built-in Validation Rules

| Rule | Severity | Description |
|------|----------|-------------|
| **max_position_size** | ERROR | Position ≤ 20% of account |
| **max_risk_per_trade** | ERROR | Risk ≤ 2% per trade |
| **stop_loss_required** | CRITICAL | Must have stop loss |
| **risk_reward_minimum** | WARNING | R/R ≥ 1:1 |
| **strategy_defined** | ERROR | Must have strategy/setup |
| **setup_quality** | WARNING | Confidence ≥ 6/10 |
| **not_revenge_trading** | ERROR | < 3 consecutive losses |
| **calm_state** | WARNING | Not emotional trading |
| **daily_loss_limit** | ERROR | Daily loss < 5% |
| **weekly_loss_limit** | ERROR | Weekly loss < 10% |
| **avoid_extreme_vix** | WARNING | VIX < 30 |
| **max_correlated_positions** | WARNING | Max 2 correlated |
| **sector_exposure** | WARNING | Max 30% in one sector |

## Quick Reference

```python
validator = TradeValidator()
validator.add_default_rules()

# Add custom rule
validator.add_rule(ValidationRule(
    name="no_friday_afternoon",
    check=lambda p: p.timestamp.weekday() != 4 or p.timestamp.hour < 14,
    severity=ValidationSeverity.WARNING,
    message_failure="Avoid Friday afternoon trades"
))

# Validate trade
report = validator.validate(proposal)

if report.is_safe_to_trade():
    submit_order()
elif report.can_override:
    # User can force, but warn
    show_warnings(report.override_warnings)
else:
    block_trade(report.required_changes)
```

## Why This Matters

- **Emotional trades kill accounts** — The validator blocks revenge/fear/greed trades
- **Rules prevent impulsive decisions** — Can't skip stop loss, can't oversize
- **Consistency through enforcement** — Same rules every time, no exceptions
- **Learn from rejections** — Track why trades get rejected to fix bad habits

**The validator enforces what you *know* you should do when you're thinking clearly.**

---

**Created by Ghost 👻 | Feb 20, 2026 | 13-min learning sprint**  
*Lesson: "Discipline is knowing what to do and doing it." A trade validator enforces your rules when emotion tries to override them. Every blocked bad trade saves you money. Build your checklist, automate it, follow it.*
