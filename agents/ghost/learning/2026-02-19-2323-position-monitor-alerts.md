# Real-Time Position Monitor & Alert System

**Purpose:** Monitor open positions and alert on risk thresholds, profit targets, and anomalies  
**Use Case:** Live trading dashboard for risk management

## The Code

```python
"""
Position Monitor & Alert System
Real-time monitoring of open positions with configurable alerts.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Literal
from datetime import datetime, timedelta
from enum import Enum
import time


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """Risk alert for a position."""
    timestamp: datetime
    symbol: str
    level: AlertLevel
    message: str
    metric: str
    current_value: float
    threshold: float


@dataclass
class MonitoredPosition:
    """Position with monitoring metadata."""
    symbol: str
    direction: Literal["long", "short"]
    entry_price: float
    current_price: float
    size: float
    stop_price: float
    target_price: float
    entry_time: datetime
    
    # Risk metrics
    initial_risk: float
    max_risk_seen: float = 0
    max_profit_seen: float = 0
    
    @property
    def pnl(self) -> float:
        mult = 1 if self.direction == "long" else -1
        return (self.current_price - self.entry_price) * self.size * mult
    
    @property
    def pnl_pct(self) -> float:
        return (self.pnl / (self.entry_price * self.size)) * 100
    
    @property
    def r_multiple(self) -> float:
        return self.pnl / self.initial_risk if self.initial_risk > 0 else 0
    
    @property
    def distance_to_stop(self) -> float:
        """Price distance to stop loss in %."""
        if self.direction == "long":
            return ((self.current_price - self.stop_price) / self.current_price) * 100
        else:
            return ((self.stop_price - self.current_price) / self.current_price) * 100
    
    @property
    def distance_to_target(self) -> float:
        """Price distance to target in %."""
        if self.direction == "long":
            return ((self.target_price - self.current_price) / self.current_price) * 100
        else:
            return ((self.current_price - self.target_price) / self.current_price) * 100
    
    @property
    def duration(self) -> timedelta:
        return datetime.now() - self.entry_time


class PositionMonitor:
    """
    Monitor open positions and generate alerts.
    """
    
    def __init__(self, account_size: float):
        self.account = account_size
        self.positions: Dict[str, MonitoredPosition] = {}
        self.alerts: List[Alert] = []
        self.alert_handlers: List[Callable[[Alert], None]] = []
        
        # Alert thresholds
        self.thresholds = {
            "profit_1r": 1.0,
            "profit_2r": 2.0,
            "loss_1r": -1.0,
            "loss_warn": -0.5,
            "approaching_stop": 2.0,  # % from stop
            "time_warning": 30,  # minutes
            "max_drawdown": 3.0,  # % from entry
        }
        
        # Track which alerts fired (prevent spam)
        self._fired_alerts: Dict[str, datetime] = {}
    
    def add_position(self, position: MonitoredPosition):
        """Add position to monitoring."""
        self.positions[position.symbol] = position
        self._fire_alert(
            Alert(
                timestamp=datetime.now(),
                symbol=position.symbol,
                level=AlertLevel.INFO,
                message=f"Monitoring started: {position.direction} {position.size} @ ${position.entry_price}",
                metric="entry",
                current_value=position.entry_price,
                threshold=0
            )
        )
    
    def update_price(self, symbol: str, price: float):
        """Update current price for a position."""
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        pos.current_price = price
        
        # Update max seen
        if pos.pnl > pos.max_profit_seen:
            pos.max_profit_seen = pos.pnl
        if pos.pnl < pos.max_risk_seen:
            pos.max_risk_seen = pos.pnl
        
        # Check all conditions
        self._check_profit_targets(pos)
        self._check_stop_proximity(pos)
        self._check_time_based(pos)
        self._check_drawdown(pos)
    
    def _check_profit_targets(self, pos: MonitoredPosition):
        """Check profit target achievements."""
        r = pos.r_multiple
        
        # 1R profit - move stop to breakeven suggestion
        if r >= self.thresholds["profit_1r"]:
            self._maybe_alert(
                pos.symbol, "profit_1r",
                Alert(
                    timestamp=datetime.now(),
                    symbol=pos.symbol,
                    level=AlertLevel.INFO,
                    message=f"🎯 1R profit reached ({r:.1f}R). Consider moving stop to breakeven.",
                    metric="r_multiple",
                    current_value=r,
                    threshold=self.thresholds["profit_1r"]
                )
            )
        
        # 2R profit - take partial suggestion
        if r >= self.thresholds["profit_2r"]:
            self._maybe_alert(
                pos.symbol, "profit_2r",
                Alert(
                    timestamp=datetime.now(),
                    symbol=pos.symbol,
                    level=AlertLevel.WARNING,
                    message=f"🎯 2R profit reached ({r:.1f}R). Consider taking partial profits.",
                    metric="r_multiple",
                    current_value=r,
                    threshold=self.thresholds["profit_2r"]
                )
            )
        
        # -1R loss - review trade
        if r <= self.thresholds["loss_1r"]:
            self._maybe_alert(
                pos.symbol, "loss_1r",
                Alert(
                    timestamp=datetime.now(),
                    symbol=pos.symbol,
                    level=AlertLevel.CRITICAL,
                    message=f"⚠️ Stop loss hit ({r:.1f}R). Exit position.",
                    metric="r_multiple",
                    current_value=r,
                    threshold=self.thresholds["loss_1r"]
                ),
                cooldown_minutes=0  # Always alert
            )
        
        # -0.5R approaching stop
        if r <= self.thresholds["loss_warn"] and r > self.thresholds["loss_1r"]:
            self._maybe_alert(
                pos.symbol, "loss_warn",
                Alert(
                    timestamp=datetime.now(),
                    symbol=pos.symbol,
                    level=AlertLevel.WARNING,
                    message=f"⚠️ Approaching stop ({r:.1f}R). Monitor closely.",
                    metric="r_multiple",
                    current_value=r,
                    threshold=self.thresholds["loss_warn"]
                )
            )
    
    def _check_stop_proximity(self, pos: MonitoredPosition):
        """Alert when price is close to stop."""
        dist = pos.distance_to_stop
        
        if dist <= self.thresholds["approaching_stop"] and dist > 0:
            self._maybe_alert(
                pos.symbol, f"stop_proximity_{pos.symbol}",
                Alert(
                    timestamp=datetime.now(),
                    symbol=pos.symbol,
                    level=AlertLevel.WARNING,
                    message=f"🛑 Only {dist:.1f}% from stop loss (${pos.stop_price:.2f})",
                    metric="distance_to_stop_pct",
                    current_value=dist,
                    threshold=self.thresholds["approaching_stop"]
                )
            )
    
    def _check_time_based(self, pos: MonitoredPosition):
        """Time-based alerts."""
        duration_mins = pos.duration.total_seconds() / 60
        
        # Position open too long (time decay, opportunity cost)
        if duration_mins > self.thresholds["time_warning"]:
            self._maybe_alert(
                pos.symbol, f"time_warning_{pos.symbol}",
                Alert(
                    timestamp=datetime.now(),
                    symbol=pos.symbol,
                    level=AlertLevel.INFO,
                    message=f"⏱️ Position open {duration_mins:.0f}min. Review thesis.",
                    metric="duration_minutes",
                    current_value=duration_mins,
                    threshold=self.thresholds["time_warning"]
                ),
                cooldown_minutes=30  # Don't spam
            )
    
    def _check_drawdown(self, pos: MonitoredPosition):
        """Alert on adverse moves from entry."""
        drawdown = ((pos.entry_price - pos.current_price) / pos.entry_price * 100)
        if pos.direction == "short":
            drawdown = -drawdown
        
        if drawdown < -self.thresholds["max_drawdown"]:
            self._maybe_alert(
                pos.symbol, f"drawdown_{pos.symbol}",
                Alert(
                    timestamp=datetime.now(),
                    symbol=pos.symbol,
                    level=AlertLevel.WARNING,
                    message=f"📉 Position down {abs(drawdown):.1f}% from entry",
                    metric="drawdown_pct",
                    current_value=drawdown,
                    threshold=-self.thresholds["max_drawdown"]
                ),
                cooldown_minutes=15
            )
    
    def _maybe_alert(self, symbol: str, alert_type: str, alert: Alert, cooldown_minutes: int = 5):
        """Fire alert if not in cooldown."""
        key = f"{symbol}_{alert_type}"
        now = datetime.now()
        
        if key in self._fired_alerts:
            last_fired = self._fired_alerts[key]
            if (now - last_fired).total_seconds() < cooldown_minutes * 60:
                return  # In cooldown
        
        self._fired_alerts[key] = now
        self._fire_alert(alert)
    
    def _fire_alert(self, alert: Alert):
        """Fire alert to all handlers."""
        self.alerts.append(alert)
        for handler in self.alert_handlers:
            handler(alert)
    
    def on_alert(self, handler: Callable[[Alert], None]):
        """Register alert handler."""
        self.alert_handlers.append(handler)
    
    def remove_position(self, symbol: str, reason: str = "closed"):
        """Stop monitoring a position."""
        if symbol in self.positions:
            pos = self.positions.pop(symbol)
            final_pnl = pos.pnl
            
            self._fire_alert(
                Alert(
                    timestamp=datetime.now(),
                    symbol=symbol,
                    level=AlertLevel.INFO,
                    message=f"📋 Position closed. P&L: ${final_pnl:.2f} ({pos.r_multiple:.1f}R)",
                    metric="final_pnl",
                    current_value=final_pnl,
                    threshold=0
                )
            )
    
    def get_dashboard(self) -> Dict:
        """Generate monitoring dashboard."""
        if not self.positions:
            return {"status": "No open positions"}
        
        total_pnl = sum(p.pnl for p in self.positions.values())
        total_risk = sum(p.initial_risk for p in self.positions.values())
        
        # Find extremes
        best = max(self.positions.values(), key=lambda p: p.r_multiple)
        worst = min(self.positions.values(), key=lambda p: p.r_multiple)
        
        return {
            "positions": len(self.positions),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round((total_pnl / self.account) * 100, 2),
            "total_risk_deployed": round(total_risk, 2),
            "best_position": {
                "symbol": best.symbol,
                "r": round(best.r_multiple, 2),
                "pnl": round(best.pnl, 2)
            },
            "worst_position": {
                "symbol": worst.symbol,
                "r": round(worst.r_multiple, 2),
                "pnl": round(worst.pnl, 2)
            },
            "positions_detail": [
                {
                    "symbol": p.symbol,
                    "direction": p.direction,
                    "entry": p.entry_price,
                    "current": p.current_price,
                    "pnl": round(p.pnl, 2),
                    "r": round(p.r_multiple, 1),
                    "to_stop": round(p.distance_to_stop, 1),
                    "to_target": round(p.distance_to_target, 1),
                    "duration_min": int(p.duration.total_seconds() / 60)
                }
                for p in self.positions.values()
            ],
            "recent_alerts": [
                {
                    "time": a.timestamp.strftime("%H:%M:%S"),
                    "symbol": a.symbol,
                    "level": a.level.value,
                    "message": a.message
                }
                for a in self.alerts[-5:]  # Last 5
            ]
        }
    
    def print_dashboard(self):
        """Print formatted dashboard."""
        dash = self.get_dashboard()
        
        print(f"\n{'='*70}")
        print(f"POSITION MONITOR - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")
        
        if "status" in dash:
            print(dash["status"])
            return
        
        print(f"\nPortfolio: ${self.account:,.0f}")
        print(f"Open Positions: {dash['positions']}")
        print(f"Total P&L: ${dash['total_pnl']:,.2f} ({dash['total_pnl_pct']:+.2f}%)")
        
        print(f"\n--- Positions ---")
        for p in dash['positions_detail']:
            status = "🟢" if p['r'] > 0 else "🔴" if p['r'] < 0 else "⚪"
            print(f"{status} {p['symbol']:6} {p['direction']:4} | "
                  f"${p['entry']:.2f} → ${p['current']:.2f} | "
                  f"P&L: ${p['pnl']:+,.0f} ({p['r']:+,.1f}R) | "
                  f"{p['duration_min']}min")
            print(f"      Stop: {p['to_stop']:.1f}% away | Target: {p['to_target']:.1f}% away")
        
        if dash['recent_alerts']:
            print(f"\n--- Recent Alerts ---")
            for a in dash['recent_alerts']:
                emoji = "🔴" if a['level'] == 'critical' else "🟡" if a['level'] == 'warning' else "🔵"
                print(f"{emoji} [{a['time']}] {a['symbol']}: {a['message']}")
        
        print(f"{'='*70}\n")


# === Example Usage ===

if __name__ == "__main__":
    # Setup monitor
    monitor = PositionMonitor(account_size=100000)
    
    # Alert handler (in real app: send to Slack/SMS/dashboard)
    def on_alert(alert: Alert):
        emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}
        print(f"{emoji.get(alert.level.value, '•')} [{alert.timestamp.strftime('%H:%M:%S')}] "
              f"{alert.symbol}: {alert.message}")
    
    monitor.on_alert(on_alert)
    
    # Add positions
    print("="*70)
    print("SIMULATION: Position Monitor")
    print("="*70)
    
    monitor.add_position(MonitoredPosition(
        symbol="AAPL",
        direction="long",
        entry_price=150.0,
        current_price=150.0,
        size=100,
        stop_price=147.0,
        target_price=156.0,
        entry_time=datetime.now(),
        initial_risk=300.0
    ))
    
    monitor.add_position(MonitoredPosition(
        symbol="TSLA",
        direction="short",
        entry_price=200.0,
        current_price=200.0,
        size=50,
        stop_price=205.0,
        target_price=190.0,
        entry_time=datetime.now() - timedelta(minutes=35),
        initial_risk=250.0
    ))
    
    # Simulate price updates
    print("\n--- Simulating Market Movement ---")
    
    # AAPL goes up
    time.sleep(0.5)
    monitor.update_price("AAPL", 151.50)  # +0.5R
    time.sleep(0.5)
    monitor.update_price("AAPL", 153.00)  # +1R - Should alert
    time.sleep(0.5)
    monitor.update_price("AAPL", 156.00)  # +2R - Should alert
    
    # TSLA goes against us
    time.sleep(0.5)
    monitor.update_price("TSLA", 203.00)  # Approaching stop
    time.sleep(0.5)
    monitor.update_price("TSLA", 204.50)  # Very close to stop
    time.sleep(0.5)
    monitor.update_price("TSLA", 205.00)  # Stop hit!
    
    # Print dashboard
    monitor.print_dashboard()
    
    # Close position
    monitor.remove_position("TSLA", "stop_hit")
    
    print("\n--- Final Status ---")
    monitor.print_dashboard()


## Alert Types

| Trigger | Level | Message | Cooldown |
|---------|-------|---------|----------|
| 1R profit | Info | Move stop to breakeven | Once |
| 2R profit | Warning | Take partial profits | Once |
| -0.5R | Warning | Approaching stop | 5 min |
| -1R | Critical | Exit position | Immediate |
| Near stop | Warning | X% from stop | 5 min |
| >30 min open | Info | Review thesis | 30 min |
| >3% drawdown | Warning | Down from entry | 15 min |

## Integration Example

```python
# In your trading system
monitor = PositionMonitor(account_size=100000)

# Connect to broker price feed
def on_price_update(symbol, price):
    monitor.update_price(symbol, price)

# Connect to order fills
def on_fill(order):
    if order.side == "buy":
        monitor.add_position(MonitoredPosition(...))
    else:  # sell
        monitor.remove_position(order.symbol)

# WebSocket/SMS alerts
def send_alert(alert):
    if alert.level == AlertLevel.CRITICAL:
        send_sms(alert.message)
    else:
        send_slack(alert.message)

monitor.on_alert(send_alert)
```

---

**Created by Ghost 👻 | Feb 19, 2026 | 11-min learning sprint**  
*Lesson: You can't watch every position every second. Automate the watching, act on the alerts.*
