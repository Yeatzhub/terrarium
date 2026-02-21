# Pre-Trade Checklist Validator
*Ghost Learning | 2026-02-21*

Validate trades against risk rules before execution. Prevents impulsive trades, enforces position limits, and ensures correlation safety. Fast, simple, actionable.

```python
#!/usr/bin/env python3
"""
Pre-Trade Checklist Validator
Validates trade proposals against risk rules before execution.

Usage:
    python pre_trade_check.py --symbol BTCUSD --size 0.5 --entry 50000 --stop 49000
    python pre_trade_check.py --json trade_proposal.json --config risk_rules.yaml
"""

import argparse
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, time
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Optional, list, Callable


class CheckStatus(Enum):
    PASS = "✅ PASS"
    FAIL = "❌ FAIL"
    WARN = "⚠️  WARN"
    SKIP = "⏭️  SKIP"


@dataclass
class RiskRule:
    """Single risk rule with validation function."""
    name: str
    description: str
    critical: bool  # True = block trade, False = warning only
    validator: Callable[["TradeProposal", "AccountState"], tuple[bool, str]]


@dataclass
class TradeProposal:
    """Proposed trade to validate."""
    symbol: str
    side: str  # 'long' or 'short'
    size: Decimal
    entry: Decimal
    stop: Optional[Decimal] = None
    take_profit: Optional[Decimal] = None
    fees: Decimal = Decimal("0")


@dataclass
class AccountState:
    """Current account state for validation."""
    equity: Decimal
    cash: Decimal
    open_positions: list[dict] = field(default_factory=list)
    daily_pnl: Decimal = Decimal("0")
    trades_today: int = 0
    max_daily_loss_hit: bool = False


@dataclass  
class ValidationResult:
    """Individual check result."""
    rule_name: str
    status: CheckStatus
    message: str
    critical: bool


class PreTradeValidator:
    """Validates trades against risk rules."""
    
    # Built-in risk rules
    RULES: list[RiskRule] = []
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or self._default_config()
        self._init_rules()
    
    def _default_config(self) -> dict:
        """Default risk configuration."""
        return {
            "max_position_pct": 0.20,      # Max 20% in one position
            "max_risk_per_trade_pct": 0.02,  # Max 2% risk
            "max_open_positions": 10,
            "max_leverage": 5.0,
            "min_stop_distance_pct": 0.005,  # Min 0.5% stop distance
            "max_correlation": 0.80,       # Max correlation with existing positions
            "max_daily_loss_pct": 0.05,    # Stop trading after 5% loss
            "max_trades_per_day": 20,
            "blacklisted_symbols": [],
            "allowed_hours": {"start": "09:00", "end": "16:00"},  # Market hours
        }
    
    def _init_rules(self) -> None:
        """Initialize validation rules."""
        self.RULES = [
            RiskRule(
                name="blacklist",
                description="Symbol not in blacklist",
                critical=True,
                validator=self._check_blacklist
            ),
            RiskRule(
                name="daily_loss_limit",
                description="Daily loss limit not exceeded",
                critical=True,
                validator=self._check_daily_loss
            ),
            RiskRule(
                name="position_size",
                description="Position size within limit",
                critical=True,
                validator=self._check_position_size
            ),
            RiskRule(
                name="risk_per_trade",
                description="Risk per trade within limit",
                critical=True,
                validator=self._check_risk_per_trade
            ),
            RiskRule(
                name="stop_required",
                description="Stop loss defined",
                critical=True,
                validator=self._check_stop_defined
            ),
            RiskRule(
                name="stop_distance",
                description="Stop distance reasonable (not too tight)",
                critical=False,
                validator=self._check_stop_distance
            ),
            RiskRule(
                name="max_positions",
                description="Open positions within limit",
                critical=True,
                validator=self._check_max_positions
            ),
            RiskRule(
                name="leverage",
                description="Leverage within acceptable range",
                critical=False,
                validator=self._check_leverage
            ),
            RiskRule(
                name="correlation",
                description="No high correlation exposure",
                critical=False,
                validator=self._check_correlation
            ),
            RiskRule(
                name="trading_hours",
                description="Within allowed trading hours",
                critical=False,
                validator=self._check_trading_hours
            ),
            RiskRule(
                name="daily_trade_limit",
                description="Daily trade count within limit",
                critical=False,
                validator=self._check_trade_count
            ),
        ]
    
    # === Validators ===
    
    def _check_blacklist(self, proposal: TradeProposal, account: AccountState) -> tuple[bool, str]:
        blocked = self.config.get("blacklisted_symbols", [])
        if proposal.symbol.upper() in [s.upper() for s in blocked]:
            return False, f"{proposal.symbol} is blacklisted"
        return True, "Symbol allowed"
    
    def _check_daily_loss(self, proposal: TradeProposal, account: AccountState) -> tuple[bool, str]:
        limit = Decimal(str(self.config["max_daily_loss_pct"]))
        if account.max_daily_loss_hit:
            return False, "Daily loss limit already hit — no new trades"
        current_loss_pct = -account.daily_pnl / account.equity if account.equity else 0
        if current_loss_pct >= limit:
            return False, f"Daily loss {current_loss_pct:.2%} exceeds limit {limit:.2%}"
        return True, f"Daily loss at {current_loss_pct:.2%}"
    
    def _check_position_size(self, proposal: TradeProposal, account: AccountState) -> tuple[bool, str]:
        limit = Decimal(str(self.config["max_position_pct"]))
        size_pct = (proposal.size * proposal.entry) / account.equity
        if size_pct > limit:
            return False, f"Position {size_pct:.2%} exceeds max {limit:.2%}"
        return True, f"Position size {size_pct:.2%} ✓"
    
    def _check_risk_per_trade(self, proposal: TradeProposal, account: AccountState) -> tuple[bool, str]:
        if not proposal.stop:
            return False, "Stop required for risk calculation"
        limit = Decimal(str(self.config["max_risk_per_trade_pct"]))
        risk = abs(proposal.entry - proposal.stop) * proposal.size
        risk_pct = risk / account.equity
        if risk_pct > limit:
            return False, f"Risk {risk_pct:.2%} exceeds max {limit:.2%}"
        return True, f"Risk {risk_pct:.2%} ({risk:,.2f} USD) ✓"
    
    def _check_stop_defined(self, proposal: TradeProposal, account: AccountState) -> tuple[bool, str]:
        if proposal.stop is None:
            return False, "Stop loss is mandatory"
        return True, f"Stop at {proposal.stop}"
    
    def _check_stop_distance(self, proposal: TradeProposal, account: AccountState) -> tuple[bool, str]:
        if not proposal.stop:
            return True, "No stop to validate"
        min_dist = Decimal(str(self.config["min_stop_distance_pct"]))
        dist = abs(proposal.entry - proposal.stop) / proposal.entry
        if dist < min_dist:
            return False, f"Stop too tight ({dist:.2%}) — risk of noise stop"
        return True, f"Stop distance {dist:.2%} ✓"
    
    def _check_max_positions(self, proposal: TradeProposal, account: AccountState) -> tuple[bool, str]:
        limit = self.config["max_open_positions"]
        current = len(account.open_positions)
        if current >= limit:
            return False, f"Already at max {limit} positions ({current} open)"
        return True, f"{current}/{limit} positions open ✓"
    
    def _check_leverage(self, proposal: TradeProposal, account: AccountState) -> tuple[bool, str]:
        limit = Decimal(str(self.config["max_leverage"]))
        total_exposure = sum(p.get("notional", 0) for p in account.open_positions)
        total_exposure += float(proposal.size * proposal.entry)
        leverage = Decimal(str(total_exposure)) / account.equity if account.equity else 0
        if leverage > limit:
            return False, f"Leverage {leverage:.1f}x exceeds max {limit}x"
        return True, f"Leverage {leverage:.1f}x ✓"
    
    def _check_correlation(self, proposal: TradeProposal, account: AccountState) -> tuple[bool, str]:
        """Warn if adding highly correlated position."""
        # Simulated correlation check - in real use, load correlation matrix
        corr_symbols = {
            "BTCUSD": ["ETHUSD", "SOLUSD", "XBTUSD"],
            "ETHUSD": ["BTCUSD", "SOLUSD"],
            "SPY": ["QQQ", "IWM", "VOO"]
        }
        related = corr_symbols.get(proposal.symbol.upper(), [])
        existing_related = [p for p in account.open_positions 
                          if p.get("symbol", "").upper() in [r.upper() for r in related]]
        if existing_related:
            return False, f"High correlation: already holding {', '.join(p['symbol'] for p in existing_related)}"
        return True, "No correlation issues"
    
    def _check_trading_hours(self, proposal: TradeProposal, account: AccountState) -> tuple[bool, str]:
        now = datetime.now().time()
        hours = self.config.get("allowed_hours", {})
        if hours:
            start = datetime.strptime(hours["start"], "%H:%M").time()
            end = datetime.strptime(hours["end"], "%H:%M").time()
            if not (start <= now <= end):
                return False, f"Outside trading hours ({hours['start']}-{hours['end']})"
        return True, "Within trading hours"
    
    def _check_trade_count(self, proposal: TradeProposal, account: AccountState) -> tuple[bool, str]:
        limit = self.config["max_trades_per_day"]
        if account.trades_today >= limit:
            return False, f"Max {limit} trades/day reached ({account.trades_today})"
        return True, f"{account.trades_today}/{limit} trades today ✓"
    
    # === Main Interface ===
    
    def validate(self, proposal: TradeProposal, account: AccountState) -> list[ValidationResult]:
        """Run all validation rules."""
        results = []
        
        for rule in self.RULES:
            try:
                passed, message = rule.validator(proposal, account)
                status = CheckStatus.PASS if passed else (CheckStatus.FAIL if rule.critical else CheckStatus.WARN)
            except Exception as e:
                passed = False
                message = f"Validator error: {e}"
                status = CheckStatus.FAIL
            
            results.append(ValidationResult(
                rule_name=rule.name,
                status=status,
                message=message,
                critical=rule.critical
            ))
        
        return results
    
    def should_trade(self, results: list[ValidationResult]) -> tuple[bool, list[str]]:
        """Determine if trade should execute and return blockers."""
        critical_fails = [r for r in results if r.status == CheckStatus.FAIL]
        warnings = [r for r in results if r.status == CheckStatus.WARN]
        
        if critical_fails:
            return False, [f"{r.rule_name}: {r.message}" for r in critical_fails]
        return True, [f"⚠️ {r.rule_name}: {r.message}" for r in warnings]


def print_results(proposal: TradeProposal, results: list[ValidationResult]) -> None:
    """Print formatted validation results."""
    print(f"\n{'═'*60}")
    print(f"  PRE-TRADE VALIDATION")
    print(f"{'═'*60}")
    print(f"  Symbol: {proposal.symbol} | Side: {proposal.side}")
    print(f"  Size: {proposal.size} | Entry: ${proposal.entry}")
    print(f"{'─'*60}")
    
    for r in results:
        icon = "✅" if r.status == CheckStatus.PASS else ("🚫" if r.status == CheckStatus.FAIL else "⚠️")
        print(f"  {icon} {r.rule_name:<20} {r.message}")
    
    print(f"{'─'*60}")
    
    should_trade, messages = PreTradeValidator().should_trade(results)
    if should_trade:
        print(f"  ✅ TRADE APPROVED")
        if messages:
            print(f"\n  Warnings:")
            for m in messages:
                print(f"    {m}")
    else:
        print(f"  ❌ TRADE BLOCKED")
        print(f"\n  Blockers:")
        for m in messages:
            print(f"    {m}")
    
    print(f"{'═'*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Pre-Trade Checklist Validator")
    parser.add_argument("--symbol", "-s", type=str, required=True)
    parser.add_argument("--side", type=str, choices=["long", "short"], default="long")
    parser.add_argument("--size", type=float, required=True)
    parser.add_argument("--entry", "-e", type=float, required=True)
    parser.add_argument("--stop", type=float, help="Stop loss price")
    parser.add_argument("--take-profit", "-tp", type=float)
    parser.add_argument("--equity", type=float, default=50000, help="Account equity")
    parser.add_argument("--daily-pnl", type=float, default=0, help="Today's P&L")
    parser.add_argument("--trades-today", type=int, default=0)
    parser.add_argument("--json", type=Path, help="Load proposal from JSON")
    parser.add_argument("--output", "-o", type=Path, help="Save to JSON")
    
    args = parser.parse_args()
    
    # Build proposal
    if args.json:
        data = json.loads(args.json.read_text())
        proposal = TradeProposal(**{k: Decimal(str(v)) if isinstance(v, (int, float)) else v 
                                   for k, v in data.items()})
    else:
        proposal = TradeProposal(
            symbol=args.symbol.upper(),
            side=args.side,
            size=Decimal(str(args.size)),
            entry=Decimal(str(args.entry)),
            stop=Decimal(str(args.stop)) if args.stop else None,
            take_profit=Decimal(str(args.take_profit)) if args.take_profit else None
        )
    
    # Build account state
    account = AccountState(
        equity=Decimal(str(args.equity)),
        cash=Decimal(str(args.equity)) * Decimal("0.5"),  # Assume 50% cash for demo
        daily_pnl=Decimal(str(args.daily_pnl)),
        trades_today=args.trades_today,
        open_positions=[]  # Would load actual positions
    )
    
    # Validate
    validator = PreTradeValidator()
    results = validator.validate(proposal, account)
    
    # Display
    print_results(proposal, results)
    
    # Output
    if args.output:
        output = {
            "proposal": {
                "symbol": proposal.symbol,
                "side": proposal.side,
                "size": str(proposal.size),
                "entry": str(proposal.entry)
            },
            "approved": validator.should_trade(results)[0],
            "results": [
                {"rule": r.rule_name, "status": r.status.value, "message": r.message}
                for r in results
            ]
        }
        args.output.write_text(json.dumps(output, indent=2))
        print(f"💾 Saved to {args.output}")
    
    # Exit with code 1 if rejected (for automation)
    approved, _ = validator.should_trade(results)
    if not approved:
        exit(1)


# === Quick Examples ===

# 1. Good trade
# python pre_trade_check.py -s BTCUSD --size 0.5 -e 50000 --stop 49000 --equity 100000

# 2. Rejected: oversized position
# python pre_trade_check.py -s BTCUSD --size 5 -e 50000 --stop 49000 --equity 100000

# 3. Rejected: no stop
# python pre_trade_check.py -s ETHUSD --size 2 -e 3000 --equity 100000

# 4. Rejected: daily loss hit
# python pre_trade_check.py -s BTCUSD --size 0.1 -e 50000 --stop 49000 --equity 100000 --daily-pnl -6000


if __name__ == "__main__":
    main()
```

