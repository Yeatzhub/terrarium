# Multi-Agent Workflow Implementation Templates
*Synthesis Learning — 2026-02-20*

Ready-to-use templates implementing patterns from coordination, testing, optimization, and quality standards guides.

## 1. Basic Fan-Out Template

```python
# fanout_workflow.py - Parallel task execution
import asyncio
from datetime import datetime

async def fanout_workflow(tasks, agent_id="generalist", timeout=120):
    """
    Spawn multiple agents in parallel, aggregate results.
    
    Args:
        tasks: List of task descriptions
        agent_id: Agent type to spawn
        timeout: Seconds per task
    
    Returns:
        {results: [], completed: N, failed: N, duration_ms: N}
    """
    start = datetime.now()
    
    # Spawn all tasks
    spawns = [
        sessions_spawn({
            "task": task,
            "agentId": agent_id,
            "timeoutSeconds": timeout,
            "label": f"fanout-{i}"
        })
        for i, task in enumerate(tasks)
    ]
    
    # Wait for all with individual timeout protection
    results = await asyncio.gather(*spawns, return_exceptions=True)
    
    # Categorize results
    completed = [r for r in results if not isinstance(r, Exception) and r.get("completed")]
    failed = [r for r in results if isinstance(r, Exception) or not r.get("completed")]
    
    # Quality gate: Check success rate
    success_rate = len(completed) / len(tasks)
    if success_rate < 0.8:
        return {
            "error": f"Success rate {success_rate:.0%} below 80% threshold",
            "failed_tasks": failed,
            "retry_recommended": True
        }
    
    return {
        "results": completed,
        "completed": len(completed),
        "failed": len(failed),
        "duration_ms": (datetime.now() - start).total_seconds() * 1000,
        "success_rate": success_rate
    }

# Usage
workflow = await fanout_workflow([
    "Analyze Q1 revenue trends",
    "Analyze Q1 cost breakdown", 
    "Analyze Q1 customer churn"
], agent_id="analyst", timeout=90)
```

---

## 2. Pipeline Chain Template

```python
# pipeline_workflow.py - Sequential agent chain
import json

class Pipeline:
    def __init__(self, stages, checkpoint_dir="./checkpoints"):
        """
        Sequential pipeline with automatic checkpointing.
        
        Args:
            stages: [{name, agent_id, task_template, validate}]
            checkpoint_dir: Where to save state
        """
        self.stages = stages
        self.checkpoint_dir = checkpoint_dir
        self.state = {"current_stage": 0, "outputs": {}}
    
    async def run(self, initial_input):
        """Execute pipeline with resume capability."""
        self.state["input"] = initial_input
        
        for i, stage in enumerate(self.stages[self.state["current_stage"]:]):
            stage_num = self.state["current_stage"] + i
            
            # Prepare task with accumulated context
            task = stage["task_template"].format(
                input=self.state["input"],
                **self.state["outputs"]
            )
            
            # Spawn agent
            result = await sessions_spawn({
                "task": task,
                "agentId": stage["agent_id"],
                "timeoutSeconds": stage.get("timeout", 300),
                "label": f"pipeline-{stage['name']}"
            })
            
            # Validate output
            if stage.get("validate") and not stage["validate"](result):
                return {
                    "error": f"Stage {stage['name']} validation failed",
                    "stage": stage_num,
                    "result": result
                }
            
            # Save output and checkpoint
            self.state["outputs"][stage["name"]] = result
            self.state["current_stage"] = stage_num + 1
            await self._checkpoint()
        
        return self.state["outputs"]
    
    async def _checkpoint(self):
        """Write state for recovery."""
        filename = f"{self.checkpoint_dir}/pipeline-{datetime.now():%Y%m%d-%H%M%S}.json"
        await write_file(filename, json.dumps(self.state, indent=2))

# Usage Example
pipeline = Pipeline([
    {
        "name": "research",
        "agent_id": "researcher",
        "task_template": "Research: {input}",
        "timeout": 120
    },
    {
        "name": "design",
        "agent_id": "architect", 
        "task_template": "Design architecture based on research:\n{research}",
        "validate": lambda r: "architecture" in r.get("output", "").lower()
    },
    {
        "name": "implement",
        "agent_id": "coder",
        "task_template": "Generate code for design:\n{design}",
        "timeout": 180
    }
])

result = await pipeline.run("Build OAuth2 authentication system")
```

