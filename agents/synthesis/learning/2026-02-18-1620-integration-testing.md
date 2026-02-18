# Integration Testing for Multi-Agent Systems
*Synthesis Learning Log | 2026-02-18*

## Overview

Integration tests verify that agent deliverables work together correctly. Unlike unit tests (agents test their own code), integration tests validate handoffs, contracts, and end-to-end workflows.

---

## 1. Contract Testing

### Purpose
Verify that Agent A's output matches what Agent B expects.

### Oracle → Ghost Contract Test
```python
# test_strategy_contract.py
import json
import pytest
from pydantic import BaseModel, ValidationError

class StrategySpec(BaseModel):
    """Contract: What Oracle must deliver to Ghost"""
    name: str
    entry_conditions: list[str]
    exit_conditions: list[str]
    position_sizing: dict  # {type: "fixed", value: 0.1}
    risk_parameters: dict  # {stop_loss: float, take_profit: float}
    timeframes: list[str]
    
def test_oracle_deliverable_valid():
    """Oracle's strategy spec must match Ghost's expected schema"""
    spec = load_from("agents/oracle/deliverables/latest_strategy.json")
    
    # Contract validation
    try:
        validated = StrategySpec(**spec)
        assert validated.risk_parameters["stop_loss"] > 0
        assert validated.risk_parameters["take_profit"] > validated.risk_parameters["stop_loss"]
    except ValidationError as e:
        pytest.fail(f"Oracle output violates contract: {e}")
```

### Ghost → Synthesis Contract Test
```python
# test_code_delivery_contract.py
import ast
import os

def test_ghost_deliverable_structure():
    """Ghost must deliver executable Python with required entry points"""
    code_path = "agents/ghost/deliverables/strategy_impl.py"
    
    assert os.path.exists(code_path), "Ghost deliverable missing"
    
    with open(code_path) as f:
        source = f.read()
    
    # Parse AST for required structure
    tree = ast.parse(source)
    
    # Must have execute() function
    functions = [node.name for node in ast.walk(tree) 
                 if isinstance(node, ast.FunctionDef)]
    assert "execute" in functions, "Missing execute() entry point"
    
    # Must have proper error handling
    has_try = any(isinstance(node, ast.Try) for node in ast.walk(tree))
    assert has_try, "No exception handling found"
```

---

## 2. End-to-End Integration Tests

### Full Workflow: Strategy → Code → Validation
```python
# test_e2e_strategy_pipeline.py
import subprocess
import tempfile
import os

class TestStrategyPipeline:
    """
    E2E: Oracle designs → Ghost implements → Synthesis validates
    """
    
    def test_momentum_bot_workflow(self):
        """Full pipeline: momentum strategy from design to executable"""
        
        # Phase 1: Oracle designs strategy
        oracle_result = spawn_oracle_agent(
            task="Design momentum strategy for SOL/USDC",
            timeout=300
        )
        assert oracle_result.returncode == 0
        strategy = load_json(oracle_result.output_path)
        
        # Phase 2: Ghost implements
        ghost_result = spawn_ghost_agent(
            task=f"Implement strategy: {strategy['name']}",
            inputs={"spec": strategy},
            timeout=600
        )
        assert ghost_result.returncode == 0
        
        # Phase 3: Verify implementation matches spec
        code = load_file(ghost_result.code_path)
        
        # Entry logic exists
        assert any(cond in code for cond in strategy["entry_conditions"])
        
        # Risk parameters match
        assert str(strategy["risk_parameters"]["stop_loss"]) in code
        assert str(strategy["risk_parameters"]["take_profit"]) in code
        
        # Phase 4: Can it run?
        self._test_code_executable(ghost_result.code_path)
    
    def _test_code_executable(self, code_path):
        """Quick smoke test - imports and basic structure"""
        result = subprocess.run(
            ["python", "-c", f"import ast; ast.parse(open('{code_path}').read())"],
            capture_output=True,
            timeout=10
        )
        assert result.returncode == 0, f"Code won't parse: {result.stderr}"
```

---

## 3. Interface Tests

### Testing Agent Handoffs
```python
# test_handoff_integrity.py
import hashlib
import json

def test_context_preserved_oracle_to_ghost():
    """Critical context must survive handoff"""
    
    # Original Oracle output
    oracle_output = load_json("agents/oracle/output.json")
    
    # What Ghost claims to have received
    ghost_received = load_json("agents/ghost/last_input.json")
    
    # Key fields must match exactly
    critical_fields = ["risk_parameters", "timeframes", "asset_pair"]
    
    for field in critical_fields:
        assert oracle_output[field] == ghost_received[field], \
            f"Context lost in handoff: {field}"
        
        # Verify no mutation occurred
        orig_hash = hashlib.md5(json.dumps(oracle_output[field]).encode()).hexdigest()
        recv_hash = hashlib.md5(json.dumps(ghost_received[field]).encode()).hexdigest()
        assert orig_hash == recv_hash, f"Data corruption in {field}"
```

---

## 4. Regression Tests

