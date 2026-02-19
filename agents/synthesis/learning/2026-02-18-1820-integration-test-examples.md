# Integration Testing for Multi-Agent Systems
## Quick Reference Guide

*Created: 2026-02-18 | 15-min practical guide*

---

## 1. Test Categories

| Type | Scope | When to Use |
|------|-------|-------------|
| **Unit** | Single agent logic | Agent in isolation |
| **Contract** | Agent A ↔ Agent B interface | Schema validation |
| **Integration** | Agent A + Agent B working together | Coordination flows |
| **End-to-End** | Full workflow chains | Business scenarios |

---

## 2. Essential Test Patterns

### Pattern A: Mock Agent Substitution
```python
# Replace real agent with controlled mock
def test_with_mock_agent():
    mock_agent = MockAgent(responses=["analysis", "result"])
    orchestrator = Orchestrator(agents={"analyzer": mock_agent})
    
    result = orchestrator.run("task")
    
    assert mock_agent.call_count == 2
    assert "result" in result
```

### Pattern B: Message Capture & Replay
```python
# Record real messages, replay in tests
class MessageRecorder:
    def __init__(self):
        self.messages = []
    
    def capture(self, msg):
        self.messages.append(msg.to_dict())
        
    def replay(self, test_agents):
        for msg in self.messages:
            test_agents.inject(msg)
```

### Pattern C: State Snapshot Validation
```python
def test_state_handoff():
    agent_a = AgentA()
    agent_b = AgentB()
    
    # Run agent A to completion
    state_a = agent_a.run("input")
    
    # Transfer and validate state integrity
    state_b = agent_b.hydrate(state_a.export())
    
    assert state_b.context_completeness == 1.0
    assert state_b.has_required_keys(["task", "metadata"])
```

---

## 3. Critical Integration Test Cases

### Case 1: Happy Path Coordination
```yaml
test: "Two-agent task handoff"
agent_a_role: "decomposer"
agent_b_role: "executor"
input: "Create Python function for factorial"
expected:
  - agent_a.outputs.subtasks.length >= 2
  - agent_b.receives.all_subtasks
  - final_output.contains("def factorial")
  - execution_time < 10s
```

### Case 2: Timeout & Recovery
```yaml
test: "Agent timeout escalation"
agent_x_timeout: 2s
agent_x_behavior: "sleep_5s"
escalation_agent: "agent_y"
expected:
  - agent_x.receives_interrupt
  - agent_y.activates_within_500ms
  - final_output.status == "recovered"
```

### Case 3: Context Preservation
```yaml
test: "Long-chain context retention"
agents: [A, B, C, D]
input: "Remember X=42, then calculate X*Y where Y=3"
expected:
  - D.output == 126
  - no_agent_requests_repeat_info
  - each_agent.context.includes[original_input]
```

### Case 4: Concurrent Execution
```yaml
test: "Parallel agent execution"
parallels: 3
max_parallel_time: 8s
sequential_time_estimate: 20s
expected:
  - total_time < 10s
  - no_race_conditions
  - results.completeness == 100%
```

### Case 5: Schema Violation Handling
```yaml
test: "Malformed message handling"
agent_a.output_format: "broken_json"
expected:
  - validation_layer.catches_error
  - retry_count >= 1
  - or: dead_letter_queue.receives_message
  - system.continues_operating
```

---

## 4. Test Data Strategy

| Fixture | Purpose |
|---------|---------|
| `minimal_task` | Fast feedback ( < 1s ) |
| `complex_decomposition` | Stress recursion limits |
| `empty_input` | Error boundary testing |
| `unicode_heavy` | Encoding edge cases |
| `nested_objects_depth_10` | Stack/overflow checks |

---

## 5. CI/CD Integration

```yaml
# .github/workflows/integration.yml
name: Agent Integration Tests
on: [push, pr]
jobs:
  test:
    steps:
      - uses: actions/checkout@v4
      - name: Start mock environment
        run: docker-compose -f tests/docker-compose.yml up -d
      - name: Run integration suite
        run: pytest tests/integration -v --timeout=300
      - name: Cleanup
        run: docker-compose down
```

---

## 6. Quick Commands

```bash
# Run specific integration test
pytest tests/integration/test_coordination.py -v -s

# Run with timing analysis
pytest --durations=10

# Run in parallel (requires pytest-xdist)
pytest -n 4 --dist=loadfile

# Generate coverage report
pytest --cov=agents --cov-report=html
```

---

## 7. Anti-Patterns to Avoid

❌ Testing real LLMs in CI (non-deterministic, slow)
❌ Shared state between tests (isolation breaks)
❌ Hardcoded sleep() (use proper sync primitives)
❌ Testing implementation details (test behavior, not code)
❌ Large test suites without parallelization

---

**Next Steps:**
1. Pick one pattern - implement it
2. Add one contract test for your most critical agent pair
3. Set up CI with mocked LLM responses
