# Observability & Debugging for Multi-Agent Systems

**Created:** 2026-02-22 14:20  
**Author:** Synthesis  
**Focus:** Execution tracing, state inspection, and debugging workflows across agents

---

## The Black Box Problem

When agents work together:
- Who did what becomes unclear
- Failures hide in handoffs
- State scatters across files
- Time spent is invisible

Observability turns black boxes into glass boxes.

---

## The Three Pillars

| Pillar | Purpose | Tool |
|--------|---------|------|
| **Tracing** | Who did what when | Execution logs |
| **Metrics** | How much how often | Counters, timers |
| **State** | What exists now | Snapshots, dumps |

---

## Tracing Patterns

### Pattern 1: Structured Event Log

Every action emits a structured event:

```json
{
  "timestamp": "2026-02-22T14:20:15.123Z",
  "event_id": "evt_a1b2c3",
  "session_id": "sess_xyz",
  "agent_id": "synthesis",
  "event_type": "TOOL_CALL",
  "action": "write",
  "params": {"path": "/tmp/test.txt"},
  "result": "success",
  "duration_ms": 45
}
```

### Pattern 2: Trace Correlation

Link events across agents with trace IDs:

```markdown
TRACE FLOW:
┌─────────────────────────────────────────────────────────┐
│ _trace_id: trace_12345_                                 │
│                                                         │
│  [14:20:01] main → synthesize request                   │
│  [14:20:02] synthesis → spawn research_agent            │
│  [14:20:03] research_agent → web_search                 │
│  [14:20:15] research_agent → complete                   │
│  [14:20:16] synthesis → spawn code_agent                │
│  [14:20:17] code_agent → read memory                    │
│  [14:20:45] code_agent → complete                       │
│  [14:20:46] synthesis → synthesize outputs              │
│  [14:20:50] main ← response delivered                   │
└─────────────────────────────────────────────────────────┘
```

### Pattern 3: Event Types Catalog

```python
EVENT_TYPES = {
    # Lifecycle
    "AGENT_START": "Agent spawned",
    "AGENT_END": "Agent completed",
    "AGENT_TIMEOUT": "Agent timed out",
    
    # Actions
    "TOOL_CALL": "Tool invoked",
    "TOOL_RESULT": "Tool returned",
    "TOOL_ERROR": "Tool failed",
    
    # Handoffs
    "HANDOFF_SEND": "Context sent to agent",
    "HANDOFF_ACK": "Context acknowledged",
    "HANDOFF_COMPLETE": "Agent finished with context",
    
    # State
    "CHECKPOINT": "State saved",
    "STATE_CHANGE": "State modified",
    
    # Errors
    "ERROR_CAUGHT": "Error handled",
    "RECOVERY_ATTEMPT": "Recovery started",
    "ESCALATION": "Human needed"
}
```

---

## Metrics Collection

### Key Metrics

```yaml
# Counters
agent_spawns_total:
  labels: [agent_id, task_type]
  help: "Total agents spawned"

tool_calls_total:
  labels: [tool, result]
  help: "Total tool invocations"

handoffs_total:
  labels: [from_agent, to_agent]
  help: "Total context handoffs"

errors_total:
  labels: [agent_id, error_type]
  help: "Total errors encountered"

# Histograms
task_duration_seconds:
  labels: [agent_id, task_type]
  buckets: [1, 5, 10, 30, 60, 300, 600]
  help: "Task execution time"

tool_duration_ms:
  labels: [tool]
  buckets: [10, 50, 100, 500, 1000, 5000]
  help: "Tool execution time"

# Gauges
active_agents:
  help: "Currently running agents"

pending_tasks:
  help: "Tasks waiting for agent"
```

### Metrics Dashboard View

