# Integration Test Examples for Multi-Agent Workflows
*Synthesis Learning — 2026-02-20*

## 1. Agent Contract Test

**Purpose**: Verify sub-agent handles expected input/output format.

```javascript
// Test: Verify analyst agent returns structured JSON
const testAnalystContract = async () => {
  const result = await sessions_spawn({
    task: "Analyze: user engagement dropped 15% this week. Return JSON with {rootCause, severity, actionItems[]}",
    agentId: "analyst",
    timeoutSeconds: 60
  });
  
  // Assertions
  assert(result.completed === true, "Task must complete");
  assert(isValidJSON(result.output), "Output must be valid JSON");
  assert(JSON.parse(result.output).rootCause, "Must contain rootCause field");
  assert(Array.isArray(JSON.parse(result.output).actionItems), "actionItems must be array");
};
```

**Run**: Spawn test task, validate structured response format.

---

## 2. Pipeline Integration Test

**Purpose**: Verify data flows correctly through agent chain.

```bash
# Stage 1: Research agent
SESSION_A=$(sessions_spawn --task "Research OAuth2 best practices" --agentId researcher)

# Stage 2: Architect agent (depends on Stage 1)
sessions_send --sessionKey $SESSION_A --message "Design auth system based on research above"

# Stage 3: Implementer agent (depends on Stage 2)
sessions_send --sessionKey $SESSION_A --message "Generate Python code for the auth system design"

# Validate: Check final output exists and compiles
read agents/output/auth_system.py
exec python3 -m py_compile agents/output/auth_system.py
```

**Key**: Each stage adds context; final validation ensures end-to-end success.

---

## 3. Fan-Out Parallel Test

**Purpose**: Verify parallel sub-agents complete and aggregate correctly.

```javascript
// Spawn 3 parallel analysis tasks
const tasks = [
  sessions_spawn({ task: "Analyze Q1 revenue", agentId: "finance", timeoutSeconds: 120 }),
  sessions_spawn({ task: "Analyze Q1 costs", agentId: "finance", timeoutSeconds: 120 }),
  sessions_spawn({ task: "Analyze Q1 churn", agentId: "analytics", timeoutSeconds: 120 })
];

const results = await Promise.all(tasks);

// Validation
assert(results.every(r => r.completed), "All parallel tasks must complete");
assert(results.every(r => r.durationMs < 120000), "All tasks within timeout");

// Aggregate check
const combined = results.map(r => r.output).join("\n");
assert(combined.includes("revenue") && combined.includes("costs"), "All topics covered");
```

**Key**: Test both individual completion AND successful aggregation.

---

## 4. Error Injection Test

**Purpose**: Verify graceful failure handling.

```bash
# Test 1: Invalid input handling
sessions_spawn --task "Analyze [CORRUPT_DATA@#$%]" --agentId analyst --timeoutSeconds=30
# Expected: Agent returns error message, does not hang

# Test 2: Timeout scenario  
sessions_spawn --task "Research quantum computing (extremely deep)" --agentId researcher --timeoutSeconds=5
# Expected: Task times out, status shows incomplete

# Test 3: Missing dependency
sessions_spawn --task "Implement based on research from session 99999" --agentId coder --timeoutSeconds=30
# Expected: Agent reports missing context, requests clarification

# Cleanup
cron action=kill jobId=<timeout-job-id>
```

**Key**: Each failure mode tested separately; verify informative error messages.

---

## 5. State Recovery Test

**Purpose**: Verify checkpoint/resume functionality.

```bash
# Start long-running workflow
SESSION=$(sessions_spawn --task "Build microservice architecture" --agentId architect)

# Simulate interruption (manual or triggered)
process action=kill sessionId=$SESSION

# Resume from checkpoint
sessions_send --sessionKey $SESSION --message "Continue from checkpoint. Previous context: [summarize from MEMORY.md entry]"

# Validate continuity
assert_output_contains "resuming" or "previously determined"
```

**Key**: Checkpoint written to workspace; resume retains context.

---

## 6. Load/Concurrency Test

**Purpose**: Verify system stability under multiple concurrent agents.

```javascript
// Spawn 10 simultaneous agents
const loadTest = async () => {
  const agents = Array(10).fill().map((_, i) => 
    sessions_spawn({
      task: `Quick analysis task ${i}: Summarize Agile methodology`,
      agentId: "generalist",
      timeoutSeconds: 60
    })
  );
  
  const startTime = Date.now();
  const results = await Promise.allSettled(agents);
  const totalTime = Date.now() - startTime;
  
  // Metrics
  const successRate = results.filter(r => r.status === 'fulfilled' && r.value.completed).length / 10;
  const avgResponseTime = totalTime / 10;
  
  assert(successRate >= 0.8, "80%+ success rate required");
  assert(avgResponseTime < 30000, "Average <30s per task");
  
  console.log(`Load test: ${successRate*100}% success, ${avgResponseTime}ms avg`);
};
```

**Key**: Monitor via `session_status` during test; verify resource limits.

---

## 7. End-to-End Quality Gate

**Purpose**: Comprehensive validation before marking workflow complete.

```bash
#!/bin/bash
# quality_gate.sh

WORKFLOW_ID=$1

# Check 1: All spawned tasks completed
INCOMPLETE=$(sessions_list | grep -c "incomplete")
[ "$INCOMPLETE" -eq 0 ] || exit 1

# Check 2: Output files exist
for file in $(cat $WORKFLOW_ID/outputs.manifest); do
  [ -f "$file" ] || exit 2
done

# Check 3: Parseable outputs
for json in $WORKFLOW_ID/*.json; do
  python3 -c "import json; json.load(open('$json'))" || exit 3
done

# Check 4: Links valid (for documentation)
for url in $(grep -oE 'https?://[^ ]+' $WORKFLOW_ID/report.md); do
  curl -s --head "$url" | head -1 | grep -q "200" || exit 4
done

echo "Quality gate passed"
```

**Run**: Execute after workflow completion; gates deployment/delivery.

---

## Quick Reference: Test Selection

| Risk Area | Test Type | Frequency |
|-----------|-----------|-----------|
| Agent behavior changes | Contract test | Every agent update |
| Workflow structure changes | Pipeline test | Every workflow change |
| Performance concerns | Load test | Weekly / before scale |
| New failure modes | Error injection | Once per pattern |
| Production workflows | Quality gate | Every run |

---

## Testing Checklist

Before deploying multi-agent workflow:
- [ ] Contract tests pass for all agent types used
- [ ] Pipeline/integration tests pass end-to-end
- [ ] Error injection produces graceful failures
- [ ] Load test confirms <N concurrent agents stable
- [ ] Recovery test validates checkpoint system
- [ ] Quality gate passes on sample production data

---

*Integration with coordination patterns: Use these tests to validate the patterns documented in 2026-02-20-0420-multi-agent-coordination-patterns.md.*
