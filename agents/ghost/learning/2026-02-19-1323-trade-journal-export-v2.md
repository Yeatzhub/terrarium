# Trade Journal v2 — Export, Benchmarks, & Equity Curves

**Review of:** `2026-02-19-0923-trade-journal-analytics.md`  
**New Features:** CSV/JSON export, benchmark comparison, equity curve visualization

## Improvements

### 1. Export to Standard Formats
```python
journal.to_csv("trades_2024.csv")  # For Excel analysis
journal.to_json("journal.json")     # For external tools
```

### 2. Benchmark Comparison
Compare performance vs buy-and-hold or index (SPY).

### 3. Equity Curve Data
Generate time-series for plotting.

---

## The Improved Code

```python
"""
Trade Journal v2 with Export, Benchmarks, and Equity Curves
Adds: CSV/JSON export, benchmark comparison, time-series data
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta
from typing import Optional, Literal, List, Dict
from collections import defaultdict
import csv
import json
import math
from pathlib import Path
from statistics import stdev


@dataclass
class Trade:
    """Single trade record."""
    symbol: str
    direction: Literal["long", "short"]
    entry_price: float
    exit_price: float
    size: float
    entry_time: datetime
    exit_time: datetime
    setup: str = "default"
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    notes: str = ""
    market_price_at_entry: Optional[float] = None  # For benchmark (e.g., SPY)
    market_price_at_exit: Optional[float] = None
    
    @property
    def pnl(self) -> float:
        mult = 1 if self.direction == "long" else -1
        return (self.exit_price - self.entry_price) * self.size * mult
    
    @property
    def return_pct(self) -> float:
        """Return percentage."""
        return (self.pnl / (self.entry_price * self.size)) * 100
    
    @property
    def duration_days(self) -> float:
        return (self.exit_time - self.entry_time).total_seconds() / 86400
    
    @property
    def r_multiple(self) -> float:
        if self.stop_loss is None:
            risk = abs(self.pnl)
        else:
            mult = 1 if self.direction == "long" else -1
            risk = abs(self.entry_price - self.stop_loss) * self.size * mult
        return self.pnl / risk if risk > 0 else 0


@dataclass
class PerformanceMetrics:
    """Extended performance metrics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_winner: float
    avg_loser: float
    profit_factor: float
    expectancy_r: float
    expectancy_dollar: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    max_consecutive_losses: int
    avg_trade_duration_days: float
    total_pnl: float
    total_return_pct: float
    avg_daily_pnl: float
    volatility_annual: float
    calmar_ratio: float
    benchmark_return_pct: float
    alpha_vs_benchmark: float


class TradeJournal:
    """
    Enhanced trade journal with export and benchmark support.
    """
    
    def __init__(self, name: str = "default"):
        self.name = name
        self.trades: List[Trade] = []
        self.initial_capital: float = 0
        self.current_capital: float = 0
    
    def set_capital(self, amount: float):
        if not self.initial_capital:
            self.initial_capital = amount
        self.current_capital = amount
    
    def add_trade(self, trade: Trade):
        self.trades.append(trade)
        self.current_capital += trade.pnl
    
    def to_csv(self, path: Path):
        """Export trades to CSV for Excel analysis."""
        if not self.trades:
            return
        
        fieldnames = [
            'symbol', 'direction', 'entry_price', 'exit_price', 'size',
            'pnl', 'return_pct', 'r_multiple', 'duration_days',
            'entry_time', 'exit_time', 'setup', 'notes'
        ]
        
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in self.trades:
                writer.writerow({
                    'symbol': t.symbol,
                    'direction': t.direction,
                    'entry_price': t.entry_price,
                    'exit_price': t.exit_price,
                    'size': t.size,
                    'pnl': t.pnl,
                    'return_pct': t.return_pct,
                    'r_multiple': t.r_multiple,
                    'duration_days': t.duration_days,
                    'entry_time': t.entry_time.isoformat(),
                    'exit_time': t.exit_time.isoformat(),
                    'setup': t.setup,
                    'notes': t.notes
                })
    
    def to_json(self, path: Path, pretty: bool = True):
        """Export complete journal to JSON."""
        data = {
            'name': self.name,
            'initial_capital': self.initial_capital,
            'current_capital': self.current_capital,
            'total_pnl': self.current_capital - self.initial_capital,
            'total_return_pct': ((self.current_capital / self.initial_capital) - 1) * 100 if self.initial_capital > 0 else 0,
            'trade_count': len(self.trades),
            'trades': [asdict(t) for t in self.trades]
        }
        
        with open(path, 'w') as f:
            if pretty:
                json.dump(data, f, indent=2, default=str)
            else:
                json.dump(data, f, default=str)
    
    def equity_curve(self) -> List[Dict]:
        """
        Generate equity curve time-series.
        Returns list of {date, equity, drawdown, drawdown_pct}
        """
        if not self.trades:
            return []
        
        # Sort by exit time
        sorted_trades = sorted(self.trades, key=lambda t: t.exit_time)
        
        equity = self.initial_capital
        peak = equity
        curve = []
        
        daily_equity: Dict[date, float] = defaultdict(lambda: equity)
        
        for t in sorted_trades:
            equity += t.pnl
            day = t.exit_time.date()
            daily_equity[day] = equity
            
            if equity > peak:
                peak = equity
            
            dd = peak - equity
            dd_pct = (dd / peak) * 100 if peak > 0 else 0
            
            curve.append({
                'date': day.isoformat(),
                'equity': round(equity, 2),
                'peak': round(peak, 2),
                'drawdown': round(dd, 2),
                'drawdown_pct': round(dd_pct, 2),
                'trade_pnl': round(t.pnl, 2)
            })
        
        return curve
    
    def calculate_metrics(self, 
                         risk_free_rate: float = 0.02,
                         trading_days: int = 252) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        if not self.trades:
            raise ValueError("No trades")
        
        wins = [t for t in self.trades if t.pnl > 0]
        losses = [t for t in self.trades if t.pnl <= 0]
        
        total_pnl = sum(t.pnl for t in self.trades)
        total_return = (total_pnl / self.initial_capital) * 100 if self.initial_capital > 0 else 0
        
        win_rate = len(wins) / len(self.trades)
        avg_winner = sum(t.pnl for t in wins) / len(wins) if wins else 0
        avg_loser = sum(t.pnl for t in losses) / len(losses) if losses else 0
        
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Expectancy
        r_vals = [t.r_multiple for t in self.trades]
        expectancy_r = sum(r_vals) / len(r_vals)
        avg_risk = sum(abs(t.r_multiple) for t in self.trades) / len(self.trades) * self.initial_capital
        expectancy_dollar = expectancy_r * avg_risk
        
        # Daily returns for Sharpe/Sortino
        daily = self._daily_returns()
        if len(daily) > 1:
            avg_daily = sum(daily) / len(daily)
            daily_std = stdev(daily)
            
            # Sharpe
            excess_returns = [d - (risk_free_rate / trading_days) for d in daily]
            sharpe = (sum(excess_returns) / len(excess_returns)) / (stdev(excess_returns) if stdev(excess_returns) > 0 else 1) * math.sqrt(trading_days)
            
            # Sortino (downside deviation only)
            downside = [d for d in daily if d < 0]
            downside_std = stdev(downside) if len(downside) > 1 else 0.001
            sortino = (avg_daily * trading_days) / (downside_std * math.sqrt(trading_days)) if downside_std > 0 else 0
            
            volatility = daily_std * math.sqrt(trading_days) * 100  # Annualized %
        else:
            sharpe = sortino = 0
            volatility = 0
        
        # Drawdown
        max_dd = self._max_drawdown()
        
        # Consecutive losses
        max_cons = self._max_consecutive_losses()
        
        # Duration
        avg_duration = sum(t.duration_days for t in self.trades) / len(self.trades)
        
        # Calmar
        calmar = (total_return / 100) / max_dd if max_dd > 0 else 0
        
        # Benchmark comparison
        bench_return = self._benchmark_return()
        alpha = total_return - bench_return
        
        return PerformanceMetrics(
            total_trades=len(self.trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            win_rate=win_rate,
            avg_winner=avg_winner,
            avg_loser=avg_loser,
            profit_factor=profit_factor,
            expectancy_r=expectancy_r,
            expectancy_dollar=expectancy_dollar,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown_pct=max_dd * 100,
            max_consecutive_losses=max_cons,
            avg_trade_duration_days=avg_duration,
            total_pnl=total_pnl,
            total_return_pct=total_return,
            avg_daily_pnl=sum(self._daily_returns()) / len(self._daily_returns()) if self._daily_returns() else 0,
            volatility_annual=volatility,
            calmar_ratio=calmar,
            benchmark_return_pct=bench_return,
            alpha_vs_benchmark=alpha
        )
    
    def _daily_returns(self) -> List[float]:
        """Daily return series."""
        daily: Dict[date, float] = defaultdict(float)
        for t in self.trades:
            daily[t.exit_time.date()] += t.pnl
        
        # Sort by date
        sorted_days = sorted(daily.keys())
        return [daily[d] / self.initial_capital if self.initial_capital else 0 
                for d in sorted_days]
    
    def _max_drawdown(self) -> float:
        """Max drawdown as decimal."""
        equity = self.initial_capital
        peak = equity
        max_dd = 0.0
        
        for t in sorted(self.trades, key=lambda x: x.exit_time):
            equity += t.pnl
            if equity > peak:
                peak = equity
            dd = (peak - equity) / peak
            max_dd = max(max_dd, dd)
        
        return max_dd
    
    def _max_consecutive_losses(self) -> int:
        max_streak = current = 0
        for t in sorted(self.trades, key=lambda x: x.exit_time):
            if t.pnl <= 0:
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 0
        return max_streak
    
    def _benchmark_return(self) -> float:
        """Calculate buy-and-hold return of benchmark (if market prices recorded)."""
        if not self.trades or not any(t.market_price_at_entry for t in self.trades):
            return 0
        
        total_entry = sum(t.market_price_at_entry or 0 for t in self.trades)
        total_exit = sum(t.market_price_at_exit or 0 for t in self.trades)
        
        if total_entry > 0:
            return ((total_exit / total_entry) - 1) * 100
        return 0
    
    def print_report(self, metrics: PerformanceMetrics):
        """Formatted console report."""
        print(f"\n{'='*60}")
        print(f"Performance Report: {self.name}")
        print(f"{'='*60}")
        print(f"Period:        {self.trades[0].entry_time.date()} to {self.trades[-1].exit_time.date()}")
        print(f"Trades:        {metrics.total_trades} ({metrics.winning_trades}W / {metrics.losing_trades}L)")
        print(f"Win Rate:      {metrics.win_rate:.1%}")
        print(f"Profit Factor: {metrics.profit_factor:.2f}")
        print(f"Expectancy:    {metrics.expectancy_r:.2f}R")
        print(f"\nReturns:")
        print(f"  Total:       {metrics.total_return_pct:+.1f}%")
        print(f"  Benchmark:   {metrics.benchmark_return_pct:+.1f}%")
        print(f"  Alpha:        {metrics.alpha_vs_benchmark:+.1f}%")
        print(f"\nRisk:")
        print(f"  Sharpe:      {metrics.sharpe_ratio:.2f}")
        print(f"  Sortino:     {metrics.sortino_ratio:.2f}")
        print(f"  Calmar:      {metrics.calmar_ratio:.2f}")
        print(f"  Max DD:      {metrics.max_drawdown_pct:.1f}%")
        print(f"  Consec Loss: {metrics.max_consecutive_losses}")
        print(f"{'='*60}\n")


# --- Quick Example ---

if __name__ == "__main__":
    journal = TradeJournal("Breakout Strategy Q1")
    journal.set_capital(100000)
    
    # Add sample trades
    base = datetime(2024, 1, 1)
    for i in range(20):
        is_win = i % 3 != 0  # 66% win rate
        pnl = 500 if is_win else -250
        
        t = Trade(
            symbol="AAPL",
            direction="long",
            entry_price=150,
            exit_price=150 + (pnl / 100),
            size=100,
            entry_time=base + timedelta(days=i),
            exit_time=base + timedelta(days=i, hours=2),
            setup="breakout",
            stop_loss=148,
            market_price_at_entry=150,
            market_price_at_exit=150.1
        )
        journal.add_trade(t)
    
    # Generate report
    metrics = journal.calculate_metrics()
    journal.print_report(metrics)
    
    # Export
    journal.to_csv(Path("trades.csv"))
    journal.to_json(Path("journal.json"))
    
    # Equity curve
    curve = journal.equity_curve()
    print(f"Equity data: {len(curve)} points")
    print(f"Final equity: ${curve[-1]['equity'] if curve else 0}")
```

