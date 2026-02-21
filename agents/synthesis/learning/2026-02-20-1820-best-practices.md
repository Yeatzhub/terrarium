# Multi-Agent Workflow Best Practices & Anti-Patterns
*Synthesis Learning — 2026-02-20*

What works, what doesn't, and why. Learn from common mistakes.

---

## Anti-Pattern 1: The Monolith Task

**DON'T**: Spawn one agent with an enormous, vague task

```python
# BAD: Everything in one task
sessions_spawn({
    "task": """
    Build a complete e-commerce platform with user auth, 
    product catalog, shopping cart, checkout, payments, 
    admin panel, analytics, and email notifications.
    Make it scalable and secure.
    """,
    "agentId": "coder",
    "timeoutSeconds": 3600
})
# Result: Overwhelmed agent, partial/incomplete output, 
# or timeout after 1 hour with unusable code
```

**DO**: Decompose into manageable, verifiable stages

```python
# GOOD: Staged pipeline with clear deliverables
stages = [
    {"agent": "architect", "task": "Design auth system", "output": "auth-design.md"},
    {"agent": "architect", "task": "Design product catalog", "output": "catalog-design.md"},
    {"agent": "coder", "task": "Implement auth from {auth-design}", "output": "auth/"},
    {"agent": "coder", "task": "Implement catalog from {catalog-design}", "output": "catalog/"},
    {"agent": "coder", "task": "Integrate auth + catalog", "output": "integration.md"},
]
# Each stage < 10min, verifiable output, clear dependencies
```

**Why**: Agents have limited context windows and reasoning depth. Large tasks lead to context loss, incomplete reasoning, and poor outputs.

---

## Anti-Pattern 2: The Infinite Fan-Out

**DON'T**: Spawn unlimited parallel agents

```python
# BAD: No limit on parallelism
tasks = [f"Process record {i}" for i in range(1000)]
results = await Promise.all([
    sessions_spawn({"task": t, "agentId": "worker"})
    for t in tasks
])
# Result: Resource exhaustion, cascade failures, 
# many timeouts, system instability
```

**DO**: Use bounded concurrency with throttling

```python
# GOOD: Controlled parallelism with semaphore
import asyncio

semaphore = asyncio.Semaphore(10)  # Max 10 concurrent

async def bounded_spawn(task):
    async with semaphore:
        return await sessions_spawn({
            "task": task, 
            "agentId": "worker",
            "timeoutSeconds": 60
        })

results = await asyncio.gather(*[bounded_spawn(t) for t in tasks])
# System remains stable, predictable performance
```

**Why**: Unbounded concurrency exhausts resources (memory, API quotas, rate limits). Leads to widespread failures that are hard to debug.

---

## Anti-Pattern 3: The Silent Failure

**DON'T**: Ignore agent errors or missing outputs

```python
# BAD: No error handling
result = await sessions_spawn({"task": "Generate report"})
# Agent times out or returns error
# Code continues as if successful
save_to_database(result.output)  # Crashes or saves garbage
```

**DO**: Explicit error checking and graceful handling

```python
# GOOD: Validate before using
result = await sessions_spawn({
    "task": "Generate report",
    "timeoutSeconds": 120
})

# Check completion
if not result.get("completed"):
    log_error(f"Report generation failed: {result.get('error')}")
    fallback_report = generate_minimal_report()
    notify_user("Full report failed, using summary")
    return fallback_report

# Verify output exists and is valid
if not result.get("output") or len(result["output"]) < 100:
    log_error("Report output empty or too short")
    return await retry_or_escalate()

# Only then use the result
save_to_database(result.output)
```

**Why**: Silent failures corrupt downstream processes and databases. Explicit handling prevents cascade failures and provides recovery options.

---

## Anti-Pattern 4: The Context Bomb

**DON'T**: Pass full conversation history to every agent

```python
# BAD: Accumulating context
chain = [
    {"agent": "researcher", "task": "Research topic"},
    {"agent": "analyst", "task": f"Analyze: {research_output}"},
    {"agent": "writer", "task": f"Write: {analysis_output}. Full context: {research_output + analysis_output}"},
    {"agent": "editor", "task": f"Edit: {draft}. Full history: {all_previous_outputs}"},
]
# By stage 4: 8000+ tokens, slow, confused agent, poor results
```

