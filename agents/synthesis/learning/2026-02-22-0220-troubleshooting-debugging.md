# Multi-Agent Troubleshooting & Debugging Guide

**Date:** 2026-02-22 02:20 AM  
**Topic:** Diagnosing and fixing common multi-agent issues

---

## Symptom → diagnosis → fix Quick Reference

| Symptom | Likely Cause | Fix |
|---------|--------------|-----|
| Agent hangs forever | Deadlock or missing dependency | Check dependency graph, add timeout |
| Results inconsistent | Non-deterministic output | Add seed, fix temperature |
| Memory grows unbounded | Leak in state accumulation | Clear buffers, use bounded queues |
| Timeout cascade | One slow agent blocks all | Add circuit breaker, parallel timeout |
| Wrong output format | Schema drift | Pin schema version, validate |
| Race conditions | Shared mutable state | Use immutable data, locks |
| Circular dependencies | Bad task graph | Detect cycles, break with checkpoint |
| Rate limit errors | Too many parallel calls | Add backoff, reduce concurrency |

---

## Diagnostic Commands

### Check Agent Status

```bash
# List all running agents
openclaw agents list --status running

# Check specific agent logs
tail -f logs/agent-{id}.log

# Find errors in last hour
grep -i "error\|exception\|fail" logs/*.log | grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')"

# Memory usage by agent
ps aux | grep agent | awk '{print $1, $6/1024 "MB", $11}'
```

### Check Dependency Graph

```bash
# Visualize dependencies
openclaw workflow graph workflow.yaml --output deps.png

# Find cycles
openclaw workflow validate workflow.yaml --check-cycles

# List blocked tasks
openclaw tasks list --status blocked
```

### Check Resource Usage

```bash
# CPU usage
top -b -n 1 | grep agent

# Network connections
netstat -an | grep ESTABLISHED | wc -l

# Open files
lsof -p $(pgrep agent) | wc -l
```

---

## Problem 1: Agent Hangs

### Symptoms
- Agent status shows "running" indefinitely
- No output file produced
- No error in logs

### Diagnosis

```javascript
async function diagnoseHang(agentId, timeout = 60000) {
  const checks = [];
  
  // 1. Check if process is alive
  const pid = await getAgentPid(agentId);
  checks.push({ 
    test: 'process_alive', 
    result: pid ? 'PASS' : 'FAIL',
    detail: pid ? `PID ${pid}` : 'No process found'
  });
  
  // 2. Check for last log entry
  const lastLog = await getLastLogEntry(agentId);
  const logAge = Date.now() - lastLog.timestamp;
  checks.push({
    test: 'recent_logs',
    result: logAge < 30000 ? 'PASS' : 'WARN',
    detail: `Last log ${logAge}ms ago`
  });
  
  // 3. Check for waiting on resource
  const locks = await getHeldLocks(agentId);
  const waiting = await getWaitingFor(agentId);
  checks.push({
    test: 'resource_wait',
    result: waiting.length === 0 ? 'PASS' : 'FAIL',
    detail: waiting.length > 0 ? `Waiting for: ${waiting.join(', ')}` : 'No waits'
  });
  
  // 4. Check input file exists
  const inputFile = await getInputFile(agentId);
  checks.push({
    test: 'input_exists',
    result: inputFile.exists ? 'PASS' : 'FAIL',
    detail: inputFile.path
  });
  
  // 5. Check disk space
  const disk = await checkDiskSpace();
  checks.push({
    test: 'disk_space',
    result: disk.availableMB > 100 ? 'PASS' : 'FAIL',
    detail: `${disk.availableMB}MB available`
  });
  
  return checks;
}
```

### Fixes

| Diagnosis | Fix |
|-----------|-----|
| Process dead | Restart: `openclaw agent restart {id}` |
| No recent logs | Add heartbeat logging at 30s intervals |
| Waiting for lock | Kill lock holder or add lock timeout |
| Input missing | Regenerate input or skip task |
| Disk full | Clean temp files: `rm -rf tmp/*` |

---

## Problem 2: Inconsistent Results

### Symptoms
- Same input produces different outputs
- Tests flaky, pass sometimes fail others
- Output varies between runs

### Diagnosis

```javascript
async function diagnoseInconsistency(agentId, input, runs = 5) {
  const results = [];
  
  for (let i = 0; i < runs; i++) {
    const result = await runAgent(agentId, input);
    results.push({
      run: i,
      output: JSON.stringify(result),
      hash: hashResult(result)
    });
  }
  
  const uniqueHashes = new Set(results.map(r => r.hash));
  
  if (uniqueHashes.size === 1) {
    console.log('✓ Deterministic: all runs identical');
  } else {
    console.log(`✗ Non-deterministic: ${uniqueHashes.size} unique results`);
    
    // Find what varies
    const keys = new Set();
    const parsed = results.map(r => JSON.parse(r.output));
    for (const obj of parsed) {
      keys.add(...Object.keys(obj));
    }
    
    for (const key of keys) {
      const values = new Set(parsed.map(o => JSON.stringify(o[key])));
      if (values.size > 1) {
        console.log(`  Varying key: ${key}`);
        values.forEach(v => console.log(`    - ${v}`));
      }
    }
  }
  
  return { uniqueHashes: uniqueHashes.size, results };
}
```

