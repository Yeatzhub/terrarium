# Integration Test Examples for Multi-Agent Systems

**Date:** 2026-02-21 12:20 PM  
**Topic:** Practical integration testing patterns for agent workflows

---

## Test Harness: AgentTestHarness

```javascript
class AgentTestHarness {
  constructor(options = {}) {
    this.runId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    this.tempDir = `test-temp/${this.runId}`;
    this.timeout = options.timeout || 60000;
    this.agents = [];
    
    // Setup
    exec(`mkdir -p ${this.tempDir}`);
  }
  
  async spawn(agentId, task, options = {}) {
    const label = `${agentId}-${this.agents.length}`;
    const spawnOptions = {
      agentId,
      task,
      label,
      timeoutSeconds: options.timeout || this.timeout / 1000,
      ...options
    };
    
    const result = await sessions_spawn(spawnOptions);
    this.agents.push({ label, agentId, startTime: Date.now() });
    return { label, ...result };
  }
  
  async waitFor(label, options = {}) {
    const timeout = options.timeout || this.timeout;
    const pollInterval = options.pollInterval || 1000;
    const start = Date.now();
    
    while (Date.now() - start < timeout) {
      const status = await subagents({ action: "list", recentMinutes: 10 });
      const agent = status.find(a => a.label === label);
      
      if (!agent) continue;
      if (agent.status === "complete") return agent;
      if (agent.status === "error") throw new Error(`Agent ${label} failed`);
      
      await sleep(pollInterval);
    }
    
    throw new Error(`Timeout waiting for ${label}`);
  }
  
  async waitForAll(options = {}) {
    return Promise.all(
      this.agents.map(a => this.waitFor(a.label, options))
    );
  }
  
  assertFileExists(path) {
    const exists = exec(`test -f ${path} && echo "true" || echo "false"`).trim() === "true";
    if (!exists) throw new Error(`Expected file ${path} to exist`);
  }
  
  assertOutputMatches(path, expected, options = {}) {
    const content = read(path);
    if (options.json) {
      const actual = JSON.parse(content);
      const exp = typeof expected === "string" ? JSON.parse(expected) : expected;
      if (JSON.stringify(actual) !== JSON.stringify(exp)) {
        throw new Error(`JSON mismatch:\nExpected: ${JSON.stringify(exp)}\nActual: ${JSON.stringify(actual)}`);
      }
    }
  }
  
  assertNoErrors(logPath = "logs/*.log") {
    const logs = exec(`grep -i "error\\|exception\\|fatal" ${logPath} 2>/dev/null || true`);
    if (logs.trim()) {
      throw new Error(`Found errors in logs:\n${logs}`);
    }
  }
  
  cleanup() {
    exec(`rm -rf ${this.tempDir}`);
  }
}

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}
```

---

## Example 1: Happy Path Pipeline Test

```javascript
// test-pipeline-happy-path.js
async function testPipelineHappyPath() {
  const harness = new AgentTestHarness({ timeout: 30000 });
  
  try {
    // Stage 1: Extract data
    const stage1 = await harness.spawn("extractor", {
      input: "data/raw.json",
      output: `${harness.tempDir}/extracted.json`
    });
    
    await harness.waitFor(stage1.label);
    harness.assertFileExists(`${harness.tempDir}/extracted.json`);
    
    // Stage 2: Transform
    const stage2 = await harness.spawn("transformer", {
      input: `${harness.tempDir}/extracted.json`,
      output: `${harness.tempDir}/transformed.json`,
      schema: "v2"
    });
    
    await harness.waitFor(stage2.label);
    harness.assertFileExists(`${harness.tempDir}/transformed.json`);
    
    // Stage 3: Load
    const stage3 = await harness.spawn("loader", {
      input: `${harness.tempDir}/transformed.json`,
      destination: "test-db"
    });
    
    await harness.waitFor(stage3.label);
    
    // Validate final state
    const result = exec("test-db query 'SELECT COUNT(*) FROM imported'");
    console.log(`✓ Pipeline completed: ${result} rows imported`);
    
  } finally {
    harness.cleanup();
  }
}

// Run
await testPipelineHappyPath();
```

---

## Example 2: Fan-Out Gather Test

