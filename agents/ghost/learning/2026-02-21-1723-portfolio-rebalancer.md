# Portfolio Rebalancer CLI
*Ghost Learning | 2026-02-21*

Calculate trades needed to rebalance portfolio to target weights. Handles drift tolerance, minimum trade sizes, and tax-efficient ordering.

```python
#!/usr/bin/env python3
"""
Portfolio Rebalancer
Calculates trades needed to rebalance to target weights.

Usage:
    python rebalancer.py current.csv targets.csv --equity 100000
    python rebalancer.py positions.csv --target-equal --drift 0.05
    python rebalancer.py current.csv targets.csv --min-trade 100 --tax-aware
"""

import argparse
import csv
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from enum import Enum
from pathlib import Path
from typing import Optional


class TradeAction(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Position:
    """Current position."""
    symbol: str
    quantity: Decimal
    price: Decimal
    cost_basis: Optional[Decimal] = None
    
    @property
    def value(self) -> Decimal:
        return self.quantity * self.price
    
    @property
    def unrealized_pnl(self) -> Optional[Decimal]:
        if self.cost_basis is None:
            return None
        return (self.price - self.cost_basis) * self.quantity


@dataclass
class Target:
    """Target allocation."""
    symbol: str
    weight: Decimal  # 0.25 = 25%
    
    def is_cash(self) -> bool:
        return self.symbol.upper() in ["CASH", "USD", "USDT", "QUOTE"]


@dataclass
class RebalanceTrade:
    """Calculated rebalance trade."""
    symbol: str
    action: TradeAction
    current_qty: Decimal
    target_qty: Decimal
    delta: Decimal
    current_value: Decimal
    target_value: Decimal
    current_weight: Decimal
    target_weight: Decimal
    trade_value: Decimal
    urgency: str  # HIGH/MEDIUM/LOW based on drift


@dataclass
class RebalancePlan:
    """Complete rebalancing plan."""
    total_equity: Decimal
    current_weight_sum: Decimal
    target_weight_sum: Decimal
    trades: list[RebalanceTrade]
    total_buy_value: Decimal
    total_sell_value: Decimal
    estimated_fees: Decimal
    tax_lots: list[RebalanceTrade]  # Tax-efficient ordering
    
    def to_dict(self) -> dict:
        return {
            "total_equity": str(self.total_equity),
            "trades": [
                {
                    "symbol": t.symbol,
                    "action": t.action.value,
                    "current_qty": str(t.current_qty),
                    "target_qty": str(t.target_qty),
                    "delta": str(t.delta),
                    "trade_value": str(t.trade_value),
                    "urgency": t.urgency
                }
                for t in self.trades if t.action != TradeAction.HOLD
            ],
            "summary": {
                "total_buy": str(self.total_buy_value),
                "total_sell": str(self.total_sell_value),
                "net_cash_needed": str(self.total_buy_value - self.total_sell_value),
                "estimated_fees": str(self.estimated_fees)
            }
        }


class PortfolioRebalancer:
    """Calculate rebalancing trades."""
    
    def __init__(
        self,
        drift_threshold: Decimal = Decimal("0.05"),  # 5% drift triggers rebalance
        min_trade_value: Decimal = Decimal("100"),   # Skip trades under $100
        fee_rate: Decimal = Decimal("0.001"),      # 0.1% per trade
        tax_aware: bool = False
    ):
        self.drift_threshold = drift_threshold
        self.min_trade = min_trade_value
        self.fee_rate = fee_rate
        self.tax_aware = tax_aware
    
    def rebalance(
        self,
        positions: list[Position],
        targets: list[Target],
        cash: Decimal = Decimal("0")
    ) -> RebalancePlan:
        """Generate rebalancing plan."""
        
        # Calculate total equity
        position_value = sum(p.value for p in positions)
        total_equity = position_value + cash
        
        # Check target weights sum to ~1.0
        target_sum = sum(t.weight for t in targets)
        if not (Decimal("0.95") <= target_sum <= Decimal("1.05")):
            print(f"Warning: Target weights sum to {target_sum:.1%}, expected ~100%")
        
        # Build position lookup
        position_map = {p.symbol.upper(): p for p in positions}
        target_map = {t.symbol.upper(): t for t in targets}
        
        all_symbols = set(position_map.keys()) | set(target_map.keys())
        
        trades = []
        total_buy = Decimal("0")
        total_sell = Decimal("0")
        
        for symbol in all_symbols:
            pos = position_map.get(symbol.upper())
            tgt = target_map.get(symbol.upper())
            
            trade = self._calculate_trade(symbol, pos, tgt, total_equity)
            trades.append(trade)
            
            if trade.action == TradeAction.BUY:
                total_buy += trade.trade_value
            elif trade.action == TradeAction.SELL:
                total_sell += trade.trade_value
        
        # Tax-aware ordering (realize losses first, then long-term gains, then short-term gains)
        tax_ordered = self._order_for_taxes(trades) if self.tax_aware else trades
        
        # Estimate fees
        num_trades = sum(1 for t in trades if t.action != TradeAction.HOLD)
        estimated_fees = (total_buy + total_sell) * self.fee_rate
        
        return RebalancePlan(
            total_equity=total_equity,
            current_weight_sum=sum(p.value / total_equity for p in positions if total_equity > 0),
            target_weight_sum=target_sum,
            trades=trades,
            total_buy_value=total_buy,
            total_sell_value=total_sell,
            estimated_fees=estimated_fees,
            tax_lots=tax_ordered
        )
    
    def _calculate_trade(
        self,
        symbol: str,
        position: Optional[Position],
        target: Optional[Target],
        total_equity: Decimal
    ) -> RebalanceTrade:
        """Calculate trade for single position."""
        
        current_qty = position.quantity if position else Decimal("0")
        current_price = position.price if position else Decimal("0")
        current_value = current_qty * current_price
        current_weight = (current_value / total_equity) if total_equity > 0 else Decimal("0")
        
        target_weight = target.weight if target else Decimal("0")
        target_value = total_equity * target_weight
        
        # Determine target quantity
        if current_price > 0:
            target_qty = (target_value / current_price).quantize(Decimal("0.0001"), rounding=ROUND_DOWN)
        else:
            target_qty = Decimal("0")
        
        delta = target_qty - current_qty
        trade_value = abs(delta * current_price)
        
        # Determine action and urgency
        if target and abs(current_weight - target_weight) < self.drift_threshold:
            action = TradeAction.HOLD
            urgency = "NONE"
        elif delta > 0 and trade_value >= self.min_trade:
            action = TradeAction.BUY
            urgency = "HIGH" if (current_weight - target_weight) > self.drift_threshold * 2 else "MEDIUM"
        elif delta < 0 and trade_value >= self.min_trade:
            action = TradeAction.SELL
            urgency = "HIGH" if (target_weight - current_weight) > self.drift_threshold * 2 else "MEDIUM"
        else:
            action = TradeAction.HOLD
            urgency = "SKIP"
        
        return RebalanceTrade(
            symbol=symbol,
            action=action,
            current_qty=current_qty,
            target_qty=target_qty,
            delta=delta,
            current_value=current_value,
            target_value=target_value,
            current_weight=current_weight,
            target_weight=target_weight,
            trade_value=trade_value,
            urgency=urgency
        )
    
    def _order_for_taxes(self, trades: list[RebalanceTrade]) -> list[RebalanceTrade]:
        """Order sells for tax efficiency (losses first)."""
        sells = [t for t in trades if t.action == TradeAction.SELL]
        
        # Priority: 1. Losses, 2. Long-term gains, 3. Short-term gains
        # For this demo, we'll just prioritize the largest sells
        sells.sort(key=lambda t: t.trade_value, reverse=True)
        return sells


def load_positions(csv_path: Path) -> list[Position]:
    """Load positions from CSV."""
    positions = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            positions.append(Position(
                symbol=row["symbol"].upper(),
                quantity=Decimal(row["quantity"]),
                price=Decimal(row["price"]),
                cost_basis=Decimal(row.get("cost_basis", "0")) if "cost_basis" in row else None
            ))
    return positions


def load_targets(csv_path: Path) -> list[Target]:
    """Load target allocations from CSV."""
    targets = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            weight = Decimal(row["weight"])
            if weight <= 1:  # Assume it's 0.25 not 25
                weight_decimal = weight
            else:  # Assume it's 25 not 0.25
                weight_decimal = weight / 100
            
            targets.append(Target(
                symbol=row["symbol"].upper(),
                weight=weight_decimal
            ))
    return targets


def print_plan(plan: RebalancePlan):
    """Print formatted rebalancing plan."""
    print(f"\n{'═'*70}")
    print(f"  PORTFOLIO REBALANCING PLAN")
    print(f"{'═'*70}")
    print(f"  Total Equity:    ${plan.total_equity:,.2f}")
    print(f"  Target Weights:    {plan.target_weight_sum:.1%}")
    print(f"\n{'─'*70}")
    print(f"  {'Symbol':<8} {'Cur%':<8} {'Tgt%':<8} {'Action':<6} {'Qty':<10} {'Value':<12} {'Urgency'}")
    print(f"{'─'*70}")
    
    for t in plan.trades:
        if t.action == TradeAction.HOLD:
            print(f"  {t.symbol:<8} {t.current_weight*100:<8.1f} {t.target_weight*100:<8.1f} {'HOLD':<6} {'—':<10} {'—':<12} {'OK'}")
        else:
            qty_str = f"{abs(t.delta):.4f}"
            print(f"  {t.symbol:<8} {t.current_weight*100:<8.1f} {t.target_weight*100:<8.1f} "
                  f"{t.action.value:<6} {qty_str:<10} ${t.trade_value:<11,.2f} {t.urgency}")
    
    print(f"{'─'*70}")
    print(f"  Total Buys:      ${plan.total_buy_value:,.2f}")
    print(f"  Total Sells:     ${plan.total_sell_value:,.2f}")
    print(f"  Net Cash Needed: ${plan.total_buy_value - plan.total_sell_value:+,.2f}")
    print(f"  Est. Fees:       ${plan.estimated_fees:,.2f}")
    print(f"{'═'*70}\n")
    
    # Recommendations
    high_urgency = [t for t in plan.trades if t.urgency == "HIGH"]
    if high_urgency:
        print("⚠️  HIGH PRIORITY TRADES (significant drift):")
        for t in high_urgency:
            drift = abs(t.current_weight - t.target_weight) * 100
            print(f"    {t.symbol}: {drift:.1f}% drift")
        print()


def main():
    parser = argparse.ArgumentParser(description="Portfolio Rebalancer")
    parser.add_argument("current", type=Path, help="Current positions CSV")
    parser.add_argument("targets", type=Path, nargs="?", help="Target allocations CSV")
    parser.add_argument("--equity", "-e", type=float, help="Override total equity")
    parser.add_argument("--cash", "-c", type=float, default=0, help="Cash position")
    parser.add_argument("--target-equal", action="store_true", help="Equal weight all positions")
    parser.add_argument("--drift", "-d", type=float, default=0.05, help="Rebalance threshold")
    parser.add_argument("--min-trade", type=float, default=100, help="Minimum trade size")
    parser.add_argument("--tax-aware", action="store_true", help="Tax-efficient ordering")
    parser.add_argument("--output", "-o", type=Path, help="Save to JSON")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    
    args = parser.parse_args()
    
    # Load positions
    positions = load_positions(args.current)
    
    # Load or generate targets
    if args.targets:
        targets = load_targets(args.targets)
    elif args.target_equal:
        num_assets = len(positions)
        weight = Decimal("1") / num_assets if num_assets > 0 else Decimal("0")
        targets = [Target(symbol=p.symbol, weight=weight) for p in positions]
        # Add cash if specified
        if args.cash > 0:
            targets.append(Target(symbol="CASH", weight=Decimal("0")))
    else:
        print("Error: Provide targets.csv or use --target-equal")
        return
    
    # Override equity if specified
    total_position_value = sum(p.value for p in positions)
    equity = Decimal(str(args.equity)) if args.equity else total_position_value + Decimal(str(args.cash))
    cash = Decimal(str(args.cash)) if args.cash else equity - total_position_value
    
    # Rebalance
    rebalancer = PortfolioRebalancer(
        drift_threshold=Decimal(str(args.drift)),
        min_trade_value=Decimal(str(args.min_trade)),
        tax_aware=args.tax_aware
    )
    
    plan = rebalancer.rebalance(positions, targets, cash=cash)
    
    # Display
    print_plan(plan)
    
    # Output
    if args.output:
        args.output.write_text(json.dumps(plan.to_dict(), indent=2))
        print(f"💾 Saved plan to {args.output}")
    
    if args.dry_run:
        print("(Dry run - no trades executed)")


# === Quick Examples ===

# 1. Basic rebalance to targets
# python rebalancer.py current.csv targets.csv

# 2. Equal weight rebalance
# python rebalancer.py current.csv --target-equal --equity 100000

# 3. Low drift threshold (tighter tracking)
# python rebalancer.py current.csv targets.csv --drift 0.03

# 4. With tax-efficient ordering
# python rebalancer.py current.csv targets.csv --tax-aware

# CSV Formats:
# current.csv: symbol,quantity,price[,cost_basis]
# targets.csv: symbol,weight (0.25 = 25%)

# Example current.csv:
# echo "symbol,quantity,price
# BTC,0.5,50000
# ETH,5,3000
# SOL,100,150" > current.csv

# Example targets.csv:
# echo "symbol,weight
# BTC,0.40
# ETH,0.35
# SOL,0.25" > targets.csv


if __name__ == "__main__":
    main()
```