### Fixes

```javascript
// Fix 1: Set random seed
const agent = new Agent({
  seed: 42,  // Fixed seed
  temperature: 0  // Deterministic
});

// Fix 2: Sort outputs
function deterministicSort(results) {
  return results.sort((a, b) => a.id.localeCompare(b.id));
}

// Fix 3: Normalize timestamps
function normalizeOutput(output) {
  return {
    ...output,
    timestamp: '1970-01-01T00:00:00Z',  // Fixed for comparison
    generated_at: null  // Remove unstable field
  };
}

// Fix 4: Pin model version
const agent = new Agent({
  model: 'model-v1.2.3',  // Specific version, not 'latest'
  modelParams: {
    temperature: 0,
    top_p: 1,
    seed: 12345
  }
});
```

---

## Problem 3: Memory Leaks

### Symptoms
- Memory grows over time
- Agent slows down after many runs
- Eventually OOM kills

### Diagnosis

```javascript
async function diagnoseLeak(agentId, iterations = 100) {
  const measurements = [];
  
  for (let i = 0; i < iterations; i++) {
    await runAgent(agentId, sampleInput);
    
    const mem = process.memoryUsage();
    measurements.push({
      iteration: i,
      heapUsed: mem.heapUsed,
      external: mem.external,
      arrayBuffers: mem.arrayBuffers
    });
    
    // Force GC every 10 iterations (if --expose-gc flag set)
    if (i % 10 === 9 && global.gc) {
      global.gc();
    }
  }
  
  // Calculate growth rate
  const first = measurements[0].heapUsed;
  const last = measurements[measurements.length - 1].heapUsed;
  const growth = (last - first) / iterations;
  
  if (growth > 10000) {  // >10KB per iteration
    console.log(`✗ Memory leak detected: ${growth} bytes/iteration`);
  } else {
    console.log(`✓ No leak detected: ${growth} bytes/iteration`);
  }
  
  return { growth, measurements };
}
```

### Fixes

```javascript
// Fix 1: Clear buffers
class Agent {
  constructor() {
    this.buffer = [];
  }
  
  process(input) {
    this.buffer = [];  // Clear before new work
    // ... process
  }
}

// Fix 2: Bounded queues
const queue = [];
const MAX_QUEUE = 100;

function enqueue(item) {
  if (queue.length >= MAX_QUEUE) {
    queue.shift();  // Remove oldest
  }
  queue.push(item);
}

// Fix 3: Weak references for caches
const cache = new WeakMap();  // Allows GC when keys are unreachable

// Fix 4: Explicit cleanup
async function processBatch(items) {
  for (const item of items) {
    await processItem(item);
    cleanupTempFiles(item.id);  // Clean immediately
  }
}

// Fix 5: Pool resources
const resourcePool = new ResourcePool({ max: 10 });

async function process(input) {
  const resource = await resourcePool.acquire();
  try {
    return await resource.process(input);
  } finally {
    resourcePool.release(resource);  // Always release
  }
}
```

---

## Problem 4: Timeout Cascades

### Symptoms
- One slow task causes timeout in dependents
- Error messages about missing inputs
- Many agents fail simultaneously

### Diagnosis

```javascript
async function diagnoseTimeoutCascasde(workflowId) {
  const tasks = await getWorkflowTasks(workflowId);
  const issues = [];
  
  for (const task of tasks) {
    const deps = task.dependencies || [];
    
    for (const depId of deps) {
      const dep = tasks.find(t => t.id === depId);
      
      if (dep && dep.timeout && task.timeout) {
        const availableTime = task.timeout - dep.estimatedDuration;
        
        if (availableTime < 0) {
          issues.push({
            task: task.id,
            issue: 'INSUFFICIENT_TIME',
            detail: `Needs ${dep.estimatedDuration}s but only ${task.timeout}s after dependency`
          });
        } else if (availableTime < dep.estimatedDuration * 0.2) {
          issues.push({
            task: task.id,
            issue: 'TIGHT_DEADLINE',
            detail: `Only ${availableTime}s buffer for ${dep.estimatedDuration}s dependency`
          });
        }
      }
    }
  }
  
  return issues;
}
```

### Fixes

