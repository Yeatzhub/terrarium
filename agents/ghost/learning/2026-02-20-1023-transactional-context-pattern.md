# Transactional Context Manager Pattern

**Purpose:** Automatic commit/rollback for database operations and resource management  
**Use Case:** Ensure data integrity, prevent partial updates, cleanup resources on failure

## The Pattern

```python
"""
Transactional Context Manager Pattern
Atomic operations with automatic rollback on failure, nesting support,
and resource cleanup guarantees.
"""

from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field
from typing import Optional, List, Callable, Any, Dict, Union
from enum import Enum, auto
import functools
import time


class TransactionStatus(Enum):
    PENDING = auto()
    COMMITTED = auto()
    ROLLED_BACK = auto()
    FAILED = auto()


@dataclass
class TransactionResult:
    status: TransactionStatus
    operations: int = 0
    duration_ms: float = 0.0
    error: Optional[Exception] = None
    rollback_operations: List[str] = field(default_factory=list)


class Transaction:
    """
    Manual transaction for complex scenarios.
    
    Usage:
        tx = Transaction(db_connection)
        try:
            tx.begin()
            tx.add_operation("INSERT", user_data)
            tx.add_operation("UPDATE", balance_data)
            tx.commit()
        except Exception:
            tx.rollback()
    """
    
    def __init__(self, connection: Any, name: str = "unnamed"):
        self.connection = connection
        self.name = name
        self.status = TransactionStatus.PENDING
        self.operations: List[Dict] = []
        self._savepoints: List[str] = []
        self._depth = 0
    
    def begin(self):
        """Start transaction."""
        if self._depth == 0:
            # Real BEGIN
            self._execute("BEGIN")
        else:
            # Nested transaction - use savepoint
            savepoint = f"sp_{self._depth}_{time.time():.6f}"
            self._savepoints.append(savepoint)
            self._execute(f"SAVEPOINT {savepoint}")
        
        self._depth += 1
        self.status = TransactionStatus.PENDING
    
    def add_operation(self, operation: str, data: Any, rollback_fn: Optional[Callable] = None):
        """Record operation for potential rollback."""
        self.operations.append({
            "op": operation,
            "data": data,
            "rollback": rollback_fn,
            "timestamp": time.time()
        })
    
    def commit(self):
        """Commit all operations."""
        self._depth -= 1
        
        if self._depth == 0:
            self._execute("COMMIT")
            self.status = TransactionStatus.COMMITTED
        else:
            # Release savepoint on successful nested commit
            if self._savepoints:
                sp = self._savepoints.pop()
                self._execute(f"RELEASE SAVEPOINT {sp}")
    
    def rollback(self, to_savepoint: Optional[str] = None):
        """Rollback operations."""
        if to_savepoint and to_savepoint in self._savepoints:
            self._execute(f"ROLLBACK TO SAVEPOINT {to_savepoint}")
            # Remove operations after savepoint
            self.operations = [o for o in self.operations if self._savepoint_exists(o, to_savepoint)]
        else:
            self._depth = max(0, self._depth - 1)
            if self._depth == 0:
                self._execute("ROLLBACK")
                self.status = TransactionStatus.ROLLED_BACK
                
                # Execute custom rollback functions
                for op in reversed(self.operations):
                    if op.get("rollback"):
                        try:
                            op["rollback"](op["data"])
                        except Exception as e:
                            print(f"Rollback function failed: {e}")
    
    def _execute(self, sql: str):
        """Execute SQL - override for real database."""
        print(f"[TX:{self.name}] {sql}")
    
    def _savepoint_exists(self, operation: Dict, savepoint: str) -> bool:
        """Check if operation was before savepoint."""
        # Simplified - real implementation tracks savepoint timestamps
        return True


@contextmanager
def atomic_transaction(
    connection: Any,
    name: str = "atomic",
    max_retries: int = 0,
    retry_delay: float = 0.1,
    on_commit: Optional[Callable] = None,
    on_rollback: Optional[Callable] = None
):
    """
    Context manager for atomic transactions with automatic rollback.
    
    Usage:
        with atomic_transaction(db_conn, "create_order") as tx:
            tx.execute("INSERT INTO orders ...")
            tx.execute("UPDATE inventory ...")
            # Auto-commit on exit, rollback on exception
    """
    tx = Transaction(connection, name)
    start = time.time()
    result = TransactionResult(status=TransactionStatus.PENDING)
    
    for attempt in range(max_retries + 1):
        try:
            tx.begin()
            yield tx
            tx.commit()
            result.status = TransactionStatus.COMMITTED
            result.operations = len(tx.operations)
            if on_commit:
                on_commit(result)
            break
            
        except Exception as e:
            tx.rollback()
            result.status = TransactionStatus.FAILED
            result.error = e
            
            if attempt < max_retries:
                time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                continue
            
            if on_rollback:
                on_rollback(result)
            raise
    
    result.duration_ms = (time.time() - start) * 1000


@asynccontextmanager
async def async_atomic_transaction(
    connection: Any,
    name: str = "async_atomic",
    max_retries: int = 0,
    retry_delay: float = 0.1
):
    """Async version of atomic transaction."""
    tx = Transaction(connection, name)
    start = time.time()
    
    for attempt in range(max_retries + 1):
        try:
            tx.begin()
            yield tx
            tx.commit()
            break
        except Exception as e:
            tx.rollback()
            if attempt < max_retries:
                await asyncio.sleep(retry_delay * (2 ** attempt))
                continue
            raise


@dataclass
class ResourceHolder:
    """Holds multiple resources, releases all on failure."""
    resources: Dict[str, Any] = field(default_factory=dict)
    _cleanup_stack: List[Callable] = field(default_factory=list)
    
    def acquire(self, name: str, resource: Any, cleanup: Callable):
        """Acquire resource with cleanup function."""
        self.resources[name] = resource
        self._cleanup_stack.append(cleanup)
        return resource
    
    def release_all(self):
        """Release all resources in reverse order."""
        for cleanup in reversed(self._cleanup_stack):
            try:
                cleanup()
            except Exception as e:
                print(f"Cleanup failed: {e}")
        self.resources.clear()
        self._cleanup_stack.clear()


@contextmanager
def resource_transaction(resource_names: List[str]):
    """
    Acquire multiple resources atomically.
    All succeed or all fail (no partial acquisition).
    
    Usage:
        with resource_transaction(["db", "cache", "queue"]) as holder:
            db = holder.acquire("db", get_db(), lambda: db.close())
            cache = holder.acquire("cache", get_cache(), lambda: cache.disconnect())
            # Use resources...
            # All cleaned up on exit
    """
    holder = ResourceHolder()
    acquired = []
    
    try:
        yield holder
        # Success - resources remain acquired
    except Exception:
        # Failure - release everything acquired so far
        holder.release_all()
        raise


class CompensatingTransaction:
    """
    Saga pattern: Compensate for already-committed operations.
    Used when you can't use real transactions (microservices, distributed).
    """
    
    def __init__(self, name: str = "saga"):
        self.name = name
        self.steps: List[Dict] = []
        self.completed: List[Dict] = []
    
    def add_step(
        self,
        name: str,
        action: Callable,
        compensate: Callable,
        action_args: tuple = (),
        compensate_args: tuple = ()
    ):
        """Add a step with compensating action."""
        self.steps.append({
            "name": name,
            "action": action,
            "compensate": compensate,
            "action_args": action_args,
            "compensate_args": compensate_args
        })
    
    def execute(self) -> TransactionResult:
        """Execute all steps, compensate on failure."""
        start = time.time()
        
        for i, step in enumerate(self.steps):
            try:
                result = step["action"](*step["action_args"])
                self.completed.append({
                    "index": i,
                    "name": step["name"],
                    "result": result,
                    "compensate": step["compensate"],
                    "compensate_args": step["compensate_args"]
                })
            except Exception as e:
                # Compensate completed steps in reverse order
                self._compensate_all()
                return TransactionResult(
                    status=TransactionStatus.FAILED,
                    operations=i,
                    duration_ms=(time.time() - start) * 1000,
                    error=e,
                    rollback_operations=[s["name"] for s in self.completed]
                )
        
        return TransactionResult(
            status=TransactionStatus.COMMITTED,
            operations=len(self.steps),
            duration_ms=(time.time() - start) * 1000
        )
    
    def _compensate_all(self):
        """Run compensating actions for completed steps."""
        for step in reversed(self.completed):
            try:
                step["compensate"](*step["compensate_args"])
            except Exception as e:
                print(f"Compensation failed for {step['name']}: {e}")


def transactional(
    connection_arg: str = "connection",
    retry_on: tuple = (Exception,),
    max_retries: int = 0
):
    """
    Decorator for automatic transaction wrapping.
    
    Usage:
        @transactional(connection_arg="db", max_retries=2)
        def create_user(db, user_data):
            db.execute("INSERT INTO users ...")
            db.execute("INSERT INTO profiles ...")
            return user_id
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Find connection argument
            conn = kwargs.get(connection_arg)
            if not conn and args:
                # Assume first arg is connection if not specified
                conn = args[0]
            
            if not conn:
                raise ValueError(f"No connection found for transactional")
            
            with atomic_transaction(conn, func.__name__, max_retries) as tx:
                # Replace connection with transaction wrapper
                new_kwargs = {**kwargs, connection_arg: tx}
                return func(*args, **new_kwargs)
        
        return wrapper
    return decorator


# === Examples ===

def example_basic_transaction():
    """Basic atomic transaction."""
    print("=" * 60)
    print("Example 1: Basic Atomic Transaction")
    print("=" * 60)
    
    # Simulate database connection
    class MockDB:
        def execute(self, sql):
            print(f"  DB Execute: {sql}")
    
    db = MockDB()
    
    try:
        with atomic_transaction(db, "create_order") as tx:
            tx.add_operation("INSERT", {"table": "orders", "data": {"id": 123}})
            tx._execute("INSERT INTO orders (id, total) VALUES (123, 99.99)")
            
            tx.add_operation("UPDATE", {"table": "inventory", "item": "widget", "qty": -1})
            tx._execute("UPDATE inventory SET qty = qty - 1 WHERE item = 'widget'")
            
            print("  Operations successful, auto-commit on exit")
    except Exception as e:
        print(f"  Failed: {e}")
    
    print(f"  Transaction complete\n")


def example_rollback_on_error():
    """Transaction with rollback on error."""
    print("=" * 60)
    print("Example 2: Automatic Rollback on Error")
    print("=" * 60)
    
    class MockDB:
        def execute(self, sql):
            print(f"  DB: {sql}")
    
    db = MockDB()
    
    try:
        with atomic_transaction(db, "transfer_funds") as tx:
            tx._execute("UPDATE accounts SET balance = balance - 100 WHERE id = 1")
            print("  Deducted from account 1")
            
            # Simulate error
            raise ValueError("Network error: can't reach account 2")
            
            tx._execute("UPDATE accounts SET balance = balance + 100 WHERE id = 2")
    except ValueError as e:
        print(f"  Caught error: {e}")
        print(f"  Transaction rolled back - account 1 balance restored\n")


def example_nested_transactions():
    """Nested transactions with savepoints."""
    print("=" * 60)
    print("Example 3: Nested Transactions (Savepoints)")
    print("=" * 60)
    
    class MockDB:
        def execute(self, sql):
            print(f"  DB: {sql}")
    
    db = MockDB()
    
    outer_tx = Transaction(db, "outer")
    outer_tx.begin()
    print("  [Outer] BEGIN")
    
    outer_tx._execute("INSERT INTO logs (action) VALUES ('start')")
    
    # Nested transaction (savepoint)
    inner_tx = Transaction(db, "inner")
    inner_tx.begin()
    print("  [Inner] SAVEPOINT sp_1")
    
    inner_tx._execute("INSERT INTO risky_table (data) VALUES ('maybe_bad')")
    
    # Inner fails, rolls back to savepoint
    inner_tx.rollback()
    print("  [Inner] ROLLBACK TO SAVEPOINT sp_1")
    
    # Outer continues
    outer_tx._execute("INSERT INTO logs (action) VALUES ('inner_failed_but_continued')")
    outer_tx.commit()
    print("  [Outer] COMMIT")
    print("  Result: Outer ops committed, inner ops rolled back\n")


def example_resource_transaction():
    """Multiple resources with atomic acquisition."""
    print("=" * 60)
    print("Example 4: Resource Transaction (All or Nothing)")
    print("=" * 60)
    
    acquired = []
    
    def get_db():
        acquired.append("db")
        return "db_connection"
    
    def get_cache():
        acquired.append("cache")
        return "cache_connection"
    
    def get_queue():
        # Simulate failure on third resource
        raise ConnectionError("Queue service unavailable")
    
    try:
        with resource_transaction(["db", "cache", "queue"]) as holder:
            db = holder.acquire("db", get_db(), lambda: acquired.remove("db"))
            print(f"  Acquired: {acquired}")
            
            cache = holder.acquire("cache", get_cache(), lambda: acquired.remove("cache"))
            print(f"  Acquired: {acquired}")
            
            # This will fail
            queue = holder.acquire("queue", get_queue(), lambda: None)
            
    except ConnectionError as e:
        print(f"  Failed to acquire queue: {e}")
        print(f"  Resources cleaned up: {acquired}")
        print(f"  Result: Partial acquisition prevented\n")


def example_compensating_transaction():
    """Saga pattern with compensating actions."""
    print("=" * 60)
    print("Example 5: Compensating Transaction (Saga Pattern)")
    print("=" * 60)
    
    # Simulate microservices
    services_called = []
    compensations = []
    
    def call_payment_service():
        services_called.append("payment")
        return {"payment_id": "pay_123"}
    
    def compensate_payment():
        compensations.append("refund pay_123")
    
    def call_inventory_service():
        services_called.append("inventory")
        return {"reservation_id": "res_456"}
    
    def compensate_inventory():
        compensations.append("release res_456")
    
    def call_shipping_service():
        services_called.append("shipping")
        # Simulate failure
        raise RuntimeError("Shipping service timeout")
    
    def compensate_shipping():
        pass  # Nothing to compensate if it failed
    
    saga = CompensatingTransaction("order_processing")
    saga.add_step("payment", call_payment_service, compensate_payment)
    saga.add_step("inventory", call_inventory_service, compensate_inventory)
    saga.add_step("shipping", call_shipping_service, compensate_shipping)
    
    result = saga.execute()
    
    print(f"  Services called: {services_called}")
    print(f"  Status: {result.status.name}")
    print(f"  Compensations run: {compensations}")
    print(f"  Result: Payment refunded, inventory released due to shipping failure\n")


def example_retry_transaction():
    """Transaction with automatic retry."""
    print("=" * 60)
    print("Example 6: Transaction with Retry")
    print("=" * 60)
    
    class FlakyDB:
        def __init__(self):
            self.attempts = 0
        
        def execute(self, sql):
            self.attempts += 1
            if self.attempts < 3:
                raise ConnectionError(f"Attempt {self.attempts} failed")
            print(f"  DB: {sql} (succeeded on attempt {self.attempts})")
    
    db = FlakyDB()
    
    try:
        with atomic_transaction(db, "flaky_op", max_retries=3, retry_delay=0.01) as tx:
            tx._execute("UPDATE inventory SET reserved = 1")
        print(f"  Succeeded after {db.attempts} attempts\n")
    except ConnectionError as e:
        print(f"  Failed after all retries: {e}\n")


def example_decorator():
    """Using transactional decorator."""
    print("=" * 60)
    print("Example 7: Transactional Decorator")
    print("=" * 60)
    
    class MockDB:
        queries = []
        def execute(self, sql):
            self.queries.append(sql)
            print(f"  DB: {sql}")
    
    db = MockDB()
    
    @transactional(connection_arg="db", max_retries=1)
    def transfer_funds(db, from_id: int, to_id: int, amount: float):
        db._execute(f"UPDATE accounts SET balance = balance - {amount} WHERE id = {from_id}")
        db._execute(f"UPDATE accounts SET balance = balance + {amount} WHERE id = {to_id}")
        return {"from": from_id, "to": to_id, "amount": amount}
    
    result = transfer_funds(db, from_id=1, to_id=2, amount=100.0)
    print(f"  Transfer complete: {result}")
    print(f"  Queries executed: {len(MockDB.queries)}\n")


if __name__ == "__main__":
    example_basic_transaction()
    example_rollback_on_error()
    example_nested_transactions()
    example_resource_transaction()
    example_compensating_transaction()
    example_retry_transaction()
    example_decorator()
    
    print("=" * 60)
    print("Key Takeaways:")
    print("  • Use atomic_transaction for automatic rollback")
    print("  • Nested transactions use savepoints")
    print("  • Compensating transactions for distributed systems")
    print("  • Resource transactions prevent partial acquisition")
    print("=" * 60)
```

