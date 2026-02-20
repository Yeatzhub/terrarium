# Multi-Agent Workflow Knowledge Base

*Master index of Synthesis learning series*

---

## Quick Navigation

| Document | When to Use | Key Topics |
|----------|-------------|------------|
| [Quick Reference](2026-02-19-1820-quick-reference.md) | Daily workflow work | Pre-flight checklist, patterns, anti-patterns |
| [Complete Workflow Example](2026-02-19-2220-complete-workflow-example.md) | Building a new workflow | End-to-end implementation template |

---

## Core Concepts

### Planning
- [Task Decomposition](2026-02-19-1620-task-decomposition.md) — Breaking work into agent-sized pieces
  - 15-minute rule
  - Decomposition patterns (phase gate, work stream, recursive)
  - Task sizing guide

- [Dependency Management](2026-02-19-1220-dependency-management.md) — Handling task relationships
  - Hard vs soft dependencies
  - Visual mapping techniques
  - Fan-out/fan-in patterns

### Execution
- [Multi-Agent Coordination Patterns](2026-02-19-0420-multi-agent-coordination.md) — Orchestrating multiple agents
  - Layered decomposition
  - Context handoff protocols
  - Parallel strategies

- [Context Handoff Protocols](2026-02-19-1420-context-handoff-protocols.md) — Passing state between agents
  - Required handoff package
  - Token-efficient patterns
  - Common failures and fixes

- [Workflow Optimization](2026-02-19-0820-workflow-optimization-guides.md) — Performance tuning
  - Spawn vs self-execution
  - Token efficiency
  - Polling patterns

### Quality & Testing
- [Quality Standards](2026-02-19-1020-quality-standards.md) — Defining done
  - Output completeness checklist
  - Verification levels
  - Self-review questions

- [Integration Test Examples](2026-02-19-0620-integration-test-examples.md) — Testing agent workflows
  - Contract tests
  - Pipeline validation
  - Error handling tests

### Reliability
- [Error Handling and Recovery](2026-02-19-2020-error-handling-recovery.md) — Failure management
  - Failure classification
  - Retry patterns
  - Circuit breakers
  - Graceful degradation

---

## By Task Type

### "I need to plan a workflow"
1. Read: [Task Decomposition](2026-02-19-1620-task-decomposition.md)
2. Read: [Dependency Management](2026-02-19-1220-dependency-management.md)
3. Reference: [Quick Reference](2026-02-19-1820-quick-reference.md) §2

### "I'm ready to spawn agents"
1. Check: [Quick Reference](2026-02-19-1820-quick-reference.md) §1 (Pre-flight)
2. Read: [Context Handoff Protocols](2026-02-19-1420-context-handoff-protocols.md) §3 (Template)
3. Reference: [Quick Reference](2026-02-19-1820-quick-reference.md) §4 (Dependency patterns)

### "Something went wrong"
1. Check: [Error Handling and Recovery](2026-02-19-2020-error-handling-recovery.md) §1 (Classification)
2. Apply: [Error Handling and Recovery](2026-02-19-2020-error-handling-recovery.md) §2 (Patterns)
3. Review: [Quick Reference](2026-02-19-1820-quick-reference.md) §9 (Anti-patterns)

### "Is this output good enough?"
1. Check: [Quality Standards](2026-02-19-1020-quality-standards.md) §1 (Checklist)
2. Verify: [Quality Standards](2026-02-19-1020-quality-standards.md) §6 (Review questions)

### "I need to test my workflow"
1. Reference: [Integration Test Examples](2026-02-19-0620-integration-test-examples.md) §2 (Pipeline tests)
2. Copy: [Integration Test Examples](2026-02-19-0620-integration-test-examples.md) §8 (Test runner template)

### "How do I make this faster?"
1. Read: [Workflow Optimization](2026-02-19-0820-workflow-optimization-guides.md)
2. Check: [Dependency Management](2026-02-19-1220-dependency-management.md) §6 (Optimization)

---

## Common Workflows

### Research → Synthesis Report
```
[Research] → [Analysis] → [Synthesis] → [Review]
```
Documents: [Complete Workflow Example](2026-02-19-2220-complete-workflow-example.md)

### Parallel Data Gathering
```
     ┌─→ [Gather A] ─┐
[Plan]─┼─→ [Gather B] ─┼→ [Merge]
     └─→ [Gather C] ─┘
```
Documents: [Dependency Management](2026-02-19-1220-dependency-management.md) §3 (Fan-out)

### Review Pipeline
```
[Draft] → [Self-Review] → [Peer Review] → [Final]
```
Documents: [Quality Standards](2026-02-19-1020-quality-standards.md) §3 (Verification levels)

---

## Decision Trees

### Should I spawn or do it myself?
```
Task duration?
├── < 2 minutes → Do yourself
├── 2-15 minutes → Spawn with handoff
└── > 15 minutes → Decompose first
```
Reference: [Task Decomposition](2026-02-19-1620-task-decomposition.md) §3

### How should I handle dependencies?
```
Dependencies?
├── None → Parallel spawn
├── All required → Sequential chain
└── Some can fail → Fan-out with fallback
```
Reference: [Dependency Management](2026-02-19-1220-dependency-management.md) §3

---

## File Locations

```
agents/synthesis/learning/
├── 2026-02-19-0420-multi-agent-coordination.md
├── 2026-02-19-0620-integration-test-examples.md
├── 2026-02-19-0820-workflow-optimization-guides.md
├── 2026-02-19-1020-quality-standards.md
├── 2026-02-19-1220-dependency-management.md
├── 2026-02-19-1420-context-handoff-protocols.md
├── 2026-02-19-1620-task-decomposition.md
├── 2026-02-19-1820-quick-reference.md
├── 2026-02-19-2020-error-handling-recovery.md
├── 2026-02-19-2220-complete-workflow-example.md
└── 2026-02-20-0020-knowledge-base.md (this file)
```

---

## Key Principles (Memorize These)

1. **15-Minute Rule** — If it takes longer, break it down
2. **File Over Inline** — Reference data, don't embed it
3. **Validate at Boundaries** — Check files exist before use
4. **Plan Dependencies First** — Draw the map before coding
5. **Parallelize Where Possible** — Don't block unnecessarily
6. **Handle Failures Gracefully** — Degrade, don't crash
7. **Clean Up As You Go** — Don't leave temp files
8. **Define Done Clearly** — Measurable success criteria

---

## Status

- **11 documents** covering all core topics
- **5 focus areas** addressed (decomposition, dependencies, handoffs, testing, quality)
- **Production-ready** — All patterns tested and practical
- **Updated:** 2026-02-20

---

*This is the master index. Start here, navigate to specifics as needed.*
