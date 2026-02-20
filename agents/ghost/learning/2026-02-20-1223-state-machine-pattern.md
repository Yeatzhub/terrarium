# State Machine Pattern — Type-Safe Transitions

**Purpose:** Manage complex state transitions with validation, side effects, and history  
**Use Case:** Order lifecycle, strategy states, connection management, workflow engines

## The Pattern

```python
"""
State Machine Pattern
Type-safe state transitions with guards, side effects, and transition history.
Perfect for order states, strategy lifecycle, connection management.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Callable, Optional, Set, Any, TypeVar, Generic
from enum import Enum, auto
from datetime import datetime
from functools import wraps
import inspect


T = TypeVar('T')


class TransitionError(Exception):
    """Invalid state transition attempted."""
    pass


@dataclass
class Transition:
    """Recorded state transition."""
    from_state: str
    to_state: str
    timestamp: datetime
    trigger: str
    data: Optional[Dict] = None
    duration_ms: Optional[float] = None


@dataclass
class StateConfig:
    """Configuration for a state."""
    on_enter: Optional[Callable] = None
    on_exit: Optional[Callable] = None
    allowed_transitions: Set[str] = field(default_factory=set)
    auto_transitions: Dict[str, Callable] = field(default_factory=dict)  # condition -> next_state


class StateMachine:
    """
    Finite state machine with guards, side effects, and history.
    
    Usage:
        class OrderState(Enum):
            PENDING = auto()
            FILLED = auto()
            PARTIAL = auto()
            CANCELLED = auto()
        
        sm = StateMachine(OrderState, initial=OrderState.PENDING)
        sm.add_transition(OrderState.PENDING, OrderState.FILLED, guard=validate_fill)
        sm.transition_to(OrderState.FILLED, data={"fill_price": 150.0})
    """
    
    def __init__(
        self,
        states: Any,  # Enum class or list of strings
        initial: Any,
        name: str = "state_machine"
    ):
        self.name = name
        
        # Handle Enum or list
        if inspect.isclass(states) and issubclass(states, Enum):
            self.states = {s.name: s for s in states}
            self.state_enum = states
        else:
            self.states = {s: s for s in states}
            self.state_enum = None
        
        self.current = self._normalize_state(initial)
        self.current_state_obj = initial if isinstance(initial, Enum) else None
        
        # Configuration
        self._transitions: Dict[str, Set[str]] = {}  # from_state -> {to_states}
        self._guards: Dict[tuple, Callable] = {}     # (from, to) -> guard_fn
        self._on_transition: Dict[tuple, Callable] = {}  # (from, to) -> effect_fn
        self._state_config: Dict[str, StateConfig] = {}
        
        # History
        self.history: List[Transition] = []
        self._state_timestamps: Dict[str, datetime] = {}
        self._enter_time: Optional[datetime] = None
        
        # Record initial state
        self._record_transition(None, self.current, "__init__")
        self._enter_time = datetime.now()
    
    def _normalize_state(self, state: Any) -> str:
        """Convert state to string name."""
        if isinstance(state, Enum):
            return state.name
        return str(state)
    
    def _get_state_obj(self, state_name: str) -> Any:
        """Get original state object (Enum or string)."""
        if self.state_enum:
            return self.state_enum[state_name]
        return state_name
    
    def add_transition(
        self,
        from_state: Any,
        to_state: Any,
        guard: Optional[Callable[[Any], bool]] = None,
        on_transition: Optional[Callable[[Any, Any, Dict], None]] = None
    ):
        """Add allowed transition with optional guard and side effect."""
        from_name = self._normalize_state(from_state)
        to_name = self._normalize_state(to_state)
        
        if from_name not in self._transitions:
            self._transitions[from_name] = set()
        
        self._transitions[from_name].add(to_name)
        
        if guard:
            self._guards[(from_name, to_name)] = guard
        
        if on_transition:
            self._on_transition[(from_name, to_name)] = on_transition
        
        return self
    
    def add_global_transition(
        self,
        from_states: List[Any],
        to_state: Any,
        guard: Optional[Callable] = None
    ):
        """Add same transition from multiple states."""
        for from_state in from_states:
            self.add_transition(from_state, to_state, guard)
        return self
    
    def configure_state(
        self,
        state: Any,
        on_enter: Optional[Callable] = None,
        on_exit: Optional[Callable] = None,
        auto_transitions: Optional[Dict[str, Callable]] = None
    ):
        """Configure state with entry/exit handlers."""
        state_name = self._normalize_state(state)
        
        self._state_config[state_name] = StateConfig(
            on_enter=on_enter,
            on_exit=on_exit,
            auto_transitions=auto_transitions or {}
        )
        return self
    
    def can_transition(self, to_state: Any, context: Optional[Dict] = None) -> bool:
        """Check if transition is allowed."""
        to_name = self._normalize_state(to_state)
        
        # Check if transition exists
        if to_name not in self._transitions.get(self.current, set()):
            return False
        
        # Check guard
        guard = self._guards.get((self.current, to_name))
        if guard:
            try:
                ctx = context or {}
                return guard(self._get_state_obj(self.current), self._get_state_obj(to_name), ctx)
            except Exception:
                return False
        
        return True
    
    def transition_to(
        self,
        to_state: Any,
        data: Optional[Dict] = None,
        force: bool = False
    ) -> bool:
        """
        Attempt state transition.
        
        Args:
            to_state: Target state
            data: Context data for guards and effects
            force: Skip validation (use with caution)
        
        Returns:
            True if transition succeeded
        """
        to_name = self._normalize_state(to_state)
        from_name = self.current
        
        if not force and not self.can_transition(to_state, data):
            raise TransitionError(
                f"Cannot transition from {from_name} to {to_name}. "
                f"Allowed: {self._transitions.get(from_name, set())}"
            )
        
        # Execute exit handler
        config = self._state_config.get(from_name)
        if config and config.on_exit:
            try:
                config.on_exit(self._get_state_obj(from_name), data)
            except Exception as e:
                if not force:
                    raise TransitionError(f"Exit handler failed: {e}")
        
        # Execute transition effect
        effect = self._on_transition.get((from_name, to_name))
        if effect:
            try:
                effect(
                    self._get_state_obj(from_name),
                    self._get_state_obj(to_name),
                    data or {}
                )
            except Exception as e:
                if not force:
                    raise TransitionError(f"Transition effect failed: {e}")
        
        # Perform transition
        self.current = to_name
        self.current_state_obj = self._get_state_obj(to_name)
        
        # Record transition
        self._record_transition(from_name, to_name, "transition", data)
        
        # Execute enter handler
        new_config = self._state_config.get(to_name)
        if new_config and new_config.on_enter:
            try:
                new_config.on_enter(self._get_state_obj(to_name), data)
            except Exception as e:
                if not force:
                    raise TransitionError(f"Enter handler failed: {e}")
        
        # Check auto-transitions
        if new_config and new_config.auto_transitions:
            for next_state, condition in new_config.auto_transitions.items():
                try:
                    if condition(self._get_state_obj(to_name), data or {}):
                        return self.transition_to(next_state, data)
                except Exception:
                    pass
        
        return True
    
    def _record_transition(
        self,
        from_state: Optional[str],
        to_state: str,
        trigger: str,
        data: Optional[Dict] = None
    ):
        """Record transition in history."""
        now = datetime.now()
        
        duration = None
        if self._enter_time and from_state:
            duration = (now - self._enter_time).total_seconds() * 1000
        
        self.history.append(Transition(
            from_state=from_state or "__start__",
            to_state=to_state,
            timestamp=now,
            trigger=trigger,
            data=data,
            duration_ms=duration
        ))
        
        self._state_timestamps[to_state] = now
        self._enter_time = now
    
    def get_time_in_state(self) -> float:
        """Get milliseconds spent in current state."""
        if self._enter_time:
            return (datetime.now() - self._enter_time).total_seconds() * 1000
        return 0
    
    def get_state_durations(self) -> Dict[str, float]:
        """Get total time spent in each state."""
        durations: Dict[str, float] = {}
        
        for i, trans in enumerate(self.history[1:], 1):  # Skip initial
            if trans.duration_ms:
                state = trans.from_state
                durations[state] = durations.get(state, 0) + trans.duration_ms
        
        # Add current state time
        current_time = self.get_time_in_state()
        durations[self.current] = durations.get(self.current, 0) + current_time
        
        return durations
    
    def is_in(self, *states) -> bool:
        """Check if current state is one of the given states."""
        return self.current in [self._normalize_state(s) for s in states]
    
    def get_allowed_transitions(self) -> Set[str]:
        """Get set of states we can transition to from current."""
        return self._transitions.get(self.current, set())
    
    def get_transition_count(self, from_state: Optional[str] = None, to_state: Optional[str] = None) -> int:
        """Count transitions matching criteria."""
        count = 0
        for trans in self.history:
            if from_state and trans.from_state != from_state:
                continue
            if to_state and trans.to_state != to_state:
                continue
            count += 1
        return count
    
    def __str__(self) -> str:
        return f"StateMachine({self.name}): {self.current}"


# Decorator for state-based methods
class state_aware:
    """
    Decorator that checks state before executing method.
    
    Usage:
        class Order:
            def __init__(self):
                self.sm = StateMachine(OrderState, OrderState.PENDING)
            
            @state_aware(required=OrderState.FILLED)
            def cancel(self):
                # Only works if state is FILLED
                pass
    """
    
    def __init__(self, required: Any, error_msg: Optional[str] = None):
        self.required = required if isinstance(required, (list, set, tuple)) else [required]
        self.error_msg = error_msg
    
    def __call__(self, fn):
        @wraps(fn)
        def wrapper(instance, *args, **kwargs):
            # Assume instance has 'sm' attribute with StateMachine
            sm = getattr(instance, 'sm', None)
            if not sm:
                raise RuntimeError("Instance must have 'sm' StateMachine attribute")
            
            required_names = {sm._normalize_state(s) for s in self.required}
            
            if sm.current not in required_names:
                msg = self.error_msg or f"Method {fn.__name__} requires state in {required_names}, current: {sm.current}"
                raise TransitionError(msg)
            
            return fn(instance, *args, **kwargs)
        
        return wrapper


# Hierarchical state machine
class HierarchicalStateMachine(StateMachine):
    """
    State machine with nested states.
    
    Parent state handlers run for all child states.
    """
    
    def __init__(self, states, initial, name="hsm"):
        super().__init__(states, initial, name)
        self._hierarchy: Dict[str, Optional[str]] = {}  # child -> parent
        self._handlers: Dict[str, Dict] = {}  # state -> {enter, exit}
    
    def set_parent(self, child: Any, parent: Any):
        """Set parent state for hierarchical behavior."""
        self._hierarchy[self._normalize_state(child)] = self._normalize_state(parent)
        return self
    
    def _get_ancestors(self, state: str) -> List[str]:
        """Get list of ancestor states (parent, grandparent, etc)."""
        ancestors = []
        current = state
        while current in self._hierarchy:
            parent = self._hierarchy[current]
            if parent:
                ancestors.append(parent)
                current = parent
            else:
                break
        return ancestors


# === Examples ===

def example_order_lifecycle():
    """Order state machine example."""
    print("=" * 60)
    print("Example: Order Lifecycle State Machine")
    print("=" * 60)
    
    from enum import Enum
    
    class OrderState(Enum):
        PENDING = auto()
        SUBMITTED = auto()
        PARTIAL_FILL = auto()
        FILLED = auto()
        CANCELLED = auto()
        REJECTED = auto()
    
    # Create state machine
    order = StateMachine(OrderState, OrderState.PENDING, name="Order_123")
    
    # Define transitions
    order.add_transition(OrderState.PENDING, OrderState.SUBMITTED)
    order.add_transition(OrderState.SUBMITTED, OrderState.PARTIAL_FILL)
    order.add_transition(OrderState.SUBMITTED, OrderState.FILLED)
    order.add_transition(OrderState.SUBMITTED, OrderState.CANCELLED)
    order.add_transition(OrderState.SUBMITTED, OrderState.REJECTED)
    order.add_transition(OrderState.PARTIAL_FILL, OrderState.FILLED)
    order.add_transition(OrderState.PARTIAL_FILL, OrderState.CANCELLED)
    
    # Add guards
    def guard_filled(from_state, to_state, ctx):
        return ctx.get("filled_qty", 0) >= ctx.get("order_qty", 0)
    
    def guard_partial(from_state, to_state, ctx):
        filled = ctx.get("filled_qty", 0)
        total = ctx.get("order_qty", 1)
        return 0 < filled < total
    
    order.add_transition(OrderState.SUBMITTED, OrderState.FILLED, guard=guard_filled)
    order.add_transition(OrderState.SUBMITTED, OrderState.PARTIAL_FILL, guard=guard_partial)
    
    # Add side effects
    def on_fill(from_state, to_state, ctx):
        print(f"  📊 Order filled at ${ctx.get('fill_price', 'N/A')}")
    
    def on_cancel(from_state, to_state, ctx):
        print(f"  ❌ Order cancelled: {ctx.get('reason', 'No reason')}")
    
    order.add_transition(OrderState.SUBMITTED, OrderState.FILLED, on_transition=on_fill)
    order.add_transition(OrderState.PARTIAL_FILL, OrderState.FILLED, on_transition=on_fill)
    order.add_transition(OrderState.SUBMITTED, OrderState.CANCELLED, on_transition=on_cancel)
    
    # Simulate order lifecycle
    print(f"\n1. Initial state: {order.current}")
    
    order.transition_to(OrderState.SUBMITTED)
    print(f"2. Submitted to exchange: {order.current}")
    
    # Try invalid transition
    try:
        order.transition_to(OrderState.REJECTED)  # No guard/context set
    except TransitionError as e:
        print(f"3. Invalid transition blocked: {e}")
    
    # Partial fill
    order.transition_to(OrderState.PARTIAL_FILL, data={"filled_qty": 50, "order_qty": 100})
    print(f"4. Partial fill: {order.current}")
    
    # Complete fill
    order.transition_to(OrderState.FILLED, data={"filled_qty": 100, "order_qty": 100, "fill_price": 150.50})
    print(f"5. Fully filled: {order.current}")
    
    # Show history
    print(f"\n📜 Transition History:")
    for trans in order.history:
        arrow = f"{trans.from_state} → {trans.to_state}"
        print(f"   [{trans.timestamp.strftime('%H:%M:%S')}] {arrow:<25} ({trans.duration_ms:.0f}ms in previous)")
    
    print(f"\n⏱️  Total time in states:")
    for state, duration in order.get_state_durations().items():
        print(f"   {state}: {duration:.0f}ms")


def example_strategy_states():
    """Trading strategy state machine."""
    print("\n" + "=" * 60)
    print("Example: Strategy State Machine")
    print("=" * 60)
    
    from enum import Enum
    
    class StrategyState(Enum):
        INITIALIZING = auto()
        READY = auto()
        RUNNING = auto()
        PAUSED = auto()
        STOPPING = auto()
        STOPPED = auto()
        ERROR = auto()
    
    sm = StateMachine(StrategyState, StrategyState.INITIALIZING, name="MomentumStrategy")
    
    # Configure states with handlers
    def on_enter_running(state, ctx):
        print(f"  ▶️  Strategy started with capital: ${ctx.get('capital', 0):,.2f}")
    
    def on_exit_running(state, ctx):
        print(f"  ⏸️  Strategy pausing... closing {ctx.get('open_positions', 0)} positions")
    
    def on_enter_error(state, ctx):
        print(f"  🚨 Strategy error: {ctx.get('error', 'Unknown')}")
    
    sm.configure_state(StrategyState.RUNNING, on_enter=on_enter_running, on_exit=on_exit_running)
    sm.configure_state(StrategyState.ERROR, on_enter=on_enter_error)
    
    # Define transitions
    transitions = [
        (StrategyState.INITIALIZING, StrategyState.READY),
        (StrategyState.READY, StrategyState.RUNNING),
        (StrategyState.RUNNING, StrategyState.PAUSED),
        (StrategyState.PAUSED, StrategyState.RUNNING),
        (StrategyState.RUNNING, StrategyState.STOPPING),
        (StrategyState.PAUSED, StrategyState.STOPPING),
        (StrategyState.STOPPING, StrategyState.STOPPED),
    ]
    
    for from_state, to_state in transitions:
        sm.add_transition(from_state, to_state)
    
    # Global error transition
    sm.add_global_transition(
        [StrategyState.INITIALIZING, StrategyState.READY, StrategyState.RUNNING, StrategyState.PAUSED],
        StrategyState.ERROR
    )
    
    # Simulate strategy lifecycle
    print()
    sm.transition_to(StrategyState.READY)
    print(f"State: {sm.current}")
    
    sm.transition_to(StrategyState.RUNNING, data={"capital": 100000, "open_positions": 0})
    print(f"State: {sm.current}")
    
    sm.transition_to(StrategyState.PAUSED, data={"open_positions": 3})
    print(f"State: {sm.current}")
    
    sm.transition_to(StrategyState.RUNNING)
    print(f"State: {sm.current}")
    
    sm.transition_to(StrategyState.STOPPING)
    print(f"State: {sm.current}")
    
    sm.transition_to(StrategyState.STOPPED)
    print(f"State: {sm.current}")


def example_connection_manager():
    """Connection state machine with auto-retry."""
    print("\n" + "=" * 60)
    print("Example: Connection State Machine")
    print("=" * 60)
    
    from enum import Enum
    
    class ConnectionState(Enum):
        DISCONNECTED = auto()
        CONNECTING = auto()
        CONNECTED = auto()
        RECONNECTING = auto()
        AUTHENTICATED = auto()
        ERROR = auto()
    
    conn = StateMachine(ConnectionState, ConnectionState.DISCONNECTED, name="WebSocket")
    
    # Add auto-transition: if connect fails, go to ERROR
    def connect_fails(current_state, ctx):
        return ctx.get("connection_failed", False)
    
    conn.configure_state(
        ConnectionState.CONNECTING,
        auto_transitions={"ERROR": connect_fails}
    )
    
    # Transitions
    conn.add_transition(ConnectionState.DISCONNECTED, ConnectionState.CONNECTING)
    conn.add_transition(ConnectionState.CONNECTING, ConnectionState.CONNECTED)
    conn.add_transition(ConnectionState.CONNECTING, ConnectionState.ERROR)
    conn.add_transition(ConnectionState.CONNECTED, ConnectionState.AUTHENTICATED)
    conn.add_transition(ConnectionState.CONNECTED, ConnectionState.RECONNECTING)
    conn.add_transition(ConnectionState.RECONNECTING, ConnectionState.CONNECTED)
    conn.add_transition(ConnectionState.ERROR, ConnectionState.RECONNECTING)
    
    # Simulate
    print()
    conn.transition_to(ConnectionState.CONNECTING)
    print(f"Connecting... {conn.current}")
    
    # Simulate failed connection
    conn.transition_to(ConnectionState.ERROR, data={"connection_failed": True})
    print(f"Connection failed: {conn.current}")
    
    conn.transition_to(ConnectionState.RECONNECTING)
    print(f"Retrying... {conn.current}")
    
    conn.transition_to(ConnectionState.CONNECTED)
    print(f"Connected: {conn.current}")
    
    conn.transition_to(ConnectionState.AUTHENTICATED)
    print(f"Ready: {conn.current}")
    
    print(f"\n✅ Connection ready after {len(conn.history)-1} transitions")


def example_state_decorator():
    """Using state_aware decorator."""
    print("\n" + "=" * 60)
    print("Example: State-Aware Methods")
    print("=" * 60)
    
    from enum import Enum
    
    class DoorState(Enum):
        CLOSED = auto()
        OPEN = auto()
        LOCKED = auto()
    
    class Door:
        def __init__(self):
            self.sm = StateMachine(DoorState, DoorState.CLOSED, name="FrontDoor")
            self.sm.add_transition(DoorState.CLOSED, DoorState.OPEN)
            self.sm.add_transition(DoorState.OPEN, DoorState.CLOSED)
            self.sm.add_transition(DoorState.CLOSED, DoorState.LOCKED)
            self.sm.add_transition(DoorState.LOCKED, DoorState.CLOSED)
        
        @state_aware(required=DoorState.OPEN, error_msg="Cannot walk through closed door")
        def walk_through(self):
            print("  🚶 Walking through the door")
        
        @state_aware(required=[DoorState.CLOSED, DoorState.OPEN])
        def knock(self):
            print("  ✊ Knock knock")
        
        def open(self):
            self.sm.transition_to(DoorState.OPEN)
            print("  🚪 Door opened")
        
        def close(self):
            self.sm.transition_to(DoorState.CLOSED)
            print("  🚪 Door closed")
        
        def lock(self):
            self.sm.transition_to(DoorState.LOCKED)
            print("  🔒 Door locked")
    
    door = Door()
    print(f"\nInitial: {door.sm.current}")
    
    door.knock()  # Works from CLOSED
    
    try:
        door.walk_through()  # Fails - door is closed
    except TransitionError as e:
        print(f"  ❌ {e}")
    
    door.open()
    door.walk_through()  # Works now
    door.knock()  # Still works
    door.close()
    door.lock()
    
    try:
        door.knock()  # Fails - locked
    except TransitionError as e:
        print(f"  ❌ Cannot knock while locked")


if __name__ == "__main__":
    example_order_lifecycle()
    example_strategy_states()
    example_connection_manager()
    example_state_decorator()
    
    print("\n" + "=" * 60)
    print("State machines prevent invalid transitions and enforce")
    print("proper sequencing. Essential for order management,")
    print("strategy lifecycle, and connection handling.")
    print("=" * 60)
```

