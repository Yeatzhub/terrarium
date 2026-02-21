# Circuit Breaker Pattern — Trading System Protection

**Purpose:** Halt trading automatically when error rates spike, volatility explodes, or conditions become unfavorable  
**Use Case:** Prevent runaway losses, stop trading during system errors, protect during market dislocations

## The Code

```python
"""
Circuit Breaker Pattern
Temporarily disable trading when conditions deteriorate.
Prevents revenge trading, system errors, and runaway losses.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Set
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque
import threading
import time


class CircuitState(Enum):
    CLOSED = auto()     # Normal trading
    OPEN = auto()       # Trading halted
    HALF_OPEN = auto()  # Testing if conditions improved


class CircuitTrigger(Enum):
    CONSECUTIVE_LOSSES = auto()
    ERROR_RATE = auto()
    VOLATILITY_SPIKE = auto()
    MAX_DRAWDOWN = auto()
    MANUAL = auto()
    SCHEDULE = auto()
    SYSTEM_ERROR = auto()


@dataclass
class CircuitEvent:
    """Circuit breaker state change event."""
    timestamp: datetime
    old_state: CircuitState
    new_state: CircuitState
    trigger: CircuitTrigger
    reason: str
    details: Dict = field(default_factory=dict)


@dataclass
class CircuitConfig:
    """Configuration for circuit breaker."""
    # Loss-based triggers
    max_consecutive_losses: int = 3
    max_daily_loss_pct: float = 5.0
    max_weekly_loss_pct: float = 10.0
    
    # Error-based triggers
    max_error_rate: float = 0.2  # 20% error rate
    error_window_minutes: int = 10
    
    # Volatility trigger
    volatility_threshold: Optional[float] = None
    
    # Drawdown trigger
    max_drawdown_pct: float = 10.0
    
    # Recovery
    recovery_test_trades: int = 1
    recovery_timeout_minutes: int = 15
    
    # Cooldown after opening
    min_open_duration_minutes: int = 5
    
    # Callbacks
    on_open: Optional[Callable] = None
    on_close: Optional[Callable] = None
    on_half_open: Optional[Callable] = None


@dataclass 
class CircuitStats:
    """Circuit breaker statistics."""
    total_opens: int
    total_closes: int
    current_state: CircuitState
    last_open_time: Optional[datetime]
    last_close_time: Optional[datetime]
    total_open_duration: timedelta
    
    # Triggers
    opens_by_trigger: Dict[CircuitTrigger, int]
    
    # Trading stats during last open
    trades_tested: int
    trades_blocked: int


class CircuitBreaker:
    """
    Circuit breaker for trading systems.
    
    Prevents trading when:
    - Consecutive losses exceed threshold
    - Error rate spikes
    - Volatility explodes
    - Drawdown limit breached
    - Manual override
    
    Usage:
        circuit = CircuitBreaker(
            max_consecutive_losses=3,
            max_daily_loss_pct=5
        )
        
        @circuit.protected
        def execute_trade(symbol, qty, price):
            # Trade logic
            return result
        
        # Or manual check
        if circuit.can_trade():
            execute_trade()
    """
    
    def __init__(self, config: Optional[CircuitConfig] = None):
        self.config = config or CircuitConfig()
        self.state = CircuitState.CLOSED
        
        # Tracking
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.errors_in_window: deque = deque()
        self.daily_pnl = 0.0
        self.peak_equity = 0.0
        self._lock = threading.Lock()
        
        # Testing
        self.test_trades_to_close = 0
        self.test_trades_successful = 0
        
        # History
        self.events: List[CircuitEvent] = []
        self.state_changes: List[CircuitEvent] = []
        
        # Stats
        self.total_opens = 0
        self.total_closes = 0
        self.last_open_time: Optional[datetime] = None
        self.last_close_time: Optional[datetime] = None
        self.total_open_duration = timedelta()
        self.opens_by_trigger: Dict[CircuitTrigger, int] = {}
        self.trades_blocked = 0
        
        # Schedule
        self.block_until: Optional[datetime] = None
        self.allowed_hours: Optional[tuple] = None
    
    def can_trade(self) -> bool:
        """Check if trading is allowed."""
        with self._lock:
            # Check scheduled blocks
            if self.block_until and datetime.now() < self.block_until:
                return False
            
            # Check time restrictions
            if self.allowed_hours:
                current_hour = datetime.now().hour + datetime.now().minute / 60
                if not (self.allowed_hours[0] <= current_hour <= self.allowed_hours[1]):
                    return False
            
            # Check state
            if self.state == CircuitState.OPEN:
                self.trades_blocked += 1
                return False
            
            if self.state == CircuitState.HALF_OPEN:
                return True  # Allow test trades
            
            return True
    
    def record_trade(self, pnl: float, is_error: bool = False) -> bool:
        """Record trade outcome and check if circuit should open."""
        with self._lock:
            # Update P&L
            self.daily_pnl += pnl
            
            # Track errors
            if is_error:
                self.errors_in_window.append(datetime.now())
                self._cleanup_error_window()
            
            # Update consecutive counts
            if pnl > 0:
                self.consecutive_wins += 1
                self.consecutive_losses = 0
            elif pnl < 0:
                self.consecutive_losses += 1
                self.consecutive_wins = 0
            
            # Check if circuit should open
            if self.state == CircuitState.CLOSED:
                self._check_triggers()
            
            # Check recovery in half-open state
            elif self.state == CircuitState.HALF_OPEN:
                self.test_trades_to_close -= 1
                if pnl > 0:
                    self.test_trades_successful += 1
                
                if self.test_trades_to_close <= 0:
                    if self.test_trades_successful > 0:
                        self.close(CircuitTrigger.CONSECUTIVE_LOSSES, "Recovery verified")
                    else:
                        # Re-open
                        self.open(CircuitTrigger.CONSECUTIVE_LOSSES, "Recovery failed")
            
            return self.state != CircuitState.OPEN
    
    def open(self, trigger: CircuitTrigger, reason: str, details: Optional[Dict] = None):
        """Manually open circuit."""
        with self._lock:
            if self.state == CircuitState.OPEN:
                return
            
            old_state = self.state
            self.state = CircuitState.OPEN
            self.last_open_time = datetime.now()
            self.total_opens += 1
            
            self.opens_by_trigger[trigger] = self.opens_by_trigger.get(trigger, 0) + 1
            
            event = CircuitEvent(
                timestamp=datetime.now(),
                old_state=old_state,
                new_state=CircuitState.OPEN,
                trigger=trigger,
                reason=reason,
                details=details or {}
            )
            self.events.append(event)
            self.state_changes.append(event)
            
            # Schedule transition to half-open
            self._schedule_half_open()
            
            # Callback
            if self.config.on_open:
                try:
                    self.config.on_open(event)
                except Exception:
                    pass
    
    def close(self, trigger: CircuitTrigger, reason: str):
        """Manually close circuit."""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return
            
            old_state = self.state
            self.state = CircuitState.CLOSED
            self.last_close_time = datetime.now()
            self.total_closes += 1
            
            if self.last_open_time:
                duration = self.last_close_time - self.last_open_time
                self.total_open_duration += duration
            
            # Reset counters
            self.consecutive_losses = 0
            self.consecutive_wins = 0
            self.test_trades_to_close = 0
            self.test_trades_successful = 0
            
            event = CircuitEvent(
                timestamp=datetime.now(),
                old_state=old_state,
                new_state=CircuitState.CLOSED,
                trigger=trigger,
                reason=reason
            )
            self.events.append(event)
            self.state_changes.append(event)
            
            if self.config.on_close:
                try:
                    self.config.on_close(event)
                except Exception:
                    pass
    
    def _check_triggers(self):
        """Check if any triggers should open circuit."""
        # Consecutive losses
        if self.consecutive_losses >= self.config.max_consecutive_losses:
            self.open(
                CircuitTrigger.CONSECUTIVE_LOSSES,
                f"{self.consecutive_losses} consecutive losses",
                {"losses": self.consecutive_losses}
            )
            return
        
        # Error rate
        self._cleanup_error_window()
        recent_errors = len(self.errors_in_window)
        recent_trades = 10  # Assume window size
        error_rate = recent_errors / recent_trades if recent_trades > 0 else 0
        
        if error_rate >= self.config.max_error_rate:
            self.open(
                CircuitTrigger.ERROR_RATE,
                f"Error rate {error_rate:.0%} exceeds threshold",
                {"error_count": recent_errors, "error_rate": error_rate}
            )
            return
        
        # Daily loss
        if self.config.max_daily_loss_pct > 0:
            if self.daily_pnl < -self.config.max_daily_loss_pct:
                self.open(
                    CircuitTrigger.MAX_DRAWDOWN,
                    f"Daily loss {self.daily_pnl:.1f}% exceeds limit",
                    {"daily_pnl": self.daily_pnl}
                )
                return
    
    def _schedule_half_open(self):
        """Schedule transition to half-open state."""
        def transition():
            time.sleep(self.config.recovery_timeout_minutes * 60)
            with self._lock:
                if self.state == CircuitState.OPEN:
                    self.state = CircuitState.HALF_OPEN
                    self.test_trades_to_close = self.config.recovery_test_trades
                    self.test_trades_successful = 0
                    
                    event = CircuitEvent(
                        timestamp=datetime.now(),
                        old_state=CircuitState.OPEN,
                        new_state=CircuitState.HALF_OPEN,
                        trigger=CircuitTrigger.MANUAL,
                        reason="Testing if conditions improved"
                    )
                    self.events.append(event)
                    
                    if self.config.on_half_open:
                        try:
                            self.config.on_half_open(event)
                        except Exception:
                            pass
        
        thread = threading.Thread(target=transition, daemon=True)
        thread.start()
    
    def _cleanup_error_window(self):
        """Remove old errors from window."""
        cutoff = datetime.now() - timedelta(minutes=self.config.error_window_minutes)
        while self.errors_in_window and self.errors_in_window[0] < cutoff:
            self.errors_in_window.popleft()
    
    def reset_daily_stats(self):
        """Reset daily counters (call at market open)."""
        with self._lock:
            self.daily_pnl = 0.0
            self.consecutive_losses = 0
            self.consecutive_wins = 0
    
    def block_for_minutes(self, minutes: int, reason: str = "Manual block"):
        """Temporarily block trading."""
        self.block_until = datetime.now() + timedelta(minutes=minutes)
        print(f"Trading blocked for {minutes} minutes: {reason}")
    
    def set_trading_hours(self, start_hour: float, end_hour: float):
        """Set allowed trading hours (e.g., 9.5 = 9:30 AM)."""
        self.allowed_hours = (start_hour, end_hour)
    
    def get_stats(self) -> CircuitStats:
        """Get circuit breaker statistics."""
        return CircuitStats(
            total_opens=self.total_opens,
            total_closes=self.total_closes,
            current_state=self.state,
            last_open_time=self.last_open_time,
            last_close_time=self.last_close_time,
            total_open_duration=self.total_open_duration,
            opens_by_trigger=self.opens_by_trigger.copy(),
            trades_tested=max(0, self.config.recovery_test_trades - self.test_trades_to_close),
            trades_blocked=self.trades_blocked
        )
    
    def get_state(self) -> CircuitState:
        """Get current state."""
        return self.state
    
    def protected(self, func: Callable) -> Callable:
        """Decorator to protect function with circuit breaker."""
        def wrapper(*args, **kwargs):
            if not self.can_trade():
                raise CircuitOpenError(f"Circuit breaker is {self.state.name}")
            return func(*args, **kwargs)
        return wrapper


class CircuitOpenError(Exception):
    """Exception raised when trying to trade with open circuit."""
    pass


def format_circuit_status(circuit: CircuitBreaker) -> str:
    """Format circuit breaker status."""
    state = circuit.get_state()
    stats = circuit.get_stats()
    
    emoji = {
        CircuitState.CLOSED: "✅",
        CircuitState.OPEN: "🔴",
        CircuitState.HALF_OPEN: "🟡"
    }[state]
    
    lines = [
        f"{'=' * 70}",
        f"CIRCUIT BREAKER STATUS",
        f"{'=' * 70}",
        "",
        f"State: {emoji} {state.name}",
        f"Consecutive Losses: {circuit.consecutive_losses}",
        f"Daily P&L: ${circuit.daily_pnl:+.2f}",
        "",
        "STATISTICS:",
        f"  Total Opens: {stats.total_opens}",
        f"  Total Closes: {stats.total_closes}",
        f"  Trades Blocked: {stats.trades_blocked}",
        f"  Time in Open: {stats.total_open_duration}",
        "",
    ]
    
    if stats.last_open_time:
        lines.append(f"Last Open: {stats.last_open_time.strftime('%Y-%m-%d %H:%M')}")
    
    if stats.opens_by_trigger:
        lines.extend(["", "OPENS BY TRIGGER:"])
        for trigger, count in stats.opens_by_trigger.items():
            lines.append(f"  {trigger.name}: {count}")
    
    if circuit.events:
        lines.extend(["", "RECENT EVENTS:"])
        for event in circuit.events[-5:]:
            lines.append(
                f"  {event.timestamp.strftime('%H:%M')} | "
                f"{event.old_state.name} → {event.new_state.name} | "
                f"{event.reason[:40]}"
            )
    
    lines.append(f"{'=' * 70}")
    
    return "\n".join(lines)


# === Examples ===

def example_circuit_basic():
    """Basic circuit breaker usage."""
    print("=" * 70)
    print("Circuit Breaker Demo - Basic Usage")
    print("=" * 70)
    
    circuit = CircuitBreaker(
        CircuitConfig(max_consecutive_losses=3)
    )
    
    trades = [100, -50, 80, -100, -60, -40, 70, 90, -30, -20, -10, 50]
    
    print("\nSimulating trades...")
    print(f"{'Trade':<10} {'P&L':<10} {'State':<15} {'Result'}")
    print("-" * 70)
    
    for i, pnl in enumerate(trades):
        allowed = circuit.can_trade()
        circuit.record_trade(pnl)
        state = circuit.get_state()
        
        status = "EXECUTED" if allowed else "BLOCKED"
        emoji = "✅" if pnl > 0 else "❌" if pnl < 0 else "⚪"
        
        print(f"{i+1:<10} ${pnl:+7.0f}    {state.name:<15} {emoji} {status}")
    
    print("\n" + format_circuit_status(circuit))


def example_circuit_decorator():
    """Using decorator pattern."""
    print("\n" + "=" * 70)
    print("Circuit Breaker Demo - Decorator Pattern")
    print("=" * 70)
    
    circuit = CircuitBreaker(
        CircuitConfig(max_consecutive_losses=2)
    )
    
    @circuit.protected
    def execute_trade(symbol: str, qty: int, price: float):
        print(f"  Executed: {qty} {symbol} @ ${price}")
        return {"filled": qty, "price": price}
    
    print("\nAttempting trades...")
    
    for i in range(5):
        try:
            result = execute_trade("AAPL", 100, 175.0 + i)
            circuit.record_trade(-100)  # Simulated loss
        except CircuitOpenError as e:
            print(f"  ❌ Blocked: {e}")
    
    print(f"\nFinal state: {circuit.get_state().name}")


def example_error_rate_protection():
    """Circuit breaker for error rate."""
    print("\n" + "=" * 70)
    print("Circuit Breaker Demo - Error Rate Protection")
    print("=" * 70)
    
    circuit = CircuitBreaker(
        CircuitConfig(max_error_rate=0.3, error_window_minutes=5)
    )
    
    # Simulate API errors
    errors = [False, False, True, True, True, False, True]
    
    print("\nSimulating API calls...")
    print(f"{'Call':<8} {'Error':<8} {'Circuit':<12} {'Result'}")
    print("-" * 70)
    
    for i, has_error in enumerate(errors):
        circuit.record_trade(100, is_error=has_error)
        state = circuit.get_state()
        
        if state == CircuitState.OPEN:
            print(f"{i+1:<8} {str(has_error):<8} {state.name:<12} 🔴 CIRCUIT OPEN")
        else:
            print(f"{i+1:<8} {str(has_error):<8} {state.name:<12} ✅ OK")


def example_daily_loss_limit():
    """Circuit breaker for daily loss."""
    print("\n" + "=" * 70)
    print("Circuit Breaker Demo - Daily Loss Limit")
    print("=" * 70)
    
    circuit = CircuitBreaker(
        CircuitConfig(max_daily_loss_pct=500)  # $500
    )
    
    trades = [-100, -150, -80, -120, -60, 90]
    
    print("\nSimulating trading day...")
    print(f"Daily loss limit: $500")
    print(f"{'Trade':<10} {'P&L':<12} {'Cumulative':<15} {'Status'}")
    print("-" * 70)
    
    for pnl in trades:
        old_state = circuit.get_state()
        circuit.record_trade(pnl)
        new_state = circuit.get_state()
        
        cum_pnl = circuit.daily_pnl
        status = "🔴 CIRCUIT OPEN" if new_state == CircuitState.OPEN else "✅ Trading"
        
        print(f"${pnl:+8.0f}    ${cum_pnl:+8.0f}       {status}")


def example_circuit_stats():
    """Circuit breaker statistics."""
    print("\n" + "=" * 70)
    print("Circuit Breaker Demo - Statistics")
    print("=" * 70)
    
    circuit = CircuitBreaker(
        CircuitConfig(max_consecutive_losses=2)
    )
    
    # Simulate trading with circuit opens
    trades = [
        (100, False),
        (-50, False),
        (-100, False),  # Circuit opens
        (-60, False),   # Blocked
        (90, False),    # Recovery
        (80, False),
        (-120, False),  # Circuit opens again
        (-50, False),   # Blocked
        (70, False),    # Recovery
    ]
    
    for pnl, is_error in trades:
        circuit.record_trade(pnl, is_error=is_error)
    
    stats = circuit.get_stats()
    
    print("\nFinal Statistics:")
    print(f"  Total times circuit opened: {stats.total_opens}")
    print(f"  Total times circuit closed: {stats.total_closes}")
    print(f"  Current state: {stats.current_state.name}")
    print(f"  Total time in open: {stats.total_open_duration}")
    print(f"  Trades blocked: {stats.trades_blocked}")
    print(f"  Opens by trigger: {dict(stats.opens_by_trigger)}")


if __name__ == "__main__":
    example_circuit_basic()
    example_circuit_decorator()
    example_error_rate_protection()
    example_daily_loss_limit()
    example_circuit_stats()
    
    print("\n" + "=" * 70)
    print("CIRCUIT BREAKER BEST PRACTICES:")
    print("=" * 70)
    print("""
1. SET APPROPRIATE THRESHOLDS:
   • Consecutive losses: 3-5 (strategy dependent)
   • Daily loss: 3-5% of account
   • Error rate: 10-20% in short window
   
2. USE RECOVERY MODE:
   • After opening, test with small positions
   • Close only after successful test trades
   • Prevent immediate re-opening

3. COMBINE TRIGGERS:
   • Multiple protection layers
   • Loss limits + Error rate + Manual override
   
4. MONITOR AND ADJUST:
   • Track circuit open frequency
   • Adjust thresholds if too sensitive/not protective enough
   • Review blocked trades for patterns

5. NEVER OVERRIDE WITHOUT REVIEW:
   • Forced closes should be rare
   • Document reasons for manual overrides
   • Learn from what triggered opens

The circuit breaker is your safety net.
    """)
    print("=" * 70)
```

