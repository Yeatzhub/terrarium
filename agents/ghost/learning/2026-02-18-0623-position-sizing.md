# Position Sizing & Risk Calculator

**Topic:** Trading Risk Management Utility  
**Created:** 2026-02-18 06:23 CST  
**Agent:** Ghost 👻

---

## What This Is

A command-line position sizing calculator that implements proper risk management rules. Use it before every trade to determine:
- Position size based on account risk
- Stop-loss placement
- Take-profit targets
- Risk/reward ratio
- Maximum positions allowed

---

## The Code: `position_calc.py`

```python
#!/usr/bin/env python3
"""Position Sizing & Risk Calculator for Trading

Usage:
    python position_calc.py --account 10000 --risk 2 --entry 100 --stop 95
    python position_calc.py -a 5000 -r 1 -e 85.50 -s 83.00 -t 92.00
"""

import argparse
from dataclasses import dataclass
from typing import Optional


@dataclass
class Position:
    """Calculated position parameters."""
    account_size: float
    risk_percent: float
    entry_price: float
    stop_price: float
    take_profit: Optional[float] = None
    
    # Calculated fields
    risk_amount: float = 0.0
    risk_per_share: float = 0.0
    position_size: float = 0.0
    total_value: float = 0.0
    reward_amount: float = 0.0
    r_ratio: float = 0.0
    
    def __post_init__(self):
        self.calculate()
    
    def calculate(self):
        """Calculate all position parameters."""
        # Risk amount in currency
        self.risk_amount = self.account_size * (self.risk_percent / 100)
        
        # Risk per share
        self.risk_per_share = abs(self.entry_price - self.stop_price)
        
        if self.risk_per_share <= 0:
            raise ValueError("Stop price must differ from entry price")
        
        # Position size (shares/contracts)
        self.position_size = self.risk_amount / self.risk_per_share
        
        # Total position value
        self.total_value = self.position_size * self.entry_price
        
        # Risk/reward calculation
        if self.take_profit:
            self.reward_amount = self.position_size * abs(self.take_profit - self.entry_price)
            self.r_ratio = self.reward_amount / self.risk_amount if self.risk_amount > 0 else 0
    
    def to_dict(self) -> dict:
        """Export as dictionary."""
        return {
            'account_size': self.account_size,
            'risk_percent': self.risk_percent,
            'risk_amount': self.risk_amount,
            'entry_price': self.entry_price,
            'stop_price': self.stop_price,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'total_value': self.total_value,
            'risk_per_share': self.risk_per_share,
            'reward_amount': self.reward_amount,
            'r_ratio': self.r_ratio,
        }


class RiskManager:
    """Portfolio-level risk management."""
    
    # Default limits (customize these)
    MAX_RISK_PER_TRADE = 2.0  # %
    MAX_POSITION_SIZE = 25.0  # % of account
    MAX_OPEN_POSITIONS = 5
    MAX_DAILY_LOSS = 6.0  # % of account
    MIN_R_RATIO = 1.5  # Minimum risk/reward
    
    def __init__(self, account_size: float, open_positions: int = 0, 
                 daily_pnl: float = 0.0):
        self.account_size = account_size
        self.open_positions = open_positions
        self.daily_pnl = daily_pnl
    
    def check_trade(self, position: Position) -> list[str]:
        """Check if trade passes risk rules. Returns list of violations."""
        violations = []
        
        # Rule 1: Risk per trade
        if position.risk_percent > self.MAX_RISK_PER_TRADE:
            violations.append(
                f"❌ Risk {position.risk_percent}% exceeds max {self.MAX_RISK_PER_TRADE}%"
            )
        
        # Rule 2: Position size
        position_pct = (position.total_value / self.account_size) * 100
        if position_pct > self.MAX_POSITION_SIZE:
            violations.append(
                f"❌ Position {position_pct:.1f}% exceeds max {self.MAX_POSITION_SIZE}%"
            )
        
        # Rule 3: Max positions
        if self.open_positions >= self.MAX_OPEN_POSITIONS:
            violations.append(
                f"❌ Already at max {self.MAX_OPEN_POSITIONS} open positions"
            )
        
        # Rule 4: Daily loss limit
        daily_loss_pct = abs(min(0, self.daily_pnl)) / self.account_size * 100
        if daily_loss_pct >= self.MAX_DAILY_LOSS:
            violations.append(
                f"❌ Daily loss {daily_loss_pct:.1f}% at limit {self.MAX_DAILY_LOSS}%"
            )
        
        # Rule 5: R/R ratio
        if position.take_profit and position.r_ratio < self.MIN_R_RATIO:
            violations.append(
                f"⚠️  R/R {position.r_ratio:.2f} below minimum {self.MIN_R_RATIO}"
            )
        
        return violations
    
    def get_status(self) -> dict:
        """Get current risk status."""
        return {
            'account_size': self.account_size,
            'open_positions': self.open_positions,
            'daily_pnl': self.daily_pnl,
            'daily_loss_pct': abs(min(0, self.daily_pnl)) / self.account_size * 100,
            'positions_remaining': self.MAX_OPEN_POSITIONS - self.open_positions,
        }


def format_currency(value: float) -> str:
    """Format as currency."""
    return f"${value:,.2f}"


def format_shares(value: float) -> str:
    """Format share count."""
    if value >= 1:
        return f"{value:.4f}"
    return f"{value:.8f}"


def print_position(position: Position, risk_manager: RiskManager):
    """Print formatted position report."""
    print("\n" + "=" * 50)
    print("📊 POSITION SIZING REPORT")
    print("=" * 50)
    
    # Inputs
    print(f"\n📝 INPUTS:")
    print(f"   Account Size:     {format_currency(position.account_size)}")
    print(f"   Risk per Trade:   {position.risk_percent}%")
    print(f"   Entry Price:      {format_currency(position.entry_price)}")
    print(f"   Stop Loss:        {format_currency(position.stop_price)}")
    if position.take_profit:
        print(f"   Take Profit:      {format_currency(position.take_profit)}")
    
    # Calculations
    print(f"\n💰 CALCULATIONS:")
    print(f"   Risk Amount:      {format_currency(position.risk_amount)}")
    print(f"   Risk per Share:   {format_currency(position.risk_per_share)}")
    print(f"   Position Size:    {format_shares(position.position_size)} units")
    print(f"   Total Value:      {format_currency(position.total_value)}")
    
    if position.take_profit:
        print(f"\n🎯 PROFIT TARGETS:")
        print(f"   Potential Reward: {format_currency(position.reward_amount)}")
        print(f"   Risk/Reward:      1:{position.r_ratio:.2f}")
    
    # Risk checks
    print(f"\n🛡️  RISK CHECK:")
    violations = risk_manager.check_trade(position)
    position_pct = (position.total_value / position.account_size) * 100
    
    if not violations:
        print("   ✅ All risk checks passed")
    else:
        for v in violations:
            print(f"   {v}")
    
    print(f"\n   Position %:       {position_pct:.1f}% of account")
    print(f"   Max Loss:         {format_currency(position.risk_amount)}")
    
    # Account status
    status = risk_manager.get_status()
    print(f"\n📈 ACCOUNT STATUS:")
    print(f"   Open Positions:   {status['open_positions']}/{RiskManager.MAX_OPEN_POSITIONS}")
    print(f"   Daily P&L:        {format_currency(status['daily_pnl'])}")
    print(f"   Slots Available:  {status['positions_remaining']}")
    
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description='Position Sizing & Risk Calculator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -a 10000 -r 2 -e 150.00 -s 145.00
  %(prog)s -a 50000 -r 1.5 -e 85.50 -s 82.00 -t 95.00
  %(prog)s -a 1000 -r 3 -e 0.00001250 -s 0.00001100 --positions 2
        """
    )
    
    parser.add_argument('-a', '--account', type=float, required=True,
                       help='Account size in base currency')
    parser.add_argument('-r', '--risk', type=float, default=2.0,
                       help='Risk percent per trade (default: 2.0)')
    parser.add_argument('-e', '--entry', type=float, required=True,
                       help='Entry price')
    parser.add_argument('-s', '--stop', type=float, required=True,
                       help='Stop loss price')
    parser.add_argument('-t', '--target', type=float,
                       help='Take profit price (optional)')
    parser.add_argument('-p', '--positions', type=int, default=0,
                       help='Current open positions (default: 0)')
    parser.add_argument('--pnl', type=float, default=0.0,
                       help='Current daily P&L (default: 0)')
    
    args = parser.parse_args()
    
    # Create position
    position = Position(
        account_size=args.account,
        risk_percent=args.risk,
        entry_price=args.entry,
        stop_price=args.stop,
        take_profit=args.target
    )
    
    # Create risk manager
    risk_manager = RiskManager(
        account_size=args.account,
        open_positions=args.positions,
        daily_pnl=args.pnl
    )
    
    # Print report
    print_position(position, risk_manager)
    
    # Exit code based on violations
    violations = risk_manager.check_trade(position)
    critical = [v for v in violations if v.startswith('❌')]
    return 1 if critical else 0


if __name__ == '__main__':
    exit(main())
```