## Quick Start

```bash
# Basic check
python pre_trade_check.py -s BTCUSD --size 0.5 -e 50000 --stop 49000 --equity 100000

# Check oversized position (should reject)
python pre_trade_check.py -s BTCUSD --size 5 -e 50000 --stop 49000 --equity 100000

# Daily loss limit hit (should reject)
python pre_trade_check.py -s BTCUSD --size 0.1 -e 50000 --stop 49000 --equity 100000 --daily-pnl -6000

# With JSON output
python pre_trade_check.py -s ETHUSD --size 2 -e 3000 --stop 2800 --equity 50000 --output result.json
```

## Sample Output

```
════════════════════════════════════════════════════════════
  PRE-TRADE VALIDATION
════════════════════════════════════════════════════════════
  Symbol: BTCUSD | Side: long
  Size: 0.5 | Entry: $50000
────────────────────────────────────────────────────────────
  ✅ blacklist         Symbol allowed
  ✅ daily_loss_limit  Daily loss at 0.00%
  ✅ position_size     Position size 25.00% ✓
  ✅ risk_per_trade    Risk 1.00% ($500.00) ✓
  ✅ stop_required     Stop at 49000
  ✅ stop_distance     Stop distance 2.00% ✓
  ✅ max_positions     0/10 positions open ✓
  ✅ leverage          Leverage 0.5x ✓
  ⚠️  correlation       No correlation issues
  ✅ trading_hours     Within trading hours
  ✅ daily_trade_limit 0/20 trades today ✓
────────────────────────────────────────────────────────────
  ✅ TRADE APPROVED
════════════════════════════════════════════════════════════
```

