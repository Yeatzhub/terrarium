# Dependency Management for Agent Workflows

*Handling task relationships, data flow, and execution order*

---

## 1. Dependency Types

### Hard Dependencies (Blocking)
Task B **cannot start** until Task A completes.
```
[A: Fetch data] ──→ [B: Analyze data]
       ↓                ↓
   data.json      requires data.json
```

### Soft Dependencies (Non-Blocking)
Task B can start with partial data from Task A.
```
[A: Full research] ──→ [B: Preliminary analysis]
       ↓                    ↓
   streaming results   works with partial data
```

### No Dependencies (Parallel)
Tasks can run simultaneously.
```
[A: Research X] ──┐
                  ├──→ [C: Merge results]
[B: Research Y] ──┘
```

---

## 2. Dependency Mapping

### Visual Map Format
```
[DATA_SOURCE]
     ↓
[FETCH] ──→ temp/raw_data.json
     ↓
[VALIDATE] ──→ temp/validated.json
     ↓
┌─────────┬─────────┐
↓         ↓         ↓
[ANALYZE] [SUMMARIZE] [EXTRACT]
     ↓         ↓         ↓
 temp/     temp/      temp/
analysis.md summary.md entities.json
     ↓         ↓         ↓
└─────────┴─────────┘
     ↓
[MERGE] ──→ output/final_report.md
```

### Dependency Table
```
Task        | Depends On        | Produces              | Parallel?
------------|-------------------|-----------------------|----------
fetch       | (none)            | temp/raw_data.json    | No
validate    | fetch             | temp/validated.json   | No
analyze     | validate          | temp/analysis.md      | Yes
summarize   | validate          | temp/summary.md       | Yes
extract     | validate          | temp/entities.json    | Yes
merge       | analyze,summarize | output/final_report   | No
```

---

## 3. Implementation Patterns

### Pattern: Sequential Chain
```python
# Hard dependencies: Wait for each to complete
fetch_job = await sessions_spawn({
    "task": "Fetch data → temp/raw.json"
})
await wait_for(fetch_job["sessionKey"])

validate_job = await sessions_spawn({
    "task": "Validate temp/raw.json → temp/valid.json"
})
await wait_for(validate_job["sessionKey"])

# Now safe to proceed
analysis_job = await sessions_spawn({
    "task": "Analyze temp/valid.json → output/analysis.md"
})
```

### Pattern: Fan-Out (Parallel)
```python
# No dependencies between these three
parallel_jobs = []
for task in ["analyze", "summarize", "extract"]:
    job = await sessions_spawn({
        "task": f"{task} temp/valid.json → temp/{task}.json"
    })
    parallel_jobs.append(job["sessionKey"])

# Wait for all
results = await asyncio.gather(*[
    wait_for(job) for job in parallel_jobs
])
```

### Pattern: Fan-In (Merge)
```python
# All must complete before merge
required_files = ["temp/analysis.md", "temp/summary.md"]
for f in required_files:
    assert os.path.exists(f), f"Missing dependency: {f}"

merge_job = await sessions_spawn({
    "task": f"Merge {', '.join(required_files)} → output/final.md"
})
```

---

## 4. Data Flow Protocols

### Contract: File-Based Handoff
```python
# Producer
write("/tmp/stage1/output.json", json.dumps({
    "schema_version": "1.0",
    "produced_by": "agent_researcher",
    "timestamp": time.time(),
    "data": results
}))

# Consumer (validates before using)
content = read("/tmp/stage1/output.json")
parsed = json.loads(content)
assert parsed["schema_version"] == "1.0"
assert "data" in parsed
```

### Contract: Status Checking
```python
async def wait_for_dependencies(dependencies: list):
    """Poll until all dependencies complete"""
    pending = set(dependencies)
    
    while pending:
        for dep in list(pending):
            status = await subagents({
                "action": "list",
                "target": dep
            })
            
            if status.get("completed"):
                pending.remove(dep)
            elif status.get("failed"):
                raise DependencyError(f"Dependency {dep} failed")
        
        if pending:
            await asyncio.sleep(5)
```

---

## 5. Error Handling in Dependency Chains

### Failure Modes

| Failure | Impact | Response |
|---------|--------|----------|
| Early task fails | All downstream blocked | Stop chain, report root cause |
| Parallel task fails | Partial results available | Continue with degraded output |
| Merge input missing | Cannot complete | Retry missing task or skip |
| Timeout | Unknown state | Check output files, decide continue/abort |

### Circuit Breaker Pattern
```python
async def resilient_dependency_chain(tasks: list):
    completed = []
    failed = []
    
    for task in tasks:
        if failed and task.get("strict_dependencies"):
            print(f"Skipping {task['name']}: dependencies failed")
            continue
            
        try:
            result = await run_task(task)
            completed.append(result)
        except Exception as e:
            failed.append((task, e))
            if task.get("abort_on_failure"):
                break
    
    return {"completed": completed, "failed": failed}
```

---

## 6. Dependency Optimization

### Techniques

**1. Early Materialization**
Generate intermediate outputs as soon as possible.
```
Instead of: [A] → [B] → [C] → write all
Do:         [A] → write → [B] → write → [C] → write
```

**2. Speculative Execution**
Start likely-to-be-needed tasks early.
```
Start [B] when [A] is 80% complete
Kill [B] if [A] fails
```

**3. Lazy Evaluation**
Only compute what's actually needed.
```
Don't: Analyze all data upfront
Do:    Analyze only the subset requested
```

---

## 7. Validation Checklist

Before starting a multi-agent workflow:
- [ ] Dependency graph drawn (even mentally)
- [ ] All file paths defined and unique
- [ ] Each task's inputs/outputs documented
- [ ] Parallel opportunities identified
- [ ] Failure modes considered
- [ ] Timeouts set for long-running deps
- [ ] Rollback/cleanup plan defined

---

## Quick Reference: Common Patterns

| Pattern | Use When | Risk |
|---------|----------|------|
| Sequential | Strong dependencies, small scale | Slow |
| Fan-Out | Independent subtasks | Resource exhaustion |
| Fan-In | Need all parts to proceed | One slow task blocks all |
| Pipeline | Streaming data | Hard to debug |

---

*Generated: 2026-02-19 | Use: Map before executing multi-agent workflows*