**DO**: Differential context with references

```python
# GOOD: Minimal context with references
context_mgr = ContextManager(max_tokens=1500)

# After each stage
context_mgr.add(agent_id, task_summary, output, key_decisions)

# Next agent gets only:
next_task = """
Workflow state: file:./state.json
Current stage: 4 of 5
Key decisions: ["Use PostgreSQL", "JWT auth", "REST API"]
Your specific task: Edit for clarity and tone
Input file: draft-v3.md
Output to: draft-v4.md
"""
# Context stays < 1500 tokens, fast responses, clear focus
```

**Why**: Large contexts slow agents, increase token costs, and dilute focus. Agents lose track of the specific task amid noise.

---

## Anti-Pattern 5: The Fire-and-Forget

**DON'T**: Spawn agents without tracking or timeouts

```python
# BAD: No monitoring
for task in tasks:
    sessions_spawn({"task": task, "agentId": "worker"})  # No await, no tracking!
# Results: Lost agents, zombie processes, resource leaks,
# no way to know what completed
```

**DO**: Track all spawns with timeouts and cleanup

```python
# GOOD: Tracked execution with cleanup
import asyncio

async def tracked_spawn(task, agent_id, timeout=120):
    try:
        result = await asyncio.wait_for(
            sessions_spawn({
                "task": task, 
                "agentId": agent_id,
                "timeoutSeconds": timeout
            }),
            timeout=timeout + 10  # Buffer for spawn overhead
        )
        return result
    except asyncio.TimeoutError:
        log_error(f"Task timeout after {timeout}s")
        return {"error": "timeout", "task": task}
    except Exception as e:
        log_error(f"Task failed: {e}")
        return {"error": str(e), "task": task}

# Use with gather for parallel, wait for all
results = await asyncio.gather(*[
    tracked_spawn(t, "worker", 120) for t in tasks
])

# Cleanup any stuck processes
subagents action=list | grep "stuck" | xargs kill
```

**Why**: Untracked agents become zombies, consume resources indefinitely, and make debugging impossible. Timeouts ensure system stability.

---

## Anti-Pattern 6: The Brittle Chain

**DON'T**: Rigid pipelines with no failure recovery

```python
# BAD: No failure handling in pipeline
stage1 = await sessions_spawn({"task": "Analyze", "agentId": "analyst"})
stage2 = await sessions_spawn({"task": f"Code: {stage1.output}", "agentId": "coder"})
stage3 = await sessions_spawn({"task": f"Test: {stage2.output}", "agentId": "tester"})
# If stage1 fails, stage2 gets garbage, stage3 tests garbage,
# entire pipeline wastes time, produces nonsense
```

**DO**: Quality gates between stages with checkpoint recovery

```python
# GOOD: Validated stages with recovery
pipeline = Pipeline(stages=[
    {
        "name": "analyze",
        "agent": "analyst",
        "validate": lambda r: len(r.output) > 200 and "conclusion" in r.output,
        "timeout": 120
    },
    {
        "name": "code",
        "agent": "coder",
        "depends_on": ["analyze"],
        "validate": lambda r: r.output.contains("def ") or r.output.contains("class "),
        "timeout": 180
    },
    {
        "name": "test",
        "agent": "tester",
        "depends_on": ["code"],
        "validate": lambda r: "test_" in r.output and "assert" in r.output,
        "timeout": 120
    }
])

result = await pipeline.run_with_recovery()
# Each stage validated, checkpointed, can resume from failures
```

**Why**: Brittle chains amplify errors. One bad stage corrupts all downstream work. Quality gates catch errors early, saving time and compute.

---

## Anti-Pattern 7: The Over-Engineered Orchestrator

**DON'T**: Build complex orchestration for simple tasks

```python
# BAD: Heavy machinery for simple job
def simple_data_processing(file_path):
    # Sets up: Circuit breaker, context manager, quality gate,
    # error recovery, metrics, logging, distributed tracing
    # ... 200 lines of setup ...
    # Actual work: read file, filter lines, write output
    # Total time: 5min setup, 10s work
```

