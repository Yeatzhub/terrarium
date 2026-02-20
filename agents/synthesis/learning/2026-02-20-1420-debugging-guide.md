# Debugging Multi-Agent Workflows
*Synthesis Learning — 2026-02-20*

When workflows fail, hang, or produce wrong outputs. Systematic diagnosis and recovery.

## 1. Quick Diagnostic Commands

### Check System State
```bash
# Active sessions
sessions_list --activeMinutes=5

# Specific workflow status
sessions_list | grep "workflow-label"

# Resource usage
session_status --sessionKey <key>

# Recent failures
cron action=list | grep -E "(failed|error)"
```

### Check Agent Health
```bash
# Test agent responsiveness
sessions_spawn --task "PING: Return 'pong'" --agentId <agent> --timeoutSeconds=10

# Check if specific agent type is stuck
subagents list | grep "agent-id"

# Kill stuck processes
subagents action=kill target=<agent-id>
```

---

## 2. Common Failure Patterns

### The Hang (No Response)

**Symptoms**: Agent spawned, no output, timeout eventually fires
**Diagnosis**:
```bash
# Check if agent is still processing
sessions_history --sessionKey <key> --limit 3

# Check system resources
exec top -n1 | head -20
```
**Causes**:
- Task too large (context >8000 tokens)
- Infinite loop in reasoning
- Resource exhaustion (OOM)
- Dependency waiting for unavailable resource

**Fixes**:
```python
# 1. Reduce context size
pruned_context = context[:4000]  # Hard limit

# 2. Break into smaller subtasks
subtasks = chunk_task(large_task, max_tokens=2000)

# 3. Add explicit termination conditions
task_with_limit = f"{original_task}\n\nStop after 3 iterations or 2 minutes."
```

### The Empty Return

**Symptoms**: Agent completes, output is empty or ""
**Diagnosis**:
```bash
# Check actual response
sessions_history --sessionKey <key> --limit 10

# Check if file write was attempted
read <output-file> 2>&1 || echo "File missing"
```
**Causes**:
- Output file path not specified
- Agent confused about output format
- Silent failure in generation

**Fixes**:
```python
# Explicit output requirements
task = """
Analyze the data and WRITE RESULTS to output.json.
Format: {"analysis": "...", "confidence": 0.95}
Must include at least 3 findings.
"""

# Verify file was written
if not os.path.exists("output.json"):
    retry_with_explicit_path()
```

### The Wrong Output

**Symptoms**: Agent responds, but answer is irrelevant/wrong
**Diagnosis**:
```bash
# Check what was actually asked
sessions_history --sessionKey <key> | head -20

# Compare with expected scope
```
**Causes**:
- Context drift (agent lost original goal)
- Ambiguous task description
- Missing domain context
- Agent capabilities mismatch

**Fixes**:
```python
# Re-anchor with original goal
correction_task = f"""
Previous response was off-topic. Focus ONLY on: {original_goal}

Original context: {pruned_context}

Required output format: {format_spec}
"""

# Or escalate to more capable agent
sessions_spawn --task correction_task --agentId "specialist" --timeoutSeconds=120
```

### The Cascade Failure

**Symptoms**: Multiple agents failing in sequence
**Diagnosis**:
```bash
# Check failure pattern
sessions_list | grep -B2 -A2 "failed"

# Look for common cause
sessions_list | grep "error" | sort | uniq -c
```
**Causes**:
- Shared dependency failed (API, database, file system)
- Bad input propagated through pipeline
- Rate limiting / quota exhaustion

**Fixes**:
```python
# 1. Identify root cause agent
root_failure = find_first_failure(failed_chain)

# 2. Fix or work around
if is_api_failure(root_failure):
    use_cached_data_or_fallback()
elif is_bad_input(root_failure):
    fix_input_and_replay_from_checkpoint()

# 3. Replay workflow from checkpoint
replay_from_stage(checkpoint_stage)
```

### The Partial Success

**Symptoms**: Some agents succeed, others fail
**Diagnosis**:
```bash
# Get success/failure breakdown
sessions_list --label workflow-id | awk '{print $3}' | sort | uniq -c
```
**Causes**:
- Load imbalance (too many parallel agents)
- Task difficulty variation
- Resource contention

**Fixes**:
```python
# Retry only failed tasks
failed = [r for r in results if not r.success]
successful = [r for r in results if r.success]

if len(successful) / len(results) > 0.7:
    # 70%+ success - retry failed with more time
    retried = await fanout_workflow(
        [f.task for f in failed],
        timeout=original_timeout * 2
    )
    all_results = successful + retried.results
else:
    # Too many failed - investigate root cause
    investigate_and_escalate()
```

---

## 3. Context Debugging

### When Context is Too Large

**Symptoms**: Slow responses, truncated outputs, agent confusion
**Diagnosis**:
```bash
# Measure context size
sessions_history --sessionKey <key> | wc -w

# Typical limits:
# - Fast responses: <1000 tokens
# - Standard tasks: <2000 tokens
# - Complex analysis: <4000 tokens
# - >8000 tokens: Expect problems
```
**Fixes**:
```python
def prune_context(history, max_tokens=2000):
    """Aggressive pruning for large contexts."""
    # Keep only: last decision, current task, original goal
    essential = {
        "goal": extract_goal(history[0]),
        "last_decision": history[-1].get("decision"),
        "current_task": history[-1].get("task"),
        "reference": f"Full history: {state_file}"
    }
    return essential
```

### When Context is Missing