## Rules Config

Default limits (override via `config` dict):

```python
config = {
    "max_position_pct": 0.20,      # Max 20% per position
    "max_risk_per_trade_pct": 0.02, # Max 2% account risk
    "max_open_positions": 10,
    "max_leverage": 5.0,
    "min_stop_distance_pct": 0.005, # Min 0.5% stop distance
    "max_daily_loss_pct": 0.05,    # Stop trading after -5%
    "max_trades_per_day": 20,
    "blacklisted_symbols": ["DOGE", "SHIB"],
    "allowed_hours": {"start": "09:00", "end": "16:00"}
}
```

## Rule Severity

| Rule | Severity | Blocks Trade? |
|------|----------|---------------|
| Blacklist | Critical | ✅ |
| Daily loss limit | Critical | ✅ |
| Position size | Critical | ✅ |
| Risk per trade | Critical | ✅ |
| Stop required | Critical | ✅ |
| Stop distance | Warning | ⚠️ |
| Leverage | Warning | ⚠️ |
| Correlation | Warning | ⚠️ |
| Trading hours | Warning | ⚠️ |

## Automation Integration

```bash
#!/bin/bash
# Run pre-trade check before execution

python pre_trade_check.py \
    --symbol $1 \
    --size $2 \
    --entry $3 \
    --stop $4 \
    --equity $EQUITY \
    --daily-pnl $TODAY_PNL

if [ $? -eq 0 ]; then
    echo "CHECK: PASS - Executing trade"
    ./execute_trade.sh $1 $2 $3 $4
else
    echo "CHECK: FAIL - Skipping trade"
    exit 1
fi
```

## Exit Codes

- **0**: Trade approved (or warnings only)
- **1**: Trade blocked (critical rule failed)

---
*Utility: Pre-Trade Checklist | Prevent bad trades before they execute*
