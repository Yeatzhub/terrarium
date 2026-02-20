# Quality Standards for Multi-Agent Systems
*Synthesis Learning — 2026-02-20*

## 1. Output Quality Standards

### File System Standards
```bash
# Required: All outputs must be verifiable
[ -f "$OUTPUT_FILE" ] || exit 1                    # File exists
[ -s "$OUTPUT_FILE" ] || exit 1                    # Non-empty
[ $(wc -l < "$OUTPUT_FILE") -gt 0 ] || exit 1     # Has content

# Documentation: Must include header
head -5 "$OUTPUT_FILE" | grep -q "^# " || exit 1  # Has H1 title
head -10 "$OUTPUT_FILE" | grep -q "202[0-9]-" || exit 1  # Dated
```

### Code Quality Gates
```python
CODE_STANDARDS = {
    "max_lines_per_function": 50,
    "max_cyclomatic_complexity": 10,
    "test_coverage_minimum": 0.8,
    "docstring_required": True,
    "type_hints_required": True
}

def validate_code(filepath):
    """All generated code must pass these checks."""
    checks = [
        ("syntax", lambda: compile(open(filepath).read(), filepath, 'exec')),
        ("complexity", lambda: radon_cc(filepath) < 10),
        ("tests", lambda: pytest(filepath.replace('.py', '_test.py')).passed > 0)
    ]
    return all(check[1]() for check in checks)
```

### Documentation Standards
| Element | Required | Format |
|---------|----------|--------|
| Title | Yes | H1 heading |
| Date | Yes | ISO 8601 (YYYY-MM-DD) |
| Author | Yes | Agent ID or user |
| Summary | For >500 words | 3-5 bullet points |
| Links | Verify working | Valid URLs |
| Code examples | If applicable | Runnable/tested |

---

## 2. Agent Behavior Standards

### Response Quality Checklist
```markdown
Every agent response must:
- [ ] Answer the specific question asked
- [ ] Include actionable next steps (if applicable)
- [ ] Reference source files/data (with paths)
- [ ] Note assumptions made
- [ ] Flag uncertainty with confidence level
- [ ] Stay within scope (no scope creep)
```

### Error Message Standards
```javascript
const ERROR_TEMPLATE = {
  error: true,
  type: "TIMEOUT|PARSE|DEPENDENCY|UNKNOWN",
  message: "Human-readable description",
  context: {
    taskId: "uuid",
    attempted: "what was tried",
    suggested: "how to fix"
  },
  recoverable: true|false,
  escalation: "user|parent|self"  // Who should handle
};

// Bad: "It didn't work"
// Good: "JSON parse failed at line 42 - malformed array bracket"
```

### Completeness Verification
```bash
# Before claiming task complete:
verify_completeness() {
  # 1. Check all deliverables exist
  for item in $(cat .deliverables); do
    [ -e "$item" ] || return 1
  done
  
  # 2. Check no TODO markers remain
  ! grep -r "TODO|FIXME|XXX" "$OUTPUT_DIR" || return 1
  
  # 3. Check cross-references valid
  for link in $(extract_links "$OUTPUT_DIR"); do
    [ -e "$link" ] || curl -s "$link" | head -1 | grep -q 200 || return 1
  done
  
  return 0
}
```

---

## 3. Workflow Quality Standards

### Pre-Flight Checklist
```markdown
Before spawning workflow:
- [ ] Input data validated (schema, format, completeness)
- [ ] Dependencies confirmed available
- [ ] Output directory exists and writable
- [ ] Timeout appropriate for task complexity
- [ ] Fallback plan defined (circuit breaker active)
- [ ] User notified if >10min expected duration
```

### In-Flight Monitoring
```javascript
const HEALTH_CHECK_INTERVAL = 30000; // 30s

function monitorWorkflow(workflowId) {
  setInterval(() => {
    const status = sessions_list({ workflowId });
    
    // Alert conditions
    if (status.stuck > 0) console.warn(`${workflowId}: ${status.stuck} stuck tasks`);
    if (status.failure_rate > 0.1) console.error(`${workflowId}: Failure rate ${status.failure_rate}`);
    if (status.avg_duration > status.expected * 2) console.warn(`${workflowId}: 2x slower than expected`);
  }, HEALTH_CHECK_INTERVAL);
}
```

### Post-Completion Audit
```bash
#!/bin/bash
# audit_workflow.sh

WORKFLOW_ID=$1
REPORT="$WORKFLOW_ID/audit.md"

echo "# Workflow Audit: $WORKFLOW_ID" > $REPORT
echo "Date: $(date -Iseconds)" >> $REPORT

# Success metrics
echo "## Metrics" >> $REPORT
echo "- Duration: $(get_duration $WORKFLOW_ID)" >> $REPORT
echo "- Agents spawned: $(count_spawns $WORKFLOW_ID)" >> $REPORT
echo "- Token usage: $(get_token_count $WORKFLOW_ID)" >> $REPORT
echo "- Retry rate: $(calculate_retries $WORKFLOW_ID)" >> $REPORT

# Quality checks
echo "## Quality Checks" >> $REPORT
echo "- [ ] All deliverables produced" >> $REPORT
echo "- [ ] No TODOs remaining" >> $REPORT
echo "- [ ] Tests passing" >> $REPORT
echo "- [ ] Documentation complete" >> $REPORT

# Anomalies
echo "## Anomalies" >> $REPORT
list_anomalies $WORKFLOW_ID >> $REPORT || echo "None detected" >> $REPORT
```

