# Multi-Agent Coordination Patterns
*Quick reference for effective subagent orchestration in OpenClaw*

## 1. Task Decomposition Patterns

### Pattern A: Parallel Fan-Out
```
Parent Task → [Agent A] → Results
            → [Agent B] → Results
            → [Agent C] → Results
```
**Use when:** Subtasks are independent, no shared dependencies.
**Example:** Research 3 different APIs simultaneously.

### Pattern B: Sequential Pipeline
```
Task → [Agent A: Extract] → [Agent B: Transform] → [Agent C: Load]
```
**Use when:** Each stage depends on previous output.
**Example:** Scrape → Parse → Format → Save.

### Pattern C: Map-Reduce
```
Task → [Agent 1..N: Process chunks] → [Aggregator: Synthesize]
```
**Use when:** Large workload needs splitting + unified summary.
**Example:** Analyze 50 files → Consolidate findings.

## 2. Dependency Management

### Explicit Contracts
Always define:
- **Input format:** Expected structure, file paths, variable names
- **Output format:** Return schema, file locations, naming conventions
- **Error handling:** What constitutes failure, retry logic, fallback values

### Checkpoints
Save intermediate results to disk when:
- Task > 5 min runtime
- Stage outputs feed multiple downstream agents
- Recovery from failure would be expensive

## 3. Context Handoff Protocol

### Minimal Viable Context
Include ONLY what the subagent needs:
```yaml
mission: One-sentence objective
timebox: "15 min" or "30 min"
inputs: Specific files/URLs/data
constraints: Must avoid / Must use
output_to: File path or memory location
```

### Anti-Patterns to Avoid
❌ Dumping full conversation history
❌ Vague instructions ("handle this")
❌ Implicit dependencies on parent state

## 4. Integration Testing Checklist

Before deploying multi-agent workflows:
- [ ] Each agent runs standalone without errors
- [ ] Input/output contracts validated with sample data
- [ ] Failure in one agent doesn't cascade (graceful degradation)
- [ ] Timeout handling tested at each boundary
- [ ] Final output meets quality bar regardless of path taken

## 5. Quality Standards

### Parent Agent Responsibilities
- Monitor subagent status (subagents list)
- Aggregate partial results if timeout occurs
- Validate final deliverable before claiming success

### Subagent Responsibilities
- Signal progress if task exceeds 10 min
- Write partial results on timeout risk
- Return structured data, not raw text dumps

## Quick Reference: When to Spawn

| Scenario | Pattern | Timeout |
|----------|---------|---------|
| Research 3 topics | Parallel | 10 min each |
| Build + Test + Deploy | Pipeline | 15 min each stage |
| Process 100 files | Map-Reduce | 30 min total |
| Complex refactoring | Single agent | 20 min |

---
*Written: 2026-02-18 20:20 CST | Next review: After 3 multi-agent runs*