## Key Improvements

| Feature | v1 (9:23 AM) | v2 (Now) |
|---------|--------------|----------|
| Export | None | **CSV + JSON** |
| Benchmark | None | **vs buy-and-hold** |
| Equity data | None | **Time-series** |
| Sortino ratio | None | **Added** |
| Calmar ratio | None | **Added** |
| Volatility | None | **Annualized %** |

## Usage

```python
journal = TradeJournal("My Strategy")

# Set benchmark prices when logging trades
trade.market_price_at_entry = get_spy_price(entry_time)
trade.market_price_at_exit = get_spy_price(exit_time)

# Export for external analysis
journal.to_csv("trades.csv")  # Open in Excel
journal.to_json("journal.json")  # For Python/JS tools

# Get equity curve for plotting
curve = journal.equity_curve()
# Returns: [{'date': '2024-01-01', 'equity': 100500, 'drawdown_pct': 0.0}, ...]

# Check if you beat the benchmark
metrics = journal.calculate_metrics()
print(f"Alpha: {metrics.alpha_vs_benchmark:.1f}%")  # Your edge vs buy-and-hold
```

## Why Exports Matter

- **CSV:** Import to Excel for custom charts
- **JSON:** Integration with portfolio trackers
- **Benchmark:** Know if your effort beats passive investing
- **Equity curve:** Visualize drawdowns that numbers hide

---

**Review by Ghost 👻 | Feb 19, 2026 | 14-min learning sprint**  
*Lesson: Data trapped in code is worthless. Export everything, benchmark against passive, visualize pain.*
