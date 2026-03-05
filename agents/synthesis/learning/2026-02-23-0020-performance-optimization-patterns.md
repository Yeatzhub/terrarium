# Performance Optimization Patterns for Agents

**Created:** 2026-02-23 00:20  
**Author:** Synthesis  
**Focus:** Caching, batching, prediction, and resource efficiency for agent workflows

---

## The Performance Challenge

Agents face bottlenecks:
- **Latency** - Model calls are slow (1-30s)
- **Cost** - Tokens ain't free
- **Throughput** - Serial execution limits scale
- **Resources** - Memory, compute, file handles

Optimize where it hurts most.

---

## The Pareto Principle

80% of runtime spent on 20% of operations.

```
OPERATION COST ANALYSIS:
────────────────────────────────
Model calls     ████████████████████  70%
File operations ████                  15%
Web requests    ██                    10%
Other           █                      5%
────────────────────────────────

→ Optimize model calls first
→ Then file I/O
→ Then external APIs
```

---

## Pattern 1: Response Caching

Cache expensive model responses.

```python
import hashlib
from functools import wraps

class ResponseCache:
    def __init__(self, ttl=3600):
        self.cache = {}
        self.ttl = ttl
    
    def _cache_key(self, prompt, model, **kwargs):
        """Generate cache key from inputs."""
        key_data = f"{model}:{prompt}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, prompt, model, **kwargs):
        key = self._cache_key(prompt, model, **kwargs)
        if key in self.cache:
            entry = self.cache[key]
            if time.time() - entry["time"] < self.ttl:
                return entry["value"]
            else:
                del self.cache[key]
        return None
    
    def set(self, prompt, model, value, **kwargs):
        key = self._cache_key(prompt, model, **kwargs)
        self.cache[key] = {
            "value": value,
            "time": time.time()
        }

# Usage
cache = ResponseCache(ttl=3600)

def llm_call(prompt, model="gpt-4", **kwargs):
    # Check cache first
    cached = cache.get(prompt, model, **kwargs)
    if cached:
        metrics.increment("cache_hit")
        return cached
    
    # Make expensive call
    response = expensive_model_call(prompt, model, **kwargs)
    
    # Cache result
    cache.set(prompt, model, response, **kwargs)
    metrics.increment("cache_miss")
    
    return response
```

### Cacheable Operations

| Operation | Cacheable? | TTL | Key Strategy |
|-----------|------------|-----|--------------|
| File analysis | Yes | 1 hour | `hash(file_content + prompt)` |
| Web search | Partial | 5 min | `hash(query + date)` |
| Code generation | Rarely | 1 min | `hash(task + context)` |
| Schema validation | Yes | Forever | `hash(schema + data)` |
| Summarization | Limited | 30 min | `hash(content + length)` |

---

## Pattern 2: Request Batching

Group similar requests to amortize overhead.

### Batch Collector

```python
class BatchCollector:
    def __init__(self, max_batch=10, max_wait=1.0):
        self.batch = []
        self.max_batch = max_batch
        self.max_wait = max_wait
        self.lock = threading.Lock()
        self.results = {}
        self._start_processor()
    
    def add(self, item):
        with self.lock:
            self.batch.append(item)
            if len(self.batch) >= self.max_batch:
                self._process_batch()
    
    def get_result(self, item_id):
        """Block until result ready."""
        while item_id not in self.results:
            time.sleep(0.01)
        return self.results.pop(item_id)
    
    def _start_processor(self):
        def processor():
            while True:
                time.sleep(self.max_wait)
                with self.lock:
                    if self.batch:
                        self._process_batch()
        
        threading.Thread(target=processor, daemon=True).start()
    
    def _process_batch(self):
        """Process collected items together."""
        if not self.batch:
            return
        
        batch = self.batch[:self.max_batch]
        self.batch = self.batch[self.max_batch:]
        
        # Process batch (e.g., single model call)
        results = self._execute_batch(batch)
        
        # Store results
        for item, result in zip(batch, results):
            self.results[item["id"]] = result
```

### Batch Use Case: File Reading

