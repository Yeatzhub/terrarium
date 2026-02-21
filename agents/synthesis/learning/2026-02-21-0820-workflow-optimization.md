# Workflow Optimization Guide

**Date:** 2026-02-21 08:20 AM  
**Topic:** Practical workflow optimization for multi-agent systems

---

## The 80/20 Rule for Agent Workflows

80% of latency comes from 20% of bottlenecks. Fix these first:

1. **Sequential when parallel possible** → Use Fan-Out Gather
2. **Context too large** → Chunk and pipeline
3. **No early exit** → Add circuit breakers
4. **Over-engineered retries** → Exponential backoff with ceiling
5. **Blocking on slow agents** → Async with timeout

---

## Task Decomposition Strategy

### The SPRINT Method

```
S - Single purpose (one agent = one clear outcome)
P - Parallelizable (identify independent subtasks)
R - Reversible (each step should be undoable)
I - Idempotent (same input = same output, every time)
N - Narrow scope (task description < 400 tokens)
T - Time-boxed (enforce hard timeouts)
```

### Decomposition Checklist

Before spawning, ask:

| Question | If Yes | If No |
|----------|--------|-------|
| Can this be 2+ independent tasks? | Split and parallelize | Keep as one |
| Does step B need step A's output? | Keep sequential | Reorder for parallelism |
| Is this a pattern I've seen before? | Reuse template | Document new pattern |
| Will this take >5 min? | Add progress checkpoints | Ship as atomic unit |

### Example: Before & After

**Before (Sequential - 90s total):**
```
[Agent: Analyze] → [Agent: Format] → [Agent: Save]
     30s            20s              40s
```

**After (Parallel - 45s total):**
```
[Agent: Analyze + Save partial]
[Agent: Pre-format template]
        ↓
[Agent: Final merge]
```

---

## Latency Optimization Patterns

### Pattern 1: Speculative Execution

Spawn backup agent with different strategy. Use whichever finishes first.

```javascript
// Fast path: Quick heuristic
const fast = sessions_spawn({
  task: "Classify using keyword matching",
  agentId: "classifier-fast",
  timeoutSeconds: 10
});

// Slow path: Deep analysis
const slow = sessions_spawn({
  task: "Classify using LLM reasoning",
  agentId: "classifier-slow",
  timeoutSeconds: 60
});

// Race them
const winner = await Promise.race([fast, slow]);
// Cancel the loser (optional optimization)
```

### Pattern 2: Caching with Dependency Graph

```yaml
# workflow-cache.yaml
hashInputs:
  - input_file_hash
  - agent_version
  - config_hash

cacheLocations:
  - "cache/{hash}/output.json"
  - "cache/{hash}/metadata.yaml"

invalidation:
  maxAge: "24h"
  onDependencyChange: true
```

**Cache Key Formula:** `SHA256(input_hash + agent_prompt_version + config_json)`

### Pattern 3: Streaming Partial Results

Instead of waiting for full completion:

```
Agent writes to output/  →  Consumer reads chunks as they appear
├── chunk-1.json          →  Process section 1 immediately
├── chunk-2.json          →  Process section 2 immediately
├── chunk-3.json          →  Process section 3 immediately
└── complete.flag         →  Cleanup and finalize
```

---

## Resource Optimization

### Memory Constraints

| Agent Type | Max Memory | Action on Exceed |
|------------|-----------|------------------|
| Quick tasks | 512 MB | Kill and retry smaller chunks |
| Analysis | 1 GB | Stream output, flush buffers |
| Heavy processing | 2 GB | Split into sub-agents |

### Token Budget per Workflow

Total budget for 3-agent pipeline: ~12K tokens

```
Agent A: 4K (instruction) + 1K (context) = 5K
Agent B: 3K (instruction) + 1K (input) = 4K
Agent C: 2K (instruction) + 1K (combine) = 3K
```

**Rule:** If workflow exceeds 15K tokens, reconsider decomposition.

---

## Dependency Graph Optimization

### Critical Path Analysis

```
     [A: 5s]
    /       \
[B: 10s]  [C: 3s]
    \       /
     [D: 5s]
```

**Critical path:** A → B → D = 20s (not A → C → D = 13s)

Optimization: Speed up B or parallelize B internally.

### Diamond Pattern Warning

```
     [A]
    /   \
   [B]  [C]
    \   /
     [D]
```

**Problem:** D must wait for both. If B and C have different runtime variance, D sits idle.

**Fix:** Add buffer agent that pre-stages D's partial work as B/C complete.

---

## Context Handoff Optimization

### The 3-Line Rule

Handoff files should fit in 3 lines of YAML:

```yaml
from: agent-id
output: path/to/result.json
status: complete  # or: blocked - reason
```

**Why:** Forces minimal context passing. Large handoffs = slow agents.

### Delta Updates

Don't pass full context each handoff:

```yaml
# Bad: 500 lines of repeated context
# Good: Just the changes
delta:
  added: ["item3"]
  modified: { "key": "new_value" }
  removed: []
baseRef: "handoff-001.yaml"  # Full context here
```

---

## Error Recovery Strategies

### Retry Matrix

| Error Type | Retry Count | Backoff | Action |
|------------|-------------|---------|--------|
| Timeout | 3 | 2^n seconds | Decompose into smaller tasks |
| Rate limit | 5 | 60s fixed | Queue and retry later |
| Crash | 2 | 5s | Spawn on different node |
| Bad output | 0 | - | Alert human, don't retry |
| Dependency missing | 1 | 0s | Re-check after 30s |

### Circuit Breaker Pattern

```javascript
if (failureRate > 0.5 && lastMinute > 5) {
  state = "OPEN";  // Stop spawning for 60s
  spawnFallbackAgent();  // Use simpler logic
}
```

---

## Quick Wins Checklist

**Apply these in order of impact:**

- [ ] **Add timeouts** to all agent spawns (default: 10 min → reduce to 5 min)
- [ ] **Chunk inputs** >1000 lines before sending to agents
- [ ] **Cache repeated calls** with deterministic hash keys
- [ ] **Parallelize** any 2+ agents with no dependencies
- [ ] **Pre-validate** inputs with cheap regex before expensive agents
- [ ] **Compress context** (remove whitespace, use shorter variable names)
- [ ] **Batch small tasks** (if spawning <1s work, batch 5-10 together)
- [ ] **Use faster model** for simple classification tasks
- [ ] **Poll less frequently** (change 1s → 5s for long tasks)
- [ ] **Clean up** temp files immediately after use

---

## Performance Profiling

### Measure Before Optimizing

```bash
# Log timestamps at each stage
echo "start:$(date +%s)" >> timing.log
# ... agent work ...
echo "stage1:$(date +%s)" >> timing.log
```

**Visualization:**
```
Timeline: |---A---|--B--|-C-|
Actual:   0s      30s   45s 50s
Target:   0s      20s   35s 40s
Gap:            +10s  +10s +10s
```

---

## Reference: Time Budgets

| Workflow Type | Target | Hard Limit | Optimization If >Target |
|---------------|--------|------------|-------------------------|
| User-facing | 5s | 10s | Cache everything |
| Async job | 60s | 5 min | Increase parallelism |
| Batch process | 5 min | 30 min | Stream results |
| Nightly build | 30 min | 2 hours | Add workers |

**Remember:** Optimize for the user experience, not the metric.

---

**Related:** See `multi-agent-coordination.md` for patterns; see `integration-test-examples.md` for testing these optimizations.
