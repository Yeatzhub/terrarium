# Error Handling & Recovery Patterns for Multi-Agent Workflows

**Created:** 2026-02-22 12:20  
**Author:** Synthesis  
**Focus:** Failure detection, recovery strategies, and resilience patterns for agent coordination

---

## The Reality: Agents Fail

Failure modes in multi-agent systems:
- **Timeouts** - Agent takes too long
- **Misunderstanding** - Wrong interpretation of task
- **Tool failures** - External service unavailable
- **Dependency breaks** - Required task failed
- **Resource exhaustion** - Memory, tokens, file handles
- **Circular waits** - Deadlock between agents

Without recovery patterns, one failure cascades into total system failure.

---

## Error Classification

| Category | Severity | Recovery | Example |
|----------|----------|----------|---------|
| **Transient** | Low | Auto-retry | API rate limit |
| **Correctable** | Medium | Re-dispatch with context | Wrong output format |
| **Blocking** | High | Escalate to human | Auth failure |
| **Catastrophic** | Critical | Full rollback | Data corruption |

---

## Recovery Strategies

### Strategy 1: Retry with Backoff

For transient failures (network, rate limits):

```python
RETRY_CONFIG = {
    "max_attempts": 3,
    "backoff_base": 2,  # Exponential
    "max_delay": 60,    # Seconds
    "jitter": True      # Randomize to avoid thundering herd
}

def retry_with_backoff(task_func, config=RETRY_CONFIG):
    for attempt in range(config["max_attempts"]):
        try:
            return task_func()
        except TransientError as e:
            if attempt == config["max_attempts"] - 1:
                raise
            delay = min(
                config["backoff_base"] ** attempt,
                config["max_delay"]
            )
            if config["jitter"]:
                delay *= random.uniform(0.5, 1.5)
            time.sleep(delay)
```

### Strategy 2: Checkpoint & Resume

For long-running tasks:

```markdown
CHECKPOINT PROTOCOL:
1. Save state every N steps (N = 5-10)
2. Include: completed_items, current_item, artifacts_created
3. On restart: load checkpoint, skip completed, resume

CHECKPOINT FILE:
```json
{
  "task_id": "auth-feature",
  "started": "2026-02-22T12:00:00Z",
  "last_checkpoint": "2026-02-22T12:15:00Z",
  "completed": ["setup", "research", "client-wrapper"],
  "current": "auth-middleware",
  "remaining": ["routes", "sessions", "tests"],
  "artifacts": ["/auth/client.ts"]
}
```
```

### Strategy 3: Fallback Agent

When primary agent fails:

```markdown
FALLBACK CHAIN:
Primary: Specialized agent (e.g., code-expert)
    ↓ on failure
Fallback 1: Generalist agent
    ↓ on failure
Fallback 2: Human escalation with context

DECISION TREE:
┌─► Task failed?
│   ├─► Transient? → Retry (Strategy 1)
│   ├─► Wrong output? → Re-dispatch with hints
│   ├─► Out of scope? → Route to fallback agent
│   └─► Unrecoverable? → Escalate to human
```

### Strategy 4: Compensation / Rollback

For irreversible operations:

```python
class Workflow:
    def __init__(self):
        self.actions = []
        self.compensations = []
    
    def execute(self, action, compensate):
        """Execute action and store compensation."""
        try:
            result = action()
            self.actions.append(action)
            self.compensations.append(compensate)
            return result
        except Exception as e:
            # Execute all compensations in reverse
            self.rollback()
            raise
    
    def rollback(self):
        """Execute compensations in reverse order."""
        for compensate in reversed(self.compensations):
            try:
                compensate()
            except Exception as e:
                log.error(f"Compensation failed: {e}")

# Usage
workflow = Workflow()
workflow.execute(
    action=lambda: create_file("config.yaml"),
    compensate=lambda: delete_file("config.yaml")
)
workflow.execute(
    action=lambda: write_to_database(data),
    compensate=lambda: rollback_database_transaction()
)
```

---

## Failure Detection Patterns

### Heartbeat Pattern

Monitor agent health during long tasks:

```python
HEARTBEAT_CONFIG = {
    "interval": 30,      # Seconds between heartbeats
    "timeout": 90,       # Consider dead after N seconds silence
    "max_missed": 3      # Heartbeats before declaring dead
}

def monitor_agent(session_key, config=HEARTBEAT_CONFIG):
    missed = 0
    while True:
        status = subagents(action="list", target=session_key)
        last_heartbeat = status[0].get("last_heartbeat")
        
        if time_since(last_heartbeat) > config["timeout"]:
            missed += 1
            if missed >= config["max_missed"]:
                return "DEAD"
        else:
            missed = 0
        
        time.sleep(config["interval"])
        return "ALIVE"
```

