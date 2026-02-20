# Position Sizing Calculator — Multi-Method

**Purpose:** Calculate optimal position size using multiple risk management methods  
**Use Case:** Never risk too much on a single trade, maximize growth while preserving capital

## The Code

```python
"""
Position Sizing Calculator
Multiple methods: fixed fractional, fixed ratio, Kelly, optimal f, risk parity.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple
from enum import Enum, auto
import math


class SizingMethod(Enum):
    FIXED_FRACTIONAL = auto()    # Risk fixed % of account per trade
    FIXED_RATIO = auto()         # Add contract after N profits
    KELLY = auto()               # Maximize log utility (aggressive)
    HALF_KELLY = auto()          # Conservative Kelly
    OPTIMAL_F = auto()           # Ralph Vince's optimal f
    RISK_PARITY = auto()         # Equal risk contribution
    VOLATILITY = auto()          # Risk-adjusted for volatility


@dataclass
class TradeSetup:
    """Inputs for position sizing calculation."""
    entry_price: float
    stop_loss: float
    take_profit: Optional[float] = None
    win_probability: Optional[float] = None  # For Kelly
    avg_win: Optional[float] = None          # Average winning trade $
    avg_loss: Optional[float] = None         # Average losing trade $
    volatility: Optional[float] = None     # ATR or std dev
    correlation: Optional[float] = None      # Correlation to portfolio


@dataclass
class SizingResult:
    """Position sizing recommendation."""
    method: SizingMethod
    shares: int
    position_value: float
    risk_amount: float
    risk_pct: float
    leverage: float
    max_loss: float
    confidence: str  # "conservative", "optimal", "aggressive"
    reason: str


class PositionSizingCalculator:
    """
    Calculate position size using multiple risk management methods.
    
    Usage:
        calc = PositionSizingCalculator(
            account_size=100000,
            max_risk_pct=2.0,
            method=SizingMethod.FIXED_FRACTIONAL
        )
        result = calc.calculate(
            entry=150.00,
            stop=145.00,
            setup=TradeSetup(entry_price=150, stop_loss=145)
        )
    """
    
    def __init__(
        self,
        account_size: float,
        max_risk_pct: float = 2.0,
        method: SizingMethod = SizingMethod.FIXED_FRACTIONAL,
        max_position_pct: float = 20.0,
        kelly_fraction: float = 0.5,
        min_position_value: float = 1000.0,
        allow_fractional: bool = False
    ):
        self.account_size = account_size
        self.base_risk_pct = max_risk_pct
        self.method = method
        self.max_position_pct = max_position_pct
        self.kelly_fraction = kelly_fraction
        self.min_position = min_position_value
        self.allow_fractional = allow_fractional
        
        # Strategy-specific state
        self.fixed_ratio_wins: int = 0
        self.fixed_ratio_units: int = 1
        self.fixed_ratio_delta: float = 0.0
        self.trade_history: List[float] = []
    
    def calculate(
        self,
        entry: float,
        stop: float,
        setup: Optional[TradeSetup] = None
    ) -> SizingResult:
        """Calculate position size for trade."""
        setup = setup or TradeSetup(entry_price=entry, stop_loss=stop)
        
        if self.method == SizingMethod.FIXED_FRACTIONAL:
            return self._fixed_fractional(entry, stop)
        elif self.method == SizingMethod.FIXED_RATIO:
            return self._fixed_ratio(entry, stop)
        elif self.method == SizingMethod.KELLY:
            return self._kelly(entry, stop, setup)
        elif self.method == SizingMethod.HALF_KELLY:
            return self._kelly(entry, stop, setup, fraction=0.5)
        elif self.method == SizingMethod.OPTIMAL_F:
            return self._optimal_f(entry, stop)
        elif self.method == SizingMethod.RISK_PARITY:
            return self._risk_parity(entry, stop, setup)
        elif self.method == SizingMethod.VOLATILITY:
            return self._volatility_based(entry, stop, setup)
        else:
            return self._fixed_fractional(entry, stop)
    
    def _fixed_fractional(self, entry: float, stop: float) -> SizingResult:
        """Van Tharp's fixed fractional method."""
        risk_per_share = abs(entry - stop)
        if risk_per_share == 0:
            return self._error_result("Stop loss must differ from entry price")
        
        max_risk_dollars = self.account_size * (self.base_risk_pct / 100)
        shares_float = max_risk_dollars / risk_per_share
        shares = shares_float if self.allow_fractional else int(shares_float)
        
        position_value = shares * entry
        risk_amount = shares * risk_per_share
        
        # Cap at max position size
        max_position = self.account_size * (self.max_position_pct / 100)
        if position_value > max_position:
            shares = max_position / entry if self.allow_fractional else int(max_position / entry)
            position_value = shares * entry
            risk_amount = shares * risk_per_share
        
        return SizingResult(
            method=SizingMethod.FIXED_FRACTIONAL,
            shares=int(shares),
            position_value=position_value,
            risk_amount=risk_amount,
            risk_pct=(risk_amount / self.account_size) * 100,
            leverage=position_value / self.account_size,
            max_loss=risk_amount,
            confidence="optimal",
            reason=f"Risk {self.base_risk_pct}% per trade ({max_risk_dollars:,.0f})"
        )
    
    def _fixed_ratio(self, entry: float, stop: float) -> SizingResult:
        """Ryan Jones' fixed ratio method."""
        # Fixed ratio: increase size after accumulating delta profits
        risk_per_share = abs(entry - stop)
        if risk_per_share == 0:
            return self._error_result("Stop loss must differ from entry price")
        
        # Base risk per trade
        base_risk = self.account_size * (self.base_risk_pct / 100)
        
        # Calculate units based on accumulated profits
        # Simplified: each unit adds delta risk
        delta = base_risk * 0.5  # Profit needed to increase size
        accumulated_profit = sum(t for t in self.trade_history if t > 0)
        
        units = 1 + int(accumulated_profit / delta) if accumulated_profit > 0 else 1
        units = max(1, min(units, 10))  # Cap at 10 units
        
        risk_per_trade = base_risk * units
        shares_float = risk_per_trade / risk_per_share
        shares = shares_float if self.allow_fractional else int(shares_float)
        
        position_value = shares * entry
        risk_amount = shares * risk_per_share
        
        return SizingResult(
            method=SizingMethod.FIXED_RATIO,
            shares=int(shares),
            position_value=position_value,
            risk_amount=risk_amount,
            risk_pct=(risk_amount / self.account_size) * 100,
            leverage=position_value / self.account_size,
            max_loss=risk_amount,
            confidence="conservative",
            reason=f"{units} units (accum profit: {accumulated_profit:,.0f})"
        )
    
    def _kelly(
        self,
        entry: float,
        stop: float,
        setup: TradeSetup,
        fraction: float = 1.0
    ) -> SizingResult:
        """Kelly criterion for position sizing."""
        if not setup.win_probability or not setup.avg_win or not setup.avg_loss:
            # Fallback to fixed fractional if no stats
            result = self._fixed_fractional(entry, stop)
            result.method = SizingMethod.KELLY
            result.confidence = "unknown"
            result.reason = "Missing Kelly inputs, used fixed fractional"
            return result
        
        W = setup.win_probability
        R = setup.avg_win / setup.avg_loss if setup.avg_loss != 0 else 1.0
        
        # Kelly % = W - (1-W)/R
        kelly_pct = W - ((1 - W) / R) if R > 0 else 0
        kelly_pct = max(0, min(kelly_pct, 0.5))  # Cap at 50%
        
        # Apply fraction (half Kelly, quarter Kelly, etc.)
        adjusted_pct = kelly_pct * fraction
        
        risk_amount = self.account_size * adjusted_pct
        risk_per_share = abs(entry - stop)
        
        if risk_per_share == 0:
            return self._error_result("Stop loss must differ from entry price")
        
        shares_float = (self.account_size * adjusted_pct) / entry
        shares = shares_float if self.allow_fractional else int(shares_float)
        
        position_value = shares * entry
        
        return SizingResult(
            method=SizingMethod.HALF_KELLY if fraction < 1 else SizingMethod.KELLY,
            shares=int(shares),
            position_value=position_value,
            risk_amount=risk_amount,
            risk_pct=adjusted_pct * 100,
            leverage=position_value / self.account_size,
            max_loss=shares * risk_per_share,
            confidence="optimal" if fraction >= 0.5 else "conservative",
            reason=f"Kelly: {kelly_pct:.1%} × {fraction} = {adjusted_pct:.1%}"
        )
    
    def _optimal_f(self, entry: float, stop: float) -> SizingResult:
        """Ralph Vince's optimal f (simplified)."""
        # Requires trade history for proper calculation
        if len(self.trade_history) < 10:
            result = self._fixed_fractional(entry, stop)
            result.method = SizingMethod.OPTIMAL_F
            result.confidence = "insufficient_data"
            result.reason = "Need 10+ trades for optimal f"
            return result
        
        # Simplified: use largest historical loss
        max_loss = abs(min(self.trade_history)) if any(t < 0 for t in self.trade_history) else self.account_size * 0.02
        
        # Optimal f = max loss / account (conservative proxy)
        optimal_f = min(0.25, max_loss / self.account_size) if max_loss > 0 else 0.02
        
        risk_per_share = abs(entry - stop)
        shares_float = (self.account_size * optimal_f) / risk_per_share if risk_per_share > 0 else 0
        shares = shares_float if self.allow_fractional else int(shares_float)
        
        position_value = shares * entry
        
        return SizingResult(
            method=SizingMethod.OPTIMAL_F,
            shares=int(shares),
            position_value=position_value,
            risk_amount=shares * risk_per_share,
            risk_pct=optimal_f * 100,
            leverage=position_value / self.account_size,
            max_loss=shares * risk_per_share,
            confidence="aggressive",
            reason=f"Optimal f based on max historical loss"
        )
    
    def _risk_parity(self, entry: float, stop: Optional[float], setup: TradeSetup) -> SizingResult:
        """Equal risk contribution sizing."""
        if not setup.volatility:
            return self._fixed_fractional(entry, stop or entry * 0.95)
        
        # Inverse volatility weighting
        vol = setup.volatility
        inv_vol = 1 / vol if vol > 0 else 1
        target_vol = 0.02  # 2% daily vol target
        
        risk_per_share = abs(entry - stop) if stop else entry * 0.02
        
        # Scale position by inverse volatility
        vol_scalar = target_vol / vol if vol > 0 else 1
        base_shares = (self.account_size * self.base_risk_pct / 100) / risk_per_share
        shares_float = base_shares * vol_scalar
        shares = shares_float if self.allow_fractional else int(shares_float)
        
        position_value = shares * entry
        
        return SizingResult(
            method=SizingMethod.RISK_PARITY,
            shares=int(shares),
            position_value=position_value,
            risk_amount=shares * risk_per_share,
            risk_pct=(shares * risk_per_share / self.account_size) * 100,
            leverage=position_value / self.account_size,
            max_loss=shares * risk_per_share,
            confidence="optimal",
            reason=f"Risk parity: vol scalar {vol_scalar:.2f}"
        )
    
    def _volatility_based(self, entry: float, stop: float, setup: TradeSetup) -> SizingResult:
        """Volatility-adjusted position sizing."""
        if not setup.volatility:
            return self._fixed_fractional(entry, stop)
        
        # ATR-based sizing: risk $X per ATR unit
        atr = setup.volatility
        risk_per_unit = self.account_size * (self.base_risk_pct / 100)
        risk_per_share = atr
        
        if risk_per_share == 0:
            return self._error_result("Volatility must be > 0")
        
        shares_float = risk_per_unit / risk_per_share
        shares = shares_float if self.allow_fractional else int(shares_float)
        
        position_value = shares * entry
        actual_risk = shares * abs(entry - stop) if stop else shares * entry * 0.02
        
        return SizingResult(
            method=SizingMethod.VOLATILITY,
            shares=int(shares),
            position_value=position_value,
            risk_amount=actual_risk,
            risk_pct=(actual_risk / self.account_size) * 100,
            leverage=position_value / self.account_size,
            max_loss=actual_risk,
            confidence="optimal",
            reason=f"ATR-based: {shares} units at ${risk_per_unit:,.0f} per ATR"
        )
    
    def _error_result(self, reason: str) -> SizingResult:
        return SizingResult(
            method=self.method,
            shares=0,
            position_value=0,
            risk_amount=0,
            risk_pct=0,
            leverage=0,
            max_loss=0,
            confidence="error",
            reason=reason
        )
    
    def record_trade(self, pnl: float):
        """Record trade result for methods that track history."""
        self.trade_history.append(pnl)
        if len(self.trade_history) > 100:
            self.trade_history.pop(0)
    
    def compare_methods(
        self,
        entry: float,
        stop: float,
        setup: Optional[TradeSetup] = None
    ) -> Dict[SizingMethod, SizingResult]:
        """Compare all sizing methods for a trade."""
        original_method = self.method
        results = {}
        
        for method in SizingMethod:
            self.method = method
            results[method] = self.calculate(entry, stop, setup)
        
        self.method = original_method
        return results


def recommend_method(
    win_rate: Optional[float] = None,
    avg_win_loss_ratio: Optional[float] = None,
    trade_frequency: str = "medium",  # low, medium, high
    account_size: float = 100000,
    volatility: str = "medium"  # low, medium, high
) -> str:
    """
    Recommend sizing method based on trader profile.
    
    Returns: method name and reasoning
    """
    # Decision tree
    if account_size < 25000:
        return "FIXED_FRACTIONAL (2%) - Simple and safe for small accounts"
    
    if volatility == "high":
        return "VOLATILITY or RISK_PARITY - Adjusts for wild swings, protects capital"
    
    if win_rate and win_rate > 0.55 and avg_win_loss_ratio and avg_win_loss_ratio > 1.5:
        return "HALF_KELLY - You have an edge, maximize it conservatively"
    
    if trade_frequency == "high":
        return "FIXED_RATIO - Builds size gradually as you accumulate profits"
    
    if len(str(account_size)) > 6:  # $1M+
        return "RISK_PARITY - Portfolio-level risk management for size"
    
    return "FIXED_FRACTIONAL (1-2%) - The standard that works for most traders"


# === Examples ===

if __name__ == "__main__":
    print("=" * 70)
    print("Position Sizing Calculator")
    print("=" * 70)
    
    # Example account
    account = 100000
    
    # Trade setup
    entry = 150.00
    stop = 145.00  # $5 risk per share
    target = 165.00
    
    print(f"\nAccount: ${account:,.0f}")
    print(f"Entry: ${entry:.2f}")
    print(f"Stop: ${stop:.2f}")
    print(f"Risk per share: ${entry - stop:.2f}")
    print(f"Reward:risk = {(target - entry) / (entry - stop):.1f}:1")
    
    # Compare methods
    print("\n" + "-" * 70)
    print("Method Comparison:")
    print("-" * 70)
    
    calc = PositionSizingCalculator(
        account_size=account,
        max_risk_pct=2.0,
        max_position_pct=20.0
    )
    
    # Setup with Kelly data
    setup = TradeSetup(
        entry_price=entry,
        stop_loss=stop,
        take_profit=target,
        win_probability=0.45,
        avg_win=800,
        avg_loss=400,
        volatility=5.0  # ATR
    )
    
    results = calc.compare_methods(entry, stop, setup)
    
    print(f"\n{'Method':<20} {'Shares':>8} {'$ Value':>12} {'Risk $':>10} {'Risk %':>8} {'Conf':<12}")
    print("-" * 70)
    
    for method, result in results.items():
        if result.shares > 0:
            print(f"{method.name:<20} {result.shares:>8} "
                  f"${result.position_value:>10,.0f} ${result.risk_amount:>8,.0f} "
                  f"{result.risk_pct:>6.1f}% {result.confidence:<12}")
        else:
            print(f"{method.name:<20} {'N/A':>8} {'':>12} {'':>10} "
                  f"{'':>8} {result.reason:<30}")
    
    # Detailed example with Fixed Fractional
    print("\n" + "=" * 70)
    print("Fixed Fractional Example (2% risk):")
    print("=" * 70)
    
    calc = PositionSizingCalculator(
        account_size=account,
        max_risk_pct=2.0,
        method=SizingMethod.FIXED_FRACTIONAL
    )
    
    result = calc.calculate(entry, stop)
    print(f"\nShares: {result.shares}")
    print(f"Position Value: ${result.position_value:,.2f}")
    print(f"Risk Amount: ${result.risk_amount:,.2f}")
    print(f"Risk %: {result.risk_pct:.2f}%")
    print(f"Leverage: {result.leverage:.1f}x")
    print(f"Max Loss if stopped: ${result.max_loss:,.2f}")
    print(f"\nIf trade hits target: +${(target - entry) * result.shares:,.2f}")
    print(f"Return on account: {((target - entry) * result.shares / account) * 100:.2f}%")
    
    # Kelly example
    print("\n" + "=" * 70)
    print("Kelly Criterion Example:")
    print("=" * 70)
    
    calc_kelly = PositionSizingCalculator(
        account_size=account,
        max_risk_pct=2.0,
        method=SizingMethod.HALF_KELLY,
        kelly_fraction=0.5
    )
    
    result = calc_kelly.calculate(entry, stop, setup)
    print(f"\nWin probability: {setup.win_probability:.0%}")
    print(f"Avg win/loss ratio: {setup.avg_win/setup.avg_loss:.1f}:1")
    print(f"Full Kelly would suggest: {result.risk_pct * 2:.1f}%")
    print(f"Half Kelly position: {result.shares} shares")
    print(f"Risk: ${result.risk_amount:,.2f} ({result.risk_pct:.1f}% of account)")
    print(f"\n{result.reason}")
    
    # Recommendation
    print("\n" + "=" * 70)
    print("Method Recommendations:")
    print("=" * 70)
    
    scenarios = [
        (0.60, 2.0, "high", 100000, "low", "High win rate scalper"),
        (0.40, 1.2, "low", 50000, "high", "Trend follower, volatile market"),
        (0.52, 1.5, "medium", 500000, "medium", "Swing trader, mid-size account"),
    ]
    
    for win_rate, wl_ratio, freq, acc_size, vol, desc in scenarios:
        rec = recommend_method(win_rate, wl_ratio, freq, acc_size, vol)
        print(f"\n{desc}:")
        print(f"  Win rate: {win_rate:.0%}, W/L: {wl_ratio:.1f}, Vol: {vol}")
        print(f"  → {rec}")
    
    print("\n" + "=" * 70)
    print("Position sizing is the most important decision after entry.")
    print("Risk 1-2% per trade. Never more.")
    print("=" * 70)
```

