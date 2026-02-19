# Trade Journal & Performance Analytics
*2026-02-19 00:23* - Capture, analyze, and learn from every trade

## Purpose
Record trade history with fills, calculate key performance metrics (expectancy, win rate, drawdown), and surface actionable insights. The missing link between execution and strategy improvement.

## Code

```python
"""
Trade Journal & Performance Analytics
Capture trades, calculate metrics, surface insights.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict
import json
import statistics

@dataclass
class Trade:
    """Complete trade record from signal to fill."""
    id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    entry_price: float
    exit_price: Optional[float] = None
    size: float = 0.0
    entry_time: datetime = field(default_factory=datetime.now)
    exit_time: Optional[datetime] = None
    entry_signal: Optional[dict] = None
    exit_reason: Optional[str] = None  # 'TARGET', 'STOP', 'SIGNAL', 'MANUAL'
    fees: float = 0.0
    tags: List[str] = field(default_factory=list)
    
    @property
    def is_open(self) -> bool:
        return self.exit_price is None
    
    @property
    def duration(self) -> Optional[timedelta]:
        if self.exit_time:
            return self.exit_time - self.entry_time
        return None
    
    @property
    def pnl(self) -> Optional[float]:
        """Profit/loss in currency terms."""
        if self.exit_price is None:
            return None
        gross = (self.exit_price - self.entry_price) * self.size
        if self.side == 'SELL':
            gross = -gross  # Invert for shorts
        return gross - self.fees
    
    @property
    def pnl_pct(self) -> Optional[float]:
        """Profit/loss as percentage of entry value."""
        if self.exit_price is None or self.entry_price == 0:
            return None
        return (self.exit_price - self.entry_price) / self.entry_price * 100
    
    @property
    def r_multiple(self) -> Optional[float]:
        """Profit in terms of initial risk (if stop was set)."""
        if not self.entry_signal or 'stop_price' not in self.entry_signal:
            return None
        stop = self.entry_signal['stop_price']
        risk = abs(self.entry_price - stop)
        if risk == 0:
            return None
        profit = self.pnl
        if profit is None:
            return None
        return profit / (risk * self.size) if self.side == 'BUY' else -profit / (risk * self.size)


@dataclass
class PerformanceMetrics:
    """Calculated performance statistics."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    avg_winner: float = 0.0
    avg_loser: float = 0.0
    profit_factor: float = 0.0
    expectancy: float = 0.0
    expectancy_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    sharpe_ratio: float = 0.0
    avg_trade_duration: Optional[timedelta] = None
    avg_r_return: Optional[float] = None


class TradeJournal:
    """Persistent trade journal with analytics."""
    
    def __init__(self, storage_path: Optional[str] = None):
        self.trades: Dict[str, Trade] = {}
        self.storage_path = storage_path
        if storage_path:
            self._load()
    
    def record_entry(self, trade: Trade) -> None:
        """Record new trade entry."""
        self.trades[trade.id] = trade
        self._save()
    
    def record_exit(
        self,
        trade_id: str,
        exit_price: float,
        exit_time: Optional[datetime] = None,
        exit_reason: str = 'SIGNAL',
        fees: float = 0.0
    ) -> Optional[Trade]:
        """Record trade exit and update trade record."""
        trade = self.trades.get(trade_id)
        if not trade:
            return None
        
        trade.exit_price = exit_price
        trade.exit_time = exit_time or datetime.now()
        trade.exit_reason = exit_reason
        trade.fees += fees
        
        self._save()
        return trade
    
    def get_closed_trades(self, days: Optional[int] = None) -> List[Trade]:
        """Get closed trades, optionally filtered by recency."""
        closed = [t for t in self.trades.values() if not t.is_open]
        if days:
            cutoff = datetime.now() - timedelta(days=days)
            closed = [t for t in closed if t.exit_time and t.exit_time > cutoff]
        return sorted(closed, key=lambda t: t.entry_time)
    
    def get_open_trades(self) -> List[Trade]:
        """Get currently open positions."""
        return [t for t in self.trades.values() if t.is_open]
    
    def calculate_metrics(
        self,
        symbol: Optional[str] = None,
        days: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> PerformanceMetrics:
        """Calculate performance metrics for filtered trades."""
        trades = self.get_closed_trades(days)
        
        if symbol:
            trades = [t for t in trades if t.symbol == symbol]
        if tags:
            trades = [t for t in trades if any(tag in t.tags for tag in tags)]
        
        if not trades:
            return PerformanceMetrics()
        
        pnls = [t.pnl for t in trades if t.pnl is not None]
        winners = [p for p in pnls if p > 0]
        losers = [p for p in pnls if p < 0]
        
        total_won = sum(winners) if winners else 0
        total_lost = sum(abs(l) for l in losers) if losers else 0
        
        # Calculate drawdown
        cumulative = 0
        peak = 0
        max_dd = 0
        for pnl in pnls:
            cumulative += pnl
            peak = max(peak, cumulative)
            dd = peak - cumulative
            max_dd = max(max_dd, dd)
        
        # R-multiples
        r_multiples = [t.r_multiple for t in trades if t.r_multiple is not None]
        
        # Trade durations
        durations = [t.duration for t in trades if t.duration]
        
        return PerformanceMetrics(
            total_trades=len(trades),
            winning_trades=len(winners),
            losing_trades=len(losers),
            win_rate=len(winners) / len(trades) * 100 if trades else 0,
            avg_winner=statistics.mean(winners) if winners else 0,
            avg_loser=statistics.mean(losers) if losers else 0,
            profit_factor=total_won / total_lost if total_lost > 0 else float('inf'),
            expectancy=statistics.mean(pnls) if pnls else 0,
            expectancy_pct=statistics.mean([t.pnl_pct for t in trades if t.pnl_pct]) if any(t.pnl_pct for t in trades) else 0,
            max_drawdown_pct=(max_dd / peak * 100) if peak > 0 else 0,
            avg_r_return=statistics.mean(r_multiples) if r_multiples else None,
            avg_trade_duration=statistics.mean(durations, key=lambda x: x.total_seconds()) if durations else None
        )
    
    def insights(self, days: int = 30) -> List[str]:
        """Generate actionable insights from recent performance."""
        insights = []
        m = self.calculate_metrics(days=days)
        
        if m.total_trades < 10:
            insights.append(f"⚠️ Only {m.total_trades} trades in last {days} days - need more data")
            return insights
        
        # Win rate analysis
        if m.win_rate < 30:
            insights.append(f"🚨 Win rate {m.win_rate:.1f}% is very low - review entry criteria")
        elif m.win_rate > 60 and m.profit_factor < 1.5:
            insights.append(f"⚠️ Win rate {m.win_rate:.1f}% but low profit factor {m.profit_factor:.2f} - winners too small")
        
        # Expectancy
        if m.expectancy <= 0:
            insights.append(f"🚨 Negative expectancy ${m.expectancy:.2f} - strategy losing money")
        elif m.expectancy > 0 and m.expectancy_pct < 0.1:
            insights.append(f"⚠️ Low expectancy {m.expectancy_pct:.2f}% - consider position sizing or comms costs")
        
        # Profit factor
        if m.profit_factor < 1.0:
            insights.append(f"🚨 Profit factor {m.profit_factor:.2f} < 1.0 - losers outweigh winners")
        elif m.profit_factor > 3.0:
            insights.append(f"✅ Strong profit factor {m.profit_factor:.2f}")
        
        # Drawdown
        if m.max_drawdown_pct > 20:
            insights.append(f"🚨 Max drawdown {m.max_drawdown_pct:.1f}% - risk too high")
        
        # R-return analysis
        if m.avg_r_return is not None:
            if m.avg_r_return < 0.5:
                insights.append(f"⚠️ Avg R-return {m.avg_r_return:.2f}R - targets may be too close to stops")
            elif m.avg_r_return > 2.0:
                insights.append(f"✅ Good R-return {m.avg_r_return:.2f}R - healthy risk/reward")
        
        return insights
    
    def by_exit_reason(self, days: int = 30) -> Dict[str, PerformanceMetrics]:
        """Analyze performance broken down by exit reason."""
        trades = self.get_closed_trades(days)
        by_reason = defaultdict(list)
        for t in trades:
            by_reason[t.exit_reason or 'UNKNOWN'].append(t)
        
        return {
            reason: self._metrics_from_trades(tlist)
            for reason, tlist in by_reason.items()
        }
    
    def _metrics_from_trades(self, trades: List[Trade]) -> PerformanceMetrics:
        """Helper to calculate metrics from a trade list."""
        if not trades:
            return PerformanceMetrics()
        pnls = [t.pnl for t in trades if t.pnl is not None]
        return PerformanceMetrics(
            total_trades=len(trades),
            expectancy=statistics.mean(pnls) if pnls else 0,
            win_rate=len([p for p in pnls if p > 0]) / len(trades) * 100
        )
    
    def _save(self) -> None:
        """Persist to JSON."""
        if not self.storage_path:
            return
        data = {
            tid: {
                'id': t.id,
                'symbol': t.symbol,
                'side': t.side,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'size': t.size,
                'entry_time': t.entry_time.isoformat(),
                'exit_time': t.exit_time.isoformat() if t.exit_time else None,
                'exit_reason': t.exit_reason,
                'fees': t.fees,
                'tags': t.tags,
                'pnl': t.pnl,
            }
            for tid, t in self.trades.items()
        }
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load(self) -> None:
        """Load from JSON."""
        try:
            with open(self.storage_path, 'r') as f:
                data = json.load(f)
            for tid, tdata in data.items():
                self.trades[tid] = Trade(
                    id=tdata['id'],
                    symbol=tdata['symbol'],
                    side=tdata['side'],
                    entry_price=tdata['entry_price'],
                    exit_price=tdata.get('exit_price'),
                    size=tdata['size'],
                    entry_time=datetime.fromisoformat(tdata['entry_time']),
                    exit_time=datetime.fromisoformat(tdata['exit_time']) if tdata.get('exit_time') else None,
                    exit_reason=tdata.get('exit_reason'),
                    fees=tdata.get('fees', 0),
                    tags=tdata.get('tags', [])
                )
        except FileNotFoundError:
            pass


# === USAGE EXAMPLES ===

def example_basic_workflow():
    """Typical journal usage."""
    journal = TradeJournal(storage_path="trades.json")
    
    # Record entry
    trade = Trade(
        id="btc-001",
        symbol="BTC-USD",
        side="BUY",
        entry_price=50000.0,
        size=0.1,
        entry_signal={'stop_price': 49000.0},
        tags=['trend', 'breakout']
    )
    journal.record_entry(trade)
    
    # Record exit later
    journal.record_exit(
        trade_id="btc-001",
        exit_price=51000.0,
        exit_reason="TARGET",
        fees=5.0
    )
    
    # Check metrics
    metrics = journal.calculate_metrics()
    print(f"Win rate: {metrics.win_rate:.1f}%")
    print(f"Expectancy: ${metrics.expectancy:.2f}")
    
    # Get insights
    for insight in journal.insights(days=30):
        print(insight)

def example_integration_with_executor():
    """Integrate journal with order execution flow."""
    
    class JournalingExecutor:
        def __init__(self, executor, journal: TradeJournal):
            self.executor = executor
            self.journal = journal
        
        async def enter_position(self, signal) -> Trade:
            # Execute
            fill = await self.executor.execute(signal)
            
            # Journal it
            trade = Trade(
                id=fill.order_id,
                symbol=signal.symbol,
                side=signal.side,
                entry_price=fill.price,
                size=fill.size,
                entry_signal=signal.__dict__,
                tags=getattr(signal, 'tags', [])
            )
            self.journal.record_entry(trade)
            return trade
        
        async def exit_position(self, trade_id: str, exit_signal):
            fill = await self.executor.execute(exit_signal)
            
            self.journal.record_exit(
                trade_id=trade_id,
                exit_price=fill.price,
                exit_reason=exit_signal.reason,
                fees=fill.fees
            )
            
            # Return completed trade with PnL
            return self.journal.trades[trade_id]

def example_weekly_review():
    """Generate weekly performance report."""
    journal = TradeJournal("trades.json")
    
    print("=== WEEKLY REVIEW ===")
    
    # Overall metrics
    m = journal.calculate_metrics(days=7)
    print(f"\nTrades: {m.total_trades} | Win Rate: {m.win_rate:.1f}%")
    print(f"Expectancy: ${m.expectancy:.2f} | Profit Factor: {m.profit_factor:.2f}")
    
    # By exit reason
    print("\n--- By Exit Reason ---")
    for reason, metrics in journal.by_exit_reason(days=7).items():
        print(f"{reason}: {metrics.total_trades} trades, ${metrics.expectancy:.2f} avg")
    
    # Insights
    print("\n--- Insights ---")
    for insight in journal.insights(days=7):
        print(insight)


# === QUICK REFERENCE ===

"""
Key Metrics Explained:

- Win Rate: % of profitable trades. High alone != profitable.
- Expectancy: Average PnL per trade. Must be > 0.
- Profit Factor: Gross profit / gross loss. > 1.5 is good, > 2.0 is excellent.
- R-Multiple: Return in terms of initial risk. 1R = broke even on risk.
- Max Drawdown: Peak-to-trough decline. Keep < 20% typically.

Integration Pattern:

journal = TradeJournal("trades.json")

# In entry handler
trade = Trade(id=generate_id(), ...)
journal.record_entry(trade)

# In exit handler (via fill callback)
journal.record_exit(trade_id, fill_price, reason)

# Daily/weekly review
for insight in journal.insights(days=7):
    if insight.startswith("🚨"):
        send_alert(insight)

# Strategy optimization
by_reason = journal.by_exit_reason()
if by_reason['STOP'].win_rate < 20:
    # Stops being hit too often - widen or improve entries
    adjust_stop_logic()
"""

if __name__ == "__main__":
    example_basic_workflow()
```