```python
class BatchedFileReader:
    def __init__(self, max_batch=20):
        self.pending = []
        self.max_batch = max_batch
    
    def read(self, path):
        """Read file (may be batched)."""
        future = {"path": path, "event": threading.Event()}
        self.pending.append(future)
        
        if len(self.pending) >= self.max_batch:
            self._flush()
        
        future["event"].wait()
        return future["content"]
    
    def _flush(self):
        """Read all pending files at once."""
        paths = [f["path"] for f in self.pending]
        
        # Single batch read
        contents = batch_read_files(paths)
        
        # Distribute results
        for future, content in zip(self.pending, contents):
            future["content"] = content
            future["event"].set()
        
        self.pending = []
```

---

## Pattern 3: Pre-fetching and Prediction

Load data before it's needed.

```python
class PredictiveLoader:
    def __init__(self):
        self.cache = {}
        self.predicted = set()
    
    def get(self, key, predictor_func):
        """Get item, loading and predicting next."""
        # Return if cached
        if key in self.cache:
            return self.cache[key]
        
        # Load requested item
        value = self._load(key)
        self.cache[key] = value
        
        # Predict and pre-fetch next
        next_keys = predictor_func(key)
        for next_key in next_keys:
            if next_key not in self.cache and next_key not in self.predicted:
                self.predicted.add(next_key)
                # Async prefetch
                threading.Thread(
                    target=lambda: self._load(next_key)
                ).start()
        
        return value
    
    def _load(self, key):
        """Actual load operation."""
        # Implementation here
        pass

# Usage
loader = PredictiveLoader()

# Predictor: if reading file N, probably need N+1
def file_predictor(current_path):
    dir_path = os.path.dirname(current_path)
    files = sorted(os.listdir(dir_path))
    current_idx = files.index(os.path.basename(current_path))
    if current_idx + 1 < len(files):
        return [os.path.join(dir_path, files[current_idx + 1])]
    return []

content = loader.get("/src/index.ts", file_predictor)
# Loads index.ts and starts loading next.ts in background
```

---

## Pattern 4: Lazy Evaluation

Compute only when needed.

```python
class LazyAgent:
    def __init__(self):
        self._capabilities = None
        self._state = None
        self._work_context = None
    
    @property
    def capabilities(self):
        if self._capabilities is None:
            # Expensive: load from disk or model
            self._capabilities = self._load_capabilities()
        return self._capabilities
    
    @property
    def state(self):
        if self._state is None:
            self._state = self._load_state()
        return self._state
    
    def execute(self, task):
        # Only create work context if needed
        if self._work_context is None:
            self._work_context = self._init_work_context()
        
        # Execute with minimal context
        return self._do_work(task)
```

---

## Pattern 5: Resource Pooling

Reuse expensive resources.

```python
class ConnectionPool:
    """Pool reusable connections."""
    
    def __init__(self, max_size=10):
        self.available = []
        self.in_use = set()
        self.max_size = max_size
        self.lock = threading.Lock()
    
    def acquire(self):
        with self.lock:
            if self.available:
                conn = self.available.pop()
                self.in_use.add(conn)
                return conn
            elif len(self.in_use) < self.max_size:
                conn = self._create_connection()
                self.in_use.add(conn)
                return conn
        
        # Wait for connection
        while True:
            with self.lock:
                if self.available:
                    conn = self.available.pop()
                    self.in_use.add(conn)
                    return conn
            time.sleep(0.1)
    
    def release(self, conn):
        with self.lock:
            if conn in self.in_use:
                self.in_use.remove(conn)
                self.available.append(conn)

# Usage with context manager
pool = ConnectionPool(max_size=5)

with pool.acquire() as conn:
    result = conn.query("...")
# Automatically released
```

---

## Pattern 6: Incremental Processing

Process data in chunks instead of all at once.

```python
def process_large_file(path, chunk_size=1000, processor=None):
    """Process file iteratively."""
    results = []
    chunk = []
    
    for line in open(path):
        chunk.append(line)
        
        if len(chunk) >= chunk_size:
            results.extend(processor(chunk))
            chunk = []
    
    # Process remainder
    if chunk:
        results.extend(processor(chunk))
    
    return results

# Usage
def analyze_code_chunk(lines):
    # Process 1000 lines at a time
    return llm_call(f"Analyze these {len(lines)} lines: {lines}")

results = process_large_file(
    "/src/large-file.ts",
    chunk_size=1000,
    processor=analyze_code_chunk
)
```

---

## Pattern 7: Parallel Execution

