# Session Manager — Trading State Persistence

**Purpose:** Maintain trading session state across restarts, track positions, and enable recovery  
**Use Case:** Resume trading after crashes, maintain P&L across sessions, persistent position tracking

## The Code

```python
"""
Trading Session Manager
Persistent session state for trading operations.
Track positions, P&L, and session lifecycle across restarts.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
import json
import uuid


class SessionStatus(Enum):
    INITIALIZING = auto()
    ACTIVE = auto()
    PAUSED = auto()
    ERROR = auto()
    CLOSING = auto()
    CLOSED = auto()


class PositionStatus(Enum):
    PENDING = auto()
    OPEN = auto()
    CLOSING = auto()
    CLOSED = auto()
    ERROR = auto()


@dataclass
class Position:
    """Tracked position in session."""
    id: str
    symbol: str
    side: str  # 'long' or 'short'
    quantity: float
    entry_price: float
    entry_time: datetime
    
    # Current state
    status: PositionStatus = PositionStatus.PENDING
    current_price: Optional[float] = None
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    
    # Exit info
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    realized_pnl: float = 0.0
    realized_pnl_pct: float = 0.0
    
    # Risk management
    stop_price: Optional[float] = None
    target_price: Optional[float] = None
    risk_amount: float = 0.0
    
    # Metadata
    strategy: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def update_price(self, price: float):
        """Update position with current price."""
        self.current_price = price
        
        if self.side == 'long':
            self.unrealized_pnl = (price - self.entry_price) * self.quantity
        else:
            self.unrealized_pnl = (self.entry_price - price) * self.quantity
        
        invested = self.entry_price * self.quantity
        self.unrealized_pnl_pct = (self.unrealized_pnl / invested) * 100 if invested else 0
    
    def close(self, price: float, time: Optional[datetime] = None):
        """Close the position."""
        self.exit_price = price
        self.exit_time = time or datetime.now()
        self.status = PositionStatus.CLOSED
        
        if self.side == 'long':
            self.realized_pnl = (price - self.entry_price) * self.quantity
        else:
            self.realized_pnl = (self.entry_price - price) * self.quantity
        
        invested = self.entry_price * self.quantity
        self.realized_pnl_pct = (self.realized_pnl / invested) * 100 if invested else 0
    
    def days_open(self) -> float:
        """Days since entry."""
        start = self.entry_time
        end = self.exit_time or datetime.now()
        return (end - start).total_seconds() / 86400


@dataclass
class SessionStats:
    """Session statistics."""
    # Counts
    total_positions: int = 0
    open_positions: int = 0
    closed_positions: int = 0
    pending_positions: int = 0
    
    # P&L
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    total_pnl: float = 0.0
    
    # Win/loss
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    
    # Risk
    total_risk: float = 0.0
    total_exposure: float = 0.0


@dataclass
class Session:
    """Trading session state."""
    id: str
    name: str
    started_at: datetime
    
    # State
    status: SessionStatus
    account_balance: float
    starting_balance: float
    
    # Collections
    positions: Dict[str, Position]
    realized_pnl: float
    
    # Tracking
    last_price_update: Optional[datetime] = None
    last_position_update: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # Metadata
    strategy: str = ""
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    @property
    def duration(self) -> timedelta:
        return datetime.now() - self.started_at
    
    @property
    def total_pnl(self) -> float:
        unrealized = sum(p.unrealized_pnl for p in self.positions.values() if p.status == PositionStatus.OPEN)
        return self.realized_pnl + unrealized


class SessionEncoder(json.JSONEncoder):
    """Custom JSON encoder for session objects."""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Enum):
            return obj.name
        if isinstance(obj, (Position, Session, SessionStats)):
            return asdict(obj)
        return super().default(obj)


def session_decoder(obj: Dict) -> Any:
    """Custom JSON decoder for session objects."""
    if 'started_at' in obj and isinstance(obj.get('started_at'), str):
        obj['started_at'] = datetime.fromisoformat(obj['started_at'])
    if 'entry_time' in obj and isinstance(obj.get('entry_time'), str):
        obj['entry_time'] = datetime.fromisoformat(obj['entry_time'])
    if 'exit_time' in obj and isinstance(obj.get('exit_time'), str):
        obj['exit_time'] = datetime.fromisoformat(obj['exit_time'])
    if 'last_price_update' in obj and isinstance(obj.get('last_price_update'), str):
        obj['last_price_update'] = datetime.fromisoformat(obj['last_price_update'])
    if 'last_position_update' in obj and isinstance(obj.get('last_position_update'), str):
        obj['last_position_update'] = datetime.fromisoformat(obj['last_position_update'])
    
    if 'positions' in obj:
        # Convert positions dict back to Position objects
        obj['positions'] = {
            k: Position(**v) for k, v in obj['positions'].items()
        }
    
    return obj


class SessionManager:
    """
    Manage trading sessions with persistence.
    
    Usage:
        manager = SessionManager(storage_dir="sessions")
        
        # Start new session
        session = manager.start_session(
            name="Momentum Trading - Jan 2024",
            account_balance=100000,
            strategy="momentum"
        )
        
        # Add positions
        position = manager.add_position(
            session_id=session.id,
            symbol="AAPL",
            side="long",
            quantity=100,
            entry_price=175.0,
            stop_price=170.0
        )
        
        # Update prices
        manager.update_prices(session.id, {"AAPL": 178.0})
        
        # Close position
        manager.close_position(session.id, position.id, 180.0)
        
        # Get stats
        stats = manager.get_stats(session.id)
        
        # Save and restore
        manager.save_session(session.id)
        restored = manager.load_session(session.id)
    """
    
    def __init__(self, storage_dir: str = "sessions"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        self.active_sessions: Dict[str, Session] = {}
        self.position_callbacks: List[Callable] = []
        self.price_update_callbacks: List[Callable] = []
    
    def start_session(
        self,
        name: str,
        account_balance: float,
        strategy: str = "",
        tags: Optional[List[str]] = None,
        notes: str = ""
    ) -> Session:
        """Start a new trading session."""
        session_id = str(uuid.uuid4())[:8]
        
        session = Session(
            id=session_id,
            name=name,
            started_at=datetime.now(),
            status=SessionStatus.ACTIVE,
            account_balance=account_balance,
            starting_balance=account_balance,
            positions={},
            realized_pnl=0.0,
            strategy=strategy,
            tags=tags or [],
            notes=notes
        )
        
        self.active_sessions[session_id] = session
        self.save_session(session_id)
        
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID."""
        return self.active_sessions.get(session_id)
    
    def get_all_sessions(self) -> List[Session]:
        """Get all active sessions."""
        return list(self.active_sessions.values())
    
    def get_active_sessions(self) -> List[Session]:
        """Get sessions with open positions."""
        return [
            s for s in self.active_sessions.values()
            if any(p.status == PositionStatus.OPEN for p in s.positions.values())
        ]
    
    def pause_session(self, session_id: str) -> bool:
        """Pause a session."""
        session = self.active_sessions.get(session_id)
        if session and session.status == SessionStatus.ACTIVE:
            session.status = SessionStatus.PAUSED
            self.save_session(session_id)
            return True
        return False
    
    def resume_session(self, session_id: str) -> bool:
        """Resume a paused session."""
        session = self.active_sessions.get(session_id)
        if session and session.status == SessionStatus.PAUSED:
            session.status = SessionStatus.ACTIVE
            self.save_session(session_id)
            return True
        return False
    
    def close_session(self, session_id: str, reason: str = "") -> bool:
        """Close a session."""
        session = self.active_sessions.get(session_id)
        if session:
            session.status = SessionStatus.CLOSED
            session.notes += f"\nClosed: {reason}" if reason else ""
            self.save_session(session_id)
            return True
        return False
    
    def add_position(
        self,
        session_id: str,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        stop_price: Optional[float] = None,
        target_price: Optional[float] = None,
        strategy: str = "",
        tags: Optional[List[str]] = None,
        notes: str = ""
    ) -> Optional[Position]:
        """Add a new position to session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        position_id = str(uuid.uuid4())[:8]
        
        position = Position(
            id=position_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            entry_price=entry_price,
            entry_time=datetime.now(),
            status=PositionStatus.OPEN,
            current_price=entry_price,
            stop_price=stop_price,
            target_price=target_price,
            risk_amount=abs(entry_price - stop_price) * quantity if stop_price else 0,
            strategy=strategy,
            tags=tags or [],
            notes=notes
        )
        
        session.positions[position_id] = position
        session.last_position_update = datetime.now()
        
        self.save_session(session_id)
        self._notify_position_added(position)
        
        return position
    
    def update_position(
        self,
        session_id: str,
        position_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update position fields."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        position = session.positions.get(position_id)
        if not position:
            return False
        
        for key, value in updates.items():
            if hasattr(position, key):
                setattr(position, key, value)
        
        session.last_position_update = datetime.now()
        self.save_session(session_id)
        
        return True
    
    def update_prices(self, session_id: str, prices: Dict[str, float]) -> Dict[str, float]:
        """Update prices for all positions."""
        session = self.active_sessions.get(session_id)
        if not session:
            return {}
        
        updated = {}
        
        for position in session.positions.values():
            if position.status != PositionStatus.OPEN:
                continue
            
            if position.symbol in prices:
                old_pnl = position.unrealized_pnl
                position.update_price(prices[position.symbol])
                updated[position.symbol] = position.unrealized_pnl - old_pnl
        
        session.last_price_update = datetime.now()
        self.save_session(session_id)
        
        self._notify_price_update(session_id, prices)
        
        return updated
    
    def close_position(
        self,
        session_id: str,
        position_id: str,
        exit_price: float,
        notes: str = ""
    ) -> bool:
        """Close a position."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        position = session.positions.get(position_id)
        if not position:
            return False
        
        position.close(exit_price)
        if notes:
            position.notes += f"\nExit note: {notes}"
        
        session.realized_pnl += position.realized_pnl
        session.account_balance += position.realized_pnl
        session.last_position_update = datetime.now()
        
        self.save_session(session_id)
        
        return True
    
    def get_position(self, session_id: str, position_id: str) -> Optional[Position]:
        """Get specific position."""
        session = self.active_sessions.get(session_id)
        if session:
            return session.positions.get(position_id)
        return None
    
    def get_open_positions(self, session_id: str) -> List[Position]:
        """Get all open positions."""
        session = self.active_sessions.get(session_id)
        if not session:
            return []
        
        return [
            p for p in session.positions.values()
            if p.status == PositionStatus.OPEN
        ]
    
    def get_position_summary(self, session_id: str) -> Dict[str, Any]:
        """Get position summary."""
        positions = self.get_open_positions(session_id)
        
        total_exposure = sum(p.entry_price * p.quantity for p in positions)
        total_risk = sum(p.risk_amount for p in positions if p.risk_amount)
        total_unrealized = sum(p.unrealized_pnl for p in positions)
        
        by_symbol = defaultdict(list)
        for p in positions:
            by_symbol[p.symbol].append(p)
        
        return {
            "open_count": len(positions),
            "total_exposure": total_exposure,
            "total_risk": total_risk,
            "total_unrealized_pnl": total_unrealized,
            "symbols": list(by_symbol.keys()),
            "positions_by_symbol": {k: len(v) for k, v in by_symbol.items()}
        }
    
    def get_stats(self, session_id: str) -> SessionStats:
        """Calculate session statistics."""
        session = self.active_sessions.get(session_id)
        if not session:
            return SessionStats()
        
        positions = list(session.positions.values())
        open_pos = [p for p in positions if p.status == PositionStatus.OPEN]
        closed_pos = [p for p in positions if p.status == PositionStatus.CLOSED]
        
        wins = sum(1 for p in closed_pos if p.realized_pnl > 0)
        losses = sum(1 for p in closed_pos if p.realized_pnl < 0)
        win_rate = wins / len(closed_pos) * 100 if closed_pos else 0
        
        unrealized = sum(p.unrealized_pnl for p in open_pos)
        
        total_exposure = sum(p.current_price * p.quantity for p in open_pos if p.current_price)
        total_risk = sum(p.risk_amount for p in open_pos)
        
        return SessionStats(
            total_positions=len(positions),
            open_positions=len(open_pos),
            closed_positions=len(closed_pos),
            pending_positions=sum(1 for p in positions if p.status == PositionStatus.PENDING),
            realized_pnl=session.realized_pnl,
            unrealized_pnl=unrealized,
            total_pnl=session.realized_pnl + unrealized,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            total_risk=total_risk,
            total_exposure=total_exposure
        )
    
    def save_session(self, session_id: str) -> bool:
        """Save session to disk."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        filepath = self.storage_dir / f"session_{session_id}.json"
        
        try:
            with open(filepath, 'w') as f:
                json.dump(asdict(session), f, cls=SessionEncoder, indent=2)
            return True
        except Exception:
            return False
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """Load session from disk."""
        filepath = self.storage_dir / f"session_{session_id}.json"
        
        if not filepath.exists():
            return None
        
        try:
            with open(filepath, 'r') as f:
                data = json.load(f, object_hook=session_decoder)
            
            session = Session(**data)
            self.active_sessions[session_id] = session
            return session
        except Exception:
            return None
    
    def list_saved_sessions(self) -> List[str]:
        """List all saved session IDs."""
        sessions = []
        for filepath in self.storage_dir.glob("session_*.json"):
            session_id = filepath.stem.replace("session_", "")
            sessions.append(session_id)
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session file."""
        filepath = self.storage_dir / f"session_{session_id}.json"
        
        if filepath.exists():
            filepath.unlink()
        
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        
        return True
    
    def register_position_callback(self, callback: Callable):
        """Register callback for position events."""
        self.position_callbacks.append(callback)
    
    def register_price_callback(self, callback: Callable):
        """Register callback for price updates."""
        self.price_update_callbacks.append(callback)
    
    def _notify_position_added(self, position: Position):
        """Notify position callbacks."""
        for callback in self.position_callbacks:
            try:
                callback("added", position)
            except Exception:
                pass
    
    def _notify_price_update(self, session_id: str, prices: Dict[str, float]):
        """Notify price callbacks."""
        for callback in self.price_update_callbacks:
            try:
                callback(session_id, prices)
            except Exception:
                pass


def format_session_summary(manager: SessionManager, session_id: str) -> str:
    """Format session summary for display."""
    session = manager.get_session(session_id)
    stats = manager.get_stats(session_id)
    
    if not session:
        return f"Session {session_id} not found"
    
    lines = [
        f"{'=' * 70}",
        f"SESSION: {session.name}",
        f"{'=' * 70}",
        f"ID: {session.id} | Status: {session.status.name}",
        f"Started: {session.started_at.strftime('%Y-%m-%d %H:%M')}",
        f"Duration: {session.duration}",
        "",
        "BALANCE:",
        f"  Starting: ${session.starting_balance:,.2f}",
        f"  Current:  ${session.account_balance:,.2f}",
        f"  Total P&L: ${session.total_pnl:+,.2f}",
        "",
        "POSITIONS:",
        f"  Total: {stats.total_positions}",
        f"  Open: {stats.open_positions}",
        f"  Closed: {stats.closed_positions}",
        f"  Win Rate: {stats.win_rate:.1f}%",
        "",
        "P&L BREAKDOWN:",
        f"  Realized:   ${stats.realized_pnl:+,.2f}",
        f"  Unrealized: ${stats.unrealized_pnl:+,.2f}",
        f"  Total:      ${stats.total_pnl:+,.2f}",
        "",
        "EXPOSURE:",
        f"  Total Exposure: ${stats.total_exposure:,.2f}",
        f"  Total Risk:     ${stats.total_risk:,.2f}",
        f"{'=' * 70}",
    ]
    
    # Open positions
    open_pos = manager.get_open_positions(session_id)
    if open_pos:
        lines.extend(["", "OPEN POSITIONS:", "-" * 70])
        for p in sorted(open_pos, key=lambda x: x.unrealized_pnl, reverse=True):
            emoji = "🟢" if p.unrealized_pnl > 0 else "🔴" if p.unrealized_pnl < 0 else "⚪"
            lines.append(
                f"{emoji} {p.symbol:<8} {p.side[:1].upper()} | "
                f"${p.entry_price:,.2f} → ${p.current_price or p.entry_price:,.2f} | "
                f"${p.unrealized_pnl:+,.0f} ({p.unrealized_pnl_pct:+.2f}%)"
            )
    
    lines.append(f"{'=' * 70}")
    
    return "\n".join(lines)


# === Examples ===

def example_session_lifecycle():
    """Demonstrate session management."""
    print("=" * 70)
    print("Session Manager Demo")
    print("=" * 70)
    
    manager = SessionManager(storage_dir="/tmp/sessions")
    
    # Start session
    print("\n--- Starting New Session ---")
    session = manager.start_session(
        name="Momentum Strategy - Feb 2024",
        account_balance=100000,
        strategy="momentum",
        tags=["equity", "swing"],
        notes="Testing breakout momentum system"
    )
    
    print(f"Session started: {session.id}")
    print(f"Balance: ${session.account_balance:,.2f}")
    
    # Add positions
    print("\n--- Adding Positions ---")
    
    positions = [
        manager.add_position(session.id, "AAPL", "long", 100, 175.0, 170.0, 185.0, "breakout"),
        manager.add_position(session.id, "TSLA", "long", 50, 250.0, 240.0, 280.0, "momentum"),
        manager.add_position(session.id, "NVDA", "long", 40, 450.0, 430.0, 500.0, "breakout"),
    ]
    
    for p in positions:
        print(f"Added {p.symbol}: {p.quantity} shares @ ${p.entry_price}")
    
    # Update prices
    print("\n--- Price Update ---")
    price_changes = manager.update_prices(session.id, {
        "AAPL": 178.0,
        "TSLA": 245.0,
        "NVDA": 455.0
    })
    
    for symbol, change in price_changes.items():
        print(f"{symbol}: P&L change ${change:+.2f}")
    
    # Get stats
    print("\n--- Session Stats ---")
    stats = manager.get_stats(session.id)
    print(f"Open positions: {stats.open_positions}")
    print(f"Unrealized P&L: ${stats.unrealized_pnl:+,.2f}")
    print(f"Total exposure: ${stats.total_exposure:,.2f}")
    
    # Print summary
    print("\n" + format_session_summary(manager, session.id))
    
    # Close a position
    print("\n--- Closing Position ---")
    manager.close_position(session.id, positions[0].id, 180.0, "Target hit")
    
    position = manager.get_position(session.id, positions[0].id)
    print(f"Closed {position.symbol}: Realized P&L ${position.realized_pnl:+.2f}")
    
    # Update and show final state
    print("\n--- Final State ---")
    stats = manager.get_stats(session.id)
    print(f"Realized P&L: ${stats.realized_pnl:+,.2f}")
    print(f"Open positions: {stats.open_positions}")
    
    # Persistence
    print("\n--- Persistence ---")
    manager.save_session(session.id)
    print(f"Session saved to disk")
    
    # Load it back
    del manager.active_sessions[session.id]
    restored = manager.load_session(session.id)
    print(f"Session restored: {restored.name}")
    print(f"Positions restored: {len(restored.positions)}")


def example_session_recovery():
    """Simulate crash recovery."""
    print("\n" + "=" * 70)
    print("Session Recovery Demo")
    print("=" * 70)
    
    manager = SessionManager(storage_dir="/tmp/recovery_test")
    
    # Create session with positions
    session = manager.start_session(
        name="Live Trading Session",
        account_balance=50000,
        strategy="multi-strat"
    )
    
    # Add multiple positions
    for symbol in ["SPY", "QQQ", "IWM"]:
        manager.add_position(session.id, symbol, "long", 100, 400.0, 390.0)
    
    # Simulate crash by clearing from memory
    session_id = session.id
    del manager.active_sessions[session_id]
    print(f"\n[CRASH SIMULATED - Session cleared from memory]")
    
    # Recovery
    print("\n--- Recovery ---")
    recovered = manager.load_session(session_id)
    
    if recovered:
        print(f"✅ Session recovered: {recovered.name}")
        print(f"   Balance: ${recovered.account_balance:,.2f}")
        print(f"   Open positions: {len(recovered.positions)}")
        
        for pos in recovered.positions.values():
            print(f"   - {pos.symbol}: {pos.quantity} shares @ ${pos.entry_price}")
    else:
        print("❌ Recovery failed")
    
    # Cleanup
    manager.delete_session(session_id)
    print("\nSession cleaned up")


def example_multi_session():
    """Multiple concurrent sessions."""
    print("\n" + "=" * 70)
    print("Multiple Sessions Demo")
    print("=" * 70)
    
    manager = SessionManager(storage_dir="/tmp/multi_test")
    
    # Create multiple sessions
    sessions = [
        manager.start_session("Day Trading", 25000, "scalping"),
        manager.start_session("Swing Trading", 100000, "momentum"),
        manager.start_session("Long Term", 50000, "buy_hold"),
    ]
    
    print(f"\nCreated {len(sessions)} sessions:")
    for s in sessions:
        print(f"  {s.name}: ${s.account_balance:,.0f} ({s.strategy})")
    
    # Add positions to each
    manager.add_position(sessions[0].id, "SPY", "long", 50, 450.0)
    manager.add_position(sessions[0].id, "QQQ", "long", 30, 380.0)
    
    manager.add_position(sessions[1].id, "AAPL", "long", 20, 175.0)
    manager.add_position(sessions[1].id, "MSFT", "long", 15, 380.0)
    manager.add_position(sessions[1].id, "GOOGL", "long", 10, 140.0)
    
    # Show session summary
    print("\n--- Session Summary ---")
    for s in sessions:
        stats = manager.get_stats(s.id)
        print(f"  {s.name:<15}: {stats.open_positions} positions, ${s.account_balance:,.0f}")
    
    # Total across all
    total_balance = sum(s.account_balance for s in sessions)
    total_positions = sum(len(s.positions) for s in sessions)
    
    print(f"\nTotal: ${total_balance:,.0f} across {total_positions} positions")
    
    # Cleanup
    for s in sessions:
        manager.delete_session(s.id)
    print("\nAll sessions cleaned up")


if __name__ == "__main__":
    example_session_lifecycle()
    example_session_recovery()
    example_multi_session()
    
    print("\n" + "=" * 70)
    print("SESSION MANAGER BENEFITS:")
    print("=" * 70)
    print("""
1. PERSISTENCE: Survive crashes and restarts
2. TRACKING: Monitor P&L in real-time
3. RECOVERY: Resume where you left off
4. MULTI-SESSION: Run different strategies in parallel
5. METRICS: Calculate stats on-demand

Use Cases:
  • Keep positions across trading system restarts
  • Track P&L for different strategies separately
  • Pause and resume trading sessions
  • Maintain audit trail of all operations
  • Recovery from unexpected shutdowns

The session manager is your trading memory.
    """)
    print("=" * 70)
```