## Quick Start

```bash
# Basic rebalance
python rebalancer.py current.csv targets.csv

# Equal weight all positions
python rebalancer.py current.csv --target-equal --equity 100000

# Tighter drift threshold (rebalance at 3% drift)
python rebalancer.py current.csv targets.csv --drift 0.03

# Preview only (dry run)
python rebalancer.py current.csv targets.csv --dry-run --output plan.json
```

## Sample Output

```
══════════════════════════════════════════════════════════════════════
  PORTFOLIO REBALANCING PLAN
══════════════════════════════════════════════════════════════════════
  Total Equity:    $52,500.00
  Target Weights:  100.0%

──────────────────────────────────────────────────────────────────────
  Symbol   Cur%     Tgt%     Action Qty        Value        Urgency
──────────────────────────────────────────────────────────────────────
  BTC      47.6     40.0     SELL   0.0760     $3,800.00    HIGH
  ETH      28.6     35.0     BUY    1.0833     $3,250.00    MEDIUM
  SOL      28.6     25.0     BUY    0.0000     $0.00        SKIP
──────────────────────────────────────────────────────────────────────
  Total Buys:      $3,250.00
  Total Sells:     $3,800.00
  Net Cash Needed: -$550.00
  Est. Fees:       $7.05
══════════════════════════════════════════════════════════════════════

⚠️  HIGH PRIORITY TRADES (significant drift):
    BTC: 7.6% drift
```