---

## 4. Testing Quality Standards

### Test Coverage Requirements
```yaml
coverage:
  statements: 80%
  branches: 70%
  functions: 90%
  lines: 80%
  
critical_paths:
  - agent_spawn
  - context_handoff
  - error_recovery
  - state_persistence
  
required_tests:
  - unit: every function
  - integration: every agent boundary
  - e2e: every user workflow
```

### Test Data Standards
```python
TEST_DATA_RULES = {
    "size": "production_like",  # Not toy datasets
    "variety": "edge_cases_included",  # Nulls, empties, extremes
    "deterministic": True,  # Same input → same output
    "documented": True,  # Origin and expected results
}

def generate_test_data(production_sample, edge_cases=10):
    """Create test data that's representative but safe."""
    sample = production_sample[:100]  # Anonymized subset
    edges = generate_edge_cases(edge_cases)
    return sample + edges
```

### Flaky Test Prevention
```javascript
// Test must be deterministic
const unstable_tests = detect_flaky_tests({
  runs: 10,
  threshold: 0.9  // Must pass 90% of runs
});

if (unstable_tests.length > 0) {
  quarantine_tests(unstable_tests);
  require_fix_before_merge(unstable_tests);
}
```

---

## 5. Context & Handoff Quality

### Context Completeness
```markdown
## Handoff Quality Checklist

**Must Include**:
- [ ] Task ID and lineage (what came before)
- [ ] Decisions made (with rationale)
- [ ] Current state (files, data structures)
- [ ] Blockers (if any)
- [ ] Success criteria (how to know when done)

**Must NOT Include**:
- [ ] Full conversation history (link instead)
- [ ] Redundant information (link to prior handoff)
- [ ] Unclear next steps (must be explicit)
```

### Context Drift Detection
```python
def detect_context_drift(original_task, current_context):
    """Alert if workflow deviates from original intent."""
    
    # Check scope creep
    original_scope = extract_intent(original_task)
    current_scope = extract_intent(current_context)
    
    if jaccard_similarity(original_scope, current_scope) < 0.7:
        return {
            "alert": "SCOPE_DRIFT",
            "original": original_scope,
            "current": current_scope,
            "action": "Confirm with user before continuing"
        }
    
    return {"alert": None}
```

### Knowledge Persistence
```bash
# Standards for memory files
MEMORY_REQUIREMENTS="""
- Daily logs: memory/YYYY-MM-DD.md (raw, chronological)
- Curated: MEMORY.md (patterns, decisions, gotchas)
- Skills: SKILL.md (capabilities, tool usage)
- Links: All references must be valid paths
- Searchable: Use consistent terminology
"""

# Verification
find memory/ -name "*.md" -exec grep -L "## " {} \;  # All must have sections
find . -name "MEMORY.md" -exec grep -c "TODO" {} \;  # Should be 0
```

---

## 6. Continuous Improvement

### Metrics Dashboard
```javascript
const QUALITY_METRICS = {
  // Output quality
  file_success_rate: track_file_creation(),
  test_pass_rate: track_test_results(),
  doc_compliance: track_doc_standards(),
  
  // Workflow quality  
  on_time_completion: track_deadlines(),
  retry_rate: track_retries(),
  escalation_rate: track_user_intervention(),
  
  // System quality
  agent_uptime: track_availability(),
  error_recovery_rate: track_recovery(),
  token_efficiency: track_tokens_per_task()
};

// Alert on degradation
if (QUALITY_METRICS.retry_rate > 0.15) {
  trigger_review("High retry rate - investigate root causes");
}
```

### Retrospective Template
```markdown
# Workflow Retrospective: [ID]

## What Went Well
- 

## What Didn't
- 

## Metrics
- Expected duration: 
- Actual duration: 
- Token usage: 
- Failure points: 

## Improvements for Next Time
1. 

## Pattern to Document
- [ ] Add to MEMORY.md
- [ ] Update SKILL.md if tool-related
```

### Feedback Loop
```bash
# After each significant workflow
1. Run audit_workflow.sh
2. Fill retrospective template
3. Update documentation if pattern discovered
4. Adjust standards if gaps found
5. Share learnings via MEMORY.md
```

---

## Quick Quality Check

Before marking ANY task complete:
1. ✓ Output exists and non-empty
2. ✓ Tests pass (if code)
3. ✓ Links work (if docs)
4. ✓ No TODOs remaining
5. ✓ Handoff context ready (if parent workflow)
6. ✓ Metrics logged

**Quality is not an act, it is a habit.** — Documented standards make quality automatic.

---

*Cross-reference: Apply these standards to the patterns in 2026-02-20-0420, tests in 2026-02-20-0620, and optimizations in 2026-02-20-0820.*
