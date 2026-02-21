# Production Readiness Checklist
*Synthesis Learning — 2026-02-21*

Pre-deployment verification for multi-agent workflows.

---

## 1. Configuration Validation

```bash
# Environment checks
[ ] Timeouts set in config (not hardcoded)
[ ] Concurrency limits configured
[ ] Resource quotas defined (memory, CPU, API calls)
[ ] Fallback agents specified for critical paths
[ ] Circuit breaker thresholds configured

# File paths
[ ] Output directories writable
[ ] Checkpoint directory exists with permissions
[ ] Log directory configured and rotating
[ ] State files have backup strategy
```

---

## 2. Security Hardening

### Input Validation
```python
# Validate before spawn
def sanitize_input(task):
    assert len(task) < 10000, "Task too large"
    assert "../" not in task, "Path traversal attempt"
    assert not re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', task), "Invalid characters"
    return task
```

### Output Sanitization
```python
# Validate before using
[ ] Output written to expected location
[ ] No unexpected file creation outside workspace
[ ] No sensitive data in logs (strip tokens, keys)
[ ] Execution results logged (no silent failures)
```

### Access Controls
```bash
[ ] Agent can only access designated directories
[ ] No unrestricted shell execution
[ ] API keys not passed to untrusted agents
[ ] Secrets in environment, not task strings
```

---

## 3. Observability Setup

### Required Metrics
```javascript
// Track these for every workflow
const REQUIRED_METRICS = {
  "workflow_id": "uuid",
  "start_time": "timestamp",
  "duration_ms": "number",
  "stages_completed": "number",
  "stages_total": "number",
  "agents_spawned": "number",
  "success_rate": "float (0-1)",
  "error_types": "array",
  "token_usage": "number",
  "cost": "number"
};
```

### Alert Thresholds
| Metric | Warning | Critical |
|--------|---------|----------|
| Success rate | < 90% | < 80% |
| Avg duration | > 2x expected | > 3x expected |
| Error rate | > 5% | > 10% |
| Cost per workflow | > 2x budget | > 3x budget |
| Token usage | > 5000/task | > 8000/task |

### Logging Requirements
```yaml
logs:
  workflow_events: required        # Start, stage, complete, error
  agent_spawns: required             # What, when, timeout
  context_operations: debug          # For troubleshooting
  performance_metrics: info          # Duration, tokens
  security_events: required          # Auth, access, failures
  
retention:
  workflow_logs: 30 days
  debug_logs: 7 days
  security_logs: 90 days
```

---

## 4. Testing Requirements

### Pre-Deployment Tests
| Test Type | Coverage | Status |
|-----------|----------|--------|
| Unit tests | > 80% | [ ] |
| Integration tests | All agent boundaries | [ ] |
| Load tests | 2x expected load | [ ] |
| Chaos tests | Random failure injection | [ ] |
| Security tests | Input validation, sanitization | [ ] |
| End-to-end | Golden path only | [ ] |

### Test Data
```bash
[ ] Production-like data (not toy datasets)
[ ] Edge cases included (null, empty, max values)
[ ] Deterministic (same input → same output)
[ ] Documented (origin, expected results)
```

---

## 5. Reliability Guarantees

### Fault Tolerance
```python
# Checklist implementation
reliability_requirements = {
    "max_retries": 3,
    "circuit_breaker_threshold": 5,
    "checkpoint_frequency": "after_expensive",
    "graceful_degradation": True,  # Fallback paths defined
    "dead_letter_queue": True,     # Failed tasks logged
    "idempotent_operations": True  # Safe to retry
}
```

### Recovery Procedures
```bash
[ ] Documented runbook for common failures
[ ] Automated recovery for known error types
[ ] Manual escalation path defined
[ ] Rollback strategy (previous checkpoint)
[ ] Data consistency checks post-recovery
```

---

## 6. Resource Management

### Limits & Quotas
```yaml
per_workflow:
  max_agents: 20
  max_duration: 600s
  max_tokens: 50000
  max_concurrent: 10

per_user:
  max_workflows_per_minute: 5
  max_tokens_per_hour: 100000
  
global:
  max_total_agents: 100
  circuit_breaker_recovery: 60s
```

### Cost Controls
```javascript
// Budget tracking
const BUDGET_LIMITS = {
  "per_workflow": "$0.50",
  "per_user_per_day": "$10",
  "circuit_breaker_at": "$0.80"  // Fail fast if expensive
};

[ ] Cost per workflow calculated
[ ] Budget limits enforced
[ ] Spending alerts configured
[ ] Cost attribution by user/workflow
```

---

## 7. Documentation Requirements

### API Documentation
```markdown
[ ] Input/output schemas defined
[ ] Error codes documented
[ ] Timeout behavior specified
[ ] Rate limits documented
[ ] Example requests/responses
[ ] Authentication requirements
```

### Operational Documentation
```markdown
[ ] Architecture diagram
[ ] Data flow diagram
[ ] Dependency graph
[ ] Monitoring dashboards linked
[ ] On-call runbook
[ ] Incident response procedure
[ ] Post-mortem template
```

---

## 8. Deployment Checklist

### Pre-Deploy
```bash
[ ] Feature flag configured
[ ] Rollback plan documented
[ ] Database migrations tested
[ ] Configuration validated in staging
[ ] Load balancer health checks defined
[ ] TLS certificates valid
```

### Deploy
```bash
[ ] Canary deployment (5% traffic)
[ ] Monitor for 30 minutes
[ ] Gradual rollout (5% → 25% → 50% → 100%)
[ ] Rollback criteria defined (>1% error rate)
```

### Post-Deploy
```bash
[ ] Smoke tests pass
[ ] Metrics within normal range
[ ] No increase in error rate
[ ] Performance acceptable
[ ] Documentation updated
```

---

## 9. Compliance Checklist

### Data Handling
```bash
[ ] PII detection and handling
[ ] Data retention policy enforced
[ ] Encryption at rest and in transit
[ ] Audit logging enabled
[ ] Access controls verified
[ ] GDPR/CCPA compliance (if applicable)
```

### Audit Trail
```json
{
  "required_fields": {
    "who": "user_id or service_account",
    "what": "workflow_id + action",
    "when": "ISO8601 timestamp",
    "where": "system/component",
    "why": "trigger/context",
    "result": "success/failure/details"
  }
}
```

---

## 10. Quick Validation Script

```bash
#!/bin/bash
# validate_production.sh - Run before deploy

echo "=== Production Readiness Check ==="

# Config
[ -f "config/production.yml" ] || { echo "FAIL: Config missing"; exit 1; }

# Tests
pytest tests/ --cov=src/ --cov-report=term-missing || { echo "FAIL: Tests"; exit 1; }

# Security
bandit -r src/ || { echo "FAIL: Security scan"; exit 1; }

# Dependencies
safety check || { echo "FAIL: Dependency vulnerabilities"; exit 1; }

# Performance
locust -f tests/load.py --headless -u 10 -r 2 --run-time 1m || { echo "FAIL: Load test"; exit 1; }

echo "=== All Checks Passed ==="
```

---

## Sign-Off

| Role | Sign-Off | Date |
|------|----------|------|
| Developer | [ ] | |
| Security | [ ] | |
| QA | [ ] | |
| Operations | [ ] | |
| Product | [ ] | |

**Blocked from deployment until all checkboxes complete.**

---

*Part of complete curriculum. See README.md for full documentation.*
