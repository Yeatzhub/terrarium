# Multi-Agent Coordination Patterns

**Created:** 2026-02-18 22:20 CT  
**Topic:** Task decomposition, dependency management, context handoff protocols

---

## 1. Pattern: Fan-Out / Gather

**Use Case:** Parallelize independent subtasks.

```
Main Agent
├── Spawn Agent A → Task X
├── Spawn Agent B → Task Y
└── Spawn Agent C → Task Z
    ↓ (await all)
Gather Results → Synthesize → Complete
```

**Implementation:**
- Spawn with `sessions_spawn` (async)
- Use `subagents list` to poll completion
- Merge outputs with consistent schema

**Context Handoff:** Pass `task` + `format` + `constraints` explicitly. Never assume shared state.

---

## 2. Pattern: Pipeline / Chain

**Use Case:** Sequential dependencies where output N = input N+1.

```
Stage 1 (Extract) → Stage 2 (Transform) → Stage 3 (Load)
```

**Implementation:**
- Use file-based handoff (`stage-1-output.json`)
- Or spawn sequentially with `sessions_send` for critical path
- Validate outputs before handoff (schema check)

**Anti-Pattern:** Chaining 5+ stages without parallel forks. Merge stages or use Fan-Out.

---

## 3. Pattern: Coordinator / Worker

**Use Case:** Dynamic task distribution based on worker availability.

**Roles:**
- **Coordinator:** Decomposes task, assigns work, aggregates
- **Worker:** Stateless, idempotent, returns structured output

**Contract:**
```json
{
  "input": { "task": "string", "parameters": {} },
  "output": { "result": "any", "status": "ok|error", "logs": [] }
}
```

---

## 4. Dependency Management Rules

| Dependency Type | Strategy | Example |
|-----------------|----------|---------|
| **Temporal** | Cron schedule or explicit wait | `cron: every 5m` |
| **Data** | File or message handoff | `read output-a.json before starting B` |
| **Resource** | Lock file or mutex | `workspace/.lock-scraper` |
| **External** | Timeout + retry + circuit breaker | API calls with exponential backoff |

**Hard Dependency:** Use `runTimeoutSeconds` to fail fast, never hang indefinitely.

---

## 5. Context Handoff Protocol

**Always Include:**
1. **Goal** — One-sentence objective
2. **Inputs** — Explicit data/files/parameters
3. **Constraints** — Deadlines, formats, limits (token/time/cost)
4. **Output Schema** — Expected structure
5. **Error Handling** — What constitutes failure vs. partial success

**Template:**
```
Goal: <action> <subject> <format>
Inputs: <file> / <data> / <search query>
Constraints: <max tokens>, <time limit>, <quality threshold>
Output: <schema>
On Failure: <fallback / retry / escalate>
```

---

## 6. Integration Testing Checklist

For multi-agent workflows, verify:

- [ ] **Isolation:** Each agent can run independently
- [ ] **Idempotency:** Re-running produces same result
- [ ] **Schema Compliance:** All handoff formats validated
- [ ] **Timeout Handling:** Agents fail gracefully, not silently
- [ ] **Cleanup:** Temporary files removed, no resource leaks
- [ ] **Observability:** Logs traceable across agent boundaries

**Quick Test:**
```bash
# Simulate failure at stage 2
openclaw sessions_spawn --task "stage 1" && \
  (exit 1) && \
  openclaw sessions_spawn --task "stage 3"
# Verify: stage 3 never starts, error propagates
```

---

## 7. Quality Standards

| Metric | Target | Measurement |
|--------|--------|-------------|
| Success Rate | >95% | `subagents list` error ratio |
| Latency | <30s per agent | Spawn → completion time |
| Cost per Task | Minimize | Token usage / API calls |
| Handoff Clarity | 100% | Peer review: can another agent continue? |

**Code Review Question:** *"If this agent crashes, can a fresh agent resume from the last artifact?"*

---

## Quick Reference: Decision Tree

```
Tasks independent? → Fan-Out
Sequential data flow? → Pipeline
Dynamic assignment needed? → Coordinator/Worker
High failure cost? → Add retries + circuit breakers
Long-running (>5 min)? → Cron + state files
```

---

**Next Steps:** Apply Pipeline pattern to current cron synthesis jobs; add schema validation for handoff files.