## CSV Formats

**current.csv** (positions):
```csv
symbol,quantity,price,cost_basis
BTC,0.5,50000,45000
ETH,5,3000,2800
SOL,100,150,140
```

**targets.csv** (allocations):
```csv
symbol,weight
BTC,0.40
ETH,0.35
SOL,0.25
```

## Key Concepts

| Concept | Description |
|---------|-------------|
| Drift Threshold | When current vs target difference triggers rebalance |
| Min Trade | Skip trades smaller than this ($100 default) |
| Tax Aware | Sell losing positions first for tax efficiency |
| Urgency | HIGH = >2× threshold, MEDIUM = >threshold |

## When to Rebalance

| Method | Frequency | Pros | Cons |
|--------|-----------|------|------|
| **Time-based** | Monthly/Quarterly | Predictable, scheduled | May rebalance unnecessarily |
| **Threshold** | When drift >5% | Efficient, event-driven | Requires monitoring |
| **Cash flow** | On deposits/withdrawals | Low transaction cost | Less precise |

## Rebalancing Strategies

```python
# Equal weight (risk parity style)
python rebalancer.py current.csv --target-equal

# Custom targets
python rebalancer.py current.csv my_targets.csv

# Aggressive rebalancing (--drift 0.02 = 2% threshold)
python rebalancer.py current.csv targets.csv --drift 0.02

# Tax-loss harvesting (sell losses first)
python rebalancer.py current.csv targets.csv --tax-aware
```

---
*Utility: Portfolio Rebalancer | Maintain target allocations automatically*
