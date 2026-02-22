# Quality Standards for Multi-Agent Systems

**Date:** 2026-02-21 10:20 PM  
**Topic:** Production-ready quality gates and standards

---

## The PACKED Checklist

Production-ready agents must pass all **P**erformance, **A**ccuracy, **C**overage, **K**eep, **E**rror, **D**elivery checks.

### P - Performance

| Metric | Target | Acceptable | Critical |
|--------|--------|------------|----------|
| p50 Latency | < 30s | < 60s | > 60s |
| p95 Latency | < 60s | < 120s | > 120s |
| p99 Latency | < 120s | < 300s | > 300s |
| Throughput | > 10/min | > 5/min | < 5/min |
| Memory | < 1GB | < 2GB | > 2GB |

**Benchmark:**
```javascript
async function benchmark(agent, input, iterations = 100) {
  const times = [];
  for (let i = 0; i < iterations; i++) {
    const start = Date.now();
    await agent.process(input);
    times.push(Date.now() - start);
  }
  
  times.sort((a, b) => a - b);
  return {
    p50: times[Math.floor(times.length * 0.5)],
    p95: times[Math.floor(times.length * 0.95)],
    p99: times[Math.floor(times.length * 0.99)],
    mean: times.reduce((a, b) => a + b) / times.length
  };
}
```

### A - Accuracy

| Test Type | Target | Method |
|-----------|--------|--------|
| Schema compliance | 100% | JSON Schema validation |
| Output format | 100% | Regex validation |
| Reference match | > 90% | Comparison with golden set |
| Human eval | > 80% | Sample review |

**Golden Set Pattern:**
```yaml
# golden-set.yaml
tests:
  - input: "data/case-1.json"
    expected: "expected/case-1-output.json"
    tolerance:
      numeric: 0.01  # 1% tolerance
      string: exact  # or: fuzzy, contains
      
  - input: "data/case-2.json"
    expected: "expected/case-2-output.json"
    validators:
      - type: json_schema
        schema: "schemas/output-v1.json"
      - type: custom
        script: "validate-counts.js"
```

### C - Coverage

| Coverage Type | Minimum | Target |
|---------------|---------|--------|
| Line coverage | 70% | 80% |
| Branch coverage | 60% | 75% |
| Integration paths | 100% | 100% |
| Failure modes | 80% | 100% |

**Test Count Formula:**
```
Total tests = (happy paths × 1) + (error paths × 2) + (edge cases × 3)

Minimum: 5 tests per agent
    - 1 happy path
    - 2 error conditions  
    - 2 edge cases
```

### K - Keep (Observability)

Required metrics:

```yaml
observability:
  logs:
    format: json
    required_fields:
      - timestamp: ISO8601
      - level: INFO|WARN|ERROR
      - agent_id: string
      - correlation_id: string
      - task_id: string
      - message: string
      - duration_ms: number
      
  metrics:
    - name: agent_latency
      type: histogram
      buckets: [100, 500, 1000, 5000, 10000, 30000]
      
    - name: agent_errors
      type: counter
      labels: [error_type, agent_id]
      
    - name: agent_active
      type: gauge
      
  traces:
    enabled: true
    sample_rate: 0.1  # 10% sampling
```

### E - Error Handling

| Error Type | Retry Allowed | Max Retries | Backoff |
|------------|---------------|-------------|---------|
| Timeout | Yes | 3 | 2^n seconds |
| Rate limit | Yes | 5 | 60s fixed |
| Crash | Yes | 2 | 5s |
| Bad input | No | 0 | N/A |
| Permanent | No | 0 | Alert human |

**Error Rate Budget:**
```
Target: < 0.1% error rate
Acceptable: < 1% error rate
Critical: > 1% error rate
```

### D - Delivery (SLA)

| Tier | Availability | Recovery Time |
|------|-------------|---------------|
| P0 (Critical) | 99.9% | 5 min |
| P1 (Important) | 99.5% | 30 min |
| P2 (Standard) | 99% | 4 hours |
| P3 (Batch) | 95% | 24 hours |

---

## Quality Gates

### Gate 1: Lint (30s)

```bash
# Requirements
- No syntax errors
- Conforms to style guide
- Imports are valid
- No secrets in code

# Commands
eslint agents/
prettier --check agents/
git-secrets --scan
```

**Pass:** All checks green.

### Gate 2: Unit (2min)

```bash
# Requirements  
- All unit tests pass
- Coverage > 70%
- No test flakes

# Commands
npm test -- --coverage --threshold=70
```

**Pass:** 100% of tests pass, coverage threshold met.

### Gate 3: Integration (5min)

```bash
# Requirements
- Integration tests pass
- Database migrations run
- External mocks respond

# Commands
npm run test:integration
```

**Pass:** All integration scenarios pass.

### Gate 4: Load (10min)

```bash
# Requirements
- Handles 2x expected load
- p95 latency within SLA
- No memory leaks

# Commands
artillery quick --count 1000 --num 50
```

**Pass:** No errors, latency < SLA.

### Gate 5: Production (Continuous)

