# Workflow Optimization Patterns: Real-World Recipes

**Date:** 2026-02-22 12:20 AM  
**Topic:** Practical optimization patterns with before/after examples

---

## The Optimization Loop

```
Measure → Identify bottleneck → Apply pattern → Verify improvement → Repeat
```

**Never optimize without measuring first.**

---

## Pattern 1: Sequential to Parallel

### Before (90s total)

```javascript
// Sequential execution
const extracted = await extractData(input);    // 30s
const cleaned = await cleanData(extracted);    // 20s
const analyzed = await analyzeData(cleaned);   // 40s
return analyzed;
```

### After (45s total)

```javascript
// Parallel execution where possible
const [raw1, raw2, raw3] = splitInput(input);

const [extracted1, extracted2, extracted3] = await Promise.all([
  extractData(raw1),  // Parallel
  extractData(raw2),
  extractData(raw3)
]);

const cleaned = await cleanData(merge(extracted1, extracted2, extracted3));
const analyzed = await analyzeData(cleaned);
return analyzed;
```

**Speedup:** 2x | **Pattern:** Data partitioning + parallel map

---

## Pattern 2: Caching Hot Paths

### Before (120s, repeated calls)

```javascript
async function enrichUser(userId) {
  const profile = await fetchProfile(userId);      // 2s
  const preferences = await fetchPreferences(userId); // 1s
  const history = await fetchHistory(userId);      // 3s
  return combine(profile, preferences, history);
}

// Called 100 times with same userId = 600s total
```

### After (12s for 100 calls)

```javascript
const cache = new Map();

async function enrichUser(userId) {
  if (cache.has(userId)) {
    return cache.get(userId);  // <1ms
  }
  
  const [profile, preferences, history] = await Promise.all([
    fetchProfile(userId),
    fetchPreferences(userId),
    fetchHistory(userId)
  ]);
  
  const result = combine(profile, preferences, history);
  cache.set(userId, result);
  
  // Invalidate after 5 minutes
  setTimeout(() => cache.delete(userId), 300000);
  
  return result;
}
```

**Speedup:** 50x | **Pattern:** Memoization with TTL

---

## Pattern 3: Speculative Execution

### Before (60s worst case)

```javascript
async function classify(input) {
  // Try fast heuristic first
  const fast = await heuristicClassify(input);  // 5s
  if (fast.confidence > 0.9) return fast;
  
  // Fall back to LLM
  return await llmClassify(input);  // 55s
}
```

### After (30s expected)

```javascript
async function classify(input) {
  // Start both approaches simultaneously
  const [fast, slow] = await Promise.allSettled([
    heuristicClassify(input),  // 5s
    llmClassify(input)         // 30s
  ]);
  
  // Use fast if confident, otherwise slow
  if (fast.status === 'fulfilled' && fast.value.confidence > 0.9) {
    return fast.value;
  }
  
  return slow.status === 'fulfilled' ? slow.value : fallback(input);
}
```

**Speedup:** 2x | **Pattern:** Race multiple strategies

---

## Pattern 4: Streaming Results

### Before (90s, user waits)

```javascript
async function generateReport(data) {
  const section1 = await generateSection(data, 1);  // 30s
  const section2 = await generateSection(data, 2);  // 30s
  const section3 = await generateSection(data, 3);  // 30s
  
  return {
    section1,
    section2,
    section3
  };
}
```

### After (15s to first result, progressive)

```javascript
async function* generateReport(data) {
  // Yield sections as they complete
  yield { type: 'section', id: 1, data: await generateSection(data, 1) };
  yield { type: 'section', id: 2, data: await generateSection(data, 2) };
  yield { type: 'section', id: 3, data: await generateSection(data, 3) };
  yield { type: 'complete' };
}

// Consumer
for await (const chunk of generateReport(data)) {
  if (chunk.type === 'section') {
    displaySection(chunk.id, chunk.data);  // Show immediately
  }
}
```

**Speedup:** 6x to first meaningful result | **Pattern:** Generator-based streaming

---

## Pattern 5: Batching Requests

### Before (50s, 100 individual calls)

```javascript
for (const item of items) {
  await processItem(item);  // 0.5s each × 100 = 50s
}
```

### After (5s, 10 batched calls)

```javascript
const BATCH_SIZE = 10;

for (let i = 0; i < items.length; i += BATCH_SIZE) {
  const batch = items.slice(i, i + BATCH_SIZE);
  await Promise.all(batch.map(item => processItem(item)));  // 0.5s per batch
}
```

**Speedup:** 10x | **Pattern:** Batching with controlled parallelism

---

## Pattern 6: Early Termination

### Before (60s always)

```javascript
async function findBestSolution(candidates) {
  const scores = [];
  for (const candidate of candidates) {
    const score = await evaluate(candidate);  // 1s each, 60 candidates
    scores.push({ candidate, score });
  }
  return scores.sort((a, b) => b.score - a.score)[0];
}
```

### After (15s average)