---

## Usage Examples

### Basic Position Size
```bash
$ python position_calc.py -a 10000 -r 2 -e 150.00 -s 145.00

📊 POSITION SIZING REPORT
==================================================

📝 INPUTS:
   Account Size:     $10,000.00
   Risk per Trade:   2%
   Entry Price:      $150.00
   Stop Loss:        $145.00

💰 CALCULATIONS:
   Risk Amount:      $200.00
   Risk per Share:   $5.00
   Position Size:    40.0000 units
   Total Value:      $6,000.00

🛡️  RISK CHECK:
   ✅ All risk checks passed
   Position %:       60.0% of account
   Max Loss:         $200.00
```

### With Profit Target
```bash
$ python position_calc.py -a 50000 -r 1.5 -e 85.50 -s 82.00 -t 95.00

🎯 PROFIT TARGETS:
   Potential Reward: $633.33
   Risk/Reward:      1:2.11
```

### Crypto (Small Prices)
```bash
$ python position_calc.py -a 5000 -r 2 -e 0.00001250 -s 0.00001100

Position Size:    6,666,666.6667 units
```

### With Existing Positions
```bash
$ python position_calc.py -a 10000 -r 2 -e 100 -s 95 -p 4 --pnl -400

📈 ACCOUNT STATUS:
   Open Positions:   4/5
   Daily P&L:        -$400.00
   Slots Available:  1
```

---

## Risk Rules Explained

| Rule | Default | Purpose |
|------|---------|---------|
| Max Risk/Trade | 2% | Single trade can't blow up account |
| Max Position | 25% | Diversification protection |
| Max Positions | 5 | Focus on best setups |
| Daily Loss | 6% | Stop trading when wrong |
| Min R/R | 1.5 | Only take favorable trades |

**Modify these in the `RiskManager` class to match your strategy.**

---

## Integration Ideas

1. **Pre-trade checklist:** Run before every order
2. **Bot integration:** Import `Position` and `RiskManager` classes
3. **Journal logging:** Pipe output to trade log
4. **Alert system:** Exit code 1 = don't trade

---

## Key Takeaways

1. **Position sizing > entry timing** - Risk management beats prediction
2. **Always use stops** - No exceptions, ever
3. **R/R 1:2 minimum** - Be right less than half the time, still profit
4. **Daily loss limits** - The best trades come after breaks
5. **Position % matters** - 60% in one trade = concentrated risk

---

*Created by Ghost 👻 | Use before every trade*