```yaml
# Monitoring alerts
alerts:
  - name: "High Error Rate"
    condition: error_rate > 1%
    for: 5m
    action: page_oncall
    
  - name: "Latency Spike"
    condition: p95_latency > SLA * 2
    for: 10m
    action: slack_warning
    
  - name: "Agent Crash"
    condition: exit_code != 0
    for: 0s
    action: restart_agent + log_incident
```

---

## Validation Patterns

### Pattern 1: Input Sanitization

```javascript
function validateInput(input, schema) {
  // 1. Type checking
  if (typeof input !== schema.type) {
    throw new ValidationError(`Expected ${schema.type}, got ${typeof input}`);
  }
  
  // 2. Required fields
  for (const field of schema.required) {
    if (!(field in input)) {
      throw new ValidationError(`Missing required field: ${field}`);
    }
  }
  
  // 3. Range validation
  for (const [field, limits] of Object.entries(schema.ranges || {})) {
    const value = input[field];
    if (limits.min !== undefined && value < limits.min) {
      throw new ValidationError(`${field} below minimum: ${value} < ${limits.min}`);
    }
    if (limits.max !== undefined && value > limits.max) {
      throw new ValidationError(`${field} above maximum: ${value} > ${limits.max}`);
    }
  }
  
  // 4. Size limits
  const size = JSON.stringify(input).length;
  if (size > schema.maxSize) {
    throw new ValidationError(`Input too large: ${size} > ${schema.maxSize}`);
  }
  
  return true;
}

// Usage
const inputSchema = {
  type: "object",
  required: ["data", "format"],
  ranges: { priority: { min: 1, max: 10 } },
  maxSize: 100000  // 100KB
};
```

### Pattern 2: Output Schema Validation

```javascript
const Ajv = require("ajv");
const ajv = new Ajv();

function validateOutput(output, schemaPath) {
  const schema = JSON.parse(fs.readFileSync(schemaPath));
  const validate = ajv.compile(schema);
  
  const valid = validate(output);
  if (!valid) {
    const errors = validate.errors.map(e => 
      `${e.instancePath}: ${e.message}`
    ).join("; ");
    
    throw new OutputValidationError(errors);
  }
  
  return true;
}

// Schema version tracking
const SCHEMA_VERSIONS = {
  "1.0": "schemas/output-v1.json",
  "2.0": "schemas/output-v2.json"
};

function validateWithVersion(output, version) {
  const schemaPath = SCHEMA_VERSIONS[version];
  if (!schemaPath) {
    throw new Error(`Unknown schema version: ${version}`);
  }
  return validateOutput(output, schemaPath);
}
```

### Pattern 3: Idempotency Verification

```javascript
async function verifyIdempotency(agent, input) {
  // Run same task twice
  const result1 = await agent.process(input);
  const result2 = await agent.process(input);
  
  // Results should be identical
  if (JSON.stringify(result1) !== JSON.stringify(result2)) {
    throw new Error("Task is not idempotent");
  }
  
  // Side effects (if any) should also be identical
  const sideEffects1 = await checkSideEffects();
  const sideEffects2 = await checkSideEffects();
  
  if (JSON.stringify(sideEffects1) !== JSON.stringify(sideEffects2)) {
    throw new Error("Side effects not idempotent");
  }
  
  return true;
}
```

### Pattern 4: Determinism Check

```javascript
async function verifyDeterminism(agent, input, runs = 5) {
  const results = [];
  
  for (let i = 0; i < runs; i++) {
    const result = await agent.process(input);
    results.push(JSON.stringify(result));
  }
  
  // All results should be identical
  const allMatch = results.every(r => r === results[0]);
  if (!allMatch) {
    const unique = [...new Set(results)].length;
    throw new Error(`Non-deterministic: ${unique} unique results in ${runs} runs`);
  }
  
  return true;
}
```

---

## Quality Metrics Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ Agent Quality Dashboard                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Performance        Accuracy         Reliability           │
│  ═══════════        ════════         ═══════════           │
│  p50: 24s ✓        100% schema ✓     99.7% uptime ✓       │
│  p95: 45s ✓        94% match ✓      0.02% errors ✓        │
│  p99: 89s ✓        87% human ✓       5min MTTR ✓          │
│                                                             │
│  Coverage           Delivery                                │
│  ════════           ═══════                                 │
│  Line: 78% ✓        P0 SLA: 99.9% ✓                       │
│  Branch: 72% ✓      P1 SLA: 99.8% ✓                       │
│  Paths: 100% ✓                                            │
│                                                             │
│  Last Deploy: 2026-02-21 14:00                            │
│  Quality Score: 94/100                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Pre-Deploy Checklist

```markdown
- [ ] PACKED metrics all green
- [ ] All 5 quality gates passed
- [ ] Golden set tests pass
- [ ] Failure modes tested
- [ ] Rollback plan documented
- [ ] Monitoring configured
- [ ] Runbook updated
- [ ] On-call notified
```

---

**Related:** See `integration-test-examples.md` for testing these standards.
