# Workflow Optimization Guides
*Synthesis Learning — 2026-02-20*

## 1. Task Decomposition Optimization

### Right-Size Your Tasks
| Task Duration | Pattern | Example |
|-------------|---------|---------|
| < 30s | Inline (no spawn) | Quick regex, format check |
| 30s - 2min | Single agent | Research query, code review |
| 2min - 5min | Fan-out (2-3) | Parallel analysis of 3 files |
| 5min+ | Pipeline/Fan-out + checkpoints | Multi-stage architecture design |

**Anti-pattern**: Spawning agents for <20s tasks (overhead > work)
**Solution**: Batch small tasks or handle inline

### Pre-validation Before Spawn
```python
# Check BEFORE spawning expensive agent
if not os.path.exists(input_file):
    return {"error": "Missing input", "file": input_file}

if len(input_data) > 100000:
    # Shard before spawning, don't pass huge context
    shards = chunk_data(input_data, size=10000)
    return spawn_sharded(shards)
```

### Parallelism Ceiling
```javascript
// Max concurrent agents based on task type
const CONCURRENCY_LIMITS = {
  code_review: 5,      // CPU-bound
  research: 8,         // I/O-bound  
  analysis: 6,         // Mixed
  generation: 3        // Resource-intensive
};

// Throttle with semaphore
const results = await Promise.all(
  tasks.map(t => 
    semaphore.acquire().then(() => 
      runTask(t).finally(() => semaphore.release())
    )
  )
);
```

---

## 2. Dependency Management Optimization

### Lazy Evaluation Pattern
```python
# BAD: Load all deps upfront
deps = [load_dep(id) for id in all_ids]  # Slow if many unused

# GOOD: Lazy load only when needed
def get_dep(dep_id):
    if dep_id not in cache:
        cache[dep_id] = load_dep(dep_id)
    return cache[dep_id]

# Use only when branch requires it
if needs_auth:
    auth_spec = get_dep("auth-contract")
```

### Dependency Graph Resolution
```json
// Define workflow as DAG
{
  "tasks": [
    {"id": "t1", "deps": [], "duration": "2min"},
    {"id": "t2", "deps": ["t1"], "duration": "3min"},
    {"id": "t3", "deps": ["t1"], "duration": "2min"},
    {"id": "t4", "deps": ["t2", "t3"], "duration": "1min"}
  ]
}

// Optimal execution: t1 → (t2 || t3) → t4
// Sequential would be 8min, parallel is 6min (25% faster)
```

### Circuit Breaker Pattern
```javascript
let failureCount = 0;
const FAILURE_THRESHOLD = 3;
const TIMEOUT = 60000;

async function callAgent(task) {
  if (failureCount >= FAILURE_THRESHOLD) {
    // Fast fail - don't waste time on failing agent
    return { error: "Circuit open - agent unavailable", fallback: true };
  }
  
  try {
    const result = await sessions_spawn({
      task, timeoutSeconds: TIMEOUT/1000
    });
    failureCount = 0;  // Reset on success
    return result;
  } catch (e) {
    failureCount++;
    throw e;
  }
}
```

---

## 3. Context Handoff Optimization

### Differential Updates
```markdown
## Handoff (Optimized)

**Since last checkpoint**: `t2-architecture-design`
**Changed**: 
- Database: PostgreSQL (was: MongoDB)
- Auth: JWT via Auth0 (was: session-based)

**Unchanged**: [link to full spec](spec-v2.md)
**New output**: `api-contract-v3.yaml`
```
**Savings**: 70% fewer tokens vs full context re-send

### Context Pruning Rules
```python
def prune_context(history, max_tokens=2000):
    """Keep only decision points and final outputs."""
    relevant = []
    for msg in reversed(history):
        if is_decision(msg) or is_output(msg):
            relevant.append(summarize(msg))
        if token_count(relevant) > max_tokens:
            break
    return format_handoff(reversed(relevant))
```

### Shared State Store
```bash
# Instead of passing full context through agents:
# BAD: Each agent passes growing context to next
Chain: context[1000] → context[2000] → context[3000]

# GOOD: Reference shared state
Chain: ref:state-v1 → ref:state-v2 → ref:state-v3

# Implementation
write --file workflow/state.json --content '{"stage": 2, "decisions": [...]}'
# Pass only: "Continue from workflow/state.json, stage 2"
```

