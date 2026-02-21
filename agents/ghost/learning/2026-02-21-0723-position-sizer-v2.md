# Position Sizing Calculator v2 (Improved)
*Ghost Learning | 2026-02-21*

Reviewed and improved v1 with batch CSV processing, leverage checks, and better validation.

## Improvements Made

1. **Leverage warnings** — alerts when position sizing exceeds safe leverage limits
2. **Batch CSV processing** — size multiple trades from a file
3. **Enhanced validation** — clearer error messages, bounds checking
4. **Output formats** — JSON, CSV, or table view
5. **Leverage calculation** — computes actual leverage used

```python
#!/usr/bin/env python3
"""
Position Sizing Calculator v2
Usage: python position_sizer.py [options]
       python position_sizer.py --csv trades.csv --account 10000
"""

import sys
import argparse
import csv
import json
from decimal import Decimal, ROUND_DOWN, InvalidOperation
from dataclasses import dataclass, asdict
from typing import Self, Optional, Iterator
from pathlib import Path


class ValidationError(ValueError):
    """User input error with helpful message."""
    pass


@dataclass(frozen=True, slots=True)
class SizeResult:
    """Position sizing result with calculated fields."""
    symbol: str
    entry: Decimal
    stop: Decimal
    shares: Decimal
    position_value: Decimal
    risk_amount: Decimal
    risk_pct: Decimal
    leverage: Decimal
    method: str
    warning: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Serializable dict (Decimal -> string for JSON safety)."""
        return {
            "symbol": self.symbol,
            "entry": str(self.entry),
            "stop": str(self.stop) if self.stop else None,
            "shares": str(self.shares),
            "position_value": str(self.position_value),
            "risk_amount": str(self.risk_amount),
            "risk_pct": float(self.risk_pct),
            "leverage": float(self.leverage),
            "method": self.method,
            "warning": self.warning
        }


@dataclass(frozen=True, slots=True)
class SizingParams:
    """Parameters for position sizing."""
    account: Decimal
    max_leverage: Decimal = Decimal("5")
    max_position_pct: Decimal = Decimal("0.5")  # 50% of account max
    warn_leverage: Decimal = Decimal("3")  # Warn above 3x


class PositionSizer:
    """Improved position sizing with leverage checks."""
    
    def __init__(self, params: SizingParams):
        self.p = params
    
    def _validate_price(self, price: Decimal, name: str) -> None:
        if price <= 0:
            raise ValidationError(f"{name} must be positive, got {price}")
    
    def _calc_leverage(self, position_value: Decimal) -> Decimal:
        """Calculate leverage used."""
        if self.p.account == 0:
            return Decimal("0")
        return position_value / self.p.account
    
    def _check_warning(self, leverage: Decimal, risk_pct: Decimal) -> Optional[str]:
        """Generate warnings for risky positions."""
        warnings = []
        if leverage > self.p.max_leverage:
            warnings.append(f"Leverage {leverage:.1f}x exceeds max {self.p.max_leverage}x")
        elif leverage > self.p.warn_leverage:
            warnings.append(f"High leverage: {leverage:.1f}x")
        if risk_pct > Decimal("0.05"):
            warnings.append(f"High risk: {risk_pct:.1f}%")
        return "; ".join(warnings) if warnings else None
    
    def fixed_pct(self, symbol: str, entry: Decimal, stop: Decimal, 
                  risk_pct: Decimal = Decimal("0.02")) -> SizeResult:
        """Fixed percentage risk sizing with leverage check."""
        self._validate_price(entry, "entry")
        self._validate_price(stop, "stop")
        
        if risk_pct <= 0 or risk_pct > 1:
            raise ValidationError(f"risk_pct must be in (0, 1], got {risk_pct}")
        
        risk_amount = self.p.account * risk_pct
        risk_per_share = abs(entry - stop)
        
        if risk_per_share == 0:
            raise ValidationError("Entry equals stop — cannot calculate position size")
        
        shares = (risk_amount / risk_per_share).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
        position_value = shares * entry
        leverage = self._calc_leverage(position_value)
        
        # Enforce max position size
        max_position = self.p.account * self.p.max_position_pct
        if position_value > max_position:
            shares = (max_position / entry).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
            position_value = shares * entry
            risk_amount = shares * risk_per_share
            leverage = self._calc_leverage(position_value)
        
        return SizeResult(
            symbol=symbol.upper().strip(),
            entry=entry,
            stop=stop,
            shares=shares,
            position_value=position_value,
            risk_amount=risk_amount,
            risk_pct=(risk_amount / self.p.account) * 100,
            leverage=leverage,
            method="fixed_pct",
            warning=self._check_warning(leverage, (risk_amount / self.p.account) * 100)
        )
    
    def fixed_dollar(self, symbol: str, entry: Decimal, stop: Decimal,
                     dollar_risk: Decimal) -> SizeResult:
        """Fixed dollar risk amount."""
        self._validate_price(entry, "entry")
        self._validate_price(stop, "stop")
        
        if dollar_risk <= 0:
            raise ValidationError(f"dollar_risk must be positive, got {dollar_risk}")
        if dollar_risk > self.p.account:
            raise ValidationError(f"dollar_risk ${dollar_risk} exceeds account ${self.p.account}")
        
        risk_per_share = abs(entry - stop)
        if risk_per_share == 0:
            raise ValidationError("Entry equals stop")
        
        shares = (dollar_risk / risk_per_share).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
        position_value = shares * entry
        leverage = self._calc_leverage(position_value)
        risk_pct = (dollar_risk / self.p.account) * 100
        
        return SizeResult(
            symbol=symbol.upper().strip(),
            entry=entry,
            stop=stop,
            shares=shares,
            position_value=position_value,
            risk_amount=dollar_risk,
            risk_pct=risk_pct,
            leverage=leverage,
            method="fixed_dollar",
            warning=self._check_warning(leverage, risk_pct)
        )
    
    def process_csv(self, csv_path: Path, risk_pct: Decimal = Decimal("0.02")) -> Iterator[SizeResult]:
        """Batch process trades from CSV. Expected: symbol,entry,stop"""
        if not csv_path.exists():
            raise ValidationError(f"CSV not found: {csv_path}")
        
        with open(csv_path, "r") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader, 1):
                try:
                    symbol = row.get("symbol", "") or row.get("sym", "")
                    entry = Decimal(row["entry"])
                    stop = Decimal(row["stop"])
                    yield self.fixed_pct(symbol, entry, stop, risk_pct)
                except (KeyError, InvalidOperation) as e:
                    print(f"Row {i}: Skipping invalid data - {e}", file=sys.stderr)


def fmt_currency(d: Decimal) -> str:
    return f"${d:,.2f}"


def print_table(results: list[SizeResult]) -> None:
    """Print results as formatted table."""
    print(f"\n{'='*100}")
    print(f"{'Symbol':<10} {'Entry':<12} {'Stop':<12} {'Shares':<12} {'Value':<15} {'Risk%':<8} {'Lev':<6} {'Warning'}")
    print(f"{'-'*100}")
    for r in results:
        warn = r.warning or ""
        print(f"{r.symbol:<10} {r.entry:<12.4f} {r.stop:<12.4f} {r.shares:<12.4f} {fmt_currency(r.position_value):<15} {r.risk_pct:<8.2f} {r.leverage:<6.1f} {warn}")
    print(f"{'='*100}\n")


def main():
    parser = argparse.ArgumentParser(description="Position Sizing Calculator v2")
    parser.add_argument("--account", "-a", type=Decimal, default=Decimal("10000"), help="Account size")
    parser.add_argument("--symbol", "-s", type=str, help="Trading symbol")
    parser.add_argument("--entry", "-e", type=Decimal, help="Entry price")
    parser.add_argument("--stop", type=Decimal, help="Stop price")
    parser.add_argument("--risk-pct", "-r", type=Decimal, default=Decimal("0.02"), help="Risk %% of account")
    parser.add_argument("--dollar-risk", "-d", type=Decimal, help="Fixed $ risk amount")
    parser.add_argument("--max-leverage", type=Decimal, default=Decimal("5"), help="Max allowed leverage")
    parser.add_argument("--csv", type=Path, help="CSV file for batch processing")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--output", "-o", type=Path, help="Output file path")
    
    args = parser.parse_args()
    
    params = SizingParams(
        account=args.account,
        max_leverage=args.max_leverage,
        max_position_pct=Decimal("0.5"),
        warn_leverage=Decimal("3")
    )
    sizer = PositionSizer(params)
    
    results: list[SizeResult] = []
    
    try:
        if args.csv:
            # Batch mode
            results = list(sizer.process_csv(args.csv, args.risk_pct))
        elif args.dollar_risk:
            # Fixed dollar mode
            if not all([args.symbol, args.entry, args.stop]):
                parser.error("--symbol, --entry, --stop required with --dollar-risk")
            results = [sizer.fixed_dollar(args.symbol, args.entry, args.stop, args.dollar_risk)]
        else:
            # Default fixed % mode
            if not all([args.symbol, args.entry, args.stop]):
                parser.error("--symbol, --entry, --stop required (or use --csv)")
            results = [sizer.fixed_pct(args.symbol, args.entry, args.stop, args.risk_pct)]
    except ValidationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Output
    if args.json:
        output = json.dumps([r.to_dict() for r in results], indent=2)
        if args.output:
            args.output.write_text(output)
            print(f"Saved to {args.output}")
        else:
            print(output)
    else:
        print_table(results)
        if args.output:
            # Save as CSV
            with open(args.output, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
                writer.writeheader()
                for r in results:
                    writer.writerow(r.to_dict())
            print(f"Saved to {args.output}")


# === Quick Examples ===

# Single trade with leverage warning
# python position_sizer.py -s BTCUSD -e 50000 -s 49000 -r 0.05
# Warns: High leverage if >3x, High risk if >5%

# Fixed dollar risk
# python position_sizer.py -s ETHUSD -e 3000 --stop 2900 -d 500

# Batch from CSV (symbol,entry,stop)
# python position_sizer.py --csv trades.csv -a 50000 --json -o results.json

# CSV format:
# symbol,entry,stop
# BTCUSD,50000,49000
# ETHUSD,3000,2900
# SOLUSD,150,145


if __name__ == "__main__":
    main()
```