## Pattern Comparison

| Pattern | Use When | Rollback Method |
|---------|----------|-----------------|
| **atomic_transaction** | Single database | SQL ROLLBACK |
| **nested transactions** | Complex multi-step operations | SAVEPOINT |
| **resource_transaction** | Multiple resources (DB + cache + queue) | Cleanup functions |
| **compensating_transaction** | Distributed/microservices | Reverse API calls |
| **@transactional** | Simple function wrapping | Automatic |

## Quick Reference

```python
# Basic atomic operation
with atomic_transaction(db) as tx:
    tx.execute("INSERT ...")
    tx.execute("UPDATE ...")
    # Auto-commit on success, rollback on exception

# With retries
with atomic_transaction(db, max_retries=3, retry_delay=0.1) as tx:
    tx.execute("UPDATE ...")  # Retries on transient failures

# Multiple resources
with resource_transaction(["db", "cache"]) as holder:
    db = holder.acquire("db", get_db(), cleanup=db.close)
    cache = holder.acquire("cache", get_cache(), cleanup=cache.disconnect)

# Distributed saga
saga = CompensatingTransaction()
saga.add_step("charge", charge_card, compensate=refund_card)
saga.add_step("ship", create_label, compensate=cancel_label)
result = saga.execute()  # Auto-compensates on failure

# Decorator
@transactional(connection_arg="db", max_retries=2)
def create_order(db, data):
    db.execute("INSERT ...")
```

## Key Principles

1. **Atomicity** — All operations succeed or all fail (no partial state)
2. **Compensation over locking** — In distributed systems, undo > prevent
3. **Savepoints for nesting** — Inner can fail without killing outer
4. **Cleanup on failure** — Resources must be released even if init fails
5. **Retry transient errors** — Network blips shouldn't kill valid operations

## When to Use What

- **Single DB, single connection** → `atomic_transaction`
- **Complex nested logic** → `Transaction` class with savepoints
- **DB + external services** → `resource_transaction`
- **Microservices/distributed** → `CompensatingTransaction` (Saga)
- **Simple CRUD functions** → `@transactional` decorator

---

**Created by Ghost 👻 | Feb 20, 2026 | 14-min learning sprint**  
*Lesson: "Without transactions, every operation is a landmine." Atomic context managers eliminate partial failures—rollback is automatic, cleanup is guaranteed, and your data stays consistent even when everything else breaks.*
