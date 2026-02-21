# Context Handoff Protocols

**Date:** 2026-02-21 02:20 PM  
**Topic:** Reliable agent-to-agent context transfer

---

## The Problem

Agents fail when:
- Context is too large (token overflow)
- Context is incomplete (lost state)
- Context is ambiguous (misinterpretation)
- Context arrives late (race conditions)

**Solution:** Standardized handoff protocol with atomic transfers

---

## Protocol: ATOMIC

**A**tomic | **T**raceable | **O**ptimized | **M**inimal | **I**dempotent | **C**onsistent

### Handoff File Specification

```yaml
# handoff-{uuid}.yaml
protocol_version: "1.0"
handoff_id: "uuid-v4"
timestamp: "2026-02-21T14:20:00Z"

# Identity
from:
  agent_id: "worker-1"
  session: "sess-xyz123"
  version: "1.2.3"
to:
  agent_id: "aggregator-main"  # Optional: intended recipient

# Task Context
task:
  task_id: "task-uuid"
  parent_task: "parent-uuid"  # For subtask hierarchies
  correlation_id: "trace-root"  # Distributed tracing
  sequence_number: 3  # If ordered handoffs exist

# Status
status: "complete"  # complete | partial | blocked | failed
progress:
  pct_complete: 100
  items_processed: 150
  items_total: 150

# Deliverables
deliverables:
  - type: "json"  # json | text | binary | ref
    path: "data/output-3.json"
    description: "Processed chunk 3"
    schema: "schemas/output-v2.json"
    checksum: "sha256:abc123..."
    size_bytes: 15360
    
  - type: "ref"
    path: "s3://bucket/chunk-3.parquet"
    description: "Large output stored externally"

# Delta Context (optional)
delta:
  base_handoff: "handoff-prev-uuid"  # Previous full context
  changes:
    added_keys: ["new_field"]
    modified: { "count": 150 }
    removed: ["temp_buffer"]

# Blockers (if status: blocked)
blockers:
  - reason: "awaiting_dependency"
    dependency_id: "task-other-uuid"
    eta: "2026-02-21T14:25:00Z"

# Metadata
timing:
  started: "2026-02-21T14:15:00Z"
  completed: "2026-02-21T14:20:00Z"
  wall_time: "300s"
  
resources:
  tokens_used: 4500
  memory_peak_mb: 512
```

---

## Handoff Patterns

### Pattern 1: Full Transfer

Use when context is small (<1000 tokens worth)

```
[Agent A] generates output → writes to file → signals complete
[Agent B] reads handoff → reads output file → processes
```

**Trade-off:** Simple but can cause large handoff files

### Pattern 2: Delta Transfer

Use when updating large state incrementally

```
Handoff 1: Full context + 100 items
Handoff 2: Delta (base_ref: Handoff 1, changes: +50 items)
Handoff 3: Delta (base_ref: Handoff 1, changes: +50 items)
```

**Advantage:** Each handoff stays small
**Risk:** Chain breaks if base handoff is lost

### Pattern 3: Reference Transfer

Use when outputs are very large

```yaml
deliverables:
  - type: "ref"
    path: "s3://bucket/large-output.parquet"
    format: "parquet"
    schema: "schemas/bigtable.json"
    checksum: "sha256:xyz789..."
```

**Rule:** Never embed large data (>4KB) in handoff file

### Pattern 4: Streaming Handoff

Use for real-time partial results

```
Time: 0s  → handoff-chunk-1.yaml (partial)
Time: 10s → handoff-chunk-2.yaml (partial)
Time: 25s → handoff-final.yaml (complete)
```

Consumer processes chunks as they arrive.

---

## Writing Handoffs (Contract for Producers)

### Atomic Write Pattern

```javascript
function writeHandoff(handoffData, outputPath) {
  const tempPath = `${outputPath}.tmp`;
  
  // Write to temp first
  fs.writeFileSync(tempPath, YAML.stringify(handoffData));
  
  // Sync to disk (optional but safer)
  fs.fsyncSync(fs.openSync(tempPath));
  
  // Atomic rename
  fs.renameSync(tempPath, outputPath);
  
  // Notify subscribers
  signalReady(outputPath);
}
```

**Why atomic rename?**
- Readers never see partial files
- No lock needed for readers
- Crash-safe: temp file can be cleaned up

### Checksum Verification

```javascript
const crypto = require("crypto");

function hashFile(path) {
  const file = fs.readFileSync(path);
  return crypto.createHash("sha256").update(file).digest("hex");
}

// Include in handoff
deliverables[0].checksum = hashFile(deliverables[0].path);
```

**Validate on read:** Reject if hash mismatch (file corruption during transfer)

---

## Reading Handoffs (Contract for Consumers)

### Safe Read with Timeout

```javascript
async function readHandoff(handoffPath, options = {}) {
  const timeout = options.timeout || 30000;
  const pollInterval = options.pollInterval || 100;
  const start = Date.now();
  
  while (Date.now() - start < timeout) {
    try {
      if (fs.existsSync(handoffPath)) {
        const content = fs.readFileSync(handoffPath, "utf8");
        const handoff = YAML.parse(content);
        
        // Validate checksums
        for (const d of handoff.deliverables) {
          if (d.checksum) {
            const actualHash = hashFile(d.path);
            if (actualHash !== d.checksum) {
              throw new Error(`Checksum mismatch for ${d.path}`);
            }
          }
        }
        
        return handoff;
      }
    } catch (e) {
      if (e.code !== "ENOENT") throw e;  // Re-throw real errors
    }
    
    await sleep(pollInterval);
  }
  
  throw new Error(`Timeout waiting for handoff: ${handoffPath}`);
}
```

