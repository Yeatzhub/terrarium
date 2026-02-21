# Performance Report Generator

**Purpose:** Generate comprehensive trading performance reports from trade data  
**Use Case:** Track metrics, review strategy performance, share with investors/stakeholders

## The Code

```python
"""
Performance Report Generator
Create comprehensive trading reports with metrics, statistics,
and analysis from trade history data.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Callable
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import math


@dataclass
class Trade:
    """Single trade record."""
    id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    entry_date: datetime
    exit_date: datetime
    entry_price: float
    exit_price: float
    quantity: float
    
    # Optional
    strategy: str = ""
    setup_type: str = ""
    stop_price: Optional[float] = None
    target_price: Optional[float] = None
    commission: float = 0.0
    
    @property
    def pnl(self) -> float:
        """Calculate P&L."""
        gross = (self.exit_price - self.entry_price) * self.quantity
        if self.side == 'sell':
            gross = -gross
        return gross - self.commission
    
    @property
    def pnl_pct(self) -> float:
        """Calculate P&L as percentage of entry."""
        if self.entry_price == 0:
            return 0.0
        return (self.pnl / (self.entry_price * self.quantity)) * 100
    
    @property
    def duration_days(self) -> int:
        """Days held."""
        return (self.exit_date - self.entry_date).days
    
    @property
    def is_win(self) -> bool:
        return self.pnl > 0
    
    @property
    def is_loss(self) -> bool:
        return self.pnl < 0


@dataclass
class PerformanceMetrics:
    """Key performance indicators."""
    # Basic stats
    total_trades: int
    winning_trades: int
    losing_trades: int
    break_even_trades: int
    
    # P&L
    gross_profit: float
    gross_loss: float
    net_profit: float
    
    # Percentages
    win_rate: float
    loss_rate: float
    
    # Average P&L
    avg_win: float
    avg_loss: float
    avg_trade: float
    
    # Ratios
    profit_factor: float
    win_loss_ratio: float
    expectancy: float
    
    # Risk-adjusted returns
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    calmar_ratio: Optional[float]
    
    # Drawdown
    max_drawdown_pct: float
    max_drawdown_dollars: float
    
    # Consistency
    consecutive_wins: int
    consecutive_losses: int
    
    # Time
    avg_trade_duration_days: float
    total_trading_days: int


@dataclass
class PeriodPerformance:
    """Performance for a specific time period."""
    period_name: str  # "2024-01" or "Week 5"
    start_date: datetime
    end_date: datetime
    
    trades: List[Trade]
    metrics: PerformanceMetrics
    
    # Daily breakdown
    daily_pnls: Dict[datetime, float]
    
    @property
    def daily_volatility(self) -> float:
        if len(self.daily_pnls) < 2:
            return 0.0
        values = list(self.daily_pnls.values())
        return statistics.stdev(values)


@dataclass
class StrategyPerformance:
    """Performance broken down by strategy."""
    strategy_name: str
    trades: List[Trade]
    metrics: PerformanceMetrics
    
    # Symbol breakdown for this strategy
    symbol_performance: Dict[str, PerformanceMetrics]


@dataclass
class Report:
    """Complete performance report."""
    report_period: str
    generated_at: datetime
    
    # Overall
    overall_metrics: PerformanceMetrics
    trades: List[Trade]
    equity_curve: List[Tuple[datetime, float]]
    
    # Breakdowns
    daily_performance: Dict[datetime, float]
    weekly_performance: List[PeriodPerformance]
    monthly_performance: List[PeriodPerformance]
    strategy_performance: List[StrategyPerformance]
    symbol_performance: Dict[str, PerformanceMetrics]
    
    # Analysis
    best_trade: Optional[Trade]
    worst_trade: Optional[Trade]
    best_day: Tuple[datetime, float]
    worst_day: Tuple[datetime, float]


class PerformanceCalculator:
    """Calculate metrics from trade list."""
    
    @staticmethod
    def calculate_metrics(trades: List[Trade]) -> PerformanceMetrics:
        """Calculate all metrics from trade list."""
        if not trades:
            return PerformanceMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
        
        # Basic counts
        total = len(trades)
        wins = [t for t in trades if t.is_win]
        losses = [t for t in trades if t.is_loss]
        break_even = [t for t in trades if t.pnl == 0]
        
        # P&L
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = sum(t.pnl for t in losses)
        net_profit = gross_profit + gross_loss
        
        # Rates
        win_rate = len(wins) / total * 100 if total > 0 else 0
        loss_rate = len(losses) / total * 100 if total > 0 else 0
        
        # Averages
        avg_win = gross_profit / len(wins) if wins else 0
        avg_loss = gross_loss / len(losses) if losses else 0
        avg_trade = net_profit / total if total > 0 else 0
        
        # Ratios
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else 0
        win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0
        expectancy = (win_rate / 100 * avg_win) - (loss_rate / 100 * abs(avg_loss))
        
        # Consecutive
        max_consec_wins = max_consec_losses = 0
        current_consec = 0
        current_is_win = None
        
        for t in sorted(trades, key=lambda x: x.exit_date):
            if t.is_win:
                if current_is_win:
                    current_consec += 1
                else:
                    current_is_win = True
                    current_consec = 1
            elif t.is_loss:
                if current_is_win == False:
                    current_consec += 1
                else:
                    current_is_win = False
                    current_consec = 1
            
            max_consec_wins = max(max_consec_wins, current_consec if current_is_win else 0)
            max_consec_losses = max(max_consec_losses, current_consec if not current_is_win else 0)
        
        # Duration
        durations = [t.duration_days for t in trades]
        avg_duration = statistics.mean(durations) if durations else 0
        
        # Total trading days
        unique_days = set()
        for t in trades:
            unique_days.add(t.exit_date.date())
        
        # Drawdown (simplified)
        equity = 0
        peak = 0
        max_dd_pct = 0
        max_dd_dollars = 0
        
        sorted_trades = sorted(trades, key=lambda x: x.exit_date)
        for t in sorted_trades:
            equity += t.pnl
            if equity > peak:
                peak = equity
            
            dd = peak - equity
            if dd > max_dd_dollars:
                max_dd_dollars = dd
                if peak > 0:
                    dd_pct = dd / peak * 100
                    max_dd_pct = max(max_dd_pct, dd_pct)
        
        # Risk-adjusted (simplified - would need returns)
        sharpe = sortino = calmar = None
        
        return PerformanceMetrics(
            total_trades=total,
            winning_trades=len(wins),
            losing_trades=len(losses),
            break_even_trades=len(break_even),
            gross_profit=gross_profit,
            gross_loss=gross_loss,
            net_profit=net_profit,
            win_rate=win_rate,
            loss_rate=loss_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_trade=avg_trade,
            profit_factor=profit_factor,
            win_loss_ratio=win_loss_ratio,
            expectancy=expectancy,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            calmar_ratio=calmar,
            max_drawdown_pct=max_dd_pct,
            max_drawdown_dollars=max_dd_dollars,
            consecutive_wins=max_consec_wins,
            consecutive_losses=max_consec_losses,
            avg_trade_duration_days=avg_duration,
            total_trading_days=len(unique_days)
        )


class ReportGenerator:
    """Generate performance reports."""
    
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.calculator = PerformanceCalculator()
    
    def generate_report(
        self,
        trades: List[Trade],
        period_name: str = "All Periods"
    ) -> Report:
        """Generate full report."""
        overall = self.calculator.calculate_metrics(trades)
        
        # Equity curve
        equity_curve = self._calculate_equity_curve(trades)
        
        # Daily P&L
        daily = self._calculate_daily_pnls(trades)
        
        # Breakdowns
        weekly = self._get_weekly_performance(trades)
        monthly = self._get_monthly_performance(trades)
        strategy_breakdown = self._get_strategy_performance(trades)
        symbol_breakdown = self._get_symbol_performance(trades)
        
        # Best/worst
        best = max(trades, key=lambda t: t.pnl) if trades else None
        worst = min(trades, key=lambda t: t.pnl) if trades else None
        best_day = max(daily.items(), key=lambda x: x[1]) if daily else (datetime.now(), 0)
        worst_day = min(daily.items(), key=lambda x: x[1]) if daily else (datetime.now(), 0)
        
        return Report(
            report_period=period_name,
            generated_at=datetime.now(),
            overall_metrics=overall,
            trades=trades,
            equity_curve=equity_curve,
            daily_performance=daily,
            weekly_performance=weekly,
            monthly_performance=monthly,
            strategy_performance=strategy_breakdown,
            symbol_performance=symbol_breakdown,
            best_trade=best,
            worst_trade=worst,
            best_day=best_day,
            worst_day=worst_day
        )
    
    def _calculate_equity_curve(self, trades: List[Trade]) -> List[Tuple[datetime, float]]:
        """Calculate equity over time."""
        equity = self.initial_capital
        curve = [(trades[0].entry_date if trades else datetime.now(), equity)]
        
        for t in sorted(trades, key=lambda x: x.exit_date):
            equity += t.pnl
            curve.append((t.exit_date, equity))
        
        return curve
    
    def _calculate_daily_pnls(self, trades: List[Trade]) -> Dict[datetime, float]:
        """Group P&L by day."""
        daily = defaultdict(float)
        for t in trades:
            day = t.exit_date.replace(hour=0, minute=0, second=0, microsecond=0)
            daily[day] += t.pnl
        return dict(daily)
    
    def _get_weekly_performance(self, trades: List[Trade]) -> List[PeriodPerformance]:
        """Get weekly breakdown."""
        weeks = defaultdict(list)
        for t in trades:
            year, week_num, _ = t.exit_date.isocalendar()
            key = f"{year}-W{week_num:02d}"
            weeks[key].append(t)
        
        periods = []
        for week_key, week_trades in sorted(weeks.items()):
            metrics = self.calculator.calculate_metrics(week_trades)
            daily = self._calculate_daily_pnls(week_trades)
            start = min(t.entry_date for t in week_trades)
            end = max(t.exit_date for t in week_trades)
            
            periods.append(PeriodPerformance(
                period_name=week_key,
                start_date=start,
                end_date=end,
                trades=week_trades,
                metrics=metrics,
                daily_pnls=daily
            ))
        
        return periods
    
    def _get_monthly_performance(self, trades: List[Trade]) -> List[PeriodPerformance]:
        """Get monthly breakdown."""
        months = defaultdict(list)
        for t in trades:
            key = t.exit_date.strftime("%Y-%m")
            months[key].append(t)
        
        periods = []
        for month_key, month_trades in sorted(months.items()):
            metrics = self.calculator.calculate_metrics(month_trades)
            daily = self._calculate_daily_pnls(month_trades)
            start = min(t.entry_date for t in month_trades)
            end = max(t.exit_date for t in month_trades)
            
            periods.append(PeriodPerformance(
                period_name=month_key,
                start_date=start,
                end_date=end,
                trades=month_trades,
                metrics=metrics,
                daily_pnls=daily
            ))
        
        return periods
    
    def _get_strategy_performance(self, trades: List[Trade]) -> List[StrategyPerformance]:
        """Get performance by strategy."""
        by_strategy = defaultdict(list)
        for t in trades:
            key = t.strategy or "Unknown"
            by_strategy[key].append(t)
        
        results = []
        for strategy, strat_trades in by_strategy.items():
            metrics = self.calculator.calculate_metrics(strat_trades)
            
            # Symbol breakdown
            symbol_metrics = {}
            by_symbol = defaultdict(list)
            for t in strat_trades:
                by_symbol[t.symbol].append(t)
            for sym, sym_trades in by_symbol.items():
                symbol_metrics[sym] = self.calculator.calculate_metrics(sym_trades)
            
            results.append(StrategyPerformance(
                strategy_name=strategy,
                trades=strat_trades,
                metrics=metrics,
                symbol_performance=symbol_metrics
            ))
        
        return results
    
    def _get_symbol_performance(self, trades: List[Trade]) -> Dict[str, PerformanceMetrics]:
        """Get performance by symbol."""
        by_symbol = defaultdict(list)
        for t in trades:
            by_symbol[t.symbol].append(t)
        
        return {
            sym: self.calculator.calculate_metrics(sym_trades)
            for sym, sym_trades in by_symbol.items()
        }


# === Formatting Functions ===

def format_report(report: Report, include_trades: bool = False) -> str:
    """Generate formatted text report."""
    m = report.overall_metrics
    
    lines = [
        "=" * 70,
        "TRADING PERFORMANCE REPORT",
        f"Period: {report.report_period}",
        f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M')}",
        "=" * 70,
        "",
        "SUMMARY",
        "-" * 70,
        f"  Net Profit:        ${m.net_profit:+,.2f}",
        f"  Total Trades:      {m.total_trades}",
        f"  Win Rate:          {m.win_rate:.1f}%",
        f"  Profit Factor:     {m.profit_factor:.2f}",
        f"  Expectancy:        ${m.expectancy:+.2f}",
        "",
        "TRADE STATISTICS",
        "-" * 70,
        f"  Wins/Losses/BE:    {m.winning_trades}/{m.losing_trades}/{m.break_even_trades}",
        f"  Gross Profit:      ${m.gross_profit:+,.2f}",
        f"  Gross Loss:        ${m.gross_loss:-,.2f}",
        f"  Avg Win:           ${m.avg_win:+,.2f}",
        f"  Avg Loss:          ${m.avg_loss:,.2f}",
        f"  Avg Trade:         ${m.avg_trade:+,.2f}",
        f"  Win/Loss Ratio:    {m.win_loss_ratio:.2f}",
        "",
        "RISK METRICS",
        "-" * 70,
        f"  Max Drawdown:      {m.max_drawdown_pct:.1f}% (${m.max_drawdown_dollars:,.2f})",
        f"  Consec Wins:       {m.consecutive_wins}",
        f"  Consec Losses:     {m.consecutive_losses}",
        f"  Avg Duration:      {m.avg_trade_duration_days:.1f} days",
        "",
    ]
    
    # Best/worst trades
    if report.best_trade:
        lines.extend([
            "EXTREMES",
            "-" * 70,
            f"  Best Trade:    {report.best_trade.symbol} ${report.best_trade.pnl:+,}",
            f"  Worst Trade:   {report.worst_trade.symbol} ${report.worst_trade.pnl:+,}",
            f"  Best Day:      {report.best_day[0].strftime('%Y-%m-%d')} ${report.best_day[1]:+,}",
            f"  Worst Day:     {report.worst_day[0].strftime('%Y-%m-%d')} ${report.worst_day[1]:+,}",
            "",
        ])
    
    # Strategy breakdown
    if report.strategy_performance:
        lines.extend([
            "STRATEGY PERFORMANCE",
            "-" * 70,
            f"  {'Strategy':<20} {'Trades':<8} {'Win%':<8} {'Net P&L':<15} {'PF':<6}",
            "-" * 70,
        ])
        for sp in sorted(report.strategy_performance, key=lambda x: x.metrics.net_profit, reverse=True):
            m = sp.metrics
            lines.append(f"  {sp.strategy_name:<20} {m.total_trades:<8} {m.win_rate:<7.1f}% ${m.net_profit:<+14,.0f} {m.profit_factor:<6.2f}")
        lines.append("")
    
    # Symbol breakdown
    if report.symbol_performance:
        lines.extend([
            "SYMBOL PERFORMANCE (Top 10)",
            "-" * 70,
            f"  {'Symbol':<8} {'Trades':<8} {'Win%':<8} {'Net P&L':<15}",
            "-" * 70,
        ])
        sorted_symbols = sorted(report.symbol_performance.items(), key=lambda x: x[1].net_profit, reverse=True)[:10]
        for sym, m in sorted_symbols:
            lines.append(f"  {sym:<8} {m.total_trades:<8} {m.win_rate:<7.1f}% ${m.net_profit:<+14,.0f}")
        lines.append("")
    
    # Monthly breakdown
    if report.monthly_performance:
        lines.extend([
            "MONTHLY PERFORMANCE",
            "-" * 70,
            f"  {'Month':<12} {'Trades':<8} {'Win%':<8} {'Net P&L':<15} {'Best Day':<12}",
            "-" * 70,
        ])
        for mp in report.monthly_performance:
            m = mp.metrics
            best_day = max(mp.daily_pnls.values()) if mp.daily_pnls else 0
            lines.append(f"  {mp.period_name:<12} {m.total_trades:<8} {m.win_rate:<7.1f}% ${m.net_profit:<+14,.0f} ${best_day:<+11,.0f}")
        lines.append("")
    
    # Recent trades
    if include_trades and report.trades:
        lines.extend([
            "RECENT TRADES",
            "-" * 70,
            f"  {'Date':<12} {'Symbol':<8} {'Side':<6} {'P&L':<12} {'Strategy':<15}",
            "-" * 70,
        ])
        for t in sorted(report.trades, key=lambda x: x.exit_date, reverse=True)[:20]:
            lines.append(f"  {t.exit_date.strftime('%Y-%m-%d'):<12} {t.symbol:<8} {t.side:<6} ${t.pnl:<+11,.2f} {t.strategy:<15}")
        lines.append("")
    
    lines.append("=" * 70)
    
    return "\n".join(lines)


# === Examples ===

def example_performance_report():
    """Generate sample performance report."""
    print("=" * 70)
    print("Performance Report Generator Demo")
    print("=" * 70)
    
    # Generate sample trades
    trades = []
    base_date = datetime(2024, 1, 1)
    
    # Trade patterns
    trade_data = [
        # (symbol, side, entry, exit, quantity, strategy, days)
        ("AAPL", "buy", 170, 175, 100, "Momentum", 3),
        ("TSLA", "buy", 250, 240, 50, "Breakout", 2),
        ("NVDA", "buy", 450, 475, 40, "Momentum", 5),
        ("MSFT", "buy", 380, 385, 60, "Pullback", 4),
        ("META", "buy", 300, 295, 70, "Mean Reversion", 1),
        ("GOOGL", "buy", 140, 145, 100, "Momentum", 6),
        ("AMZN", "buy", 180, 178, 80, "Breakout", 2),
        ("NFLX", "buy", 600, 615, 30, "Momentum", 4),
        ("AMD", "buy", 140, 145, 90, "Pullback", 5),
        ("CRM", "buy", 250, 255, 50, "Momentum", 3),
        ("AAPL", "buy", 178, 185, 80, "Breakout", 7),
        ("TSLA", "buy", 240, 232, 60, "Mean Reversion", 2),
        ("NVDA", "buy", 475, 490, 35, "Momentum", 5),
        ("MSFT", "buy", 385, 390, 55, "Pullback", 4),
        ("META", "buy", 295, 310, 65, "Mean Reversion", 6),
    ]
    
    for i, (sym, side, entry, exit, qty, strat, days) in enumerate(trade_data):
        entry_date = base_date + timedelta(days=i * 2)
        exit_date = entry_date + timedelta(days=days)
        
        trades.append(Trade(
            id=f"T{i+1:03d}",
            symbol=sym,
            side=side,
            entry_date=entry_date,
            exit_date=exit_date,
            entry_price=entry,
            exit_price=exit,
            quantity=qty,
            strategy=strat,
            commission=5.0
        ))
    
    # Generate report
    generator = ReportGenerator(initial_capital=100000)
    report = generator.generate_report(trades, "January 2024")
    
    # Print report
    print(format_report(report, include_trades=True))


def analyze_performance():
    """Analyze what makes good vs bad performance."""
    print("\n" + "=" * 70)
    print("Performance Analysis Guide")
    print("=" * 70)
    
    scenarios = [
        ("Win Rate 70%, PF 1.2", [
            Trade("1", "A", "buy", datetime.now(), datetime.now(), 100, 102, 100, "", "", commission=5),
            Trade("2", "A", "buy", datetime.now(), datetime.now(), 100, 101, 100, "", "", commission=5),
            Trade("3", "A", "buy", datetime.now(), datetime.now(), 100, 95, 100, "", "", commission=5),
        ]),
        ("Win Rate 40%, PF 2.0", [
            Trade("1", "A", "buy", datetime.now(), datetime.now(), 100, 108, 100, "", "", commission=5),
            Trade("2", "A", "buy", datetime.now(), datetime.now(), 100, 104, 100, "", "", commission=5),
            Trade("3", "A", "buy", datetime.now(), datetime.now(), 100, 104, 100, "", "", commission=5),
            Trade("4", "A", "buy", datetime.now(), datetime.now(), 100, 96, 100, "", "", commission=5),
            Trade("5", "A", "buy", datetime.now(), datetime.now(), 100, 93, 100, "", "", commission=5),
        ]),
    ]
    
    calc = PerformanceCalculator()
    
    for name, trades in scenarios:
        m = calc.calculate_metrics(trades)
        print(f"\n{name}:")
        print(f"  Net P&L:      ${m.net_profit:+,.2f}")
        print(f"  Win Rate:     {m.win_rate:.1f}%")
        print(f"  Profit Factor: {m.profit_factor:.2f}")
        print(f"  Expectancy:    ${m.expectancy:+.2f}")
    
    print("\n" + "-" * 70)
    print("INSIGHT: Win rate matters less than profit factor.")
    print("A 40% win rate with 2:1 win/loss ratio can be very profitable.")
    print("Focus on expectancy, not just being 'right'.")


if __name__ == "__main__":
    example_performance_report()
    analyze_performance()
    
    print("\n" + "=" * 70)
    print("KEY METRICS EXPLAINED:")
    print("=" * 70)
    print("""
Win Rate:          % of profitable trades (focus on >50% minimum)
Profit Factor:     Gross profit / gross loss (>1.5 is good, >2.0 is great)
Expectancy:        Average profit per trade (must be positive)
Win/Loss Ratio:    Avg win / avg loss (>1.5 is good)
Max Drawdown:      Largest peak-to-trough decline (compare to returns)

Which to prioritize:
1. Positive expectancy ($/trade > 0)
2. Reasonable drawdown (< 20%)
3. Profit factor (> 1.5)
4. Win rate (> 40% with good R/R)

A "good" system:
• Expectancy: $50+ per trade
• Profit Factor: > 1.5
• Max DD: < 15%
• Win Rate: 45-60%
• Win/Loss Ratio: > 1.3
    """)
    print("=" * 70)
```