**Symptoms**: Agent asks for information already provided
**Diagnosis**:
```bash
# Check what context was actually sent
sessions_history --sessionKey <key> | grep -A5 "context"

# Verify context file exists
read <context-file> | head -50
```
**Fixes**:
```python
# Include context inline, not just by reference
task = f"""
Context (DO NOT ask for this again):
{context}

Your task: {specific_task}
"""

# Or use differential updates
task = f"""
Since last checkpoint (full history: {state_file}):
- Decision: Switched to PostgreSQL
- New constraint: Must support 10k concurrent users

Your task: {specific_task}
"""
```

---

## 4. Recovery Procedures

### Resume from Checkpoint

```bash
# 1. Find last checkpoint
ls -la checkpoints/ | tail -5

# 2. Read checkpoint state
checkpoint=$(cat checkpoints/pipeline-20260220-143000.json)

# 3. Resume workflow
sessions_spawn --task "Resume from checkpoint: $checkpoint" --agentId orchestrator
```

### Replay with Fixes

```python
async def replay_with_fix(workflow_id, fix_fn):
    """Replay workflow with corrected input/fixture."""
    # 1. Get original workflow
    original = await get_workflow_history(workflow_id)
    
    # 2. Apply fix
    fixed_input = fix_fn(original.input)
    
    # 3. Clear intermediate state
    await clear_stale_checkpoints(workflow_id)
    
    # 4. Replay
    return await run_workflow(original.definition, fixed_input)
```

### Emergency Escalation

```python
def escalate_to_user(error, context):
    """Surface unrecoverable errors to user with full context."""
    escalation = f"""
WORKFLOW FAILED - Manual intervention required

Error: {error}

Context:
- Workflow ID: {context.workflow_id}
- Failed at: {context.stage}
- Last checkpoint: {context.checkpoint_file}
- Attempts: {context.retry_count}

Options:
1. Retry from checkpoint (may repeat failure)
2. Modify input and replay
3. Escalate to developer
4. Abort and preserve partial results

Partial results available at: {context.output_dir}
"""
    
    # Send to user
    sessions_send --target user --message escalation
```

---

## 5. Prevention: Defensive Patterns

### Pre-flight Validation

```python
def validate_before_spawn(task, context, agent_id):
    """Catch issues before expensive agent spawn."""
    issues = []
    
    # Check context size
    if estimate_tokens(context) > 4000:
        issues.append("Context too large, prune required")
    
    # Check task clarity
    if len(task) < 50 or "?" in task[:100]:
        issues.append("Task unclear or contains questions")
    
    # Check agent capability
    if agent_id not in AGENT_CAPABILITIES:
        issues.append(f"Unknown agent: {agent_id}")
    
    # Check dependencies
    for dep in extract_dependencies(task):
        if not check_dependency(dep):
            issues.append(f"Missing dependency: {dep}")
    
    if issues:
        raise PreFlightError(issues)
```

### Health Checks During Execution

```python
async def monitored_spawn(task, agent_id, timeout):
    """Spawn with progress monitoring."""
    spawn_task = sessions_spawn({
        "task": task,
        "agentId": agent_id,
        "timeoutSeconds": timeout
    })
    
    # Parallel monitoring
    monitor_task = monitor_progress(agent_id, timeout)
    
    done, pending = await asyncio.wait(
        [spawn_task, monitor_task],
        return_when=asyncio.FIRST_COMPLETED
    )
    
    result = done.pop().result()
    
    # Cancel monitor
    for task in pending:
        task.cancel()
    
    return result

async def monitor_progress(agent_id, timeout):
    """Alert if agent appears stuck."""
    await asyncio.sleep(timeout * 0.5)  # Check at 50%
    
    status = subagents list | grep agent_id
    if status == "no_progress":
        log_warning(f"Agent {agent_id} may be stuck at 50% mark")
```

---

## 6. Diagnostic Decision Tree

```
Workflow Failed
├── Agent spawned?
│   ├── NO → Check spawn limits, agent availability
│   └── YES → Check response received
│       ├── NO (timeout) → Context too large? Task too complex? Resource issue?
│       └── YES → Check output quality
│           ├── Empty/Invalid → Bad task spec? Missing dependencies?
│           ├── Wrong content → Context drift? Wrong agent type?
│           └── Partial → Retry failed? Replay from checkpoint?
└── Check logs
    ├── Error message → Handle specific error
    └── No error → Instrumentation gap, add logging
```

---

## 7. Debugging Checklist

When workflow fails:
- [ ] Check `sessions_list` for stuck agents
- [ ] Check `session_status` for resource issues
- [ ] Verify context size <2000 tokens
- [ ] Check all dependencies available
- [ ] Review last 3 messages in `sessions_history`
- [ ] Check for checkpoint to resume from
- [ ] Verify agent_id exists and healthy
- [ ] Check if rate limits/quota exceeded
- [ ] Look for error patterns in logs
- [ ] Test agent with simple PING task

---

## 8. Logging Best Practices

```python
def log_workflow_event(workflow_id, event, data):
    """Structured logging for debugging."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "workflow_id": workflow_id,
        "event": event,
        "data": data,
        "context_size": estimate_tokens(data.get("context", "")),
        "agent_id": data.get("agent_id"),
        "stage": data.get("stage")
    }
    
    # Write to searchable log
    append_to_file(f"logs/{workflow_id}.jsonl", json.dumps(entry))
    
    # Key events to console
    if event in ["SPAWN", "COMPLETE", "ERROR", "RETRY"]:
        console.log(f"[{workflow_id}] {event}: {data.get('summary', '')}")
```

---

*Use with implementation templates (2026-02-20-1220) for robust error handling.*