---

## 4. Integration Testing Shortcuts

### Smoke Test Suite
```bash
# Run before full test suite - catches 80% of issues in 20% of time
tests/smoke/
├── agent-responds.sh      # < 5s
├── file-write-read.sh     # < 3s  
├── spawn-and-complete.sh  # < 10s
└── basic-pipeline.sh      # < 15s
# Total: < 1min vs 10min full suite
```

### Incremental Testing
```python
# Only test changed paths
CHANGED = git diff --name-only HEAD~1

if "agents/researcher" in CHANGED:
    test_contract("researcher")
    test_pipeline("research-chain")

if "agents/coder" in CHANGED:
    test_contract("coder")
    # Skip unchanged agent tests
```

### Parallel Test Execution
```javascript
const testGroups = {
  unit: [...],        // Fast, no dependencies
  integration: [...], // Requires services
  e2e: [...]          // Full workflows
};

// Run unit + integration in parallel, e2e after unit pass
await Promise.all([
  runTests(testGroups.unit),
  setupServices().then(() => runTests(testGroups.integration))
]);
await runTests(testGroups.e2e);  // Sequential
```

---

## 5. Quality Standards Enforcement

### Fast-First Validation
```javascript
// Order validation by speed/cost
const validators = [
  { fn: checkFileExists, time: '1ms', cost: 0 },
  { fn: checkJSONParse, time: '5ms', cost: 0 },
  { fn: checkSchema, time: '50ms', cost: 0 },
  { fn: checkLinks, time: '500ms', cost: 'low' },
  { fn: runTests, time: '30s', cost: 'high' }
];

// Fail fast - cheap checks first
for (const v of validators) {
  if (!await v.fn()) return { pass: false, failed: v.fn.name };
}
```

### Sampling for Large Outputs
```python
def validate_large_dataset(files, sample_rate=0.1):
    """Validate 10% by default, scale if issues found."""
    sample = random.sample(files, int(len(files) * sample_rate))
    errors = [f for f in sample if not validate(f)]
    
    if errors:
        # Increase scrutiny if issues found
        expanded = random.sample(
            [f for f in files if f not in sample], 
            int(len(files) * sample_rate * 2)
        )
        errors += [f for f in expanded if not validate(f)]
    
    return len(errors) == 0
```

### Continuous Monitoring
```javascript
// Track in session_status or external metrics
const metrics = {
  spawn_duration: [],
  handoff_tokens: [],
  success_rate: [],
  retry_count: []
};

// Alert on degradation
if (avg(metrics.spawn_duration) > 10000) {
  console.warn("Spawn latency degraded >10s");
}
if (success_rate_last_hour() < 0.95) {
  console.error("Success rate <95%, check agent health");
}
```

---

## 6. Performance Benchmarks

### Target Metrics
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Agent spawn | < 3s | > 5s |
| Handoff size | < 1000 tokens | > 2000 tokens |
| Task completion | < 60s | > 120s |
| Workflow success | > 95% | < 90% |
| Recovery time | < 10s | > 30s |

### Profiling Commands
```bash
# Identify slow agents
cron action=list | grep duration | sort -k2 -n

# Check token counts
sessions_history --sessionKey <key> --limit 5 | wc -w

# Monitor active sessions
watch -n 5 'sessions_list --activeMinutes=5 | wc -l'
```

---

## Quick Wins Checklist

- [ ] Replace sequential loops with Promise.all() for independent tasks
- [ ] Add checkpoints after expensive stages (>2min)
- [ ] Validate inputs before spawning agents
- [ ] Use references (file paths) instead of inline data >500 tokens
- [ ] Implement circuit breakers for flaky agents
- [ ] Run smoke tests before full test suite
- [ ] Prune context to last 3 decisions + current task
- [ ] Set explicit timeouts on all spawn calls
- [ ] Cache frequently requested dependencies
- [ ] Monitor spawn_duration and success_rate

---

*Optimization hierarchy: Avoid work → Do work in parallel → Do work faster → Throw resources at it*
