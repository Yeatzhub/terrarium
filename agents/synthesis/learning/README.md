# Getting Started with Multi-Agent Workflows
*Synthesis Learning — 2026-02-20*

Start here. Complete curriculum from fundamentals to production.

---

## Learning Path

### Level 1: Fundamentals (Start Here)
1. **[Quick Reference](2026-02-20-2020-quick-reference.md)** — Commands, patterns, thresholds, one-liners
2. **[Coordination Patterns](2026-02-20-0420-multi-agent-coordination-patterns.md)** — Fan-out, Pipeline, Map-Reduce, Circuit Breaker

**Time**: 30 minutes  
**Goal**: Understand when to use which pattern

---

### Level 2: Building (Do Next)
3. **[Implementation Templates](2026-02-20-1220-implementation-templates.md)** — Copy-paste Python code for common workflows
4. **[Case Studies](2026-02-20-1620-case-studies.md)** — 6 complete real-world examples

**Time**: 1 hour  
**Goal**: Start building with working code

---

### Level 3: Quality (Essential)
5. **[Integration Test Examples](2026-02-20-0620-integration-test-examples.md)** — 6 test patterns with code
6. **[Quality Standards](2026-02-20-1020-quality-standards.md)** — Output, agent, workflow quality gates

**Time**: 45 minutes  
**Goal**: Build reliable, testable workflows

---

### Level 4: Optimization (Scale)
7. **[Workflow Optimization](2026-02-20-0820-workflow-optimization-guides.md)** — Performance, efficiency, cost reduction

**Time**: 30 minutes  
**Goal**: Make workflows fast and economical

---

### Level 5: Operations (Production)
8. **[Best Practices](2026-02-20-1820-best-practices.md)** — 8 anti-patterns and how to avoid them
9. **[Debugging Guide](2026-02-20-1420-debugging-guide.md)** — Diagnose and fix common failures

**Time**: 45 minutes  
**Goal**: Run workflows in production confidently

---

## Quick Start: First Workflow

```python
# 20-line complete example
import asyncio

async def first_workflow():
    """Your first multi-agent workflow."""
    
    # Step 1: Parallel research (Fan-out)
    research = await asyncio.gather(
        sessions_spawn({
            "task": "Research: OAuth2 flows",
            "agentId": "researcher",
            "timeoutSeconds": 60
        }),
        sessions_spawn({
            "task": "Research: JWT best practices", 
            "agentId": "researcher",
            "timeoutSeconds": 60
        })
    )
    
    # Step 2: Synthesize findings (Pipeline)
    design = await sessions_spawn({
        "task": f"Design auth system based on:\n{research[0]['output']}\n{research[1]['output']}",
        "agentId": "architect",
        "timeoutSeconds": 90
    })
    
    # Step 3: Implementation with validation
    code = await sessions_spawn({
        "task": f"Generate Python code:\n{design['output']}",
        "agentId": "coder",
        "timeoutSeconds": 120
    })
    
    # Quality gate
    if not code.get("completed") or len(code.get("output", "")) < 100:
        return {"error": "Code generation failed"}
    
    return {
        "research_completed": 2,
        "design": design["output"][:200],
        "code_length": len(code["output"]),
        "status": "success"
    }

# Run it
result = asyncio.run(first_workflow())
print(f"Workflow complete: {result}")
```

**What it demonstrates**:
- Fan-out: Parallel research tasks
- Pipeline: Sequential design → code
- Timeout: Every spawn has limit
- Validation: Quality gate before return

---

## Common First Tasks

| Your Goal | Pattern | See |
|-----------|---------|-----|
| Research multiple topics | Fan-out | Case Study 4 |
| Build a feature | Pipeline | Case Study 5 |
| Process files | Map-Reduce | Case Study 6 |
| Code review | Fan-out + Gate | Case Study 1 |
| Generate docs | Map-Reduce + Polish | Case Study 2 |
| Handle incident | Parallel + Escalation | Case Study 3 |

---

## Decision Quick-Reference

```
Task length? → 
  < 30s: Inline (no agent)
  30s-5min: Single agent
  > 5min: Decompose

Dependencies? →
  None: Fan-out
  Linear: Pipeline  
  Complex DAG: Orchestrator

Data size? →
  Small (<100 items): Direct
  Medium (100-1000): Batched
  Large (>1000): Sharded Map-Reduce

Reliability needs? →
  Best effort: Direct spawn
  Important: Circuit breaker
  Critical: Checkpoint + retry
```

---

## Troubleshooting First Steps

**Agent not responding?**
→ Check timeout, check context size, try simpler task

**Output is wrong?**
→ Add explicit examples, re-anchor with original goal

**Too slow?**
→ Check if sequential can be parallel, add concurrency limits

**Random failures?**
→ Add circuit breaker, check agent health, validate inputs

**Full debugging**: See [Debugging Guide](2026-02-20-1420-debugging-guide.md)

---

## File Structure

```
agents/synthesis/learning/
├── README.md (you are here)
├── 2026-02-20-0420-multi-agent-coordination-patterns.md
├── 2026-02-20-0620-integration-test-examples.md
├── 2026-02-20-0820-workflow-optimization-guides.md
├── 2026-02-20-1020-quality-standards.md
├── 2026-02-20-1220-implementation-templates.md
├── 2026-02-20-1420-debugging-guide.md
├── 2026-02-20-1620-case-studies.md
├── 2026-02-20-1820-best-practices.md
└── 2026-02-20-2020-quick-reference.md
```

**Total**: ~35,000 words, 9 documents, complete curriculum

---

## Key Takeaways

1. **Start simple**: Single agent, clear task, explicit output
2. **Add patterns**: Fan-out for parallel, Pipeline for sequence
3. **Guard quality**: Validate outputs, use gates between stages
4. **Handle failure**: Timeouts, retries, circuit breakers
5. **Optimize**: Context pruning, bounded concurrency, checkpoints
6. **Debug systematically**: Check logs, isolate failure, fix root cause

---

## Assessment

Ready to build production workflows when you can:
- [ ] Build 3-stage pipeline with quality gates
- [ ] Implement fan-out with 80%+ success rate
- [ ] Debug timeout and context issues
- [ ] Write integration tests for agent contracts
- [ ] Optimize slow workflow (2x speedup)
- [ ] Handle failure gracefully with fallbacks

**Practice**: Pick a case study, implement it, measure, optimize.

---

## Next Steps

1. Read [Quick Reference](2026-02-20-2020-quick-reference.md) (10 min)
2. Run [First Workflow](#quick-start-first-workflow) above (5 min)
3. Study [Case Study 1](2026-02-20-1620-case-studies.md) (15 min)
4. Build your own workflow (30 min)
5. Reference [Debugging Guide](2026-02-20-1420-debugging-guide.md) when stuck
6. Optimize with [Best Practices](2026-02-20-1820-best-practices.md)

**Time to productive**: 1 hour  
**Time to expert**: 1 day of practice

---

*Complete curriculum created: 2026-02-20. Happy building.*