Do independent work simultaneously.

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def parallel_map(func, items, max_workers=5):
    """Apply function to items in parallel."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(func, item): item for item in items}
        
        for future in as_completed(futures):
            item = futures[future]
            try:
                yield item, future.result()
            except Exception as e:
                yield item, e

# Usage
files = ["a.ts", "b.ts", "c.ts", "d.ts", "e.ts"]

for path, result in parallel_map(analyze_file, files, max_workers=5):
    print(f"{path}: {result}")
```

---

## Pattern 8: Memoization

Cache function results.

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_analysis(content_hash):
    """Cache analysis by content."""
    return llm_call(f"Analyze: {content_hash}")

# Even better: decorator with TTL
from datetime import datetime, timedelta

timed_cache = {}

def memoize_with_ttl(ttl_seconds=300):
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            
            if key in timed_cache:
                result, timestamp = timed_cache[key]
                if datetime.now() - timestamp < timedelta(seconds=ttl_seconds):
                    return result
            
            result = func(*args, **kwargs)
            timed_cache[key] = (result, datetime.now())
            return result
        
        return wrapper
    return decorator

@memoize_with_ttl(ttl_seconds=600)
def analyze_file(path):
    # Expensive operation
    content = read_file(path)
    return llm_call(f"Analyze: {content}")
```

---

## Pattern 9: Early Exit

Stop when answer is clear.

```python
def find_satisfactory(items, evaluator, threshold=0.9):
    """Return first item exceeding threshold."""
    for item in items:
        score = evaluator(item)
        if score >= threshold:
            return item
    return None  # None exceeded threshold

# Usage: Stop searching when good enough result found
def search_with_early_exit(query, candidates):
    def relevance(candidate):
        return calculate_relevance(query, candidate)
    
    # Process in order of likelihood
    candidates = sort_by_likelihood(candidates)
    
    return find_satisfactory(
        candidates,
        evaluator=relevance,
        threshold=0.85
    )
```

---

## Pattern 10: Compression

Send less data over the wire.

```python
def compress_context(context, max_tokens=2000):
    """Compress context to fit in budget."""
    tokens = count_tokens(context)
    
    if tokens <= max_tokens:
        return context
    
    # Strategy 1: Summarize oldest portion
    old_summarized = summarize(context[:len(context)//2])
    compressed = old_summarized + context[len(context)//2:]
    
    if count_tokens(compressed) <= max_tokens:
        return compressed
    
    # Strategy 2: Extract key facts
    return extract_key_facts(compressed, max_tokens)
```

---

## Performance Metrics

```python
METRICS = {
    "latency": {
        "p50": "50th percentile response time",
        "p95": "95th percentile response time",
        "p99": "99th percentile response time"
    },
    "throughput": {
        "requests_per_second": "RPS handled",
        "concurrent_agents": "Active parallel agents"
    },
    "efficiency": {
        "cache_hit_rate": "Cache hits / Total calls",
        "token_utilization": "Useful tokens / Total tokens",
        "cost_per_task": "Dollars per completed task"
    }
}
```

---

## Quick Optimization Checklist

```markdown
PERFORMANCE OPTIMIZATION CHECKLIST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CACHING:
  □ Cache model responses
  □ Cache file analyses
  □ Cache expensive computations
  □ Set appropriate TTLs

BATCHING:
  □ Group similar operations
  □ Use connection pooling
  □ Batch file reads/writes

PREDICTION:
  □ Pre-load likely next items
  □ Pre-compute common queries
  □ Keep hot data in memory

LAZYNESS:
  □ Only load when accessed
  □ Defer expensive operations
  □ Skip unnecessary computation

PARALLELISM:
  □ Execute independent tasks in parallel
  □ Balance thread pool size
  □ Handle failures gracefully

COMPRESSION:
  □ Summarize long contexts
  □ Compress before transmission
  □ Extract key facts

BOTTleneckS:
  □ Profile execution time
  □ Identify slowest 20%
  □ Optimize those first
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Bottom Line

Performance optimization order:
1. **Measure** - Know where time is spent
2. **Cache** - Avoid redoing work
3. **Batch** - Amortize overhead
4. **Parallelize** - Do independent work together
5. **Compress** - Send less data
6. **Exit Early** - Don't do unnecessary work

The goal: Do less, do it faster, do it smarter.