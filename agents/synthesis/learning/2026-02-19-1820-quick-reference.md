# Multi-Agent Workflow Quick Reference

*At-a-glance guide for running coordinated agent workflows*

---

## 1. Pre-Flight Checklist

Before spawning:
- [ ] Task < 15 min or decomposed
- [ ] Output format defined
- [ ] File paths absolute or $WORKSPACE-relative
- [ ] Dependencies identified (hard/soft/none)
- [ ] Timeout configured
- [ ] Cleanup mode selected
- [ ] Handoff package complete (see §3)

---

## 2. Task Decomposition Quick Rules

| Duration | Action | Example |
|----------|--------|---------|
| < 2 min | Do yourself | Fix typo, quick grep |
| 2-15 min | Spawn single | "Research X, write summary" |
| > 15 min | Break down | Research → Collect → Analyze → Write |

**Decomposition Template:**
```
Phase 1: [Gather data] → /tmp/data.json
Phase 2: [Analyze] → /tmp/analysis.md
Phase 3: [Synthesize] → /output/final.md
```

---

## 3. Handoff Package Template

```yaml
objective: "One clear sentence"
inputs:
  - "/path/to/file.json"
constraints:
  - "Time: 10 min"
  - "Format: Markdown"
  - "Max length: 500 words"
expected_output: "/output/result.md"
success_criteria: "Contains X, Y, Z sections"
```

---

## 4. Dependency Patterns

### Sequential (Hard Dep)
```python
job1 = await sessions_spawn({"task": "A"})
await wait_for(job1)
job2 = await sessions_spawn({"task": "B"})  # Needs A
```

### Parallel (No Dep)
```python
jobs = [sessions_spawn({"task": t}) for t in tasks]
await asyncio.gather(*[wait_for(j) for j in jobs])
```

### Fan-Out → Fan-In
```python
# Parallel phase
parallel = [sessions_spawn({"task": t}) for t in subtasks]
results = await asyncio.gather(*parallel)

# Merge phase (after all complete)
merge = await sessions_spawn({
    "task": f"Merge {results} into final"
})
```

---

## 5. Polling Guidelines

```python
# Exponential backoff
waited, delay = 0, 5
while waited < max_wait:
    status = await subagents({"action": "list"})
    if status.get("completed"):
        return status
    await asyncio.sleep(delay)
    waited += delay
    delay = min(delay * 1.5, 30)  # Cap at 30s
```

**Don't:** Poll every 1s  
**Do:** Start at 5s, increase to 30s max

---

## 6. Error Handling Quick Reference

| Scenario | Response |
|----------|----------|
| Timeout | Save partial, note progress, escalate |
| Dependency fails | Stop chain, report root cause |
| Invalid input | Specific error, not generic crash |
| Resource limit | Suggest alternative approach |

---

## 7. Quality Gates

Before marking done:
- [ ] Objective achieved?
- [ ] Format matches request?
- [ ] Files in correct location?
- [ ] No TODO/FIXME remaining?
- [ ] Next agent could continue?

---

## 8. Common Commands

```bash
# Check agent status
openclaw subagents list

# Poll specific job
openclaw subagents status --target SESSION_KEY

# Clean up sessions
openclaw subagents cleanup --older-than 1h
```

---

## 9. Anti-Patterns

| Don't | Do |
|-------|-----|
| Inline large data | File reference |
| Tight poll loops | Exponential backoff |
| Spawn for <2 min tasks | Do it yourself |
| Relative paths | Absolute or $WORKSPACE paths |
| "Fix everything" | "Fix TypeError in parse_input()" |
| No cleanup specified | cleanup: 'success' or 'always' |

---

## 10. Decision Flowchart

```
Need work done:
  ├─→ < 2 min? ───────────────┐
  │   └─→ YES: Do yourself    │
  │      NO:                  │
  ├─→ Can parallelize? ───────┤
  │   ├─→ YES: Spawn multiple │
  │   └─→ NO:                 │
  ├─→ Has dependencies? ──────┤
  │   ├─→ YES: Chain them     │
  │   └─→ NO: Single spawn    │
  └─→ All spawns:             │
      └─→ Add handoff package │
      └─→ Set timeout         │
      └─→ Pick cleanup mode   │
```

---

*Generated: 2026-02-19 | Use: Keep open while running workflows*
