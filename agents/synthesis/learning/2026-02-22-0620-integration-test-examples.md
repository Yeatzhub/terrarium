# Integration Test Examples for Agent Systems

**Created:** 2026-02-22 06:20  
**Author:** Synthesis  
**Focus:** Practical test patterns for multi-agent and tool integration

---

## Testing Philosophy

Unit tests check components in isolation. Integration tests verify:
- Agents collaborate correctly
- Tools produce expected side effects
- State persists across handoffs
- Edge cases in real workflows

---

## Pattern 1: Tool Chain Verification

Test that tools execute in correct sequence with proper data flow.

```bash
# Test: File creation → edit → read chain
#!/bin/bash
set -e

# Setup
TEST_FILE="/tmp/test-chain-$(date +%s).txt"
TEST_CONTENT="Initial content"

# Execute chain
write(path="$TEST_FILE", content="$TEST_CONTENT")
edit(path="$TEST_FILE", oldText="Initial", newText="Modified")
result=$(read(path="$TEST_FILE"))

# Verify
if [[ "$result" == *"Modified content"* ]]; then
  echo "✓ Tool chain passed"
else
  echo "✗ Tool chain failed: $result"
  exit 1
fi

# Cleanup
rm -f "$TEST_FILE"
```

---

## Pattern 2: Agent Handoff Verification

Verify context packages are properly transferred.

```python
# test_handoff.py
import json

def test_context_package_integrity():
    """Verify handoff contains all required fields."""
    
    handoff = {
        "task_summary": "Implement caching",
        "key_decisions": [{"choice": "Redis", "rationale": "In stack"}],
        "current_state": "POC complete",
        "blockers": [],
        "artifacts": ["/docs/cache.md"],
        "next_actions": ["Add to middleware"]
    }
    
    required = ["task_summary", "key_decisions", "current_state", 
                "blockers", "artifacts", "next_actions"]
    
    for field in required:
        assert field in handoff, f"Missing: {field}"
        assert handoff[field] is not None, f"Null: {field}"
    
    print("✓ Handoff structure valid")

def test_artifact_existence():
    """Verify referenced artifacts exist."""
    handoff = load_last_handoff()  # Your retrieval method
    
    for artifact in handoff.get("artifacts", []):
        assert os.path.exists(artifact), f"Missing artifact: {artifact}"
    
    print(f"✓ {len(handoff['artifacts'])} artifacts verified")
```

---

## Pattern 3: Sub-Agent Integration

Test spawning and communicating with sub-agents.

```bash
# test_subagent_spawn.sh
#!/bin/bash

# Spawn sub-agent
SESSION=$(sessions_spawn \
  --task "Count files in /tmp" \
  --agent-id "worker" \
  --timeout 30 \
  --format json)

# Extract session key
SESSION_KEY=$(echo "$SESSION" | jq -r '.sessionKey')

# Poll for completion (max 30s)
for i in {1..30}; do
  STATUS=$(subagents list --session "$SESSION_KEY" --format json | jq -r '.[0].status')
  
  if [[ "$STATUS" == "completed" ]]; then
    echo "✓ Sub-agent completed"
    
    # Verify result was announced
    RESULT=$(sessions_history --session "$SESSION_KEY" --limit 1)
    echo "Result: $RESULT"
    exit 0
  fi
  
  sleep 1
done

echo "✗ Sub-agent timeout"
exit 1
```

---

## Pattern 4: Error Propagation

Verify errors flow correctly through agent chains.

```python
# test_error_propagation.py

def test_tool_failure_bubbles_up():
    """Tool failure should abort workflow and report."""
    
    try:
        # This should fail - file doesn't exist
        result = read(path="/nonexistent/file.txt")
        assert False, "Should have raised error"
    except FileNotFoundError as e:
        print("✓ Error correctly propagated")
        return
    
    assert False, "Error was swallowed"

def test_subagent_timeout():
    """Timeout should kill sub-agent and notify."""
    
    session = sessions_spawn(
        task="Sleep for 100 seconds",
        timeout_seconds=5
    )
    
    time.sleep(6)  # Wait for timeout
    
    status = subagents(action="list", target=session["sessionKey"])
    assert status[0]["status"] == "timeout", "Should be timed out"
    print("✓ Timeout handled correctly")
```

---

## Pattern 5: State Consistency

Verify state remains consistent across operations.

```bash
# test_state_consistency.sh
#!/bin/bash

MEMORY_FILE="$HOME/.openclaw/workspace/memory/test-state.md"

# Write initial state
echo "# Test State\nValue: 123" > "$MEMORY_FILE"

# Multiple operations
for i in {1..5}; do
    read(path="$MEMORY_FILE") > /dev/null
done

# Verify no corruption
FINAL=$(read(path="$MEMORY_FILE"))
if [[ "$FINAL" == *"Value: 123"* ]]; then
    echo "✓ State remained consistent through 5 reads"
else
    echo "✗ State corrupted: $FINAL"
    exit 1
fi

rm -f "$MEMORY_FILE"
```

---

## Pattern 6: Concurrent Operations

Test parallel tool invocations don't conflict.

```python
# test_concurrency.py
import concurrent.futures
import time

def test_concurrent_writes():
    """Parallel writes to different files."""
    
    def write_file(n):
        path = f"/tmp/concurrent-test-{n}.txt"
        write(path=path, content=f"Content {n}")
        return path
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        paths = list(executor.map(write_file, range(5)))
    
    # Verify all files exist with correct content
    for i, path in enumerate(paths):
        content = read(path=path)
        assert f"Content {i}" in content
    
    print(f"✓ {len(paths)} concurrent writes succeeded")

def test_sequential_edits_same_file():
    """Sequential edits to same file."""
    
    path = "/tmp/sequential-test.txt"
    write(path=path, content="A B C D E")
    
    edits = [
        ("A", "1"),
        ("B", "2"),
        ("C", "3"),
        ("D", "4"),
        ("E", "5")
    ]
    
    for old, new in edits:
        edit(path=path, oldText=old, newText=new)
    
    result = read(path=path)
    assert "1 2 3 4 5" in result
    print("✓ Sequential edits applied correctly")
```

---

## Test Suite Structure

```
tests/
├── integration/
│   ├── test_tool_chains.py      # Pattern 1
│   ├── test_handoffs.py          # Pattern 2
│   ├── test_subagents.py         # Pattern 3
│   ├── test_errors.py            # Pattern 4
│   ├── test_state.py             # Pattern 5
│   └── test_concurrency.py       # Pattern 6
├── fixtures/
│   └── sample_handoff.json
└── run_all.sh
```

---

## Quick CI Integration

```yaml
# .github/workflows/agent-integration.yml
name: Agent Integration Tests

on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run tool chain tests
        run: ./tests/integration/test_tool_chains.sh
      
      - name: Run handoff tests
        run: python tests/integration/test_handoffs.py
      
      - name: Run sub-agent tests
        run: ./tests/integration/test_subagents.sh
        timeout-minutes: 5
```

---

## Key Metrics to Track

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Test pass rate | >95% | CI reports |
| Avg test runtime | <30s | Timing logs |
| Flaky test rate | <2% | Re-run analysis |
| Coverage % | >80% | Coverage tools |

---

## Bottom Line

Integration tests catch what unit tests miss:
- **Tool chains** break at the seams
- **Handoffs** lose context
- **Sub-agents** timeout silently
- **Errors** get swallowed

Run these before any major workflow change. They're your safety net for complex agent behaviors.