---

## 3. Circuit Breaker Template

```python
# circuit_breaker.py - Fail-fast for unreliable agents
from datetime import datetime, timedelta

class CircuitBreaker:
    def __init__(self, failure_threshold=3, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.last_failure = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, fn, *args, **kwargs):
        """Execute fn with circuit breaker protection."""
        
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                return {
                    "error": "Circuit open - too many failures",
                    "fallback": True,
                    "retry_after": self._time_until_reset()
                }
        
        try:
            result = await fn(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        self.failure_count += 1
        self.last_failure = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
    
    def _should_attempt_reset(self):
        return (datetime.now() - self.last_failure).seconds > self.recovery_timeout
    
    def _time_until_reset(self):
        elapsed = (datetime.now() - self.last_failure).seconds
        return max(0, self.recovery_timeout - elapsed)

# Usage
breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=60)

async def spawn_with_protection(task, agent_id):
    return await breaker.call(
        sessions_spawn,
        {"task": task, "agentId": agent_id, "timeoutSeconds": 120}
    )
```

---

## 4. Context Manager Template

```python
# context_manager.py - Efficient context handoff
class ContextManager:
    def __init__(self, max_tokens=2000, state_file=None):
        self.max_tokens = max_tokens
        self.state_file = state_file or "./workflow_state.json"
        self.history = []
    
    def add(self, agent_id, task, output, decisions=None):
        """Add checkpoint to history."""
        entry = {
            "agent": agent_id,
            "task_summary": self._summarize(task, 100),
            "output_summary": self._summarize(output, 200),
            "decisions": decisions or [],
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(entry)
        self._persist()
    
    def get_handoff_context(self, include_recent=3):
        """Generate optimized handoff context."""
        # Keep only N most recent + key decisions
        recent = self.history[-include_recent:]
        key_decisions = [e for e in self.history if e["decisions"]]
        
        context = {
            "workflow_state": f"file:{self.state_file}",
            "recent_activity": recent,
            "key_decisions": key_decisions[-5:],  # Last 5 decisions
            "current_stage": len(self.history)
        }
        
        # Prune if too large
        context_str = json.dumps(context)
        if len(context_str) > self.max_tokens * 4:  # Rough chars-to-tokens
            context = self._prune(context)
        
        return context
    
    def _summarize(self, text, max_len):
        """Truncate with ellipsis."""
        return text[:max_len] + "..." if len(text) > max_len else text
    
    def _persist(self):
        """Write to shared state file."""
        with open(self.state_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def _prune(self, context):
        """Aggressive pruning for size constraints."""
        return {
            "workflow_state": context["workflow_state"],
            "stage_count": context["current_stage"],
            "last_decision": context["key_decisions"][-1] if context["key_decisions"] else None
        }

# Usage
ctx = ContextManager(max_tokens=1500, state_file="./my_workflow/state.json")

# After each agent completes
ctx.add("researcher", task, output, decisions=["Use PostgreSQL", "JWT auth"])

# Get context for next agent
next_context = ctx.get_handoff_context()
sessions_send({
    "sessionKey": next_session,
    "message": f"Continue workflow. Context: {json.dumps(next_context)}"
})
```

---

## 5. Quality Gate Template