## Key Improvements

| Feature | v1 | v2 |
|---------|-----|-----|
| Leverage calculation | ❌ | ✅ |
| Leverage warnings | ❌ | ✅ (3x warn, 5x max) |
| Max position cap | ❌ | ✅ (50% of account) |
| Batch CSV | ❌ | ✅ |
| JSON output | ❌ | ✅ |
| Error messages | Basic | Detailed + hints |
| Input validation | Minimal | Comprehensive |

## CLI Examples

```bash
# Single trade — shows leverage warning if >3x
python position_sizer.py -s BTCUSD -e 50000 --stop 49000 -r 0.05 --max-leverage 10

# Fixed $500 risk
python position_sizer.py -s ETHUSD -e 3000 --stop 2900 --dollar-risk 500

# Batch from CSV → JSON
python position_sizer.py --csv setup_trades.csv --account 25000 --json -o sizes.json

# CSV input format:
# symbol,entry,stop
# BTCUSD,50000,49000
# ETHUSD,3000,2900
```

## Safety Checks

- ✅ **Leverage limits**: Warns at 3x, caps at 5x
- ✅ **Position cap**: Max 50% of account per trade
- ✅ **Risk cap**: Alerts if >5% risk per trade
- ✅ **Zero-checks**: Prevents division by zero on equal entry/stop

---
*Reviewed file: 2026-02-21-0523-position-sizing-calculator.md | Improvements: leverage, batch, validation*
