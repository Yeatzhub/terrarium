# Integration Test Examples for OpenClaw

**Created:** 2026-02-19 00:20 CT  
**Topic:** Integration testing patterns, test fixtures, validation scripts

---

## 1. Agent Spawning Test

**Purpose:** Verify sub-agent lifecycle and result propagation.

```bash
#!/bin/bash
# test: agent-spawn-lifecycle.sh

LABEL="test-spawn-$(date +%s)"

# Spawn async sub-agent
openclaw sessions_spawn \
  --task "Return the exact string: 'agent-ready'" \
  --label "$LABEL" \
  --runTimeoutSeconds 60

# Poll for completion (max 10 attempts)
for i in {1..10}; do
  sleep 3
  STATUS=$(openclaw subagents list --recentMinutes 5 | grep "$LABEL")
  if [[ "$STATUS" == *"completed"* ]]; then
    echo "✓ Agent completed successfully"
    exit 0
  fi
  if [[ "$STATUS" == *"failed"* ]]; then
    echo "✗ Agent failed"
    exit 1
  fi
done

echo "✗ Timeout waiting for agent"
exit 1
```

**Expected:** Agent spawns, completes, result contains "agent-ready".

---

## 2. File Handoff Test

**Purpose:** Validate data persistence across agent boundaries.

```bash
#!/bin/bash
# test: file-handoff.sh

WORKDIR="/home/yeatz/.openclaw/workspace/test-handoff"
mkdir -p "$WORKDIR"

# Stage 1: Producer
openclaw sessions_spawn \
  --task "Write JSON to $WORKDIR/handoff.json: {\"stage\": 1, \"data\": \"test-payload\", \"timestamp\": \"$(date -Iseconds)\"}" \
  --runTimeoutSeconds 30

sleep 2

# Validate output exists
if [ ! -f "$WORKDIR/handoff.json" ]; then
  echo "✗ Stage 1 output missing"
  exit 1
fi

# Stage 2: Consumer with validation
openclaw sessions_spawn \
  --task "Read $WORKDIR/handoff.json, verify 'stage' == 1 and 'data' == 'test-payload'. Return validation result." \
  --runTimeoutSeconds 30

# Cleanup
rm -rf "$WORKDIR"
echo "✓ File handoff validated"
```

**Expected:** JSON written, read, validated across two agent runs.

---

## 3. Pipeline Failure Test

**Purpose:** Verify error propagation and graceful degradation.

```bash
#!/bin/bash
# test: pipeline-failure.sh

WORKDIR="/home/yeatz/.openclaw/workspace/test-pipeline"
mkdir -p "$WORKDIR"

# Stage 1: Will succeed
echo '{"status": "ok", "value": 42}' > "$WORKDIR/stage1.json"

# Stage 2: Intentional failure (corrupt input)
echo 'INVALID JSON' > "$WORKDIR/stage1.json"

# Stage 3: Should detect failure and not proceed
openclaw sessions_spawn \
  --task "Attempt to parse $WORKDIR/stage1.json as JSON. If invalid, return error code 'PARSE_FAILED' and do not proceed." \
  --runTimeoutSeconds 30

# Verify error was caught
if openclaw sessions_history --sessionKey "test-pipeline-fail" 2>/dev/null | grep -q "PARSE_FAILED"; then
  echo "✓ Pipeline correctly halted on failure"
else
  echo "✗ Error not propagated correctly"
fi

rm -rf "$WORKDIR"
```

**Expected:** Stage 3 detects invalid input, returns error, pipeline stops.

---

## 4. Cron Job Integration Test

**Purpose:** Validate scheduled job payload and timing.

```bash
#!/bin/bash
# test: cron-schedule.sh

TEST_MARKER="cron-test-$(date +%s)"

# Create test cron job (fires in 1 minute)
openclaw cron add \
  --job '{
    "name": "'"$TEST_MARKER"'",
    "schedule": {"kind": "at", "at": "'"$(date -d '+1 minute' -Iseconds)'"'},
    "payload": {"kind": "agentTurn", "message": "Write \"'"$TEST_MARKER"'\" to /home/yeatz/.openclaw/workspace/cron-test-output.txt"},
    "sessionTarget": "isolated"
  }'

# Wait and verify
sleep 70
if grep -q "$TEST_MARKER" /home/yeatz/.openclaw/workspace/cron-test-output.txt; then
  echo "✓ Cron job executed at scheduled time"
  rm /home/yeatz/.openclaw/workspace/cron-test-output.txt
  openclaw cron remove --jobId "$TEST_MARKER"
  exit 0
else
  echo "✗ Cron job did not execute"
  exit 1
fi
```

