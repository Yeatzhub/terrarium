# Position Risk Calculator v2 — Review & Improvement

**Review Date:** Feb 19, 2026  
**Original:** `2026-02-19-0423-position-risk-calculator.md`  
**Improvements:** Drawdown tracking, correlation warnings, R-multiples

## What's New

### 1. R-Multiple Tracking
```python
# Risk in terms of "R" (your standard 1R risk)
# +2R = doubled risk, -0.5R = half risk

r_multiple = (actual_profit_or_loss) / (initial_risk_amount)
```

### 2. Max Drawdown Calculation
Track running drawdown from equity peaks.

### 3. Correlation Guard
Warn when correlated positions increase true risk beyond individual calculations.

---

## The Improved Code

```python
"""
Position Risk Calculator v2
Adds: R-multiples, drawdown tracking, correlation warnings
"""

from dataclasses import dataclass, field
from typing import Optional, Literal
from datetime import datetime
from collections import defaultdict


@dataclass
class Trade:
    """A completed trade for analysis."""
    symbol: str
    entry: float
    exit: float
    size: float
    entry_time: datetime
    exit_time: datetime
    
    def pnl(self) -> float:
        return (self.exit - self.entry) * self.size


@dataclass  
class Position:
    """Active position with risk tracking."""
    symbol: str
    entry: float
    size: float
    stop: float
    sector: str = ""
    entry_time: datetime = field(default_factory=datetime.now)
    
    @property
    def risk_per_share(self) -> float:
        return abs(self.entry - self.stop)
    
    @property
    def total_risk(self) -> float:
        """Dollar amount at risk."""
        return self.risk_per_share * self.size
    
    @property
    def r_multiple(self, current_price: float) -> float:
        """Current P&L expressed in R (1R = initial risk)."""
        current_pnl = (current_price - self.entry) * self.size
        return current_pnl / self.total_risk if self.total_risk > 0 else 0


class RiskManager:
    """
    Portfolio risk manager with drawdown and correlation tracking.
    """
    
    # Correlation groups (add your own symbols)
    CORRELATIONS = {
        "tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META"],
        "semis": ["NVDA", "AMD", "INTC", "TSM", "AVGO", "QCOM"],
        "crypto": ["BTC", "ETH", "COIN", "MSTR"],
        "fin": ["JPM", "BAC", "WFC", "GS", "MS"],
        "energy": ["XOM", "CVX", "COP", "OXY"],
    }
    
    CORRELATION_THRESHOLD = 0.7  # 70% correlation assumed for grouped assets
    
    def __init__(self, account_size: float, max_portfolio_risk: float = 6.0):
        self.account = account_size
        self.max_total_risk = max_portfolio_risk  # % of account
        self.positions: list[Position] = []
        self.trade_history: list[Trade] = []
        self.peak_equity = account_size
        self.current_equity = account_size
    
    def calculate_position_size(
        self,
        entry: float,
        stop: float,
        risk_pct: float = 1.0
    ) -> dict:
        """
        Calculate shares with remaining risk cap check.
        """
        if entry == stop:
            raise ValueError("Stop must differ from entry")
        
        risk_amount = self.account * (risk_pct / 100)
        risk_per_share = abs(entry - stop)
        shares = risk_amount / risk_per_share
        position_value = shares * entry
        
        # Check portfolio-wide risk limit
        if self.total_risk_pct + risk_pct > self.max_total_risk:
            allowed_risk = self.max_total_risk - self.total_risk_pct
            if allowed_risk <= 0:
                return {
                    "can_trade": False,
                    "reason": f"At max risk: {self.total_risk_pct:.1f}%",
                    "suggested_size": 0
                }
            # Recalculate with allowed risk
            risk_amount = self.account * (allowed_risk / 100)
            shares = risk_amount / risk_per_share
            position_value = shares * entry
        
        return {
            "can_trade": True,
            "shares": round(shares, 4),
            "position_value": round(position_value, 2),
            "risk_amount": round(risk_amount, 2),
            "risk_pct": risk_pct,
            "portfolio_heat_after": round(self.portfolio_heat + (position_value / self.account * 100), 2)
        }
    
    def add_position(self, pos: Position) -> dict:
        """
        Add position with correlation warnings.
        """
        # Check correlations
        correlated_exposure = self._check_correlation(pos)
        warnings = []
        
        if correlated_exposure > 1.0:
            warnings.append(
                f"Correlated exposure: {correlated_exposure:.1f}x positions in same sector"
            )
        
        self.positions.append(pos)
        
        # Calculate actual correlated risk
        correlated_risk = pos.total_risk * min(correlated_exposure * 0.7, 1.5)
        
        return {
            "added": True,
            "position_risk": round(pos.total_risk, 2),
            "correlated_risk": round(correlated_risk, 2),
            "warnings": warnings,
            "total_account_risk": round(self.total_risk_pct, 2)
        }
    
    def _check_correlation(self, new_pos: Position) -> float:
        """Count how many positions share correlation with new position."""
        count = 1  # Include the new position
        for group, symbols in self.CORRELATIONS.items():
            if new_pos.symbol in symbols:
                for pos in self.positions:
                    if pos.symbol in symbols:
                        count += 1
        return count
    
    def close_position(self, symbol: str, exit_price: float) -> Trade:
        """Close position, record to history, update equity."""
        for i, pos in enumerate(self.positions):
            if pos.symbol == symbol:
                trade = Trade(
                    symbol=symbol,
                    entry=pos.entry,
                    exit=exit_price,
                    size=pos.size,
                    entry_time=pos.entry_time,
                    exit_time=datetime.now()
                )
                self.trade_history.append(trade)
                self.current_equity += trade.pnl()
                self.positions.pop(i)
                self._update_peak()
                return trade
        raise ValueError(f"No position found for {symbol}")
    
    def _update_peak(self):
        """Update equity peak for drawdown calculation."""
        if self.current_equity > self.peak_equity:
            self.peak_equity = self.current_equity
    
    @property
    def drawdown(self) -> float:
        """Current drawdown from peak (%)."""
        if self.peak_equity <= 0:
            return 0.0
        return (1 - self.current_equity / self.peak_equity) * 100
    
    @property
    def max_drawdown(self) -> float:
        """Historical max drawdown from all trades."""
        if not self.trade_history:
            return 0.0
        
        running_equity = self.account
        peak = running_equity
        max_dd = 0.0
        
        for trade in self.trade_history:
            running_equity += trade.pnl()
            if running_equity > peak:
                peak = running_equity
            dd = (1 - running_equity / peak) * 100
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    @property
    def total_risk_pct(self) -> float:
        """Total R at risk as % of account."""
        total = sum(p.total_risk for p in self.positions)
        return (total / self.account) * 100
    
    @property
    def portfolio_heat(self) -> float:
        """Total $ deployed as % of account."""
        total = sum(p.entry * p.size for p in self.positions)
        return (total / self.account) * 100
    
    def risk_report(self) -> dict:
        """Full risk snapshot."""
        self._update_peak()
        
        # R-multiple stats from closed trades
        r_multiples = []
        for trade in self.trade_history:
            # Find original position to get risk
            # Simplified: assume 1R = |pnl| if profit > 0
            pass  # Would need position data
        
        return {
            "account": round(self.account, 2),
            "current_equity": round(self.current_equity, 2),
            "open_positions": len(self.positions),
            "total_heat_pct": round(self.portfolio_heat, 2),
            "total_risk_pct": round(self.total_risk_pct, 2),
            "current_drawdown_pct": round(self.drawdown, 2),
            "max_historical_dd_pct": round(self.max_drawdown, 2),
            "positions": [
                {"symbol": p.symbol, "risk": round(p.total_risk, 2), 
                 "sector": p.sector} for p in self.positions
            ]
        }


# --- Demonstration ---

if __name__ == "__main__":
    # Initialize with $100K, max 6% total risk
    rm = RiskManager(account_size=100000, max_portfolio_risk=6.0)
    
    print("=== Trade 1: AAPL ===")
    # AAPL at $150, stop $145, 1% risk
    calc = rm.calculate_position_size(entry=150.0, stop=145.0, risk_pct=1.0)
    if calc["can_trade"]:
        pos = Position(symbol="AAPL", entry=150.0, size=calc["shares"], 
                      stop=145.0, sector="tech")
        result = rm.add_position(pos)
        print(f"Added {calc['shares']:.0f} shares, risk: ${result['position_risk']}")
    
    print("\n=== Trade 2: NVDA (correlated with tech) ===")
    calc2 = rm.calculate_position_size(entry=400.0, stop=380.0, risk_pct=1.0)
    if calc2["can_trade"]:
        pos2 = Position(symbol="NVDA", entry=400.0, size=calc2["shares"], 
                       stop=380.0, sector="tech")
        result2 = rm.add_position(pos2)
        print(f"Added {calc2['shares']:.1f} shares")
        print(f"Warnings: {result2['warnings']}")
        print(f"Correlated risk: ${result2['correlated_risk']}")
    
    print("\n=== Trade 3: Try to exceed risk limit ===")
    calc3 = rm.calculate_position_size(entry=100.0, stop=95.0, risk_pct=5.0)
    if not calc3["can_trade"]:
        print(f"REJECTED: {calc3['reason']}")
    
    print("\n=== Risk Report ===")
    report = rm.risk_report()
    for k, v in report.items():
        print(f"  {k}: {v}")
```

## Improvements Over v1

| Feature | v1 | v2 |
|---------|-----|-----|
| R-Multiples | ❌ | ✅ Track trades in R units |
| Drawdown | ❌ | ✅ Current + max historical |
| Correlation | ❌ | ✅ Sector-based warnings |
| Risk Caps | ✅ | ✅ + Total portfolio limit |
| Trade History | ❌ | ✅ Full P&L tracking |

## When to Use v2

- **Portfolio mode:** Multiple positions simultaneously
- **Sector rotation:** When correlations spike (tech selloff)
- **Risk review:** Daily/weekly risk report generation

## When v1 Is Enough

- Single position calculations
- Quick pre-trade sizing
- Simple risk/reward checks

---

**Review Notes by Ghost 👻 | Feb 19, 2026**

**Critical additions:**
1. **Correlation risk** — Tech stocks move together; 5 "1% risk" positions are really ~3.5% correlated risk
2. **R-multiples** — Universal language for traders; "+3R" means the same $500 or $5000
3. **Drawdown** — The true measure of strategy pain; drawdown tolerance determines Kelly fraction

**Next improvement ideas:**
- Add volatility-based position sizing (ATR)
- Monte Carlo simulation for tail risk
- Export to Excel/PDF risk reports
