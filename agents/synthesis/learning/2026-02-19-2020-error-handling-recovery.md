# Error Handling and Recovery Patterns

*Graceful failure management in multi-agent workflows*

---

## 1. Failure Classification

### Agent-Level Failures
| Type | Cause | Detection |
|------|-------|-----------|
| Timeout | Task exceeded limit | Poll status shows timeout |
| Crash | Exception in agent | Status shows error |
| Wrong output | Misunderstood task | Output validation fails |
| Resource exhaustion | Out of memory/disk | System-level error |

### Workflow-Level Failures
| Type | Cause | Impact |
|------|-------|--------|
| Dependency failure | Upstream task failed | All downstream blocked |
| Cascading timeout | Chain too long | Multiple agents timeout |
| Deadlock | Circular dependency | Workflow hangs |
| Data corruption | Invalid intermediate file | Subsequent tasks fail |

---

## 2. Recovery Patterns

### Pattern: Retry with Backoff
```python
async def retry_spawn(task, max_attempts=3):
    for attempt in range(max_attempts):
        try:
            job = await sessions_spawn({
                "task": task,
                "runTimeoutSeconds": 120
            })
            result = await wait_with_backoff(job["sessionKey"])
            if result["status"] == "completed":
                return result
        except TimeoutError:
            wait_time = 2 ** attempt  # 1, 2, 4 seconds
            await asyncio.sleep(wait_time)
    
    raise MaxRetriesExceeded(f"Failed after {max_attempts} attempts")
```

### Pattern: Circuit Breaker
```python
class CircuitBreaker:
    def __init__(self, threshold=3, reset_time=300):
        self.failures = 0
        self.threshold = threshold
        self.reset_time = reset_time
        self.last_failure = None
    
    async def call(self, fn, *args):
        if self.failures >= self.threshold:
            if time.time() - self.last_failure < self.reset_time:
                raise CircuitOpen("Service temporarily unavailable")
            self.failures = 0  # Reset after cooldown
        
        try:
            result = await fn(*args)
            self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure = time.time()
            raise
```

### Pattern: Fallback Chain
```python
async def resilient_task(primary_fn, fallbacks):
    """Try primary, then fallbacks in order"""
    attempts = [primary_fn] + fallbacks
    
    for i, fn in enumerate(attempts):
        try:
            return await fn()
        except Exception as e:
            if i == len(attempts) - 1:
                raise  # All failed
            log.warning(f"Attempt {i+1} failed, trying fallback")
```

### Pattern: Graceful Degradation
```python
async def analysis_with_fallback(data):
    try:
        # Try comprehensive analysis
        return await deep_analysis(data)
    except TimeoutError:
        log.warning("Deep analysis timed out, using quick analysis")
        return await quick_analysis(data)  # Less thorough but fast
    except Exception as e:
        log.error(f"Analysis failed: {e}")
        return {"error": str(e), "partial": True, "data": data[:100]}
```

---

## 3. Error Reporting Standards

### Structured Error Format
```json
{
  "error": {
    "type": "timeout",
    "message": "Task exceeded 120 second limit",
    "context": {
      "task": "Analyze large dataset",
      "agent": "synthesis",
      "input_size": "50MB",
      "progress": "45% complete"
    },
    "recovery": {
      "suggested_action": "Increase timeout or chunk data",
      "partial_output": "/tmp/partial_result.json"
    }
  }
}
```

### Error Message Template
```
[ERROR TYPE]: Brief classification
[WHAT]: What was being attempted
[WHY]: Root cause or constraint violated
[IMPACT]: Effect on overall workflow
[RECOVERY]: Specific next steps
```

---

## 4. Monitoring and Alerting

### Health Check Pattern
```python
async def workflow_health_check(workflow_id):
    checks = {
        "agents_running": await count_active_agents(),
        "failed_last_hour": await count_recent_failures(minutes=60),
        "avg_completion_time": await get_avg_duration(),
        "queue_depth": await get_pending_count()
    }
    
    if checks["failed_last_hour"] > 5:
        alert("High failure rate detected")
    
    if checks["queue_depth"] > 10:
        alert("Queue backup - consider scaling")
    
    return checks
```

### Failure Rate Tracking
```python
# Alert if failure rate > 20% over 10 minutes
recent = get_failures(since=minutes_ago(10))
total = get_attempts(since=minutes_ago(10))

if total > 0 and (recent / total) > 0.2:
    escalate("Failure rate critical: {}%".format(recent/total*100))
```

---

## 5. Cleanup and Recovery

### Partial Result Preservation
```python
async def spawn_with_recovery(task, checkpoint_dir="/tmp/checkpoints"):
    checkpoint_file = f"{checkpoint_dir}/{uuid4()}.json"
    
    try:
        job = await sessions_spawn({
            "task": f"{task}; write checkpoint to {checkpoint_file}",
            "cleanup": "never"  # Keep for debugging
        })
        result = await wait_for(job["sessionKey"])
        
        if result["status"] == "timeout":
            # Try to resume from checkpoint
            if os.path.exists(checkpoint_file):
                return await resume_from_checkpoint(checkpoint_file)
        
        return result
    finally:
        # Cleanup after success or confirmed unrecoverable
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
```

### Dependency Failure Handling
```python
async def execute_with_deps(task, dependencies):
    failed_deps = []
    
    # Check all dependencies first
    for dep in dependencies:
        status = await check_dependency(dep)
        if status != "completed":
            failed_deps.append(dep)
    
    if failed_deps:
        return {
            "status": "blocked",
            "reason": f"Dependencies failed: {failed_deps}",
            "action": "Retry dependencies or modify workflow"
        }
    
    return await execute_task(task)
```

---

## 6. Prevention Strategies

### Input Validation
```python
def validate_spawn_request(request):
    required = ["task", "expected_output", "timeout"]
    
    for field in required:
        if field not in request:
            raise ValidationError(f"Missing required field: {field}")
    
    if request["timeout"] > 600:
        log.warning("Timeout > 10min - consider decomposition")
    
    if len(request["task"]) > 10000:
        log.warning("Large task description - use file reference")
```

### Resource Limits
```python
# Enforce limits at spawn time
MAX_CONCURRENT = 5

semaphore = asyncio.Semaphore(MAX_CONCURRENT)

async def bounded_spawn(task):
    async with semaphore:
        return await sessions_spawn(task)
```

---

## 7. Error Recovery Checklist

When an agent fails:
- [ ] Check error type (timeout/crash/validation)
- [ ] Preserve partial results if available
- [ ] Log full context (task, inputs, attempt #)
- [ ] Determine if retryable
- [ ] If retryable: apply backoff
- [ ] If not retryable: activate fallback
- [ ] If all fail: escalate to user
- [ ] Update workflow state
- [ ] Notify dependent tasks

---

## Quick Reference: Error Actions

| Error | Immediate Action | Recovery |
|-------|-----------------|----------|
| Timeout | Check partial output | Retry with longer timeout or chunk task |
| Crash | Capture stack trace | Fix bug and retry |
| Bad output | Validate format | Retry with clearer instructions |
| Dep failure | Stop dependent tasks | Retry dependency or use fallback |
| Resource limit | Free resources | Retry with smaller input |

---

*Generated: 2026-02-19 | Use: Reference when building resilient workflows*