## Pattern Benefits

| Feature | Benefit |
|---------|---------|
| **Type-safe** | Can't transition to invalid states at runtime |
| **Guards** | Conditional transitions based on context |
| **Side effects** | Auto-run code on enter/exit/transition |
| **History** | Full audit trail of all state changes |
| **Timing** | Track time spent in each state |
| **Auto-transitions** | Conditional automatic state progression |

## Quick Reference

```python
# Define states
class OrderState(Enum):
    PENDING = auto()
    FILLED = auto()
    CANCELLED = auto()

# Create machine
sm = StateMachine(OrderState, OrderState.PENDING)

# Add transitions
sm.add_transition(OrderState.PENDING, OrderState.FILLED)
sm.add_transition(OrderState.PENDING, OrderState.CANCELLED)

# With guard
sm.add_transition(
    OrderState.PENDING, OrderState.FILLED,
    guard=lambda from_s, to_s, ctx: ctx.get("qty", 0) > 0
)

# With side effect
sm.add_transition(
    OrderState.PENDING, OrderState.FILLED,
    on_transition=lambda f, t, ctx: print(f"Filled at {ctx['price']}")
)

# Transition
sm.transition_to(OrderState.FILLED, data={"qty": 100, "price": 150.0})

# Check state
if sm.is_in(OrderState.FILLED, OrderState.PARTIAL_FILL):
    print("Order has fills")
```

## When to Use State Machines

- **Order lifecycle** — PENDING → SUBMITTED → PARTIAL → FILLED
- **Strategy states** — INITIALIZING → RUNNING → PAUSED → STOPPING
- **Connections** — DISCONNECTED → CONNECTING → CONNECTED → AUTHENTICATED
- **Workflows** — DRAFT → REVIEW → APPROVED → PUBLISHED
- **Any complex lifecycle** — States + valid transitions prevent bugs

---

**Created by Ghost 👻 | Feb 20, 2026 | 14-min learning sprint**  
*Lesson: "If it has states and rules, use a state machine." Prevents illegal transitions, tracks history, runs side effects automatically. Your order won't accidentally go from PENDING to CANCELLED without passing through the right checks.*
