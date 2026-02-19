# Trading Alert & Notification System
*2026-02-19 03:23* - Unified notification manager for trading events

## Purpose
Centralize all trading notifications: fill confirmations, risk breaches, daily summaries, and strategy insights. Integrates seamlessly with journal, risk monitor, and position sizer to keep you informed without noise.

## Code

```python
"""
Trading Alert & Notification System
Unified notification manager with severity levels and throttling.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict
from enum import Enum, auto
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict


class AlertSeverity(Enum):
    CRITICAL = auto()   # Immediate action required (risk breach, large loss)
    WARNING = auto()    # Attention needed (position limit, drawdown)
    INFO = auto()       # Good to know (fill confirmation, daily summary)
    DEBUG = auto()      # Detailed logs (execution traces)


class AlertChannel(Enum):
    CONSOLE = auto()
    TELEGRAM = auto()
    EMAIL = auto()
    WEBHOOK = auto()
    FILE = auto()


@dataclass
class Alert:
    """Individual alert message."""
    id: str
    severity: AlertSeverity
    category: str  # 'RISK', 'FILL', 'PERFORMANCE', 'SYSTEM'
    title: str
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict = field(default_factory=dict)
    acknowledged: bool = False


@dataclass
class AlertRule:
    """Rule for auto-generating alerts."""
    name: str
    condition: Callable[[any], bool]
    severity: AlertSeverity
    message_template: str
    cooldown_minutes: int = 60  # Don't repeat same alert within this time
    channels: List[AlertChannel] = field(default_factory=lambda: [AlertChannel.CONSOLE])


class AlertManager:
    """Centralized alert management with routing and throttling."""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.rules: List[AlertRule] = []
        self.handlers: Dict[AlertChannel, Callable] = {}
        self.last_alert_time: Dict[str, datetime] = {}
        self.daily_stats: Dict = defaultdict(float)
        self.suppressed_categories: set = set()
    
    def register_handler(self, channel: AlertChannel, handler: Callable[[Alert], None]):
        """Register a handler for a specific channel."""
        self.handlers[channel] = handler
        return self
    
    def add_rule(self, rule: AlertRule):
        """Add an auto-alert rule."""
        self.rules.append(rule)
        return self
    
    def send(
        self,
        severity: AlertSeverity,
        category: str,
        title: str,
        message: str,
        metadata: Optional[Dict] = None,
        channels: Optional[List[AlertChannel]] = None
    ) -> Alert:
        """Send an alert through specified channels."""
        
        if category in self.suppressed_categories:
            return None
        
        alert = Alert(
            id=f"{category}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            severity=severity,
            category=category,
            title=title,
            message=message,
            metadata=metadata or {}
        )
        
        self.alerts.append(alert)
        
        # Route to channels
        target_channels = channels or self._default_channels(severity)
        
        for channel in target_channels:
            if channel in self.handlers:
                try:
                    self.handlers[channel](alert)
                except Exception as e:
                    print(f"Alert handler failed for {channel}: {e}")
        
        return alert
    
    def check_rules(self, data: any):
        """Check all rules against current data and fire if triggered."""
        now = datetime.now()
        
        for rule in self.rules:
            rule_key = f"{rule.name}:{rule.severity.name}"
            
            # Check cooldown
            last_time = self.last_alert_time.get(rule_key)
            if last_time and (now - last_time) < timedelta(minutes=rule.cooldown_minutes):
                continue
            
            # Check condition
            if rule.condition(data):
                message = rule.message_template.format(**data.__dict__ if hasattr(data, '__dict__') else data)
                self.send(
                    severity=rule.severity,
                    category='AUTO',
                    title=rule.name,
                    message=message,
                    channels=rule.channels
                )
                self.last_alert_time[rule_key] = now
    
    def _default_channels(self, severity: AlertSeverity) -> List[AlertChannel]:
        """Default routing based on severity."""
        if severity == AlertSeverity.CRITICAL:
            return [AlertChannel.CONSOLE, AlertChannel.TELEGRAM]
        elif severity == AlertSeverity.WARNING:
            return [AlertChannel.CONSOLE, AlertChannel.TELEGRAM]
        else:
            return [AlertChannel.CONSOLE]
    
    def acknowledge(self, alert_id: str):
        """Mark alert as acknowledged."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return True
        return False
    
    def get_unacknowledged(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get unacknowledged alerts, optionally filtered by severity."""
        alerts = [a for a in self.alerts if not a.acknowledged]
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def suppress(self, category: str, duration_minutes: Optional[int] = None):
        """Temporarily suppress a category of alerts."""
        self.suppressed_categories.add(category)
        if duration_minutes:
            # Would schedule re-enable in real implementation
            pass
    
    def summary(self, hours: int = 24) -> str:
        """Generate alert summary for recent period."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [a for a in self.alerts if a.timestamp > cutoff]
        
        by_severity = defaultdict(int)
        by_category = defaultdict(int)
        unack = 0
        
        for alert in recent:
            by_severity[alert.severity.name] += 1
            by_category[alert.category] += 1
            if not alert.acknowledged:
                unack += 1
        
        lines = [
            f"📊 Alert Summary ({hours}h)",
            f"Total: {len(recent)} | Unacknowledged: {unack}",
            "",
            "By Severity:",
        ]
        for sev, count in sorted(by_severity.items()):
            lines.append(f"  {sev}: {count}")
        
        lines.append("")
        lines.append("By Category:")
        for cat, count in sorted(by_category.items()):
            lines.append(f"  {cat}: {count}")
        
        return "\n".join(lines)


# === INTEGRATION HELPERS ===

class TradeAlertIntegrations:
    """Pre-built integrations with trading utilities."""
    
    @staticmethod
    def on_fill(alert_manager: AlertManager, fill: dict):
        """Alert on order fill."""
        pnl = fill.get('realized_pnl', 0)
        
        if pnl != 0:
            severity = AlertSeverity.INFO if pnl > 0 else AlertSeverity.WARNING
            emoji = "🟢" if pnl > 0 else "🔴"
            alert_manager.send(
                severity=severity,
                category='FILL',
                title=f"Position Closed: {fill.get('symbol', 'Unknown')}",
                message=f"{emoji} {fill.get('side')} {fill.get('size')} @ {fill.get('price')}\nPnL: ${pnl:+.2f}",
                metadata=fill
            )
        else:
            alert_manager.send(
                severity=AlertSeverity.INFO,
                category='FILL',
                title=f"Position Opened: {fill.get('symbol', 'Unknown')}",
                message=f"📥 {fill.get('side')} {fill.get('size')} @ {fill.get('price')}",
                metadata=fill
            )
    
    @staticmethod
    def on_risk_breach(alert_manager: AlertManager, breach_type: str, details: dict):
        """Alert on risk limit breach."""
        alert_manager.send(
            severity=AlertSeverity.CRITICAL,
            category='RISK',
            title=f"🚨 Risk Breach: {breach_type}",
            message=f"{details.get('description', 'Risk limit exceeded')}\n"
                    f"Current: {details.get('current', 'N/A')} | Limit: {details.get('limit', 'N/A')}",
            metadata=details,
            channels=[AlertChannel.CONSOLE, AlertChannel.TELEGRAM]
        )
    
    @staticmethod
    def on_drawdown(alert_manager: AlertManager, drawdown_pct: float, threshold: float):
        """Alert on drawdown milestones."""
        if drawdown_pct >= threshold:
            alert_manager.send(
                severity=AlertSeverity.WARNING,
                category='RISK',
                title=f"⚠️ Drawdown Alert: {drawdown_pct:.1f}%",
                message=f"Portfolio drawdown has reached {drawdown_pct:.1f}% (threshold: {threshold:.1f}%)\n"
                        f"Consider reducing position sizes or pausing new trades.",
                metadata={'drawdown_pct': drawdown_pct, 'threshold': threshold}
            )
    
    @staticmethod
    def daily_summary(alert_manager: AlertManager, journal_metrics: dict):
        """Send daily performance summary."""
        total = journal_metrics.get('total_trades', 0)
        win_rate = journal_metrics.get('win_rate', 0)
        pnl = journal_metrics.get('total_pnl', 0)
        
        emoji = "🟢" if pnl >= 0 else "🔴"
        
        alert_manager.send(
            severity=AlertSeverity.INFO,
            category='PERFORMANCE',
            title=f"Daily Summary: {emoji} ${pnl:+.2f}",
            message=f"Trades: {total} | Win Rate: {win_rate:.1f}%\n"
                    f"PnL: ${pnl:+.2f}",
            metadata=journal_metrics,
            channels=[AlertChannel.CONSOLE]  # Less intrusive
        )
    
    @staticmethod
    def setup_default_rules(alert_manager: AlertManager):
        """Setup common alert rules."""
        
        # Large loss rule
        alert_manager.add_rule(AlertRule(
            name="Large Single Loss",
            condition=lambda trade: trade.get('pnl', 0) < -500,
            severity=AlertSeverity.CRITICAL,
            message_template="Large loss detected: ${pnl:.2f} on {symbol}",
            cooldown_minutes=30,
            channels=[AlertChannel.CONSOLE, AlertChannel.TELEGRAM]
        ))
        
        # Consecutive losses rule
        alert_manager.add_rule(AlertRule(
            name="Consecutive Losses",
            condition=lambda data: data.get('consecutive_losses', 0) >= 3,
            severity=AlertSeverity.WARNING,
            message_template="{consecutive_losses} consecutive losses detected. Consider pausing.",
            cooldown_minutes=120,
            channels=[AlertChannel.CONSOLE, AlertChannel.TELEGRAM]
        ))
        
        # Win rate drop rule
        alert_manager.add_rule(AlertRule(
            name="Win Rate Drop",
            condition=lambda metrics: metrics.get('recent_win_rate', 100) < 30 and metrics.get('recent_trades', 0) >= 10,
            severity=AlertSeverity.WARNING,
            message_template="Recent win rate dropped to {recent_win_rate:.1f}% over last {recent_trades} trades",
            cooldown_minutes=240,
            channels=[AlertChannel.CONSOLE]
        ))


# === HANDLER IMPLEMENTATIONS ===

def console_handler(alert: Alert):
    """Print alert to console with formatting."""
    severity_emoji = {
        AlertSeverity.CRITICAL: "🔴",
        AlertSeverity.WARNING: "🟡",
        AlertSeverity.INFO: "🟢",
        AlertSeverity.DEBUG: "⚪"
    }
    
    emoji = severity_emoji.get(alert.severity, "⚪")
    timestamp = alert.timestamp.strftime("%H:%M:%S")
    
    print(f"\n{emoji} [{timestamp}] {alert.category} - {alert.title}")
    print(f"   {alert.message}")
    if alert.metadata:
        print(f"   Meta: {alert.metadata}")


def file_handler(filepath: str):
    """Create a handler that writes alerts to file."""
    def handler(alert: Alert):
        with open(filepath, 'a') as f:
            f.write(f"{alert.timestamp.isoformat()} | {alert.severity.name} | {alert.category} | {alert.title} | {alert.message}\n")
    return handler


def telegram_handler(bot_token: str, chat_id: str):
    """Create a handler that sends alerts via Telegram."""
    async def handler(alert: Alert):
        import aiohttp
        
        severity_emoji = {
            AlertSeverity.CRITICAL: "🚨",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.DEBUG: "🔍"
        }
        
        emoji = severity_emoji.get(alert.severity, "ℹ️")
        text = f"{emoji} *{alert.title}*\n\n{alert.message}"
        
        if alert.severity == AlertSeverity.CRITICAL:
            text = "🔴🔴🔴 " + text + " 🔴🔴🔴"
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    print(f"Telegram alert failed: {resp.status}")
    
    # Return sync wrapper for non-async callers
    def sync_handler(alert: Alert):
        try:
            asyncio.create_task(handler(alert))
        except:
            # Fallback for non-async context
            import threading
            threading.Thread(target=lambda: asyncio.run(handler(alert))).start()
    
    return sync_handler


# === USAGE EXAMPLES ===

def example_basic_usage():
    """Basic alert setup."""
    alerts = AlertManager()
    
    # Register console handler
    alerts.register_handler(AlertChannel.CONSOLE, console_handler)
    
    # Send alerts
    alerts.send(
        severity=AlertSeverity.INFO,
        category='SYSTEM',
        title='Trading Bot Started',
        message='All systems operational. Monitoring markets.'
    )
    
    alerts.send(
        severity=AlertSeverity.CRITICAL,
        category='RISK',
        title='Position Size Limit Exceeded',
        message='BTC position exceeds 25% account limit'
    )

def example_with_integrations():
    """Using pre-built integrations."""
    alerts = AlertManager()
    alerts.register_handler(AlertChannel.CONSOLE, console_handler)
    
    # Setup default rules
    TradeAlertIntegrations.setup_default_rules(alerts)
    
    # Simulate fill
    fill = {
        'symbol': 'BTC',
        'side': 'SELL',
        'size': 0.5,
        'price': 51000,
        'realized_pnl': 250.0
    }
    TradeAlertIntegrations.on_fill(alerts, fill)
    
    # Simulate risk breach
    TradeAlertIntegrations.on_risk_breach(
        alerts,
        'Daily Loss Limit',
        {'current': '2.5%', 'limit': '2.0%', 'description': 'Daily loss limit exceeded'}
    )
    
    # Daily summary
    metrics = {
        'total_trades': 5,
        'win_rate': 60.0,
        'total_pnl': 450.0
    }
    TradeAlertIntegrations.daily_summary(alerts, metrics)
    
    # Print summary
    print("\n" + alerts.summary(hours=1))

def example_with_telegram():
    """Setup with Telegram notifications for critical alerts."""
    alerts = AlertManager()
    
    # Console for everything
    alerts.register_handler(AlertChannel.CONSOLE, console_handler)
    
    # Telegram for critical (commented - needs real credentials)
    # tg_handler = telegram_handler("YOUR_BOT_TOKEN", "YOUR_CHAT_ID")
    # alerts.register_handler(AlertChannel.TELEGRAM, tg_handler)
    
    # Add rules with Telegram routing
    alerts.add_rule(AlertRule(
        name="Emergency Stop",
        condition=lambda data: data.get('drawdown', 0) > 0.15,
        severity=AlertSeverity.CRITICAL,
        message_template="EMERGENCY: Drawdown at {drawdown:.1%}. Halting trading.",
        cooldown_minutes=9999,  # Only alert once
        channels=[AlertChannel.CONSOLE, AlertChannel.TELEGRAM]
    ))
    
    # Simulate emergency
    alerts.check_rules({'drawdown': 0.18})


# === QUICK REFERENCE ===

"""
Integration Pattern:

# Setup
alerts = AlertManager()
alerts.register_handler(AlertChannel.CONSOLE, console_handler)
alerts.register_handler(AlertChannel.FILE, file_handler("alerts.log"))

# Optional: Telegram for critical
# alerts.register_handler(AlertChannel.TELEGRAM, telegram_handler(token, chat_id))

# Auto-rules
TradeAlertIntegrations.setup_default_rules(alerts)

# In trade execution flow
TradeAlertIntegrations.on_fill(alerts, fill_data)

# In risk monitoring
if portfolio.drawdown > 0.10:
    TradeAlertIntegrations.on_drawdown(alerts, portfolio.drawdown, 0.10)

# Periodic checks
alerts.check_rules({'consecutive_losses': loss_streak})

# Daily summary
if time_for_daily_summary():
    TradeAlertIntegrations.daily_summary(alerts, journal.calculate_metrics(days=1))

Alert Routing by Severity:
- CRITICAL: Console + Telegram (immediate)
- WARNING: Console + Telegram (batched if needed)
- INFO: Console only (or file)
- DEBUG: File only

Throttling:
- Same rule won't fire within cooldown period
- Suppress categories temporarily if needed
- Acknowledge alerts to track what's been seen
"""

if __name__ == "__main__":
    example_basic_usage()
    print("\n" + "="*50 + "\n")
    example_with_integrations()
```

## Features

| Feature | Purpose |
|---------|---------|
| **Severity Levels** | CRITICAL/WARNING/INFO/DEBUG routing |
| **Channel Routing** | Console, Telegram, Email, Webhook, File |
| **Auto-Rules** | Fire alerts based on conditions with cooldowns |
| **Throttling** | Prevent spam with per-rule cooldowns |
| **Acknowledgment** | Track which alerts have been seen |
| **Integrations** | Pre-built hooks for fills, risk, drawdown |

## Integration Points

1. **On Fill** → Fill confirmation + PnL
2. **On Risk Breach** → Immediate notification
3. **On Drawdown** → Warning at thresholds
4. **Daily Summary** → Performance digest
5. **Auto-Rules** → Consecutive losses, win rate drops

**File:** `agents/ghost/learning/2026-02-19-0323-trading-alert-system.md`

Immediately useful for: staying informed without noise, getting critical alerts instantly, tracking what's been acknowledged, and integrating alerts across all trading utilities (journal, risk monitor, position sizer).