## Performance Metrics

| Metric | Good | Great | Bad |
|--------|------|-------|-----|
| **Win Rate** | >45% | >55% | <35% |
| **Profit Factor** | >1.5 | >2.0 | <1.2 |
| **Expectancy** | >$0 | >$50/trade | <$0 |
| **Win/Loss Ratio** | >1.3 | >1.5 | <1.0 |
| **Max Drawdown** | <15% | <10% | >25% |

## Report Sections

| Section | Contains |
|---------|----------|
| **Summary** | Net P&L, trades, win rate, PF, expectancy |
| **Trade Stats** | Wins/losses, gross P&L, averages |
| **Risk Metrics** | Drawdown, consecutive stats, duration |
| **Strategy Breakdown** | Per-strategy performance comparison |
| **Symbol Breakdown** | Which symbols performed best |
| **Monthly Performance** | Trend over time |
| **Extremes** | Best/worst trades and days |

## Quick Reference

```python
trades = load_trade_history()  # Your data source

generator = ReportGenerator(initial_capital=100000)
report = generator.generate_report(trades, "Q1 2024")

# Print formatted report
print(format_report(report, include_trades=True))

# Access metrics directly
print(f"Net P&L: ${report.overall_metrics.net_profit:,.2f}")
print(f"Win Rate: {report.overall_metrics.win_rate:.1f}%")

# Compare strategies
for sp in report.strategy_performance:
    print(f"{sp.strategy_name}: ${sp.metrics.net_profit:+,}")
```

## Why This Matters

- **You can't improve what you don't measure** — Track everything
- **Data beats intuition** — Your memory is selective; the data isn't
- **Find your edge** — Which strategies/symbols/timeframes work?
- **Accountability** — Numbers don't lie about your performance
- **Expectancy > Win rate** — Being right 40% with 2:1 R/R beats 70% with 1:0.8

**Review your performance weekly. The numbers tell you what to fix.**

---

**Created by Ghost 👻 | Feb 20, 2026 | 13-min learning sprint**  
*Lesson: "You can't improve what you don't measure." A performance reporter turns trade data into actionable insights—what works, what doesn't, where to focus. Review weekly, optimize monthly, succeed long-term.*
