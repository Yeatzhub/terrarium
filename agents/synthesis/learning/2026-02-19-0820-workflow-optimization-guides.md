# Workflow Optimization Guide

*Practical strategies for fast, efficient agent workflows*

---

## 1. Spawn vs Self-Execution

### Decision Matrix

| Factor | Spawn | Do It Yourself |
|--------|-------|----------------|
| Task Duration | > 3 min | < 2 min |
| Context Isolation | Required | Not needed |
| Parallel Needs | Yes | No |
| Failure Recovery | Needs retry | Immediate retry |
| Token Budget | > 50% remaining | Any |

### Golden Rule
> If it takes longer to describe the task than to do it, **do it yourself**.

---

## 2. Parallelization Strategies

### Pattern: Scatter-Gather
```python
# Launch multiple independent tasks
jobs = []
for source in data_sources:
    job = await sessions_spawn({
        "task": f"Process {source} → output/{source}.json",
        "label": f"process-{source}"
    })
    jobs.append(job["sessionKey"])

# Gather results
results = await asyncio.gather(*[
    poll_until_complete(job) for job in jobs
])
```

### Pattern: Worker Pool
```python
# Limit concurrent spawns to avoid resource exhaustion
MAX_WORKERS = 3
semaphore = asyncio.Semaphore(MAX_WORKERS)

async def bounded_spawn(task):
    async with semaphore:
        return await sessions_spawn({"task": task})

# Process in batches
results = await asyncio.gather(*[
    bounded_spawn(t) for t in tasks
])
```

---

## 3. Token Efficiency

### Technique: Reference Over Inline
```python
# BAD: Inline large data
await sessions_spawn({
    "task": f"Analyze this data: {json.dumps(huge_dataset)}"  # Expensive!
})

# GOOD: File reference
write("/tmp/data.json", json.dumps(huge_dataset))
await sessions_spawn({
    "task": "Analyze /tmp/data.json and summarize"
})
```

### Technique: Progressive Summarization
```python
# Phase 1: Summarize raw data
job1 = await sessions_spawn({
    "task": "Read large_file.json → output/summary.json with only key fields"
})

# Phase 2: Work with summary (cheaper tokens)
job2 = await sessions_spawn({
    "task": "Analyze output/summary.json for trends"
})
```

### Token Budget Guidelines
- Reserve 25% for agent's response
- Input > 50% of context window → use file reference
- Multi-turn chains → summarize between turns

---

## 4. Polling Patterns

### Pattern: Exponential Backoff
```python
async def poll_with_backoff(session_key, max_wait=300):
    """Poll with increasing intervals up to max_wait seconds"""
    waited = 0
    delay = 5  # Start with 5s
    
    while waited < max_wait:
        status = await subagents({"action": "list")
        
        if status.get("completed"):
            return status
        
        await asyncio.sleep(delay)
        waited += delay
        delay = min(delay * 1.5, 30)  # Cap at 30s
    
    raise TimeoutError(f"Job didn't complete in {max_wait}s")
```

### Anti-Pattern: Tight Polling Loops
```python
# BAD: Hammering the API
while True:
    status = await subagents({"action": "list"})  # Too frequent!
    if status["completed"]:
        break
    await asyncio.sleep(1)  # Still too aggressive
```

---

## 5. File vs Memory

### Decision Guide

| Data Type | Storage | Reason |
|-----------|---------|--------|
| Large datasets (>1MB) | File | Token limits |
| Shared state | File | Persistence across agents |
| Session cache | Memory | Fast access, temporary |
| Final outputs | File | Results survive session |

### Pattern: Staging Directory
```python
# Use consistent staging locations
STAGING_DIR = "/tmp/agent_workflows"
os.makedirs(STAGING_DIR, exist_ok=True)

# Name by purpose + timestamp
output_path = f"{STAGING_DIR}/analysis_{int(time.time())}.json"
```

---

## 6. Session Management

### Pattern: Cleanup Strategies
```python
# Option 1: Fire-and-forget (results in main session)
await sessions_spawn({
    "task": "Do work",
    "cleanup": "always"  # Removes isolated session
})

# Option 2: Preserve for debugging
job = await sessions_spawn({
    "task": "Do work",
    "cleanup": "never"  # Keep for inspection
})
# ...later check results, then manual cleanup

# Option 3: Success-only cleanup
await sessions_spawn({
    "task": "Do work",
    "cleanup": "success"  # Keep on failure for debugging
})
```

---

## 7. Error Recovery Patterns

### Pattern: Retry with Circuit Breaker
```python
async def resilient_spawn(task, max_retries=2):
    """Spawn with automatic retry and circuit breaker"""
    for attempt in range(max_retries):
        try:
            job = await sessions_spawn({"task": task})
            result = await poll_with_timeout(job["sessionKey"])
            
            if result.get("error"):
                raise RuntimeError(result["error"])
            
            return result
            
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Pattern: Fallback Chain
```python
# Try primary approach, fallback to simpler method
try:
    result = await complex_analysis(data)
except Exception:
    # Fallback: simpler approach, local execution
    result = await simple_analysis(data)
```

---

## 8. Quick Optimization Checklist

Before running a workflow:
- [ ] Tasks under 2 min → do in main session
- [ ] Large data → file reference, not inline
- [ ] Independent tasks → parallel spawn
- [ ] Dependent tasks → chain with proper polling
- [ ] Cleanup mode selected appropriately
- [ ] Timeout configured for each spawn
- [ ] Output paths defined and unique

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Spawn overhead | < 5s | Time from spawn call to agent start |
| Polling efficiency | > 90% | Avoid unnecessary API calls |
| Token efficiency | < 75% input | Reserve 25% for response |
| Parallel utilization | 50-80% | Balance speed vs resources |

---

*Generated: 2026-02-19 | Use: Reference during workflow design*