## Session States

| State | Meaning | Action |
|-------|---------|--------|
| **INITIALIZING** | Setting up | Wait for ready |
| **ACTIVE** | Trading enabled | Normal operation |
| **PAUSED** | Temporarily stopped | Can resume |
| **ERROR** | Error occurred | Fix and resume |
| **CLOSING** | Shutting down | Close positions |
| **CLOSED** | Complete | Archive |

## Position Lifecycle

| State | Meaning |
|-------|---------|
| **PENDING** | Order placed, not filled |
| **OPEN** | Position active |
| **CLOSING** | Exit order pending |
| **CLOSED** | Position complete |
| **ERROR** | Something went wrong |

## Quick Reference

```python
manager = SessionManager(storage_dir="sessions")

# Start session
session = manager.start_session(
    name="My Strategy",
    account_balance=100000
)

# Add position
pos = manager.add_position(
    session_id=session.id,
    symbol="AAPL",
    side="long",
    quantity=100,
    entry_price=175.0,
    stop_price=170.0
)

# Update prices
manager.update_prices(session.id, {"AAPL": 178.0})

# Check stats
stats = manager.get_stats(session.id)
print(f"Open: {stats.open_positions}, Unrealized: ${stats.unrealized_pnl:+.2f}")

# Close position
manager.close_position(session.id, pos.id, 180.0)

# Save/restore
manager.save_session(session.id)
restored = manager.load_session(session.id)
```

## Storage Format

Sessions saved as JSON:
```
sessions/
  session_a1b2c3d4.json
  session_e5f6g7h8.json
```

## Why This Matters

- **Survive crashes** — Restart without losing track of positions
- **Track real-time P&L** — Always know where you stand
- **Multiple strategies** — Run day trading + swing separately
- **Audit trail** — Every operation logged and recoverable
- **Pause/resume** — Step away without losing state

**Never lose track of your positions again.**

---

**Created by Ghost 👻 | Feb 20, 2026 | 12-min learning sprint**  
*Lesson: "What happens if your system crashes mid-trade?" A session manager persists your state—positions, P&L, settings—so you can recover exactly where you left off. Persistence prevents panic.*