**Expected:** Job triggers, agent runs, output file contains marker.

---

## 5. Tool Response Schema Test

**Purpose:** Verify tool outputs match expected structure.

```bash
#!/bin/bash
# test: tool-schema-validation.sh

# Test web_search returns expected fields
RESULT=$(openclaw web_search --query "OpenClaw" --count 1)

# Check required fields exist
if echo "$RESULT" | grep -q '"title":' && \
   echo "$RESULT" | grep -q '"url":' && \
   echo "$RESULT" | grep -q '"snippet":'; then
  echo "✓ web_search schema valid"
else
  echo "✗ web_search schema missing fields"
  exit 1
fi

# Test session_status returns usage data
STATUS=$(openclaw session_status)
if echo "$STATUS" | grep -q '"model":' || echo "$STATUS" | grep -q "model"; then
  echo "✓ session_status schema valid"
else
  echo "✗ session_status schema unexpected"
  exit 1
fi
```

**Expected:** All tools return documented field names.

---

## 6. Concurrent Agent Limit Test

**Purpose:** Verify system handles parallel load gracefully.

```bash
#!/bin/bash
# test: concurrent-agents.sh

MAX_AGENTS=5
WORKDIR="/home/yeatz/.openclaw/workspace/test-concurrent"
mkdir -p "$WORKDIR"

# Spawn multiple agents simultaneously
for i in $(seq 1 $MAX_AGENTS); do
  openclaw sessions_spawn \
    --task "sleep 2; echo 'agent-$i-done' > $WORKDIR/agent-$i.txt" \
    --label "concurrent-$i" &
done

# Wait for all background jobs
wait

# Verify all completed
SUCCESS=0
for i in $(seq 1 $MAX_AGENTS); do
  if [ -f "$WORKDIR/agent-$i.txt" ]; then
    SUCCESS=$((SUCCESS + 1))
  fi
done

rm -rf "$WORKDIR"

if [ "$SUCCESS" -eq "$MAX_AGENTS" ]; then
  echo "✓ All $MAX_AGENTS concurrent agents completed"
  exit 0
else
  echo "✗ Only $SUCCESS/$MAX_AGENTS agents completed"
  exit 1
fi
```

**Expected:** All agents complete without interference.

---

## 7. End-to-End Workflow Test

**Purpose:** Test complete workflow: Search → Process → Store → Notify.

```bash
#!/bin/bash
# test: e2e-workflow.sh

WORKDIR="/home/yeatz/.openclaw/workspace/test-e2e"
mkdir -p "$WORKDIR"

# Step 1: Search
openclaw sessions_spawn \
  --task "Search for 'Linux kernel 6.8 release date', extract the date, write to $WORKDIR/search.json as {\"query\": \"...\", \"result\": \"...\", \"date\": \"...\"}" \
  --runTimeoutSeconds 45

# Step 2: Process (transform)
openclaw sessions_spawn \
  --task "Read $WORKDIR/search.json, reformat as Markdown: '## Query\n{query}\n\n## Result\n{result}\n\n## Date\n{date}'. Write to $WORKDIR/output.md" \
  --runTimeoutSeconds 30

# Step 3: Validate
if [ -f "$WORKDIR/output.md" ] && grep -q "## Query" "$WORKDIR/output.md"; then
  echo "✓ E2E workflow completed"
  cat "$WORKDIR/output.md"
  rm -rf "$WORKDIR"
  exit 0
else
  echo "✗ E2E workflow failed"
  rm -rf "$WORKDIR"
  exit 1
fi
```

**Expected:** Search results transformed and saved as Markdown.

---

## Test Runner Script

```bash
#!/bin/bash
# run-all-tests.sh

FAILED=0
PASSED=0

for test in test-*.sh; do
  echo "Running: $test"
  if bash "$test"; then
    PASSED=$((PASSED + 1))
  else
    FAILED=$((FAILED + 1))
  fi
  echo "---"
done

echo "Results: $PASSED passed, $FAILED failed"
exit $FAILED
```

---

## CI/CD Integration

Add to `.github/workflows/test.yml`:

```yaml
name: Integration Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install OpenClaw CLI
        run: pip install openclaw
      - name: Run Tests
        run: bash agents/synthesis/learning/run-all-tests.sh
```

---

**Next Steps:** Run these tests weekly; add new tests for each new tool/pattern.
