# Multi-Agent Coordination Patterns

*Quick reference for effective agent collaboration*

---

## 1. Task Decomposition

### Pattern: Layered Decomposition
Break complex work into 3 tiers:
- **Tier 1**: Major phases (research → design → implement → validate)
- **Tier 2**: Functional blocks within each phase
- **Tier 3**: Atomic, assignable tasks (15-60 min each)

### Rule of Thumb
> If a task needs >1 sub-agent spawn, decompose further.

---

## 2. Context Handoff Protocol

### Required Handoff Package
Every spawn should receive:
```
1. Objective (one sentence)
2. Constraints (time, resources, must-nots)
3. Input artifacts (file paths, data)
4. Expected output format
5. Success criteria
```

### Pattern: Context Window Budgeting
- Reserve 20% tokens for agent's own reasoning
- Put critical info at start/end of prompt
- Use file references over inline dumps

---

## 3. Dependency Management

### Pattern: Dependency Chain Visualization
Before spawning, map:
```
Task A (research) → output/data.json
         ↓
Task B (analyze)  → output/report.md
         ↓
Task C (implement) → output/feature.py
```

### Rule: Never Block
- Parallelize where possible
- Use `sessions_spawn` with `cleanup` for fire-and-forget
- Poll dependencies, don't hard-wait

---

## 4. Integration Testing

### Pattern: Contract-First Testing
Define interface contracts before implementation:
```python
# test_contract.py — verify before coding
def test_output_format():
    result = module.process(input)
    assert "required_key" in result
    assert isinstance(result["value"], int)
```

### Pattern: Agent Output Validation
- Always validate spawned agent results
- Check file existence before proceeding
- Handle timeouts gracefully

---

## 5. Quality Standards

### Required Checklist
- [ ] Output matches specified format
- [ ] Files written to correct paths
- [ ] No orphaned temp files
- [ ] Error states handled
- [ ] Time budget respected

### Pattern: Self-Review Step
Every agent should end with:
```
1. Did I complete the objective?
2. Are outputs in the right place?
3. Can the next agent consume my output?
```

---

## Quick Reference: Spawn Patterns

| Scenario | Strategy |
|----------|----------|
| Research + Synthesis | Sequential spawn, pass file path |
| Parallel data gathering | Multiple spawns, collect results |
| Review/Critique | Spawn critic with full context |
| Long-running task | Use `runTimeoutSeconds`, poll status |

---

## Anti-Patterns to Avoid

1. **Spawning without cleanup** → Use `cleanup: 'success'` or `cleanup: 'always'`
2. **Over-delegation** → If it takes <2 mins, do it yourself
3. **Tight coupling** → Agents should work with files, not live state
4. **Silent failures** → Always check spawn return status

---

*Generated: 2026-02-19 | Use: Reference before multi-agent workflows*
