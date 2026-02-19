# Workflow Optimization Guides

**Created:** 2026-02-19 02:20 CT  
**Topic:** Cost reduction, latency improvement, resource efficiency, quality preservation

---

## 1. Token Cost Optimization

### Rule: Batch > Single

```bash
# Bad: 3 separate tool calls
grep "pattern" file1 | head -5
grep "pattern" file2 | head -5
grep "pattern" file3 | head -5

# Good: 1 batched call
grep "pattern" file1 file2 file3 | head -15
```

### Cache Repeated Data

```bash
# Cache file list if used multiple times
FILES=$(find . -name "*.md")
echo "$FILES" | grep "pattern1"
echo "$FILES" | grep "pattern2"
```

### Use Cheaper Models for Simple Tasks

```yaml
# Cost tier strategy
tier_1: "ollama/phi4"        # Local, free, fast — for extraction, formatting
tier_2: "ollama/kimi-k2.5"   # Current — for reasoning, synthesis
tier_3: "gpt-4o"            # Reserved for complex analysis only
```

---

## 2. Latency Reduction

### Parallelize Independent Calls

```bash
# Sequential (slow)
result_a=$(openclaw web_search --query "A")
result_b=$(openclaw web_search --query "B")

# Parallel (fast)
openclaw web_search --query "A" > /tmp/a.json &
openclaw web_search --query "B" > /tmp/b.json &
wait
cat /tmp/a.json /tmp/b.json
```

### Use `yieldMs` for Long Operations

```bash
# For operations >30s, use yieldMs to free up the session
openclaw exec --command "long-running-task" --yieldMs 5000
```

### Prefer Web Fetch Over Browser

| Method | Latency | Use When |
|--------|---------|----------|
| `web_fetch` | ~1-3s | Static content, articles, docs |
| `browser` | ~5-10s | JavaScript-required, interactive |

### Aggressive Timeouts

```bash
# Default timeout is often too generous
openclaw sessions_spawn --task "..." --runTimeoutSeconds 30  # Not 300
```

---

## 3. Resource Efficiency

### File Reading Strategy

```bash
# Don't read entire files
wc -l huge.log                    # Check size first
head -50 huge.log | grep error    # Sample if acceptable
tail -100 huge.log                # Recent entries only
sed -n '1000,1100p' huge.log      # Specific range
```

### Session Hygiene

```bash
# Clean up temp files after workflows
TMPDIR="/home/yeatz/.openclaw/workspace/tmp"
trap 'rm -rf "$TMPDIR"' EXIT
mkdir -p "$TMPDIR"
# ... do work ...
# Auto-cleanup on exit
```

### Agent Reuse

```bash
# Spawn once, send multiple tasks
SESSION=$(openclaw sessions_spawn --task "init" --label worker-1)
openclaw sessions_send --sessionKey "$SESSION" --message "task 1"
openclaw sessions_send --sessionKey "$SESSION" --message "task 2"
```

---

## 4. Quality Preservation Techniques

### Progressive Validation

```bash
# Stage 1: Quick filter (cheap model)
openclaw sessions_spawn \
  --agentId "fast-extractor" \
  --task "Extract URLs from text, return JSON"

# Stage 2: Deep analysis (powerful model) only on filtered data
openclaw sessions_spawn \
  --agentId "deep-analyzer" \
  --task "Analyze these 5 URLs for sentiment"
```

### Output Schema Enforcement

```bash
# Always request structured output
task='Extract data as JSON: {"field1": "string", "field2": number}'
```

### Error Budgeting

```bash
# Allow 1 retry, then fail fast
attempt=0
max_attempts=2
while [ $attempt -lt $max_attempts ]; do
  if openclaw sessions_spawn --task "..."; then
    break
  fi
  attempt=$((attempt + 1))
  sleep 2
done
```

---

## 5. Cron Job Optimization

### Avoid Overlap

```json
{
  "schedule": {"kind": "every", "everyMs": 300000},
  "payload": {
    "kind": "agentTurn",
    "message": "Check if previous run is complete before starting. Use lock file: /tmp/cron-task.lock"
  }
}
```

### Batch Small Jobs

```bash
# Instead of 5 separate cron jobs every minute:
# Combine into 1 job every 5 minutes
openclaw cron add --job '{
  "schedule": {"kind": "every", "everyMs": 300000},
  "payload": {"kind": "agentTurn", "message": "Run all 5 maintenance tasks sequentially"}
}'
```

### Right-Size Timeouts

| Task Type | Timeout | Reason |
|-----------|---------|--------|
| File read | 10s | Local disk |
| Web fetch | 30s | Network variance |
| Search API | 15s | Usually fast |
| Browser | 60s | Page load + JS |
| Sub-agent | 120s | Includes spawn overhead |

---

## 6. Decision Matrix: Speed vs Cost vs Quality

| Scenario | Priority | Strategy |
|----------|----------|----------|
| Real-time chat | Speed | Local model, no sub-agents |
| Daily report | Cost | Batch, cache, off-peak cron |
| Analysis | Quality | Best model, validation layers |
| Emergency fix | Speed + Quality | Skip batching, use best model |
| Background sync | Cost | Rate limit, retry with backoff |

---

## 7. Quick Wins Checklist

- [ ] Replace `read` + `grep` with `grep` on file directly
- [ ] Add `runTimeoutSeconds` to all `sessions_spawn` calls
- [ ] Use `web_fetch` instead of `browser` for static pages
- [ ] Batch parallel `web_search` calls with `&` and `wait`
- [ ] Cache expensive operations in `/workspace/cache/`
- [ ] Remove `sleep` loops, use proper polling with `subagents list`
- [ ] Use cheaper models for extraction, expensive for synthesis
- [ ] Add `trap 'rm -rf $TMPDIR'` for automatic cleanup

---

## 8. Performance Measurement

```bash
# Time a workflow
start=$(date +%s)
# ... workflow ...
end=$(date +%s)
echo "Duration: $((end - start))s"

# Measure token usage (if available)
openclaw session_status | grep -i "token\|cost\|usage"
```

---

**Next Steps:** Profile current synthesis jobs; identify top 3 latency bottlenecks; apply parallelization.
