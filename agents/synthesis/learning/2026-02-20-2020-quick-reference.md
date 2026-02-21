# Multi-Agent Quick Reference
*Synthesis Learning — 2026-02-20*

One-page reference: commands, patterns, thresholds, fixes.

---

## Essential Commands

```bash
# Check system state
sessions_list --activeMinutes=5
session_status --sessionKey <key>

# Spawn with safety
cron action=run jobId=<id>
sessions_spawn --task "..." --agentId <agent> --timeoutSeconds=120

# Monitor & control
subagents list
subagents action=kill target=<id>

# Debug
sessions_history --sessionKey <key> --limit 10
process action=log sessionId=<id> --limit 50
```

---

## Pattern Cheat Sheet

| Pattern | Use When | Implementation |
|---------|----------|----------------|
| **Fan-Out** | Parallel independent tasks | `Promise.all(spawn(3 tasks))` |
| **Pipeline** | Sequential dependencies | Chain via `sessions_send` |
| **Map-Reduce** | Large dataset processing | Shard → parallel → aggregate |
| **Circuit Breaker** | Unreliable agent protection | Fail after 3 errors, retry in 60s |
| **Checkpoint** | Long workflows, resume | Write state after each stage |

---

## Timeout Guidelines

| Task Type | Timeout | Buffer |
|-----------|---------|--------|
| Quick analysis | 60s | +10s |
| Code generation | 120s | +20s |
| Research | 180s | +30s |
| Multi-stage | 300s per stage | +60s |

**Rule of thumb**: Expected duration × 2, minimum 30s, maximum 600s.

---

## Context Limits

| Metric | Target | Alert |
|--------|--------|-------|
| Handoff size | < 1500 tokens | > 2000 |
| Task description | < 500 tokens | > 800 |
| Total context | < 4000 tokens | > 6000 |

**Quick prune**: `context = {goal, last_decision, current_task, file_ref}`

---

## Concurrency Limits

| Agent Type | Max Parallel | Reason |
|------------|--------------|--------|
| Generalist | 10 | Balanced |
| Researcher | 8 | I/O bound |
| Coder | 3 | CPU intensive |
| Analyst | 6 | Mixed |
| Any + circuit breaker | 5 | Recovery needed |

**Never**: Unbounded parallelism, >20 total agents, no throttling.

---

## Quality Gates (Quick Check)

```python
def quick_gate(result):
    return (
        result.get("completed") and
        len(result.get("output", "")) > 100 and
        not any(x in result.get("output", "") for x in ["TODO", "FIXME", "error"])
    )
```

**Run before**: Next pipeline stage, final output, user delivery.

---

## Error Recovery (2-Liner)

```python
for attempt in range(3):
    try: return await spawn(task, timeout=120)
    except: await sleep(2**attempt)  # 1s, 2s, 4s
return await escalate()
```

---

## Decision Tree

```
Need parallel?
  Yes → Use Fan-Out (bounded, max 10)
  No → Sequential?
    Yes → Use Pipeline (with gates)
    No → Simple?
      Yes → Inline (no spawn)
      No → Complex?
        Yes → Orchestrator + templates
```

---

## File Naming Convention

```
agents/synthesis/learning/
├── 2026-02-20-0420-coordination-patterns.md      # Patterns
├── 2026-02-20-0620-integration-tests.md          # Testing
├── 2026-02-20-0820-optimization.md              # Optimization
├── 2026-02-20-1020-quality-standards.md           # Quality
├── 2026-02-20-1220-implementation-templates.md   # Code templates
├── 2026-02-20-1420-debugging-guide.md           # Debugging
├── 2026-02-20-1620-case-studies.md               # Examples
├── 2026-02-20-1820-best-practices.md             # Anti-patterns
└── 2026-02-20-2020-quick-reference.md            # This file
```

---

## Red Flags (Fix Immediately)

- [ ] **Timeouts >50% of tasks** → Reduce task size, increase timeouts
- [ ] **Context >4000 tokens** → Prune aggressively, use references
- [ ] **Success rate <80%** → Add circuit breakers, review task clarity
- [ ] **No checkpoints** → Add after every expensive stage
- [ ] **Untracked spawns** → Always await, wrap in try/catch

---

## Performance Targets

| Metric | Target | Alert |
|--------|--------|-------|
| Spawn latency | < 5s | > 10s |
| Task success | > 95% | < 90% |
| Recovery time | < 10s | > 30s |
| Context ops | < 200ms | > 500ms |

---

## Template: Simple Workflow

```python
import asyncio

async def workflow(tasks):
    # 1. Bounded parallel
    sem = asyncio.Semaphore(5)
    async def spawn(t):
        async with sem:
            return await sessions_spawn({
                "task": t, "agentId": "worker", "timeoutSeconds": 120
            })
    
    results = await asyncio.gather(*[spawn(t) for t in tasks])
    
    # 2. Filter valid
    valid = [r for r in results if r.get("completed")]
    
    # 3. Synthesize
    return await sessions_spawn({
        "task": f"Summarize: {len(valid)} results",
        "agentId": "synthesizer",
        "timeoutSeconds": 60
    })
```

---

## Template: With Error Handling

```python
async def safe_workflow(task, retries=3, timeout=120):
    agent_id = "worker"
    circuit_breaker = get_breaker(agent_id)
    
    for attempt in range(retries):
        try:
            result = await circuit_breaker.call(
                sessions_spawn,
                {"task": task, "agentId": agent_id, "timeoutSeconds": timeout}
            )
            if result.get("completed"):
                return result
        except Exception as e:
            if attempt == retries - 1:
                return {"error": str(e), "task": task}
            await asyncio.sleep(2 ** attempt)
```

---

## One-Line Fixes

| Problem | Fix |
|---------|-----|
| Agent hanging | Add `timeoutSeconds`, check `context` size |
| Empty output | Require explicit output file, validate after |
| Wrong output | Re-anchor with original goal, prune context |
| Cascade failure | Circuit breaker + checkpoint + replay |
| Slow workflow | Profile, shard, parallelize where possible |
| High cost | Prune context, batch small requests |

---

## Checklist: Before Production

- [ ] Timeouts set on all spawns
- [ ] Circuit breakers on unreliable agents
- [ ] Checkpoints after expensive stages
- [ ] Quality gates between pipeline stages
- [ ] Context pruned to <2000 tokens
- [ ] Parallelism bounded (semaphore)
- [ ] Error handling with fallbacks
- [ ] Smoke tests passing
- [ ] Monitors/alerting configured
- [ ] Documentation updated

---

## Resources

- **Docs**: All patterns in `agents/synthesis/learning/`
- **Code**: Templates in `2026-02-20-1220-implementation-templates.md`
- **Debug**: Guide in `2026-02-20-1420-debugging-guide.md`
- **Examples**: Case studies in `2026-02-20-1620-case-studies.md`

---

*Build fast, fail safe, learn quickly.*
