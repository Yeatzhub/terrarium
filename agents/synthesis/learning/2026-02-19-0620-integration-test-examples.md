# Integration Test Examples for Agent Workflows

*Practical testing patterns for OpenClaw multi-agent systems*

---

## 1. Spawn-to-Session Contract Tests

### Test: Verify Agent Output Format
```python
# test_agent_contract.py
async def test_research_agent_output():
    """Ensure research agent produces consumable output"""
    spawn_result = await sessions_spawn({
        "task": "Research X and write to output/x_research.md",
        "agentId": "researcher"
    })
    
    # Contract: Must return sessionKey
    assert "sessionKey" in spawn_result
    
    # Contract: Must create expected file
    await subagents_poll(spawn_result["sessionKey"], timeout=120)
    assert os.path.exists("output/x_research.md")
    
    # Contract: Content must have required sections
    content = read("output/x_research.md")
    assert "## Summary" in content
    assert "## Sources" in content
```

---

## 2. Multi-Agent Chain Validation

### Test: End-to-End Research→Synthesis Pipeline
```python
# test_research_pipeline.py
async def test_research_to_synthesis_chain():
    """Verify dependency chain works correctly"""
    
    # Phase 1: Spawn researcher
    research_job = await sessions_spawn({
        "task": "Research topic X, save to /tmp/research.json",
        "label": "research-phase"
    })
    
    # Wait completion
    research_result = await wait_for_completion(research_job["sessionKey"])
    assert research_result["status"] == "completed"
    
    # Phase 2: Spawn analyst with research output
    analysis_job = await sessions_spawn({
        "task": f"Analyze {research_result['output_path']}, write insights to /tmp/analysis.md",
        "label": "analysis-phase"
    })
    
    analysis_result = await wait_for_completion(analysis_job["sessionKey"])
    
    # Validate final output
    assert os.path.exists("/tmp/analysis.md")
    assert file_size("/tmp/analysis.md") > 500  # Has content
```

---

## 3. Error Handling & Recovery Tests

### Test: Graceful Timeout Handling
```python
# test_error_resilience.py
async def test_spawn_timeout_recovery():
    """Verify system handles slow agents gracefully"""
    
    spawn_result = await sessions_spawn({
        "task": "Long-running task that might timeout",
        "runTimeoutSeconds": 30  # Short timeout for test
    })
    
    # Should return immediately with sessionKey
    assert "sessionKey" in spawn_result
    
    # Poll for status
    status = await subagents({
        "action": "list",
        "target": spawn_result["sessionKey"]
    })
    
    # Must have status field regardless of outcome
    assert "status" in status
    
    # If timeout occurred, should be marked accordingly
    if status["status"] == "timeout":
        # Verify cleanup occurred
        assert not os.path.exists(spawn_result.get("tempPath", "/dev/null"))
```

### Test: Invalid Input Handling
```python
async def test_agent_handles_bad_input():
    """Verify agent fails gracefully with malformed input"""
    
    # Create intentionally bad input file
    write("/tmp/bad_input.json", "not valid json{}")
    
    spawn_result = await sessions_spawn({
        "task": "Process /tmp/bad_input.json and report errors",
        "label": "error-test"
    })
    
    result = await wait_for_completion(spawn_result["sessionKey"])
    
    # Should complete (not hang) with error noted
    assert result["completed"] is True
    assert "error" in result.get("output", "").lower() or \
           "failed" in result.get("output", "").lower()
```

---

## 4. Resource Cleanup Verification

### Test: Cleanup Flag Behaviors
```python
# test_resource_cleanup.py
async def test_cleanup_modes():
    """Verify cleanup options work as expected"""
    
    temp_files = []
    
    # Test 1: cleanup='always' removes files
    job1 = await sessions_spawn({
        "task": "Write to /tmp/temp_test_1.txt then exit",
        "cleanup": "always"
    })
    await wait_for_completion(job1["sessionKey"])
    assert not os.path.exists("/tmp/temp_test_1.txt")
    
    # Test 2: cleanup='success' removes only on success
    job2 = await sessions_spawn({
        "task": "Write to /tmp/temp_test_2.txt",
        "cleanup": "success"
    })
    await wait_for_completion(job2["sessionKey"])
    # If succeeded, file should be gone
    if job2["status"] == "completed":
        assert not os.path.exists("/tmp/temp_test_2.txt")
    
    # Test 3: No cleanup leaves files
    job3 = await sessions_spawn({
        "task": "Write to /tmp/temp_test_3.txt"
    })
    await wait_for_completion(job3["sessionKey"])
    assert os.path.exists("/tmp/temp_test_3.txt")  # Still there
```

---

## 5. Context Handoff Integrity Tests

### Test: Verify Context Propagation
```python
# test_context_handoff.py
async def test_context_preserved_across_spawns():
    """Ensure critical context flows through agent chain"""
    
    original_context = {
        "project_id": "PROJ-123",
        "deadline": "2026-02-20",
        "constraints": ["budget < $1000", "use Python"]
    }
    
    # Write context file
    write("/tmp/context.json", json.dumps(original_context))
    
    # Spawn agent that reads and extends context
    job = await sessions_spawn({
        "task": "Read /tmp/context.json, add 'status: processing', save to /tmp/context_v2.json",
    })
    
    await wait_for_completion(job["sessionKey"])
    
    # Verify original context preserved + new fields added
    v2 = json.loads(read("/tmp/context_v2.json"))
    assert v2["project_id"] == "PROJ-123"  # Original preserved
    assert v2["deadline"] == "2026-02-20"
    assert v2["status"] == "processing"  # New field added
```

---

## Quick Test Runner Template

```python
# run_tests.py
async def main():
    tests = [
        test_research_agent_output,
        test_research_to_synthesis_chain,
        test_spawn_timeout_recovery,
        test_cleanup_modes,
        test_context_preserved_across_spawns
    ]
    
    results = []
    for test in tests:
        try:
            await test()
            results.append((test.__name__, "PASS"))
        except AssertionError as e:
            results.append((test.__name__, f"FAIL: {e}"))
        except Exception as e:
            results.append((test.__name__, f"ERROR: {e}"))
    
    # Summary
    passed = sum(1 for _, r in results if r == "PASS")
    print(f"Results: {passed}/{len(results)} passed")
    for name, result in results:
        status = "✓" if result == "PASS" else "✗"
        print(f"  {status} {name}: {result}")
```

---

## Testing Checklist

Before deploying multi-agent workflows:
- [ ] Each spawn has defined output contract
- [ ] Timeout scenarios handled
- [ ] Cleanup verified for each cleanup mode used
- [ ] Error paths tested with invalid inputs
- [ ] Context propagation verified end-to-end
- [ ] File dependencies checked (existence + format)

---

*Generated: 2026-02-19 | Use: Copy patterns into your test suite*