## Circuit States

| State | Meaning | Action |
|-------|---------|--------|
| **CLOSED** | Normal operation | Trade freely |
| **OPEN** | Trading halted | No new trades |
| **HALF_OPEN** | Testing conditions | Small test trades only |

## Triggers

| Trigger | When It Opens | Recovery |
|---------|---------------|----------|
| **CONSECUTIVE_LOSSES** | N losses in a row | Wait + test trades |
| **ERROR_RATE** | API errors spike | Wait for stability |
| **MAX_DRAWDOWN** | Daily loss limit hit | Next day |
| **MANUAL** | You intervene | Manual close |
| **VOLATILITY** | Market chaos | Wait for calm |

## Quick Reference

```python
# Create circuit
circuit = CircuitBreaker(
    max_consecutive_losses=3,
    max_daily_loss_pct=5.0
)

# Check before trading
if circuit.can_trade():
    result = execute_trade()
    circuit.record_trade(pnl)

# Or use decorator
@circuit.protected
def trade():
    # Trading logic
    pass

# Manual control
circuit.open(CircuitTrigger.MANUAL, "Emergency stop")
circuit.close(CircuitTrigger.MANUAL, "Conditions improved")
```

## Why This Matters

- **Prevents runaway losses** — Stop trading when you're off
- **Protects from errors** — API failures don't cascade
- **Enforces discipline** — Can't revenge trade through it
- **Automatic recovery** — Tests before resuming
- **Saves accounts** — Better to pause than blow up

**The circuit breaker is your emergency brake. Use it before you need it.**

---

**Created by Ghost 👻 | Feb 20, 2026 | 12-min learning sprint**  
*Lesson: "The best time to stop trading is before you're forced to." A circuit breaker automatically halts trading when conditions turn bad—consecutive losses, error spikes, volatility. It's your safety net when emotions override discipline.*
