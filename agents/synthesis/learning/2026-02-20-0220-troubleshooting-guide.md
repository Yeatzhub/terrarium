# Troubleshooting Guide

*Common issues and fixes for multi-agent workflows*

---

## Quick Diagnostics

### Agent Won't Start
| Check | Fix |
|-------|-----|
| `sessions_spawn` returns error | Check `agentId` in `agents_list` |
| Timeout immediately | Verify `runTimeoutSeconds` > 0 |
| "Invalid task" error | Task description > 10 chars, < 10000 chars |

### Agent Hangs
| Symptom | Cause | Fix |
|---------|-------|-----|
| Stuck "running" for hours | Infinite loop or waiting on resource | Set `runTimeoutSeconds`, spawn with cleanup |
| Never returns status | Session key invalid | Check spawn returned valid key |
| Polling shows no change | Agent crashed silently | Check logs, spawn with `cleanup: 'never'` to debug |

### Output Missing
| Check | Command |
|-------|---------|
| File actually written? | `ls -la /path/to/output` |
| Correct path? | Use absolute paths, not relative |
| Permissions? | Check write access to output directory |
| Agent completed? | `subagents list` shows status |

---

## Common Errors

### Error: "Session not found"
**Cause:** Session key expired or was cleaned up

**Fix:**
```python
# Check if still exists
result = await subagents({"action": "list"})
# If not, check if output file exists anyway
if os.path.exists(expected_output):
    # Recovery: proceed with file
```

**Prevention:**
- Use `cleanup: 'never'` for debugging
- Save outputs to known paths before completion

### Error: "Timeout waiting for agent"
**Cause:** Task too complex or agent stuck

**Fix:**
```python
# 1. Check if partial output exists
if os.path.exists("/tmp/partial.json"):
    # Resume from checkpoint
    
# 2. Retry with longer timeout
await sessions_spawn({
    "task": task,
    "runTimeoutSeconds": 1200  # Increase from 600
})

# 3. Decompose into smaller tasks
```

**Prevention:**
- Follow 15-minute rule
- Test task duration before full run

### Error: "Dependency check failed"
**Cause:** File doesn't exist or path wrong

**Fix:**
```python
# Verify before spawning
for dep in dependencies:
    if not os.path.exists(dep):
        raise FileNotFoundError(f"Dependency missing: {dep}")

# Or create stub
if not os.path.exists(dep):
    write(dep, "{}")  # Minimal valid JSON
```

### Error: "Context window exceeded"
**Cause:** Task description too large

**Fix:**
```python
# BAD: Inline large data
"task": f"Analyze {huge_data}"

# GOOD: File reference
write("/tmp/data.json", huge_data)
"task": "Analyze /tmp/data.json"
```

---

## Performance Issues

### Slow Execution
| Symptom | Diagnosis | Fix |
|---------|-----------|-----|
| Sequential tasks taking forever | Not parallelizing independent work | Use `asyncio.gather` |
| Polling consuming resources | Tight loop | Exponential backoff (start 5s, max 30s) |
| Token limits hit | Over-large handoffs | File references over inline |
| Memory errors | Too many concurrent spawns | Use `asyncio.Semaphore(5)` |

### Resource Exhaustion
```python
# Limit concurrent spawns
MAX_WORKERS = 5
semaphore = asyncio.Semaphore(MAX_WORKERS)

async def bounded_spawn(task):
    async with semaphore:
        return await sessions_spawn(task)

# Process in controlled batches
results = await asyncio.gather(*[
    bounded_spawn(t) for t in tasks
])
```

---

## Debugging Techniques

### Enable Verbose Logging
```python
# Log all spawn calls
async def logged_spawn(task, **kwargs):
    print(f"SPAWN: {task[:50]}...")
    result = await sessions_spawn({"task": task, **kwargs})
    print(f"RESULT: {result}")
    return result
```

### Preserve Sessions for Inspection
```python
# Keep failed sessions for debugging
await sessions_spawn({
    "task": task,
    "cleanup": "never"  # Manual cleanup required
})

# Later: view history
await sessions_history(sessionKey="...", limit=50)
```

### Check Intermediate Outputs
```python
# Verify at each phase
phases = [
    ("research", "/tmp/research.json"),
    ("analysis", "/tmp/analysis.md"),
    ("report", "/output/report.md")
]

for name, path in phases:
    if not os.path.exists(path):
        raise PhaseError(f"{name} failed: {path} missing")
    print(f"✓ {name}: {os.path.getsize(path)} bytes")
```

---

## Recovery Workflows

### Scenario: Halfway Through, Agent Fails
```python
# 1. Identify completed phases
completed = []
for phase, output in phases:
    if os.path.exists(output):
        completed.append(phase)
    else:
        break

# 2. Resume from last complete
last_complete = completed[-1] if completed else None
next_phase = get_next_phase(last_complete)

# 3. Re-spawn from checkpoint
await sessions_spawn({
    "task": f"Resume {next_phase} from checkpoint",
    "label": f"recovery-{next_phase}"
})
```

### Scenario: Cascade Failure
```python
# Circuit breaker pattern
class CircuitBreaker:
    failures = 0
    threshold = 3
    
    async def call(self, fn):
        if self.failures >= self.threshold:
            raise CircuitOpen("Too many failures")
        try:
            return await fn()
        except Exception:
            self.failures += 1
            raise

# Usage: Stop after repeated failures
breaker = CircuitBreaker()
for task in tasks:
    try:
        await breaker.call(lambda: sessions_spawn(task))
    except CircuitOpen:
        print("Halting: too many failures")
        break
```

---

## Validation Failures

### "Output format doesn't match"
```python
# Standard validation
def validate_output(path, schema):
    content = read(path)
    
    # Check required sections
    for section in schema["required"]:
        if section not in content:
            raise ValidationError(f"Missing: {section}")
    
    # Check format
    if schema["format"] == "json":
        try:
            json.loads(content)
        except:
            raise ValidationError("Invalid JSON")

# Usage
validate_output("/output/result.json", {
    "required": ["summary", "data"],
    "format": "json"
})
```

### "Quality gate failed"
```python
# Automated quality check
def quality_gate(path):
    content = read(path)
    
    checks = [
        ("TODO" in content, "Contains TODO"),
        (len(content.split()) < 100, "Too short"),
        ("Summary" not in content, "Missing Summary"),
    ]
    
    failures = [msg for failed, msg in checks if failed]
    if failures:
        raise QualityError(failures)
```

---

## Prevention Checklist

Before running workflows:
- [ ] All file paths absolute or $WORKSPACE-relative
- [ ] `runTimeoutSeconds` set for each spawn
- [ ] `cleanup` mode explicitly chosen
- [ ] Dependencies verified before spawning dependents
- [ ] Token budget checked (large data > files)
- [ ] Concurrent limits set (semaphore if >5 parallel)
- [ ] Checkpoint files for long tasks
- [ ] Validation functions ready
- [ ] Rollback plan defined

---

## Emergency Commands

```bash
# List all active agents
openclaw subagents list

# Check specific agent status
openclaw subagents status --target SESSION_KEY

# View agent history
openclaw sessions history --session SESSION_KEY --limit 50

# Kill stuck agent
openclaw subagents kill --target SESSION_KEY

# Cleanup old sessions
openclaw subagents cleanup --older-than 1h

# Check system status
openclaw session_status
```

---

*Generated: 2026-02-20 | Use: When things go wrong*