## Method Quick Reference

| Method | Risk Level | Best For | Formula |
|--------|-----------|----------|---------|
| **Fixed Fractional** | Low | Beginners, any strategy | Risk $ = Account × % |
| **Fixed Ratio** | Low-Med | Consistent traders | Increase after N profits |
| **Kelly** | High | Proven edge, high win rate | W - (1-W)/R |
| **Half Kelly** | Med | Most traders with stats | Kelly × 0.5 |
| **Optimal F** | Very High | Systematic traders | Based on worst loss |
| **Risk Parity** | Med | Portfolios, diversification | Inverse volatility |
| **Volatility** | Med | Variable volatility | Risk $ / ATR |

## Sizing Rules

```python
# Standard 2% rule
calc = PositionSizingCalculator(
    account_size=100000,
    max_risk_pct=2.0,
    method=SizingMethod.FIXED_FRACTIONAL
)

# Half Kelly with edge
setup = TradeSetup(
    entry_price=150, stop_loss=145,
    win_probability=0.55,
    avg_win=1000, avg_loss=400
)
calc = PositionSizingCalculator(
    account_size=100000,
    method=SizingMethod.HALF_KELLY,
    kelly_fraction=0.5
)

# Volatility-adjusted (for volatile stocks)
calc = PositionSizingCalculator(
    account_size=100000,
    method=SizingMethod.VOLATILITY
)
setup = TradeSetup(entry_price=150, stop_loss=145, volatility=8.0)
```

## The 1% Rule (Conservative)

Most professional traders risk **1% per trade**:
- $100k account = $1,000 max loss per trade
- With $5 stop = 200 shares
- 10 losing trades = only 10% drawdown
- Account survives bad streak

## Position Size Formula

```
Position Size = Risk $ / (Entry - Stop)

Where:
  Risk $ = Account Size × Risk %
  
Example:
  $100k account, 2% risk, $150 entry, $145 stop
  Risk $ = $100,000 × 0.02 = $2,000
  Risk per share = $150 - $145 = $5
  Shares = $2,000 / $5 = 400 shares
  Position Value = 400 × $150 = $60,000
```

## Key Insights

1. **Position size matters more than entry** — A good entry with bad size still loses
2. **Kelly is maximum, not target** — Half Kelly is safer and often performs better
3. **Lower risk % = more trades** — Survive to catch the big winners
4. **Volatility adjusts size** — Wild stocks need smaller positions
5. **Correlation affects risk** — Correlated positions add risk, not diversify

---

**Created by Ghost 👻 | Feb 20, 2026 | 13-min learning sprint**  
*Lesson: "It's not how much you make on winners, it's how little you lose on losers." Position sizing keeps you in the game. Risk 1-2%, live to trade another day.*