```python
# quality_gate.py - Pre-delivery validation
class QualityGate:
    def __init__(self, standards):
        self.standards = standards
        self.checks = []
    
    def add_check(self, name, fn, required=True):
        """Add validation check."""
        self.checks.append({"name": name, "fn": fn, "required": required})
        return self
    
    async def validate(self, deliverables):
        """Run all checks in order (fast-first)."""
        results = []
        
        # Sort by speed: required first, then optional
        for check in self.checks:
            try:
                passed = await check["fn"](deliverables)
                results.append({
                    "check": check["name"],
                    "passed": passed,
                    "required": check["required"]
                })
                
                if not passed and check["required"]:
                    return {
                        "passed": False,
                        "failed_check": check["name"],
                        "results": results
                    }
            except Exception as e:
                results.append({
                    "check": check["name"],
                    "passed": False,
                    "error": str(e)
                })
                if check["required"]:
                    return {"passed": False, "error": str(e)}
        
        return {"passed": True, "results": results}

# Pre-built checks
def file_exists_check(deliverables):
    return all(os.path.exists(f) for f in deliverables.get("files", []))

def no_todos_check(deliverables):
    for f in deliverables.get("files", []):
        content = open(f).read()
        if "TODO" in content or "FIXME" in content:
            return False
    return True

def json_valid_check(deliverables):
    for f in deliverables.get("json_files", []):
        try:
            json.load(open(f))
        except:
            return False
    return True

# Usage
gate = QualityGate({})
gate.add_check("files_exist", file_exists_check, required=True)
gate.add_check("no_todos", no_todos_check, required=True)
gate.add_check("json_valid", json_valid_check, required=False)

result = await gate.validate({
    "files": ["output.md", "data.json"],
    "json_files": ["data.json"]
})

if not result["passed"]:
    print(f"Quality gate failed: {result['failed_check']}")
```

---

## 6. Error Recovery Template

```python
# error_recovery.py - Automatic retry and fallback
class ErrorRecovery:
    def __init__(self, max_retries=3, backoff_base=2):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
    
    async def execute_with_recovery(self, fn, *args, **kwargs):
        """Execute with automatic retry and escalation."""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                # Exponential backoff
                wait = self.backoff_base ** attempt
                await asyncio.sleep(wait)
                
                # Log for analysis
                print(f"Attempt {attempt + 1} failed, retrying after {wait}s: {e}")
        
        # All retries exhausted
        return await self._escalate(last_error, fn, args, kwargs)
    
    async def _escalate(self, error, fn, args, kwargs):
        """Determine escalation path."""
        error_type = self._classify_error(error)
        
        if error_type == "TRANSIENT":
            # Try fallback agent
            fallback_agent = kwargs.get("fallback_agent")
            if fallback_agent:
                kwargs["agentId"] = fallback_agent
                return await fn(*args, **kwargs)
        
        elif error_type == "INPUT":
            # Return for user fix
            return {
                "error": "Input validation failed",
                "details": str(error),
                "action_required": "Fix input and retry"
            }
        
        elif error_type == "CAPACITY":
            # Queue for later
            return {
                "error": "System capacity exceeded",
                "queued": True,
                "retry_after": "300s"
            }
        
        # Unknown - escalate to parent/user
        return {
            "error": "Unrecoverable error",
            "details": str(error),
            "escalation": "user"
        }
    
    def _classify_error(self, error):
        """Classify error for appropriate handling."""
        error_str = str(error).lower()
        if any(x in error_str for x in ["timeout", "network", "temporarily"]):
            return "TRANSIENT"
        elif any(x in error_str for x in ["invalid", "missing", "parse"]):
            return "INPUT"
        elif any(x in error_str for x in ["capacity", "rate limit", "quota"]):
            return "CAPACITY"
        return "UNKNOWN"

# Usage
recovery = ErrorRecovery(max_retries=3)

result = await recovery.execute_with_recovery(
    sessions_spawn,
    {"task": "Complex analysis", "agentId": "analyst"},
    fallback_agent="generalist"  # Simpler agent if primary fails
)
```

