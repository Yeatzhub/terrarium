# Quality Standards for Multi-Agent Systems

**Created:** 2026-02-22 10:20  
**Author:** Synthesis  
**Focus:** Validation gates, review protocols, and acceptance criteria for agent outputs

---

## Why Quality Standards Matter

Agents generate outputs autonomously. Without standards:
- Errors compound across handoffs
- Inconsistencies create technical debt
- Success becomes subjective
- Debugging becomes guesswork

---

## The QUALITY Framework

Each agent output should pass these checks:

| Check | Question | Pass Criteria |
|-------|----------|---------------|
| **Q**uery | Does it solve the problem? | Matches original task requirements |
| **U**niqueness | Is it non-redundant? | Doesn't duplicate existing work |
| **A**ccuracy | Is it correct? | Factual, logical, tested |
| **L**int | Is it well-formed? | Follows format/style standards |
| **I**ntegration | Does it fit? | Compatible with existing system |
| **T**raceability | Can we track it? | Linked to request, has artifacts |
| **Y**ield | Is it minimal? | No unnecessary complexity |

---

## Quality Gates

### Gate 1: Pre-Dispatch Quality

Before spawning sub-agents:

```markdown
CHECKLIST:
- [ ] Task scope is bounded (SMART criteria)
- [ ] Success criteria are explicit
- [ ] Resources are available
- [ ] Dependencies resolved
- [ ] Timeout is appropriate
```

### Gate 2: In-Progress Quality

During execution:

```markdown
MONITOR:
- Progress checkpoints at 25%, 50%, 75%
- Time remaining vs work remaining
- Error rate tracking
- Resource usage
```

### Gate 3: Output Quality

Before handoff or completion:

```markdown
VALIDATE:
- [ ] Output matches success criteria
- [ ] No obvious errors or hallucinations
- [ ] Artifacts exist and are readable
- [ ] Documentation updated if needed
- [ ] Tests pass (if applicable)
```

---

## Output Validation Patterns

### Pattern 1: Schema Validation

For structured outputs, validate against schema:

```python
# Example: Validate handoff package
HANDOFF_SCHEMA = {
    "required": ["task_summary", "current_state", "artifacts"],
    "properties": {
        "task_summary": {"type": "string", "maxLength": 200},
        "current_state": {"type": "string"},
        "artifacts": {"type": "array", "items": {"type": "string"}},
        "key_decisions": {"type": "array"},
        "blockers": {"type": "array"}
    }
}

def validate_handoff(package):
    for field in HANDOFF_SCHEMA["required"]:
        if field not in package:
            return False, f"Missing required: {field}"
    return True, "Valid"
```

### Pattern 2: Cross-Check Validation

Compare outputs from multiple sources:

```bash
# Cross-check file content
FILE_A=$(read path="output/summary.md")
FILE_B=$(read path="output/summary-backup.md")

if [[ "$FILE_A" != "$FILE_B" ]]; then
    echo "⚠️  Consistency check failed"
fi
```

### Pattern 3: Artifact Integrity

Verify referenced files exist and are valid:

```python
def verify_artifacts(artifact_paths):
    """Check all artifacts exist and are non-empty."""
    issues = []
    for path in artifact_paths:
        if not os.path.exists(path):
            issues.append(f"Missing: {path}")
        elif os.path.getsize(path) == 0:
            issues.append(f"Empty: {path}")
    return len(issues) == 0, issues
```

---

## Review Protocols

### Self-Review Checklist

Agent should verify own output before handoff:

```markdown
## Self-Review

### Functionality
- [ ] Does this solve the stated problem?
- [ ] Are all requirements addressed?
- [ ] Do tests pass?

### Quality
- [ ] Is code/docs readable?
- [ ] Are there unnecessary parts?
- [ ] Is error handling adequate?

### Integration
- [ ] Does it break existing functionality?
- [ ] Are dependencies correct?
- [ ] Is it backwards compatible?

### Documentation
- [ ] Are decisions documented?
- [ ] Is usage clear?
- [ ] Are edge cases noted?
```

### Peer-Review Protocol

When receiving another agent's output:

```markdown
## Peer Review

### Incoming Check
1. Read context package completely
2. Verify artifacts exist
3. Run any provided tests
4. Check against success criteria

### Accept/Reject Decision
- ✓ ACCEPT: All criteria met, no blocking issues
- ⚠️ CONDITIONAL: Minor issues, can proceed with notes
- ✗ REJECT: Blocking issues, needs rework

### Feedback Format
```
REVIEW_DECISION: [ACCEPT | CONDITIONAL | REJECT]
ISSUES:
  - [issue 1]
  - [issue 2]