```javascript
async function findBestSolution(candidates) {
  let best = { score: -Infinity };
  
  for (const candidate of candidates) {
    const score = await evaluate(candidate);
    
    if (score > best.score) {
      best = { candidate, score };
    }
    
    // Early termination: if we hit perfection, stop
    if (score >= 0.99) {
      console.log(`Found perfect solution after ${candidates.indexOf(candidate) + 1} evaluations`);
      return best;
    }
    
    // If current best is insurmountable, stop
    const remaining = candidates.length - candidates.indexOf(candidate) - 1;
    if (best.score > 0.95 && remaining > 10) {
      console.log(`Good enough solution found, skipping ${remaining} candidates`);
      return best;
    }
  }
  
  return best;
}
```

**Speedup:** 4x average | **Pattern:** Satisficing with thresholds

---

## Pattern 7: Lazy Loading

### Before (30s startup)

```javascript
class AgentOrchestrator {
  constructor() {
    this.modelA = loadModel('model-a');    // 10s
    this.modelB = loadModel('model-b');    // 10s
    this.modelC = loadModel('model-c');    // 10s
  }
  
  async process(input) {
    if (input.type === 'a') return this.modelA.process(input);
    if (input.type === 'b') return this.modelB.process(input);
    return this.modelC.process(input);
  }
}
```

### After (0.5s startup)

```javascript
class AgentOrchestrator {
  constructor() {
    this.models = {};  // Empty initially
  }
  
  async getModel(name) {
    if (!this.models[name]) {
      this.models[name] = loadModel(name);  // Load on first use
    }
    return this.models[name];
  }
  
  async process(input) {
    if (input.type === 'a') {
      const model = await this.getModel('model-a');
      return model.process(input);
    }
    // ...
  }
}
```

**Speedup:** 60x startup | **Pattern:** Lazy initialization

---

## Pattern 8: Circuit Breaker

### Before (Cascading failures)

```javascript
async function callService(endpoint) {
  return await fetch(endpoint);  // Fails immediately if service down
}

// If service is down, every call fails after 30s timeout
// 100 calls = 3000s of waiting
```

### After (Fast failure)

```javascript
class CircuitBreaker {
  constructor(threshold = 5, timeout = 60000) {
    this.failures = 0;
    this.threshold = threshold;
    this.timeout = timeout;
    this.state = 'CLOSED';  // CLOSED, OPEN, HALF_OPEN
    this.lastFailure = 0;
  }
  
  async call(fn) {
    if (this.state === 'OPEN') {
      if (Date.now() - this.lastFailure > this.timeout) {
        this.state = 'HALF_OPEN';
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }
    
    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }
  
  onSuccess() {
    this.failures = 0;
    this.state = 'CLOSED';
  }
  
  onFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.threshold) {
      this.state = 'OPEN';
    }
  }
}

const breaker = new CircuitBreaker(5, 60000);

async function callService(endpoint) {
  return breaker.call(() => fetch(endpoint));
}

// After 5 failures, circuit opens
// Subsequent calls fail immediately
// After 60s, circuit enters HALF_OPEN and tries again
```

**Speedup:** Immediate failure vs 30s timeout | **Pattern:** Fail-fast

---

## Optimization Decision Matrix

| Symptom | Diagnosis | Pattern | Expected Gain |
|---------|-----------|---------|---------------|
| Long sequential chain | No parallelism | Sequential→Parallel | 2-4x |
| Repeated identical calls | No caching | Caching | 10-100x |
| Uncertain which path | Sequential fallback | Speculative execution | 1.5-2x |
| User waits for all | Batch delivery | Streaming | 5-10x first result |
| Many small calls | Too granular | Batching | 5-10x |
| Always runs full search | No early exit | Early termination | 2-5x avg |
| Slow startup | Eager loading | Lazy loading | 10-100x startup |
| Cascading failures | No protection | Circuit breaker | Prevents timeout cascade |

---

## Quick Diagnostics

```bash
# Find slowest agent
grep "duration" logs/*.log | awk '{print $NF}' | sort -n | tail -10

# Find most called function
grep "function_call" logs/*.log | awk '{print $3}' | sort | uniq -c | sort -rn | head

# Find memory leaks
ps aux | grep agent | awk '{print $6}' | sort -n

# Find timeout patterns
grep "timeout" logs/*.log | wc -l
```

---

## Measurement Template

```javascript
async function measure(name, fn) {
  const start = Date.now();
  const memBefore = process.memoryUsage().heapUsed;
  
  try {
    const result = await fn();
    const duration = Date.now() - start;
    const memAfter = process.memoryUsage().heapUsed;
    
    console.log(JSON.stringify({
      name,
      duration_ms: duration,
      memory_delta_mb: (memAfter - memBefore) / 1024 / 1024,
      status: 'success'
    }));
    
    return result;
  } catch (error) {
    const duration = Date.now() - start;
    
    console.log(JSON.stringify({
      name,
      duration_ms: duration,
      status: 'error',
      error: error.message
    }));
    
    throw error;
  }
}

// Usage
await measure('extract_data', () => extractData(input));
await measure('transform_data', () => transformData(extracted));
```

---

## Before You Optimize

1. **Measure baseline** - What's the actual current performance?
2. **Identify bottleneck** - Which step takes the most time?
3. **Apply ONE pattern** - Don't change multiple things at once
4. **Measure improvement** - Did it actually help?
5. **Document** - Why did this work?

**Golden Rule:** Only optimize what you've measured.

---

**Related:** See `task-decomposition.md` for splitting work; `dependency-management.md` for parallel execution.