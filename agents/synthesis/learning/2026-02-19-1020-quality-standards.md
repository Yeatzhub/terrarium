# Quality Standards for Agent Outputs

*Defining done: measurable criteria for agent deliverables*

---

## 1. Output Completeness Checklist

### Required for All Deliverables
- [ ] **Objective Met**: Primary goal stated in task is achieved
- [ ] **Format Correct**: Output matches requested format (markdown, JSON, code, etc.)
- [ ] **Location Valid**: Files written to specified paths, not orphaned
- [ ] **No Placeholders**: No "TODO", "FIXME", or empty sections in final output
- [ ] **Self-Contained**: References external resources, doesn't require them unexplained

### Format-Specific Criteria

| Format | Quality Gate |
|--------|-------------|
| **Markdown** | Headers structured, code blocks labeled, links valid |
| **JSON** | Valid syntax, all required keys present, typed correctly |
| **Code** | Runs without error, has docstrings/comments, follows style guide |
| **Report** | Executive summary present, data cited, conclusions supported |

---

## 2. Accuracy Standards

### Verification Levels

**Level 1: Self-Check** (All outputs)
```
Before completing, verify:
1. Numbers add up correctly
2. Dates are valid and logical
3. Names are spelled correctly
4. Code executes without errors
```

**Level 2: Cross-Reference** (Research/data tasks)
```
- Claim made → Source cited
- Statistic quoted → Original source linked
- Comparison stated → Both sides represented fairly
```

**Level 3: Peer Review** (Critical deliverables)
```
- Second agent validates findings
- Contradictions flagged and resolved
- Confidence level stated (high/medium/low)
```

---

## 3. Context Handoff Quality

### Package Completeness Score
Rate handoff packages 0-5:

| Criterion | Points |
|-----------|--------|
| Clear one-sentence objective | 1 |
| Explicit constraints listed | 1 |
| Input artifacts referenced with paths | 1 |
| Expected output format defined | 1 |
| Success criteria measurable | 1 |

**Score Guide:**
- 5: Excellent handoff, zero ambiguity
- 4: Good, minor clarifications needed
- 3: Acceptable, some assumptions required
- 2: Poor, frequent interruptions likely
- 1: Incomplete, will likely fail
- 0: Unusable, restart required

---

## 4. Error Handling Standards

### Graceful Degradation Rules

**Must Handle:**
- Missing input files → Clear error message + suggestion
- Timeout → Partial results saved, progress noted
- Invalid input → Specific validation error, not generic crash
- Resource limits → Alternative approach suggested

**Error Message Template:**
```
[WHAT FAILED]: Brief description
[WHY]: Root cause or constraint violated
[IMPACT]: What this means for the task
[NEXT STEPS]: Specific recovery action
```

---

## 5. Documentation Standards

### Code Outputs
```python
"""
Purpose: One-line description
Inputs: What it expects
Outputs: What it produces
Errors: What can go wrong
Example: Brief usage example
"""
```

### Research Outputs
```markdown
## Summary
3-5 bullet points covering key findings

## Methodology
How the information was gathered

## Sources
- [Name](URL) - Relevance description

## Confidence
High/Medium/Low with rationale

## Gaps
What wasn't found or remains uncertain
```

---

## 6. Review Protocol

### Self-Review Questions
Before marking complete, ask:
1. Would I understand this if I hadn't done the work?
2. Are all file paths absolute or clearly relative?
3. Could someone continue this work if I stopped now?
4. Is the most important information easiest to find?
5. Have I removed all brainstorming notes and false starts?

### Peer Review Triggers
Auto-escalate to review when:
- Output > 1000 lines
- Multiple files with dependencies
- Security or financial implications
- External stakeholder visibility

---

## 7. Quality Metrics

### Track These
| Metric | Target | How to Measure |
|--------|--------|----------------|
| First-pass acceptance | > 80% | No revision requests |
| Handoff score | > 4.0 | Package completeness |
| Error clarity | 100% | Users understand what failed |
| Documentation coverage | > 90% | Functions/files documented |

---

## Quick Reference: Is It Done?

```
☐ Objective achieved?
☐ Format matches request?
☐ Files in right place?
☐ No TODOs remaining?
☐ Errors handled gracefully?
☐ Next agent could continue?
☐ You'd be proud to sign your name?
```

All checked? **It's done.**

---

*Generated: 2026-02-19 | Use: Apply before marking any task complete*