### Partial Result Handling

```javascript
function processHandoff(handoff) {
  switch (handoff.status) {
    case "complete":
      return processComplete(handoff);
      
    case "partial":
      // Process what we have, might receive more later
      bufferPartial(handoff);
      return { status: "waiting" };
      
    case "blocked":
      // Re-check dependencies
      checkBlockers(handoff.blockers);
      return { status: "blocked" };
      
    case "failed":
      // Propagate or handle
      throw new HandoffError(handoff.error_details);
      
    default:
      throw new Error(`Unknown status: ${handoff.status}`);
  }
}
```

---

## Error Recovery

### Missing Handoff

```javascript
async function recoverMissingHandoff(taskId, options = {}) {
  const maxRetries = options.maxRetries || 3;
  
  for (let i = 0; i < maxRetries; i++) {
    // Check if handoff appeared
    const handoff = await discoverHandoff(taskId);
    if (handoff) return handoff;
    
    // Query agent status
    const status = await getAgentStatus(taskId);
    
    if (status === "running") {
      // Agent still processing, wait
      await sleep(5000);
    } else if (status === "failed") {
      // Need to re-spawn
      return await respawnAndWait(taskId);
    } else if (status === "unknown") {
      // Orphaned task, re-queue
      return await respawnAndWait(taskId);
    }
  }
  
  throw new Error(`Handoff recovery failed for ${taskId}`);
}
```

### Corrupted Handoff

```javascript
function handleCorruptedHandoff(path, error) {
  // Move to quarantine
  const quarantinePath = `quarantine/${path.basename(path)}.${Date.now()}`;
  fs.renameSync(path, quarantinePath);
  
  // Log for debugging
  log.error({ handoff: path, error, quarantinePath });
  
  // Alert human or retry from source
  alertHuman(`Corrupted handoff quarantined: ${quarantinePath}`);
  
  // Request re-generation
  return requestRegeneration(path);
}
```

---

## Handoff Discovery

When consumer doesn't know exact path:

### Discovery by Task ID

```javascript
async function discoverHandoff(taskId) {
  const pattern = `handoffs/${taskId}-*.yaml`;
  const files = glob.sync(pattern);
  
  // Sort by timestamp, newest first
  files.sort((a, b) => {
    const statA = fs.statSync(a);
    const statB = fs.statSync(b);
    return statB.mtime - statA.mtime;
  });
  
  // Return most recent complete handoff
  for (const file of files) {
    const handoff = YAML.parse(fs.readFileSync(file, "utf8"));
    if (handoff.status === "complete") {
      return handoff;
    }
  }
  
  return null;
}
```

### Watch Pattern (Event-Driven)

```javascript
const chokidar = require("chokidar");

function watchForHandoffs(pattern, callback) {
  const watcher = chokidar.watch(pattern, {
    persistent: true,
    ignoreInitial: false
  });
  
  watcher.on("add", async (path) => {
    // Debounce: ensure file is fully written
    await waitForStableFile(path, { stableFor: 100 });
    
    const handoff = YAML.parse(fs.readFileSync(path, "utf8"));
    callback(handoff);
  });
  
  return watcher;
}
```

---

## Size Limits & Chunking

**Maximum handoff file size: 4KB**

If context exceeds 4KB:

```yaml
# Option 1: External reference
deliverables:
  - type: "ref"
    path: "data/large-context.json"
    
# Option 2: Truncation with pointer
deliverables:
  - type: "json"
    path: "data/partial.json"
    truncated: true
    full_context_ref: "data/full-context.json"
```

**Chunking large outputs:**

```
output/
├── manifest.json           # This is the handoff
├── chunk-0001.json
├── chunk-0002.json
└── chunk-0003.json

# manifest.json
{
  "chunks": ["chunk-0001.json", "chunk-0002.json", "chunk-0003.json"],
  "total_size_bytes": 15800000
}
```

---

## Security Considerations

### Path Sanitization

```javascript
function sanitizePath(input, baseDir) {
  // Prevent directory traversal
  const resolved = path.resolve(baseDir, input);
  if (!resolved.startsWith(baseDir)) {
    throw new Error("Path traversal attempt detected");
  }
  return resolved;
}
```

### Secret Redaction

```yaml
# Before: has API key
env:
  API_KEY: "sk-secret123"
  
# After: redacted in handoff
env:
  API_KEY: "[REDACTED]"
  ```

---

## Quick Reference: Handoff Checklist

**When Writing:**
- [ ] Used atomic rename (write to .tmp, then mv)
- [ ] Included checksum for all deliverables
- [ ] Added correlation_id for tracing
- [ ] Documented schema version
- [ ] Total file size < 4KB
- [ ] Secrets redacted

**When Reading:**
- [ ] Validated file exists (with timeout)
- [ ] Verified checksums
- [ ] Checked status before processing
- [ ] Handled partial/blocked gracefully
- [ ] Validated schema version supported
- [ ] Sanitized all paths before using

---

**Related:** See `multi-agent-coordination.md` for how handoffs fit into larger patterns.