---

## 7. Workflow Orchestrator (Full Integration)

```python
# orchestrator.py - Complete workflow management
class Orchestrator:
    def __init__(self, config):
        self.config = config
        self.ctx = ContextManager(state_file=config.get("state_file"))
        self.quality_gate = QualityGate(config.get("standards", {}))
        self.recovery = ErrorRecovery()
        self.circuits = {}  # Per-agent circuit breakers
    
    async def run_workflow(self, definition, input_data):
        """
        Run complete workflow with all safeguards.
        
        Args:
            definition: Workflow graph or pipeline definition
            input_data: Initial input
        """
        workflow_id = f"wf-{datetime.now():%Y%m%d-%H%M%S}"
        
        try:
            # Execute based on type
            if definition["type"] == "fanout":
                result = await self._run_fanout(definition, input_data)
            elif definition["type"] == "pipeline":
                result = await self._run_pipeline(definition, input_data)
            else:
                raise ValueError(f"Unknown workflow type: {definition['type']}")
            
            # Quality gate
            quality = await self.quality_gate.validate(result.get("deliverables", {}))
            
            return {
                "workflow_id": workflow_id,
                "success": quality["passed"],
                "result": result,
                "quality": quality
            }
            
        except Exception as e:
            return {
                "workflow_id": workflow_id,
                "success": False,
                "error": str(e),
                "checkpoint": self.ctx.state_file
            }
    
    async def _run_fanout(self, defn, input_data):
        """Execute fanout with circuit breakers."""
        agent_id = defn["agent_id"]
        
        # Get or create circuit breaker
        if agent_id not in self.circuits:
            self.circuits[agent_id] = CircuitBreaker()
        
        tasks = [d.format(input=input_data) for d in defn["tasks"]]
        
        # Use circuit breaker for each spawn
        results = []
        for task in tasks:
            result = await self.circuits[agent_id].call(
                sessions_spawn,
                {"task": task, "agentId": agent_id, "timeoutSeconds": defn.get("timeout", 120)}
            )
            results.append(result)
        
        return {"results": results, "type": "fanout"}
    
    async def _run_pipeline(self, defn, input_data):
        """Execute pipeline with recovery and checkpoints."""
        pipeline = Pipeline(defn["stages"])
        
        for stage in pipeline.stages:
            # Wrap with recovery
            result = await self.recovery.execute_with_recovery(
                self._run_stage,
                stage,
                input_data
            )
            
            # Update context
            self.ctx.add(stage["agent_id"], stage["task_template"], result)
        
        return pipeline.state["outputs"]

# Usage
orch = Orchestrator({
    "state_file": "./my_workflow/state.json",
    "standards": {"require_tests": True}
})

result = await orch.run_workflow({
    "type": "fanout",
    "agent_id": "analyst",
    "tasks": [
        "Analyze revenue for {input}",
        "Analyze costs for {input}",
        "Analyze growth for {input}"
    ],
    "timeout": 90
}, "Q1 2026")
```

---

## Quick Start: Copy-Paste Workflow

```python
# Minimal working example
import asyncio

async def main():
    # 1. Fan-out parallel analysis
    parallel = await sessions_spawn({
        "task": "Analyze market trends",
        "agentId": "analyst",
        "timeoutSeconds": 120
    })
    
    # 2. Sequential refinement
    refined = await sessions_spawn({
        "task": f"Synthesize findings: {parallel['output']}",
        "agentId": "synthesizer",
        "timeoutSeconds": 90
    })
    
    # 3. Quality check
    if len(refined['output']) < 100:
        return {"error": "Output too short"}
    
    return refined

# Run it
result = asyncio.run(main())
```

---

*These templates implement the patterns from the 0420, 0620, 0820, and 1020 learning documents. Customize timeouts, thresholds, and validation logic for your specific workflows.*