```javascript
// test-fanout-gather.js
async function testFanOutGather() {
  const harness = new AgentTestHarness({ timeout: 60000 });
  const chunkCount = 5;
  
  try {
    // Spawn parallel workers
    const workers = [];
    for (let i = 0; i < chunkCount; i++) {
      const worker = await harness.spawn("processor", {
        chunkId: i,
        input: `data/chunk-${i}.json`,
        output: `${harness.tempDir}/result-${i}.json`
      });
      workers.push(worker);
    }
    
    // Wait for all workers
    await Promise.all(
      workers.map(w => harness.waitFor(w.label, { timeout: 45000 }))
    );
    
    // Verify all outputs exist
    for (let i = 0; i < chunkCount; i++) {
      harness.assertFileExists(`${harness.tempDir}/result-${i}.json`);
    }
    
    // Spawn aggregator
    const aggregator = await harness.spawn("aggregator", {
      inputs: Array.from({ length: chunkCount }, (_, i) => 
        `${harness.tempDir}/result-${i}.json`
      ),
      output: `${harness.tempDir}/final.json`
    });
    
    await harness.waitFor(aggregator.label);
    
    // Validate aggregation
    const final = JSON.parse(read(`${harness.tempDir}/final.json`));
    if (final.itemCount !== chunkCount * 100) {
      throw new Error(`Expected ${chunkCount * 100} items, got ${final.itemCount}`);
    }
    
    console.log("✓ Fan-out gather completed successfully");
    
  } finally {
    harness.cleanup();
  }
}

await testFanOutGather();
```

---

## Example 3: Error Recovery Test

```javascript
// test-error-recovery.js
async function testErrorRecovery() {
  const harness = new AgentTestHarness({ timeout: 45000 });
  
  try {
    // Test 1: Retry on transient failure
    let attempt = 0;
    const flakyAgent = await harness.spawn("flaky-worker", {
      failFirst: 2,  // Fails first 2 attempts
      input: "data/test.json",
      output: `${harness.tempDir}/retry-result.json`,
      maxRetries: 3
    });
    
    const result = await harness.waitFor(flakyAgent.label);
    console.log("✓ Retry succeeded after transient failures");
    
    // Test 2: Circuit breaker on permanent failure
    const badAgent = await harness.spawn("always-fails", {
      input: "data/invalid.json",
      output: `${harness.tempDir}/fail-result.json`,
      maxRetries: 2
    });
    
    try {
      await harness.waitFor(badAgent.label, { timeout: 15000 });
      throw new Error("Expected agent to fail");
    } catch (e) {
      if (e.message.includes("Expected agent to fail")) throw e;
      console.log("✓ Permanent failure correctly propagated");
    }
    
    // Test 3: Graceful degradation
    const degraded = await harness.spawn("processor", {
      input: "data/large-file.json",
      output: `${harness.tempDir}/degraded.json`,
      fallbackMode: true  // Uses lighter model if primary fails
    });
    
    await harness.waitFor(degraded.label);
    harness.assertFileExists(`${harness.tempDir}/degraded.json`);
    console.log("✓ Graceful degradation succeeded");
    
  } finally {
    harness.cleanup();
  }
}

await testErrorRecovery();
```

---

## Example 4: Timeout Handling Test

