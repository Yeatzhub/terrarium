# Integration Test Examples for Multi-Agent Systems

**Date:** 2026-02-21 06:20 PM  
**Topic:** Testing agent workflows end-to-end

---

## Test Harness: AgentTestHarness

```javascript
class AgentTestHarness {
  constructor(options = {}) {
    this.runId = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    this.tempDir = `test-temp/${this.runId}`;
    this.timeout = options.timeout || 60000;
    this.agents = [];
    exec(`mkdir -p ${this.tempDir}`);
  }
  
  async spawn(agentId, task, options = {}) {
    const label = `${agentId}-${this.agents.length}`;
    const result = await sessions_spawn({
      agentId,
      task,
      label,
      timeoutSeconds: options.timeout || this.timeout / 1000,
      ...options
    });
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
      await new Promise(r => setTimeout(r, pollInterval));
    }
    throw new Error(`Timeout waiting for ${label}`);
  }
  
  assertFileExists(path) {
    const exists = exec(`test -f ${path} && echo "true" || echo "false"`).trim() === "true";
    if (!exists) throw new Error(`Expected file ${path} to exist`);
  }
  
  cleanup() {
    exec(`rm -rf ${this.tempDir}`);
  }
}
```

---

## Test 1: Pipeline Happy Path

```javascript
async function testPipelineHappyPath() {
  const harness = new AgentTestHarness({ timeout: 30000 });
  
  try {
    // Stage 1: Extract
    const stage1 = await harness.spawn("extractor", {
      input: "data/raw.json",
      output: `${harness.tempDir}/extracted.json`
    });
    await harness.waitFor(stage1.label);
    harness.assertFileExists(`${harness.tempDir}/extracted.json`);
    
    // Stage 2: Transform
    const stage2 = await harness.spawn("transformer", {
      input: `${harness.tempDir}/extracted.json`,
      output: `${harness.tempDir}/transformed.json`
    });
    await harness.waitFor(stage2.label);
    harness.assertFileExists(`${harness.tempDir}/transformed.json`);
    
    // Stage 3: Load
    const stage3 = await harness.spawn("loader", {
      input: `${harness.tempDir}/transformed.json`,
      destination: "test-db"
    });
    await harness.waitFor(stage3.label);
    
    console.log("✓ Pipeline passed");
  } finally {
    harness.cleanup();
  }
}
```

---

## Test 2: Parallel Fan-Out

```javascript
async function testFanOutGather() {
  const harness = new AgentTestHarness({ timeout: 60000 });
  const chunks = 5;
  
  try {
    // Spawn 5 parallel workers
    const workers = [];
    for (let i = 0; i < chunks; i++) {
      const worker = await harness.spawn("processor", {
        chunkId: i,
        input: `data/chunk-${i}.json`,
        output: `${harness.tempDir}/result-${i}.json`
      });
      workers.push(worker);
    }
    
    // Wait for all
    await Promise.all(workers.map(w => harness.waitFor(w.label, { timeout: 45000 })));
    
    // Verify all outputs exist
    for (let i = 0; i < chunks; i++) {
      harness.assertFileExists(`${harness.tempDir}/result-${i}.json`);
    }
    
    // Aggregate
    const agg = await harness.spawn("aggregator", {
      inputs: Array.from({ length: chunks }, (_, i) => `${harness.tempDir}/result-${i}.json`),
      output: `${harness.tempDir}/final.json`
    });
    await harness.waitFor(agg.label);
    
    console.log("✓ Fan-out gather passed");
  } finally {
    harness.cleanup();
  }
}
```

---

## Test 3: Error Recovery

```javascript
async function testErrorRecovery() {
  const harness = new AgentTestHarness({ timeout: 45000 });
  
  try {
    // Retry on transient failure
    const flaky = await harness.spawn("flaky-worker", {
      failCount: 2,  // Fails twice then succeeds
      input: "data/test.json",
      output: `${harness.tempDir}/retry-result.json`,
      maxRetries: 3
    });
    await harness.waitFor(flaky.label);
    console.log("✓ Retry succeeded");
    
    // Circuit breaker on permanent failure
    const bad = await harness.spawn("always-fails", {
      input: "data/invalid.json",
      maxRetries: 2
    });
    try {
      await harness.waitFor(bad.label, { timeout: 15000 });
      throw new Error("Should have failed");
    } catch (e) {
      if (e.message.includes("Should have failed")) throw e;
      console.log("✓ Permanent failure handled");
    }
    
  } finally {
    harness.cleanup();
  }
}
```

---

## Test 4: Timeout Handling

```javascript
async function testTimeoutHandling() {
  const harness = new AgentTestHarness();
  
  try {
    const slowAgent = await harness.spawn("slow-processor", {
      input: "data/test.json",
      output: `${harness.tempDir}/output.json`,
      delay: 30000
    });
    
    try {
      await harness.waitFor(slowAgent.label, { timeout: 5000 });
      throw new Error("Expected timeout");
    } catch (e) {
      if (!e.message.includes("Timeout")) throw e;
      console.log("✓ Timeout correctly triggered");
    }
    
  } finally {
    harness.cleanup();
  }
}
```

---

## Test 5: Resource Contention

```javascript
async function testResourceContention() {
  const harness = new AgentTestHarness({ timeout: 60000 });
  const counterFile = `${harness.tempDir}/counter.json`;
  write(counterFile, JSON.stringify({ count: 0 }));
  
  try {
    // 10 agents increment shared counter
    const agents = [];
    for (let i = 0; i < 10; i++) {
      const agent = await harness.spawn("incrementer", {
        resource: counterFile,
        incrementBy: 1
      });
      agents.push(agent);
    }
    
    await Promise.all(agents.map(a => harness.waitFor(a.label)));
    
    // Verify race condition handling
    const final = JSON.parse(read(counterFile));
    if (final.count !== 10) {
      throw new Error(`Race condition: expected 10, got ${final.count}`);
    }
    console.log("✓ Resource contention handled");
    
  } finally {
    harness.cleanup();
  }
}
```

---

## Mock Pattern

```javascript
// Agent checks TEST_MODE for canned response
async function agentTask({ input, canned }) {
  if (process.env.TEST_MODE === "true") {
    return { output: canned, tokensUsed: 0 };
  }
  return await callLLM(input);
}

// Usage
process.env.TEST_MODE = "true";
const result = await agentTask({ input: "x", canned: { result: "mock" } });
```

---

## CI/CD Integration

```yaml
name: Agent Tests
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup
        run: openclaw gateway start
      - name: Test
        run: node test/run-all.js
```

---

## Failure Mode Matrix

| Component | Success | Failure 1 | Failure 2 | Failure 3 |
|-----------|---------|-----------|-----------|-----------|
| Extractor | JSON output | Empty file | Invalid JSON | Timeout |
| Transformer | Valid schema | Schema mismatch | Missing fields | Crash |
| Loader | DB updated | Connection fail | Constraint error | Rollback fail |

---

**Related:** See `multi-agent-coordination.md` for patterns tested here.