**DO**: Match complexity to task needs

```python
# GOOD: Simple tasks get simple solutions
def simple_data_processing(file_path):
    # Inline for simple, fast tasks
    content = read_file(file_path)
    filtered = [line for line in content if "ERROR" in line]
    write_file("errors.log", "\n".join(filtered))
    return len(filtered)

# Complex workflow gets orchestration
def complex_microservice_generation(spec):
    orch = Orchestrator(config)  # Full machinery
    return orch.run_workflow(service_pipeline, spec)
```

**Why**: Over-engineering wastes development time, adds failure points, and reduces maintainability. Use the simplest solution that works.

---

## Anti-Pattern 8: The Circular Dependency

**DON'T**: Create circular dependencies between agents

```python
# BAD: Circular waiting
# Agent A: "Need output from Agent B to proceed"
# Agent B: "Need output from Agent C to proceed"
# Agent C: "Need output from Agent A to proceed"
# Result: Deadlock, infinite wait, timeout
```

**DO**: Acyclic dependency graph with clear data flow

```python
# GOOD: DAG with topological ordering
workflow = {
    "stages": [
        {"id": "data_load", "deps": [], "agent": "loader"},
        {"id": "clean_a", "deps": ["data_load"], "agent": "cleaner"},
        {"id": "clean_b", "deps": ["data_load"], "agent": "cleaner"},
        {"id": "merge", "deps": ["clean_a", "clean_b"], "agent": "merger"},
        {"id": "analyze", "deps": ["merge"], "agent": "analyst"},
    ]
}
# Clear flow: load → (clean_a || clean_b) → merge → analyze
# No cycles, parallel where possible, sequential where required
```

**Why**: Circular dependencies cause deadlocks. DAGs ensure progress, enable parallelism, and make dependencies explicit.

---

## Best Practices Summary

### Task Design
- ✓ Keep tasks focused (< 5min execution)
- ✓ Include explicit output requirements
- ✓ Set appropriate timeouts (2x expected duration)
- ✓ Define clear success criteria

### Concurrency
- ✓ Limit parallel agents (5-10 typical max)
- ✓ Use semaphores for throttling
- ✓ Match parallelism to task type (I/O vs CPU)

### Error Handling
- ✓ Check completion status before using results
- ✓ Validate output format and content
- ✓ Implement graceful fallbacks
- ✓ Log errors with context for debugging

### Context Management
- ✓ Prune context to < 2000 tokens
- ✓ Use differential updates, not full history
- ✓ Reference files instead of inline large data
- ✓ Include key decisions, not every thought

### Quality Assurance
- ✓ Quality gates between pipeline stages
- ✓ Checkpoint after expensive operations
- ✓ Verify deliverables exist and are valid
- ✓ Test with smoke tests before full suite

### System Health
- ✓ Track all spawned agents
- ✓ Set and enforce timeouts
- ✓ Clean up zombie processes
- ✓ Monitor resource usage

---

## Quick Decision Matrix

| Situation | Pattern | Anti-Pattern |
|-----------|---------|--------------|
| Simple task (< 1min) | Inline code | Agent spawn |
| Parallel independent | Fan-out (bounded) | Infinite spawn |
| Sequential dependent | Pipeline + gates | Brittle chain |
| Large dataset | Map-Reduce + shards | Single giant task |
| Unreliable agent | Circuit breaker | Retry forever |
| Time-critical | Parallel + fast-fail | Overly cautious |
| Complex workflow | Orchestrator with config | Hard-coded chaos |

---

## Red Flags Checklist

Your workflow may have problems if:
- [ ] Tasks regularly exceed timeouts
- [ ] Context size grows without bound
- [ ] Success rate < 80% on repeated runs
- [ ] Hard to debug when failures occur
- [ ] Takes longer than manual approach
- [ ] Outputs vary wildly between runs
- [ ] Resource usage grows continuously
- [ ] No way to resume from failures

**Fix**: Review against anti-patterns above, apply corresponding best practice.

---

*Reference implementations in 2026-02-20-1220, debugging in 2026-02-20-1420.*