```javascript
// test-timeout-handling.js
async function testTimeoutHandling() {
  const harness = new AgentTestHarness();
  
  try {
    // Test: Agent that exceeds timeout
    const slowAgent = await harness.spawn("slow-processor", {
      input: "data/test.json",
      output: `${harness.tempDir}/slow-result.json`,
      artificialDelay: 30000  // Takes 30s
    });
    
    try {
      // Set short timeout to trigger failure
      await harness.waitFor(slowAgent.label, { timeout: 5000 });
      throw new Error("Expected timeout");
    } catch (e) {
      if (!e.message.includes("Timeout")) throw e;
      console.log("✓ Timeout correctly triggered");
    }
    
    // Test: Cleanup after timeout
    harness.assertNoErrors(`${harness.tempDir}/*.log`);
    
    // Test: Partial results saved on timeout
    const partial = `${harness.tempDir}/slow-result.partial`;
    if (exec(`test -f ${partial} && echo "true" || echo "false"`).trim() === "true") {
      console.log("✓ Partial results preserved on timeout");
    }
    
  } finally {
    harness.cleanup();
  }
}

await testTimeoutHandling();
```

---

## Example 5: Resource Contention Test

```javascript
// test-resource-contention.js
async function testResourceContention() {
  const harness = new AgentTestHarness({ timeout: 60000 });
  const resourceFile = `${harness.tempDir}/shared-counter.json`;
  
  // Initialize shared resource
  write(resourceFile, JSON.stringify({ count: 0 }));
  
  try {
    // Spawn 10 agents all trying to increment counter
    const agents = [];
    for (let i = 0; i < 10; i++) {
      const agent = await harness.spawn("incrementer", {
        resource: resourceFile,
        incrementBy: 1,
        delay: Math.random() * 100  // Random delay to increase contention
      });
      agents.push(agent);
    }
    
    // Wait for all to complete
    await Promise.all(agents.map(a => harness.waitFor(a.label)));
    
    // Verify final count is exactly 10 (no race conditions)
    const final = JSON.parse(read(resourceFile));
    if (final.count !== 10) {
      throw new Error(`Race condition detected: expected 10, got ${final.count}`);
    }
    
    console.log("✓ Resource contention handled correctly");
    
  } finally {
    harness.cleanup();
  }
}

await testResourceContention();
```

---

## Mock Agent Pattern

```javascript
// test-doubles/mock-classifier.js
// Set TEST_MODE=true to use canned responses instead of LLM

async function mockAgent({ input, canned }) {
  if (process.env.TEST_MODE === "true") {
    // Return predetermined output
    return {
      output: canned || { label: "test", confidence: 0.99 },
      latency: 10,
      tokensUsed: 0
    };
  }
  
  // Normal LLM call
  return await callLLM(input);
}

// Usage in test
process.env.TEST_MODE = "true";
const result = await mockAgent({
  input: "test data",
  canned: { label: "positive", confidence: 0.95 }
});
```

---

## Schema Validation Helper

```javascript
// helpers/schema-validator.js
const Ajv = require("ajv");
const ajv = new Ajv();

function assertValid(output, schema, path) {
  const validate = ajv.compile(schema);
  const valid = validate(output);
  
  if (!valid) {
    throw new Error(
      `Schema validation failed for ${path}:\n` +
      validate.errors.map(e => `  - ${e.instancePath}: ${e.message}`).join("\n")
    );
  }
}

// Example schema for handoff files
const HandoffSchema = {
  type: "object",
  required: ["from", "output", "status"],
  properties: {
    from: { type: "string" },
    output: { type: "string" },
    status: { enum: ["complete", "partial", "blocked"] },
    timestamp: { type: "string", format: "date-time" }
  }
};

harness.assertOutputMatches = function(path, schema) {
  const content = JSON.parse(read(path));
  assertValid(content, schema, path);
};
```

---

## CI/CD Integration

```yaml
# .github/workflows/agent-tests.yml
name: Agent Integration Tests

on:
  push:
    paths:
      - "agents/**"
      - "test/**"

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test: [pipeline, fanout, error-recovery, timeout, contention]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup OpenClaw
        run: |
          npm install -g openclaw-cli
          openclaw gateway start
          
      - name: Run ${{ matrix.test }} tests
        run: |
          node test/test-${{ matrix.test }}.js
          
      - name: Upload test artifacts
        if: failure()
        uses: actions/upload-artifact@v3
        with:
          name: test-logs-${{ matrix.test }}
          path: test-temp/**/*.log
```

---

## Golden Path + Failure Mode Matrix

| Component | Happy Path | Failure Mode 1 | Failure Mode 2 | Failure Mode 3 |
|-----------|-----------|----------------|----------------|----------------|
| Extractor | Returns JSON | Empty file | Invalid JSON | Timeout |
| Transformer | Schema v2 output | Schema mismatch | Missing fields | Type error |
| Loader | DB updated | Connection fail | Constraint violation | Rollback fail |
| Aggregator | Merged result | Missing inputs | Partial data | Disk full |

**Test each cell independently.**

---

**Related:** See `multi-agent-coordination.md` for patterns these tests validate.