STRENGTHS:
  - [strength 1]
SUGGESTIONS:
  - [suggestion 1]
```
```

---

## Acceptance Criteria Templates

### Code Tasks

```markdown
ACCEPTANCE CRITERIA:
- [ ] Function implements specification
- [ ] Unit tests added, all pass
- [ ] No lint errors
- [ ] Edge cases handled
- [ ] Documentation updated
- [ ] No performance regression
```

### Research Tasks

```markdown
ACCEPTANCE CRITERIA:
- [ ] Sources are credible
- [ ] Findings are factual
- [ ] Summary is clear and actionable
- [ ] Gaps are identified
- [ ] Recommendations are prioritized
```

### Documentation Tasks

```markdown
ACCEPTANCE CRITERIA:
- [ ] Accurate and up-to-date
- [ ] Follows style guide
- [ ] Examples are correct
- [ ] Links are valid
- [ ] Audience-appropriate language
```

### Integration Tasks

```markdown
ACCEPTANCE CRITERIA:
- [ ] Components communicate correctly
- [ ] No breaking changes
- [ ] Integration tests pass
- [ ] Error handling across boundaries
- [ ] Logging/tracing in place
```

---

## Quality Metrics Dashboard

Track these metrics over time:

| Metric | Formula | Target |
|--------|---------|--------|
| First-pass acceptance rate | Accepted / Total submissions | >80% |
| Rework rate | Rejected / Total submissions | <10% |
| Defect escape rate | Bugs found after acceptance | <5% |
| Handoff clarity score | Average rating from receivers | >4/5 |
| Artifact validity rate | Valid artifacts / Total artifacts | >95% |

---

## Error Classification

Standardize error types for pattern analysis:

| Code | Type | Example | Fix Pattern |
|------|------|---------|-------------|
| E001 | Missing output | No artifact created | Add validation gate |
| E002 | Wrong format | JSON instead of Markdown | Schema validation |
| E003 | Incomplete | Only 3/5 requirements met | Check pre-dispatch |
| E004 | Incorrect | Factually wrong | Fact-check gate |
| E005 | Incompatible | Breaks integration | Integration test |
| E006 | Redundant | Duplicates existing work | Uniqueness check |
| E007 | Untraceable | No link to request | Require task ID |

---

## Quality Automation

### Pre-Commit Hooks

```bash
#!/bin/bash
# .git/hooks/pre-commit-qa

# Run quality checks before committing agent outputs
echo "Running quality checks..."

# Check for required fields in handoff files
for file in agents/*/handoffs/*.md; do
    if ! grep -q "task_summary:" "$file"; then
        echo "✗ Missing task_summary in $file"
        exit 1
    fi
done

echo "✓ Quality checks passed"
```

### CI Quality Gate

```yaml
# .github/workflows/agent-qa.yml
name: Agent Quality Gate

on:
  pull_request:
    paths:
      - 'agents/**'

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - name: Validate handoff packages
        run: python scripts/validate_handoffs.py
      
      - name: Check artifact integrity
        run: python scripts/check_artifacts.py
      
      - name: Run agent tests
        run: pytest tests/agents/
```

---

## Quick Reference Card

```
QUALITY CHECKS (copy-paste):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Solves stated problem
□ Meets success criteria
□ No obvious errors
□ Artifacts exist
□ Tests pass
□ Documented decisions
□ No redundancy
□ Compatible with system
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REJECT IF:
- Missing required artifacts
- Fails success criteria
- Breaks existing functionality
- Contains factual errors

CONDITIONAL IF:
- Minor formatting issues
- Non-blocking suggestions
- Missing optional documentation

ACCEPT IF:
- All required checks pass
- No blocking issues
- Ready for next phase
```

---

## Bottom Line

Quality isn't a phase—it's a gate at every step:
1. **Pre-dispatch:** Scope and criteria are clear
2. **In-progress:** Monitor and checkpoint
3. **Output:** Validate, self-review, peer-review
4. **Post-handoff:** Track metrics, learn patterns

The QUALITY framework ensures nothing slips through: Query, Uniqueness, Accuracy, Lint, Integration, Traceability, Yield.