# Multi-Agent Coordination Patterns

**Date:** 2026-02-21 04:20 AM  
**Topic:** Task Decomposition, Dependency Management & Context Handoff

---

## 1. Pattern: Fan-Out Gather
**Use Case:** Parallelize independent subtasks

```
Parent Spawn → [Agent A] [Agent B] [Agent C] → Parent Gather
```

**Implementation:**
```javascript
// Fire all agents without waiting
sessions_spawn({ task: "analyze-sentiment", agentId: "worker-1" });
sessions_spawn({ task: "extract-entities", agentId: "worker-2" });
sessions_spawn({ task: "summarize", agentId: "worker-3" });

// Poll for completion or use push-based completion
subagents({ action: "list", recentMinutes: 5 });
```

**Key:** Each agent writes results to a shared file before signaling completion. Parent polls file or waits for push notification.

---

## 2. Pattern: Pipeline Chain
**Use Case:** Sequential dependencies where output(n) = input(n+1)

```
Source → [Stage 1] → [Stage 2] → [Stage 3] → Sink
```

**Implementation:**
1. Stage 1 writes to `tmp/stage1-output.json`
2. Spawn Stage 2 with `inputPath: "tmp/stage1-output.json"`
3. Repeat for each stage
4. Final stage writes to `output/final.json`

**Error Handling:** Each stage validates input; on failure, write error to `tmp/error-{stage}.log` and halt chain.

---

## 3. Pattern: Dynamic Orchestrator
**Use Case:** Unknown number of subtasks at runtime

```
Orchestrator analyzes task → spawns N workers → aggregates
```

**Implementation:**
```javascript
// Orchestrator pseudocode
const chunks = splitLargeTask(data, chunkSize=100);
const workerIds = [];

for (const [i, chunk] of chunks.entries()) {
  const worker = sessions_spawn({
    task: `process chunk ${i}`,
    agentId: "dynamic-worker",
    label: `worker-${i}`
  });
  workerIds.push(worker);
}

// Wait for all (poll or push)
await Promise.all(workerIds.map(w => waitFor(w)));
const results = workerIds.map(w => read(w.outputPath));
write("output/aggregated.json", merge(results));
```

---

## 4. Context Handoff Protocol

**Standard Format:**
```yaml
# handoff-{timestamp}.yaml
from: "agent-id"
timestamp: "ISO-8601"
task_id: "uuid"
status: "complete|partial|blocked"
deliverables:
  - path: "output/file.json"
    description: "What this file contains"
    schema_version: "1.0"
blockers: []  # If blocked, list reasons
dependencies_satisfied: true
next_steps:
  - "Validate output with schema checker"
  - "Pass to aggregation agent"
```

**Rules:**
- Always write handoff file before signaling completion
- Include schema version for forward compatibility
- Never pass large data in handoff; use file paths
- Use atomic writes (write to temp, then mv)

---

## 5. Dependency Management Strategies

**Explicit Declaration:**
```yaml
# task-manifest.yaml
dependencies:
  must_complete:
    - "task-a-uuid"
    - "task-b-uuid"
  shared_resources:
    - "database-write-lock"
conflicts_with:
  - "task-c-uuid"  # Cannot run concurrently
```

**Resource Tokens:**
- Acquire semaphore before starting
- Release in finally block
- Timeout after N seconds to prevent deadlocks

**Dependency Graph:**
```
     A
    / \
   B   C
   |   |
   D   E
    \ /
     F
```
- Topological sort to determine spawn order
- Level-order for parallelization within levels
- Critical path determines minimum runtime

---

## 6. Integration Testing Multi-Agent Flows

**Test Types:**

| Type | Scope | Tool |
|------|-------|------|
| Unit | Single agent logic | sessions_spawn + mock input |
| Integration | Agent-to-agent handoff | Full pipeline with tmp files |
| E2E | Full orchestration | Production-like setup |

**Mock Agent Pattern:**
```javascript
// For testing, spawn agent with dryRun flag
sessions_spawn({
  task: "process-data",
  agentId: "test-double",
  // Agent reads env.TEST_MODE, returns canned response
});
```

**Assertion Pattern:**
```javascript
// Wait for handoff file
assert(fileExists("handoff-*.yaml"));
assert(jsonMatchesSchema(read("output/result.json"), schema));
assert(noErrorsIn("logs/*.log"));
```

---

## 7. Quality Standards Checklist

**Before Spawning:**
- [ ] Task description < 500 tokens (for speed)
- [ ] Input/output paths specified
- [ ] Timeout set (default: 10 min max for quick tasks)
- [ ] Fallback agent defined (for critical paths)

**During Execution:**
- [ ] Progress logged every 60s (for long tasks)
- [ ] Heartbeat file touched every 30s
- [ ] Memory usage monitored (kill if > 2GB)

**On Completion:**
- [ ] Exit code written to `meta/exit-code`
- [ ] Output validated against schema
- [ ] Handoff file present and parseable
- [ ] Temp files cleaned (unless DEBUG_MODE)

---

## Quick Reference: When to Use What

| Situation | Pattern | Max Agents |
|-----------|---------|------------|
| Map-reduce on dataset | Fan-Out Gather | 10 (avoid rate limits) |
| Build pipeline (lint → test → deploy) | Pipeline Chain | 3-5 stages |
| Process user uploads of unknown size | Dynamic Orchestrator | 20 (with backoff) |
| Critical path with retries | Pipeline + Circuit Breaker | 2 (primary + backup) |

---

**Next Reading:** See `SKILL.md` for tool specifics; `AGENTS.md` for workspace conventions.
