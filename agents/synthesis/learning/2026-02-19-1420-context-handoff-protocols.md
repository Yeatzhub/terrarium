# Context Handoff Protocols

*Passing state between agents without losing the thread*

---

## 1. The Handoff Package

### Required Fields
Every spawn must include:
```yaml
objective: "One clear sentence of what to accomplish"
constraints:
  - "Time limit"
  - "Resource limits"
  - "Must-nots"
inputs:
  - "/path/to/file.json"
  - "URL or reference"
expected_output: "Format and location of deliverable"
success_criteria: "How to know it's done"
```

---

## 2. Handoff Patterns

### Pattern: File Bridge
```python
# Phase 1: Output structured data
handoff = {
    "objective": "Analyze Q3 sales trends",
    "inputs": ["/data/q3_sales.csv"],
    "constraints": ["Use pandas", "Focus on YoY growth"],
    "expected_output": "/output/q3_analysis.json",
    "key_findings": ["Revenue up 15%", "Churn at 4%"],
    "confidence": "high"
}
write("/tmp/handoff_p1.json", json.dumps(handoff))

# Phase 2: Read and continue
spawn_result = await sessions_spawn({
    "task": "Read /tmp/handoff_p1.json, generate report from key_findings, save to expected_output"
})
```

### Pattern: Summary + Full Context
```
Spawn package structure:

[1] Summary (2-3 sentences) - What was done, what needs doing
[2] Critical info - Must-know facts, decisions, numbers
[3] References - File paths to full context if needed
[4] Open questions - What remains uncertain
```

### Pattern: Chain State
```python
# Pass minimal state forward
chain_state = {
    "step": 2,
    "of": 5,
    "completed": ["research"],
    "current": "analysis",
    "artifacts": {
        "research": "/tmp/research.json",
        "analysis": "/tmp/analysis.json"  # Will be written
    }
}

await sessions_spawn({
    "task": f"Step {chain_state['step']}: Analyze {chain_state['artifacts']['research']}, write to {chain_state['artifacts']['analysis']}"
})
```

---

## 3. Token-Efficient Handoffs

### Do This
```
[GOOD] "Analyze /tmp/data.json, focus on 'revenue' and 'churn' columns"

[BAD]  "Analyze this data: {500 lines of JSON}"
```

### Do This
```
[GOOD] "See key findings in /tmp/summary.json, detailed data in /tmp/full/"

[BAD]  "The analysis revealed that in Q1 revenue was 15% higher than Q2... {continues for 1000 tokens}"
```

---

## 4. State Preservation Checklist

When handing off, verify:
- [ ] **Objective clear** - Next agent knows what to do
- [ ] **Inputs accessible** - All referenced files exist and are readable
- [ ] **Context sufficient** - Key decisions/rationale included
- [ ] **No repetition** - Don't repeat what agent could compute
- [ ] **Deadlines clear** - Time constraints explicit
- [ ] **Escalation path** - What to do if stuck

---

## 5. Common Failures

| Failure | Fix |
|---------|-----|
| "Works on my machine" paths | Use absolute paths or env vars |
| Missing rationale | Include "why" not just "what" |
| Context overload | File reference over inline |
| Orphaned temp files | Cleanup strategy defined |
| Silent assumptions | Constraints section explicit |

---

## 6. Handoff Template

```markdown
## CONTEXT HANDOFF

**From:** [Agent name]  
**To:** [Next agent]  
**Task:** [Brief objective]

### What Was Done
[2-3 sentence summary]

### What You Need to Do
[Clear, actionable instruction]

### Files Provided
- `/path/to/input.json` - Description
- `/path/to/context.md` - Full background

### Critical Info
- [Key point 1]
- [Key point 2]

### Constraints
- [Time/resource limits]
- [Must/must-not requirements]

### Success Criteria
[How to know when you're done]

### Questions?
Check `/path/to/faq.md` or escalate to user if blocked.
```

---

## 7. Quick Scoring

Rate each handoff 1-5:
- Agent starts immediately without questions? (+2)
- All required files present? (+1)
- Objective unambiguous? (+1)
- Constraints clear? (+1)

**5:** Perfect handoff  
**4:** Minor questions  
**3:** Needs clarification  
**2:** Major gaps  
**1:** Cannot proceed

---

*Generated: 2026-02-19 | Use: Include in every sessions_spawn call*