```
┌────────────────────────────────────────────────────────────┐
│  AGENT SYSTEM METRICS - Last 24h                           │
├────────────────────────────────────────────────────────────┤
│  Agents spawned:     156    ✓ +12% vs yesterday            │
│  Avg duration:       4m32s  ↑ +30s (investigate)           │
│  Error rate:         2.3%   ✓ Within threshold            │
│  Active now:         3      [synthesis, coder, researcher]│
├────────────────────────────────────────────────────────────┤
│  TOP TOOLS USED                     TOP ERRORS             │
│  ──────────────                     ──────────             │
│  read:      234 calls               timeout: 5             │
│  write:     189 calls               not_found: 3           │
│  edit:      145 calls               permission: 1          │
│  exec:      89 calls                                        │
├────────────────────────────────────────────────────────────┤
│  HANDOFF HEALTH                                             │
│  ──────────────                                             │
│  Total handoffs:    42                                      │
│  Avg latency:       0.8s                                    │
│  Recovery rate:     95%                                     │
└────────────────────────────────────────────────────────────┘
```

---

## State Inspection

### Snapshot Protocol

Capture system state at key moments:

```python
def capture_snapshot(reason="manual"):
    """Capture current system state."""
    return {
        "snapshot_id": generate_id(),
        "timestamp": now(),
        "reason": reason,
        "agents": {
            "active": list_active_agents(),
            "pending": list_pending_tasks()
        },
        "files": {
            "workspace": list_workspace_files(),
            "memory": list_memory_files()
        },
        "sessions": {
            "main": get_main_session(),
            "subagents": list_subagents()
        },
        "metrics": {
            "tokens_used": get_token_count(),
            "tools_called": get_tool_call_count()
        }
    }
```

### State Diff

Compare snapshots to debug changes:

```markdown
## State Diff: snap_before → snap_after

### Agents
+ spawned: coder_agent (sess_abc)
- completed: research_agent (sess_xyz)

### Files Created
+ /workspace/output/summary.md (2.3KB)
+ /workspace/output/research.md (5.1KB)

### Files Modified
~ /workspace/memory/2026-02-22.md (+15 lines)

### Metrics Change
↑ tokens_used: +12,450
↑ tools_called: +23
```

---

## Debugging Workflows

### Workflow 1: Failed Task Debug

```bash
# 1. Find the trace ID
grep "task_id: <TASK_ID>" traces/*.json

# 2. Extract full trace
cat traces/*.json | jq 'select(.trace_id == "<TRACE_ID>")'

# 3. Identify failure point
cat traces/*.json | jq 'select(.trace_id == "<TRACE_ID>") | select(.event_type == "ERROR_CAUGHT")'

# 4. Get state at failure
cat snapshots/failure_<TIMESTAMP>.json

# 5. Replay with debug logging
DEBUG=1 TRACE_ID=<TRACE_ID> re_run_task
```

### Workflow 2: Performance Investigation

```bash
# 1. Find slow tasks
cat metrics.json | jq '.task_duration | select(.value > 300)' 

# 2. Get trace for slow task
TRACE_ID=$(cat metrics.json | jq -r '.task_duration | select(.value > 300) | .trace_id')

# 3. Analyze tool calls
cat traces/*.json | jq "select(.trace_id == \"$TRACE_ID\" and .event_type == \"TOOL_CALL\") | {tool: .action, duration: .duration_ms}"

# 4. Identify bottlenecks
# Output: Which tools took longest? Where were waits?
```

### Workflow 3: Handoff Debug

```bash
# 1. Find all handoffs in trace
cat traces/*.json | jq 'select(.trace_id == "<TRACE_ID>" and .event_type | startswith("HANDOFF"))'

# 2. Verify context package integrity
cat handoffs/<HANDOFF_ID>.json | jq 'keys'

# 3. Check artifacts referenced
for artifact in $(cat handoffs/<HANDOFF_ID>.json | jq -r '.artifacts[]'); do
  ls -la "$artifact" || echo "MISSING: $artifact"
done
```

---

## Log Aggregation

### Unified Log Format

```python
LOG_FORMAT = {
    "timestamp": "ISO8601",
    "level": "DEBUG | INFO | WARN | ERROR",
    "trace_id": "correlation_id",
    "session_id": "agent_session",
    "agent_id": "agent_type",
    "message": "human readable",
    "context": {"key": "value"},  # Structured context
    "duration_ms": 123
}

# Example
{
    "timestamp": "2026-02-22T14:20:15.123Z",
    "level": "INFO",
    "trace_id": "trace_abc123",
    "session_id": "sess_xyz",
    "agent_id": "coder",
    "message": "File created successfully",
    "context": {"path": "/output/code.ts", "lines": 150},
    "duration_ms": 45
}
```