```javascript
// Fix 1: Propagate timeouts
function calculateTaskTimeout(task, upstreamTime = 0) {
  const taskTime = task.estimatedDuration || 60;
  const buffer = taskTime * 0.5;  // 50% buffer
  
  return {
    ...task,
    timeout: upstreamTime + taskTime + buffer,
    cumulativeTime: upstreamTime + taskTime
  };
}

// Fix 2: Independent timeouts
// Don't inherit from parent; each agent has its own
const task = {
  id: 'transform',
  timeout: 300,  // Fixed 5 min, regardless of upstream
  independentTimeout: true
};

// Fix 3: Circuit breaker on dependency wait
async function waitForDependency(depId, timeout = 30000) {
  const breaker = new CircuitBreaker({
    threshold: 3,
    timeout: timeout
  });
  
  return breaker.call(async () => {
    const result = await checkDependency(depId);
    if (!result.ready) {
      throw new Error('Dependency not ready');
    }
    return result;
  });
}

// Fix 4: Partial results on timeout
async function processWithTimeout(input, timeout) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  
  try {
    const result = await process(input, { signal: controller.signal });
    return { status: 'complete', result };
  } catch (e) {
    if (e.name === 'AbortError') {
      const partial = await getPartialResults();
      return { status: 'partial', result: partial };
    }
    throw e;
  } finally {
    clearTimeout(timer);
  }
}
```

---

## Problem 5: Race Conditions

### Symptoms
- Output varies based on timing
- Works in serial but fails in parallel
- Intermittent data corruption

### Diagnosis

```javascript
async function diagnoseRaceCondition(agentId, parallelism = 10) {
  const sharedResource = { counter: 0 };
  const results = [];
  
  // Run multiple instances in parallel
  await Promise.all(Array(parallelism).fill(null).map(async (_, i) => {
    const before = sharedResource.counter;
    await new Promise(r => setTimeout(r, Math.random() * 100));  // Random delay
    sharedResource.counter++;  // Race condition!
    const after = sharedResource.counter;
    results.push({ id: i, before, after });
  }));
  
  // Expected: counter = parallelism
  const expected = parallelism;
  const actual = sharedResource.counter;
  
  if (actual !== expected) {
    console.log(`✗ Race condition detected: expected ${expected}, got ${actual}`);
    console.log('Lost updates:', parallelism - actual);
    return { hasRace: true, actual, expected };
  }
  
  return { hasRace: false };
}
```

### Fixes

```javascript
// Fix 1: Mutex/locks
import { Mutex } from 'async-mutex';

const mutex = new Mutex();

async function safeIncrement(sharedResource) {
  const release = await mutex.acquire();
  try {
    sharedResource.counter++;
  } finally {
    release();
  }
}

// Fix 2: Atomic operations
const counter = new AtomicCounter();
counter.increment();  // Thread-safe

// Fix 3: Actor model (single writer)
class SharedStateActor {
  constructor() {
    this.state = { counter: 0 };
    this.queue = [];
    this.processQueue();
  }
  
  async processQueue() {
    while (true) {
      const { op, resolve } = await this.queue.shift();
      if (op === 'increment') {
        this.state.counter++;
        resolve(this.state.counter);
      }
    }
  }
  
  increment() {
    return new Promise(resolve => {
      this.queue.push({ op: 'increment', resolve });
    });
  }
}

// Fix 4: Partition data
function partitionByKey(items, keyFn) {
  const partitions = new Map();
  
  for (const item of items) {
    const key = keyFn(item);
    if (!partitions.has(key)) {
      partitions.set(key, []);
    }
    partitions.get(key).push(item);
  }
  
  // Each partition processed independently
  return partitions;
}
```

---

## Debugging Workflow

```
1. REPRODUCE
   - Isolate the failing agent
   - Create minimal test case
   - Document exact steps

2. OBSERVE
   - Check logs at crash/hang point
   - Monitor resource usage
   - Capture exact state

3. HYPOTHESIZE
   - Map symptom to known pattern
   - Check similar issues
   - Review recent changes

4. EXPERIMENT
   - Apply fix
   - Run diagnostic tests
   - Verify improvement

5. DOCUMENT
   - Root cause
   - Fix applied
   - Prevention measure
```

---

## Log Analysis Cheat Sheet

```bash
# Find the error that started it all
grep -i "error" logs/*.log | head -1

# Count errors by type
grep -i "error" logs/*.log | sed 's/.*error: //' | sort | uniq -c | sort -rn

# Timeline of events
grep -E "error|warn|fail" logs/*.log | awk '{print $1, $2, $NF}' | sort

# Memory over time
grep "heap" logs/*.log | awk '{print $1, $2, $4}' | tr -d 'MB' | sort -k3 -n

# Request duration distribution
grep "duration" logs/*.log | sed 's/.*duration_ms: //' | sort -n | awk '{sum+=$1; count++} END {print "avg:", sum/count, "total:", count}'
```

---

## Quick Fixes Reference

| Issue | Quick Fix Command |
|-------|-------------------|
| Agent stuck | `openclaw agent kill {id} && openclaw agent restart {id}` |
| Clear all temp | `rm -rf tmp/* cache/* logs/*.log` |
| Reset locks | `redis-cli DEL "lock:*"` |
| Force GC | `kill -SIGUSR2 {pid}` (Node.js) |
| Check deps | `openclaw workflow validate workflow.yaml` |
| View graph | `openclaw workflow graph workflow.yaml | open -` |

---

**Related:** See `quality-standards.md` for monitoring setup; `dependency-management.md` for cycle detection.