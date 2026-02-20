# Pre-Trade Checklist Validator

**Purpose:** Multi-layer validation before executing any trade  
**Critical Rule:** No trade bypasses the checklist

## The Code

```python
"""
Pre-Trade Checklist Validator
Prevent bad trades through systematic validation.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Callable
from datetime import datetime, time
from enum import Enum


class CheckStatus(Enum):
    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


@dataclass
class CheckResult:
    """Result of a single validation check."""
    name: str
    status: CheckStatus
    message: str
    details: Dict = None


@dataclass
class TradeIntent:
    """Trade about to be executed."""
    symbol: str
    direction: str  # long, short
    entry_price: float
    stop_price: float
    target_price: float
    size: float
    setup: str
    account_size: float
    current_positions: List[Dict]
    timestamp: datetime


class PreTradeValidator:
    """
    Multi-layer trade validation system.
    All checks must pass (at least no FAILs) before trading.
    """
    
    def __init__(self):
        self.rules: List[Tuple[str, Callable, CheckStatus]] = []
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Register default validation rules."""
        self.rules = [
            ("Risk Limit", self._check_risk_limit, CheckStatus.FAIL),
            ("Position Size", self._check_position_size, CheckStatus.FAIL),
            ("Risk-Reward", self._check_risk_reward, CheckStatus.FAIL),
            ("Daily Loss", self._check_daily_loss, CheckStatus.FAIL),
            ("Market Hours", self._check_market_hours, CheckStatus.FAIL),
            ("Portfolio Heat", self._check_portfolio_heat, CheckStatus.WARN),
            ("Correlation", self._check_correlation, CheckStatus.WARN),
            ("Max Positions", self._check_max_positions, CheckStatus.FAIL),
            ("Setup Validation", self._check_setup_defined, CheckStatus.WARN),
            ("Concentration", self._check_concentration, CheckStatus.WARN),
            ("Volatility", self._check_volatility, CheckStatus.WARN),
            ("Price Check", self._check_price_reasonable, CheckStatus.WARN),
        ]
    
    def validate(self, trade: TradeIntent, custom_rules: Optional[List] = None) -> List[CheckResult]:
        """
        Run all validation checks.
        
        Returns: List of CheckResults
        Trade is SAFE if no FAIL results
        """
        results = []
        
        for name, check_fn, severity in self.rules:
            try:
                passed, message, details = check_fn(trade)
                status = CheckStatus.PASS if passed else severity
                results.append(CheckResult(name, status, message, details))
            except Exception as e:
                # Check failed to run - assume FAIL
                results.append(CheckResult(
                    name, 
                    CheckStatus.FAIL, 
                    f"Check error: {str(e)}",
                    {}
                ))
        
        return results
    
    def can_trade(self, trade: TradeIntent) -> Tuple[bool, List[str]]:
        """
        Quick check if trade can proceed.
        
        Returns: (can_trade, list_of_blockers)
        """
        results = self.validate(trade)
        
        failures = [r for r in results if r.status == CheckStatus.FAIL]
        warnings = [r for r in results if r.status == CheckStatus.WARN]
        
        blockers = [f"{r.name}: {r.message}" for r in failures]
        
        return len(failures) == 0, blockers
    
    def print_report(self, trade: TradeIntent):
        """Print formatted validation report."""
        results = self.validate(trade)
        
        print(f"\n{'='*70}")
        print(f"PRE-TRADE CHECKLIST: {trade.symbol} {trade.direction.upper()}")
        print(f"{'='*70}")
        
        fails = [r for r in results if r.status == CheckStatus.FAIL]
        warns = [r for r in results if r.status == CheckStatus.WARN]
        passes = [r for r in results if r.status == CheckStatus.PASS]
        
        if fails:
            print(f"\n❌ FAILURES ({len(fails)}):")
            for r in fails:
                print(f"   {r.name}: {r.message}")
        
        if warns:
            print(f"\n⚠️  WARNINGS ({len(warns)}):")
            for r in warns:
                print(f"   {r.name}: {r.message}")
        
        if passes:
            print(f"\n✓ PASSED ({len(passes)}):")
            for r in passes[:3]:  # Show first 3
                print(f"   {r.name}")
            if len(passes) > 3:
                print(f"   ... and {len(passes)-3} more")
        
        print(f"\n{'='*70}")
        if fails:
            print("❌ TRADE BLOCKED - Fix failures before proceeding")
        elif warns:
            print("⚠️  PROCEED WITH CAUTION - Review warnings")
        else:
            print("✅ ALL CLEAR - Trade validated")
        print(f"{'='*70}\n")
    
    # === VALIDATION RULES ===
    
    def _check_risk_limit(self, t: TradeIntent) -> Tuple[bool, str, Dict]:
        """Max 2% risk per trade (ideal: 1%)."""
        risk_amount = abs(t.entry_price - t.stop_price) * t.size
        risk_pct = (risk_amount / t.account_size) * 100
        
        if risk_pct > 2:
            return False, f"Risk {risk_pct:.2f}% > maximum 2%", {"risk_pct": risk_pct}
        elif risk_pct > 1:
            return True, f"Risk {risk_pct:.2f}% (acceptable but high)", {"risk_pct": risk_pct}
        return True, f"Risk {risk_pct:.2f}%", {"risk_pct": risk_pct}
    
    def _check_position_size(self, t: TradeIntent) -> Tuple[bool, str, Dict]:
        """Max 20% of account in one position."""
        position_value = t.entry_price * t.size
        position_pct = (position_value / t.account_size) * 100
        
        if position_pct > 20:
            return False, f"Position {position_pct:.1f}% > maximum 20%", {"position_pct": position_pct}
        return True, f"Position {position_pct:.1f}%", {"position_pct": position_pct}
    
    def _check_risk_reward(self, t: TradeIntent) -> Tuple[bool, str, Dict]:
        """Minimum 1.5:1 risk/reward."""
        risk = abs(t.entry_price - t.stop_price)
        reward = abs(t.target_price - t.entry_price)
        
        if risk == 0:
            return False, "Invalid stop loss (same as entry)", {"rr": 0}
        
        rr = reward / risk
        
        if rr < 1.0:
            return False, f"R:R {rr:.1f}:1 < minimum 1:1 (unprofitable)", {"rr": rr}
        elif rr < 1.5:
            return True, f"R:R {rr:.1f}:1 (bare minimum)", {"rr": rr}
        return True, f"R:R {rr:.1f}:1", {"rr": rr}
    
    def _check_daily_loss(self, t: TradeIntent) -> Tuple[bool, str, Dict]:
        """Max 5% daily loss limit."""
        # Simplified: check if this trade would exceed 5% daily loss
        daily_loss = sum(p.get("pnl", 0) for p in t.current_positions if p.get("pnl", 0) < 0)
        daily_loss_pct = abs(daily_loss) / t.account_size * 100
        
        risk_amount = abs(t.entry_price - t.stop_price) * t.size
        risk_pct = risk_amount / t.account_size * 100
        
        total_potential = daily_loss_pct + risk_pct
        
        if total_potential > 5:
            return False, f"Would exceed 5% daily loss ({total_potential:.1f}%)", {"daily_loss_pct": daily_loss_pct}
        elif total_potential > 3:
            return True, f"Daily loss at {total_potential:.1f}% (high)", {"daily_loss_pct": daily_loss_pct}
        return True, f"Daily loss {total_potential:.1f}%", {"daily_loss_pct": daily_loss_pct}
    
    def _check_market_hours(self, t: TradeIntent) -> Tuple[bool, str, Dict]:
        """Check if market is open."""
        ts = t.timestamp
        
        # Assume US equity hours: 9:30 AM - 4:00 PM ET
        market_open = time(9, 30)
        market_close = time(16, 0)
        
        if ts.weekday() >= 5:  # Weekend
            return False, "Market closed (weekend)", {}
        
        if not (market_open <= ts.time() <= market_close):
            return False, f"Market closed ({ts.time()}). Hours: {market_open}-{market_close}", {}
        
        return True, "Market open", {}
    
    def _check_portfolio_heat(self, t: TradeIntent) -> Tuple[bool, str, Dict]:
        """Max 60% total exposure."""
        current_exposure = sum(p.get("size", 0) * p.get("entry_price", 0) for p in t.current_positions)
        current_heat = (current_exposure / t.account_size) * 100
        
        new_exposure = t.entry_price * t.size
        new_heat = ((current_exposure + new_exposure) / t.account_size) * 100
        
        if new_heat > 80:
            return False, f"Heat {new_heat:.0f}% > 80% (extreme)", {"heat": new_heat}
        elif new_heat > 60:
            return True, f"Heat {new_heat:.0f}% > 60% (high)", {"heat": new_heat}
        return True, f"Heat {new_heat:.0f}%", {"heat": new_heat}
    
    def _check_correlation(self, t: TradeIntent) -> Tuple[bool, str, Dict]:
        """Check correlation with existing positions."""
        # Simplified: check if same sector
        symbol_sectors = {
            "AAPL": "tech", "MSFT": "tech", "GOOGL": "tech", "AMZN": "tech", "NVDA": "tech",
            "JPM": "finance", "BAC": "finance", "GS": "finance",
            "XOM": "energy", "CVX": "energy",
            "PFE": "healthcare", "JNJ": "healthcare"
        }
        
        trade_sector = symbol_sectors.get(t.symbol, "unknown")
        same_sector = [p for p in t.current_positions 
                      if symbol_sectors.get(p.get("symbol"), "") == trade_sector]
        
        sector_exposure = sum(p.get("size", 0) * p.get("entry_price", 0) for p in same_sector)
        sector_pct = (sector_exposure / t.account_size) * 100
        
        if len(same_sector) >= 2:
            return True, f"{len(same_sector)} positions in {trade_sector} ({sector_pct:.0f}%)", {"sector": trade_sector}
        return True, "No correlation concern", {"sector": trade_sector}
    
    def _check_max_positions(self, t: TradeIntent) -> Tuple[bool, str, Dict]:
        """Max 10 open positions."""
        current = len(t.current_positions)
        if current >= 10:
            return False, f"Max 10 positions ({current} open)", {"count": current}
        return True, f"Positions: {current}/10", {"count": current}
    
    def _check_setup_defined(self, t: TradeIntent) -> Tuple[bool, str, Dict]:
        """Trade must have defined setup."""
        if not t.setup or t.setup == "":
            return False, "No setup defined", {}
        valid_setups = ["breakout", "pullback", "reversal", "trend", "range", "earnings"]
        if t.setup.lower() not in valid_setups:
            return True, f"Setup '{t.setup}' not in standard list", {"setup": t.setup}
        return True, f"Setup: {t.setup}", {"setup": t.setup}
    
    def _check_concentration(self, t: TradeIntent) -> Tuple[bool, str, Dict]:
        """Max 40% in single sector."""
        # Calculate existing + new position value
        position_value = t.entry_price * t.size
        total_value = sum(p.get("size", 0) * p.get("entry_price", 0) 
                         for p in t.current_positions) + position_value
        
        # Simple check: would this one position exceed 40%?
        if position_value / t.account_size > 0.40:
            return True, f"Position > 40% of account (concentrated)", {"concentration": "high"}
        return True, "Concentration OK", {}
    
    def _check_volatility(self, t: TradeIntent) -> Tuple[bool, str, Dict]:
        """Check stop distance for volatility."""
        risk_pct = abs(t.entry_price - t.stop_price) / t.entry_price * 100
        
        if risk_pct > 5:
            return True, f"Wide stop: {risk_pct:.1f}% of price (normal for volatile stocks)", {"stop_pct": risk_pct}
        elif risk_pct < 0.5:
            return True, f"Tight stop: {risk_pct:.1f}% (may be too tight)", {"stop_pct": risk_pct}
        return True, f"Stop distance: {risk_pct:.1f}%", {"stop_pct": risk_pct}
    
    def _check_price_reasonable(self, t: TradeIntent) -> Tuple[bool, str, Dict]:
        """Sanity check on price levels."""
        if t.entry_price <= 0:
            return False, "Invalid entry price", {}
        if t.stop_price <= 0:
            return False, "Invalid stop price", {}
        if t.target_price <= 0:
            return False, "Invalid target price", {}
        
        # Check if entry between stop and target
        if t.direction == "long":
            if not (t.stop_price < t.entry_price < t.target_price):
                return False, "Long entry not between stop and target", {}
        else:  # short
            if not (t.target_price < t.entry_price < t.stop_price):
                return False, "Short entry not between target and stop", {}
        
        return True, "Price levels valid", {}
    
    def add_custom_rule(self, name: str, check_fn: Callable, severity: CheckStatus):
        """Add custom validation rule."""
        self.rules.append((name, check_fn, severity))


# === Example Usage ===

if __name__ == "__main__":
    validator = PreTradeValidator()
    
    # Example 1: Valid trade
    print("="*70)
    print("EXAMPLE 1: Valid Trade")
    print("="*70)
    
    trade1 = TradeIntent(
        symbol="AAPL",
        direction="long",
        entry_price=150.0,
        stop_price=147.0,
        target_price=156.0,
        size=100,
        setup="breakout",
        account_size=100000,
        current_positions=[
            {"symbol": "MSFT", "size": 50, "entry_price": 300, "pnl": 500},
        ],
        timestamp=datetime(2024, 1, 15, 10, 30)
    )
    
    validator.print_report(trade1)
    can_trade, blockers = validator.can_trade(trade1)
    print(f"Can execute: {'YES' if can_trade else 'NO'}")
    
    # Example 2: Invalid trade
    print("="*70)
    print("\nEXAMPLE 2: Invalid Trade (Multiple Failures)")
    print("="*70)
    
    trade2 = TradeIntent(
        symbol="NVDA",
        direction="long",
        entry_price=500.0,
        stop_price=480.0,  # 4% stop
        target_price=505.0,  # 1% reward = 0.25 R:R
        size=500,  # $250k position
        setup="",  # No setup
        account_size=100000,
        current_positions=[
            {"symbol": "AAPL", "size": 200, "entry_price": 150, "pnl": -2000},
            {"symbol": "MSFT", "size": 200, "entry_price": 300, "pnl": -1500},
            {"symbol": "AMD", "size": 100, "entry_price": 100, "pnl": -800},
        ],
        timestamp=datetime(2024, 1, 15, 8, 0)  # Pre-market
    )
    
    validator.print_report(trade2)
    
    # Example 3: Warning but allowed
    print("="*70)
    print("\nEXAMPLE 3: Warning (High Heat but Passable)")
    print("="*70)
    
    trade3 = TradeIntent(
        symbol="JPM",
        direction="long",
        entry_price=150.0,
        stop_price=147.0,
        target_price=156.0,
        size=300,
        setup="pullback",
        account_size=100000,
        current_positions=[
            {"symbol": "GS", "size": 100, "entry_price": 350, "pnl": 200},
            {"symbol": "BAC", "size": 150, "entry_price": 35, "pnl": 100},
        ],
        timestamp=datetime(2024, 1, 15, 14, 0)
    )
    
    validator.print_report(trade3)


## Validation Checklist Summary

| Check | Fail If | Warn If |
|-------|---------|---------|
| **Risk Limit** | > 2% of account | > 1% of account |
| **Position Size** | > 20% of account | - |
| **Risk-Reward** | < 1:1 R:R | < 1.5:1 R:R |
| **Daily Loss** | Would exceed 5% daily | Approaching 5% |
| **Market Hours** | Closed/Pre/Post | - |
| **Portfolio Heat** | > 80% | > 60% |
| **Correlation** | - | 2+ in same sector |
| **Max Positions** | ≥ 10 open | - |
| **Setup** | Undefined | Non-standard setup |
| **Concentration** | - | > 40% single position |
| **Volatility** | - | Unusual stop width |
| **Price Check** | Invalid prices | - |

## Usage in Trading System

```python
validator = PreTradeValidator()

# Before executing any trade
intent = create_trade_intent(signal)
can_trade, blockers = validator.can_trade(intent)

if not can_trade:
    print(f"BLOCKED: {blockers}")
    return False

# If warnings exist, log but proceed
validate(intent).print_report(intent)
execute_trade(intent)
```

## Why This Matters

- **Prevents emotional trades** - Systematic validation overrides panic/FOMO
- **Enforces discipline** - Hard stops on risk limits
- **Catches errors** - Price typos, wrong directions, bad R:R
- **Documents decisions** - Every trade validated and logged

---

**Created by Ghost 👻 | Feb 19, 2026 | 13-min learning sprint**  
*Lesson: Never trade without validation. Automate discipline so emotion has no entry point.*