### Deadline Pattern

Hard timeout with graceful termination:

```markdown
DEADLINE PROTOCOL:
1. Set absolute deadline at task start
2. Check elapsed time at each step
3. If 80% deadline reached: prepare quick finish
4. If 100% deadline reached: save state, report partial
5. If 110% deadline: force terminate

DEADLINE MESSAGE:
{
  "deadline": "2026-02-22T12:45:00Z",
  "soft_deadline": "2026-02-22T12:36:00Z",  # 80%
  "hard_deadline": "2026-02-22T12:49:30Z",  # 110%
  "action": "save_and_report"
}
```

---

## Cascading Failure Prevention

### Circuit Breaker

Stop calling failing components:

```python
CIRCUIT_BREAKER = {
    "failure_threshold": 5,    # Failures before opening
    "reset_timeout": 300,       # Seconds before trying again
    "state": "CLOSED"           # CLOSED | OPEN | HALF_OPEN
}

class CircuitBreaker:
    def __init__(self, config=CIRCUIT_BREAKER):
        self.failures = 0
        self.state = "CLOSED"
        self.last_failure = None
        self.config = config
    
    def call(self, func):
        if self.state == "OPEN":
            if time_since(self.last_failure) > self.config["reset_timeout"]:
                self.state = "HALF_OPEN"
            else:
                raise CircuitOpenError("Circuit breaker is open")
        
        try:
            result = func()
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure = time.now()
            if self.failures >= self.config["failure_threshold"]:
                self.state = "OPEN"
            raise
```

### Bulkhead Pattern

Isolate failures to prevent spread:

```markdown
BULKHEAD ISOLATION:
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   Agent Pool A  │ │   Agent Pool B  │ │   Agent Pool C  │
│  (File Ops)     │ │  (API Calls)    │ │  (Processing)   │
│  Limit: 3       │ │  Limit: 5       │ │  Limit: 2       │
└─────────────────┘ └─────────────────┘ └─────────────────┘
        ↓                   ↓                   ↓
   File failure      API rate limit      Processing OK
   contained         contained           continues
   to Pool A         to Pool B           unaffected

RULE: One pool's failure doesn't affect others
```

---

## Error Reporting Protocol

### Standard Error Package

```markdown
ERROR_PACKAGE:
├── error_id: unique identifier
├── timestamp: when it occurred
├── agent_id: which agent failed
├── task_id: what was being attempted
├── error_type: classification
├── error_message: human-readable
├── stack_trace: if applicable
├── context_dump: relevant state
├── recovery_attempted: what was tried
└── recovery_result: success/failure
```

### Error Report Template

```markdown
## Error Report: [ERROR_ID]

**When:** [timestamp]
**Agent:** [agent_id]
**Task:** [task_id]

### Error
Type: [TRANSIENT | CORRECTABLE | BLOCKING | CATASTROPHIC]
Message: [description]

### Context
```
[last 5 actions before failure]
```

### Attempted Recovery
1. [attempt 1] - [result]
2. [attempt 2] - [result]

### Status
- [ ] Auto-recovery failed
- [ ] Requires human intervention
- [ ] Workaround available: [description]

### Recommended Action
[specific next step]
```

---

## Recovery Decision Matrix

| Error Type | Agent Response | Escalate After |
|------------|---------------|----------------|
| Rate limit | Wait + retry | 3 failures |
| Wrong format | Re-run with schema | 2 failures |
| Dependency failed | Wait for dependency | Dependency timeout |
| Timeout | Checkpoint + restart | 2 restarts |
| Permission denied | Request access | Immediate |
| Resource exhausted | Scale down | 5 min |
| Unknown error | Log + fallback agent | 1 failure |

---

## Quick Recovery Checklist

```markdown
FAILURE DETECTED. NOW WHAT?
━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Classify error type
□ Check if retry-able
□ Check checkpoint exists
□ Identify affected downstream tasks
□ Notify or pause dependent agents
□ Attempt recovery strategy
□ Document error package
□ Update metrics
━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Metrics to Track

| Metric | Formula | Alert Threshold |
|--------|---------|-----------------|
| Error rate | Failures / Total tasks | >5% |
| Mean time to recovery | Average recovery time | >5 min |
| Retry success rate | Successful retries / Retries | <50% |
| Cascade rate | Multi-agent failures / Failures | >10% |
| Escalation rate | Human escalations / Failures | >20% |

---

## Bottom Line

Errors are inevitable. Recovery is design:

1. **Classify** - Know what type of failure
2. **Contain** - Don't let it spread (bulkhead, circuit breaker)
3. **Recover** - Apply appropriate strategy
4. **Report** - Document for learning
5. **Monitor** - Track patterns over time

The goal isn't zero failures—it's resilient systems that fail gracefully and recover automatically.