### Preventing Repeat Failures
```python
# test_regression.py
REGRESSION_CASES = [
    {
        "id": "GHOST-001",
        "description": "Ghost forgot to handle API timeout",
        "trigger": "spawn ghost with network task",
        "check": "code contains timeout parameter"
    },
    {
        "id": "ORACLE-003", 
        "description": "Oracle delivered stop_loss >= take_profit",
        "trigger": "check risk_parameters",
        "check": "stop_loss < take_profit"
    }
]

def test_regression_suite():
    """Run all regression cases against latest deliverables"""
    for case in REGRESSION_CASES:
        result = check_regression_case(case)
        assert result.passed, f"Regression {case['id']}: {case['description']}"
```

---

## 5. Mock Patterns for Agent Dependencies

### When Testing Synthesis Integration
```python
# test_synthesis_integration.py
from unittest.mock import Mock, patch

def test_synthesis_with_mocked_agents():
    """Test coordination logic without spawning real agents"""
    
    mock_oracle = Mock()
    mock_oracle.spawn.return_value = Mock(
        returncode=0,
        output_path="test/fixtures/oracle_output.json"
    )
    
    mock_ghost = Mock()
    mock_ghost.spawn.return_value = Mock(
        returncode=0,
        code_path="test/fixtures/ghost_output.py"
    )
    
    with patch.dict('agents', {'oracle': mock_oracle, 'ghost': mock_ghost}):
        result = synthesis.coordinate("Build momentum bot")
        
        # Verify correct sequence
        mock_oracle.spawn.assert_called_once()
        mock_ghost.spawn.assert_called_once()
        
        # Verify Ghost received Oracle's output
        ghost_input = mock_ghost.spawn.call_args[1]['inputs']
        assert 'strategy' in ghost_input
```

---

## 6. Automated Integration Checklist

```python
# integration_checklist.py
CHECKS = {
    "pre_spawn": [
        ("input_schema_valid", "Input matches agent's expected schema"),
        ("dependencies_exist", "All file dependencies present"),
        ("timeout_set", "Non-default timeout configured"),
    ],
    "post_spawn": [
        ("returncode_zero", "Agent exited successfully"),
        ("output_exists", "Deliverable file exists"),
        ("output_valid", "Output passes schema validation"),
        ("no_timeout", "Completed within allocated time"),
    ],
    "handoff": [
        ("critical_fields_preserved", "Key data unchanged across handoff"),
        ("context_complete", "No missing context from prior steps"),
        ("format_correct", "Output format matches input schema of next agent"),
    ]
}

def run_integration_checklist(agent_result, phase):
    """Run all checks for a given phase."""
    for check_id, description in CHECKS[phase]:
        passed = run_check(check_id, agent_result)
        assert passed, f"Integration check failed: {description}"
```

---

## 7. Continuous Integration Pattern

```yaml
# .github/workflows/agent-integration.yml
name: Agent Integration Tests

on:
  push:
    paths:
      - 'agents/**/deliverables/**'
      - 'test_integration/**'

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Contract Tests
        run: pytest test/contract/ -v
      
  handoff-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Context Preservation Tests
        run: pytest test/handoff/ -v
      
  e2e-tests:
    runs-on: ubuntu-latest
    needs: [contract-tests, handoff-tests]
    steps:
      - uses: actions/checkout@v4
      - name: End-to-End Pipeline
        run: pytest test/e2e/ -v --timeout=1200
```

---

## 8. Failure Mode Testing

```python
# test_failure_modes.py

def test_oracle_failure_handling():
    """Synthesis must handle Oracle failure gracefully"""
    
    # Simulate Oracle failure
    with patch('agents.oracle.spawn') as mock:
        mock.return_value = Mock(returncode=1, stderr="Strategy validation failed")
        
        result = synthesis.coordinate("Build bot")
        
        # Should not proceed with failed Oracle
        assert result.status == "blocked"
        assert "Oracle" in result.block_reason
        assert not result.ghost_spawned  # Ghost never spawned

def test_ghost_timeout_recovery():
    """Partial results on timeout must be captured"""
    
    with patch('agents.ghost.spawn') as mock:
        mock.return_value = Mock(
            returncode=None,  # Timeout
            output_path="ghost_partial.py",
            partial_results={"lines_written": 45}
        )
        
        result = synthesis.coordinate("Build bot")
        
        # Save partial for debugging
        assert result.partial_output_path.exists()
```

---

## Quick Reference: When to Add Tests

| Scenario | Test Type | Priority |
|----------|-----------|----------|
| New agent added | Contract tests | Required |
| Handoff format changes | Handoff tests | Required |
| New workflow pattern | E2E test | High |
| Agent bug found | Regression test | Required |
| Timeout issues | Failure mode tests | Medium |

---

## Remember

**Integration tests validate connections, not implementations.** Agents test their own code. Synthesis tests that they connect correctly.

**Fail fast on contract violations.** Don't let bad data propagate downstream.

**Capture partial results.** When agents timeout or fail, save what they completed for debugging.