### Log Query Examples

```bash
# All errors in last hour
cat logs/*.json | jq 'select(.timestamp > "2026-02-22T13:20" and .level == "ERROR")'

# All events for a trace
cat logs/*.json | jq 'select(.trace_id == "trace_abc123")' | jq -s 'sort_by(.timestamp)'

# Slow operations (>1s)
cat logs/*.json | jq 'select(.duration_ms > 1000)'

# Handoff latency
cat logs/*.json | jq 'select(.event_type == "HANDOFF_ACK") | .duration_ms' | avg
```

---

## Debugging Tools

### Quick Diagnostics Script

```bash
#!/bin/bash
# debug_agent.sh - Quick system diagnostics

echo "=== AGENT SYSTEM DIAGNOSTICS ==="
echo "Generated: $(date -Iseconds)"
echo

echo "Active Agents:"
sessions_list --kinds "subagent" --active-minutes 5

echo
echo "Recent Errors (last 1h):"
grep -r '"level": "ERROR"' logs/ --include="*.json" | tail -10

echo
echo "Workspace Files:"
find ~/.openclaw/workspace -type f -mmin -60 | head -20

echo
echo "Memory Files:"
ls -la ~/.openclaw/workspace/memory/ | tail -10

echo
echo "Recent Tool Calls:"
grep -r '"event_type": "TOOL_CALL"' traces/ --include="*.json" | tail -10
```

### Interactive Debug Session

```python
# Interactive Python debug shell

from agent_debug import (
    list_traces, get_trace, list_agents, get_agent_state,
    list_handoffs, get_handoff, replay_trace, capture_snapshot
)

# Start interactive session
print("Agent Debug Shell. Type 'help' for commands.")
print("Current trace: None")

while True:
    cmd = input("debug> ").strip()
    
    if cmd.startswith("trace "):
        trace_id = cmd.split()[1]
        trace = get_trace(trace_id)
        for event in trace:
            print(f"[{event['timestamp']}] {event['event_type']}: {event.get('message', '')}")
    
    elif cmd.startswith("agent "):
        agent_id = cmd.split()[1]
        state = get_agent_state(agent_id)
        print(json.dumps(state, indent=2))
    
    elif cmd == "snapshot":
        snap = capture_snapshot(reason="interactive")
        print(f"Snapshot saved: {snap['snapshot_id']}")
    
    elif cmd == "help":
        print("""
Commands:
  trace <id>     - Show trace events
  agent <id>     - Show agent state
  snapshot       - Capture current state
  handoffs       - List recent handoffs
  replay <id>    - Replay a trace
  quit           - Exit
        """)
```

---

## Alerting Rules

```yaml
# alerts.yaml
groups:
  - name: agent_health
    rules:
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate: {{ $value | humanizeRate }}"
      
      - alert: AgentTimeout
        expr: agent_duration_seconds > 600
        labels:
          severity: critical
        annotations:
          summary: "Agent {{ $labels.agent_id }} running >10 min"
      
      - alert: HandoffFailure
        expr: rate(handoffs_total{result="failed"}[5m]) > 0
        labels:
          severity: warning
        annotations:
          summary: "Handoff failures detected"
      
      - alert: CascadingFailure
        expr: delta(errors_total[1m]) > 3
        labels:
          severity: critical
        annotations:
          summary: "Possible cascading failure"
```

---

## Quick Debug Checklist

```markdown
AGENTS MISBEHAVING? START HERE.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Check active agents (sessions_list)
□ Look for errors in logs (grep ERROR)
□ Verify files exist (ls workspace)
□ Check recent handoffs (grep HANDOFF)
□ Capture snapshot before investigation
□ Find trace ID for failing task
□ Review timing for slow operations
□ Compare state before/after issue
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Bottom Line

Observability requires:
1. **Structured logs** with trace correlation
2. **Metrics** for patterns and trends
3. **State capture** for forensics
4. **Debug workflows** for common scenarios
5. **Alerts** for proactive detection

When something goes wrong, you should be able to answer: Who? What? When? How long? and Why? in under 5 minutes.