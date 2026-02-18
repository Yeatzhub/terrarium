# Multi-Agent Coordination Patterns
*Synthesis Learning Log | 2026-02-18*

## 1. Task Decomposition Patterns

### Fan-Out Pattern
**When to use:** Independent sub-tasks that can run in parallel.

```
Parent Agent
├── Spawn Agent A → Task A
├── Spawn Agent B → Task B
└── Spawn Agent C → Task C
     ↓
Collect results, synthesize
```

**Key rule:** Ensure sub-agents have ALL context they need. No mid-task questions.

### Pipeline Pattern
**When to use:** Sequential dependencies where output of step N is input to step N+1.

```
Raw Input → Agent A (Extract) → Agent B (Transform) → Agent C (Load) → Output
```

**Key rule:** Define clear output contracts upfront. Validate at handoff points.

### Map-Reduce Pattern
**When to use:** Processing large datasets or aggregating many inputs.

```
Input Chunk 1 → Agent 1 → Result 1
Input Chunk 2 → Agent 2 → Result 2   →  Aggregator Agent  → Final Output
Input Chunk N → Agent N → Result N
```

---

## 2. Dependency Management

### Explicit Dependencies
Always declare dependencies in spawn context:
```
"Task: Generate API docs"
"Depends on: PR #123 merged (commit: abc123)"
"Schema version: v2.1"
```

### Dependency Types
| Type | Signal | Action if Missing |
|------|--------|-------------------|
| Hard | Blocks execution | Wait or fail fast |
| Soft | Degrades gracefully | Proceed with fallback |
| Temporal | Time-sensitive | Check freshness |

### Checkpoint Pattern
Before spawning sub-agents, verify prerequisites:
- File exists? Check.
- Previous job complete? Confirm.
- Rate limits? Respect.

---

## 3. Context Handoff Protocols

### Standard Handoff Package
Every sub-agent spawn includes:
1. **Goal** - One sentence, outcome-focused
2. **Context** - Background, decisions made, constraints
3. **Inputs** - Files, data, references needed
4. **Constraints** - Time, format, quality standards
5. **Success criteria** - How to know it's done

### Anti-Patterns to Avoid
- **The Treasure Hunt:** "Use the file from yesterday" → Use absolute paths
- **The Mystery:** "Fix the bug" → Specify which bug, where, expected behavior
- **The Unlimited:** "Take your time" → Always set time limits

### Handoff Template
```
TASK: [Clear action verb + noun]

CONTEXT:
- Why this matters: [business/user value]
- Previous decisions: [what's already set in stone]
- Constraints: [must/not must, nice-to-haves]

INPUTS:
- File: [absolute path]
- Data: [relevant excerpts]
- References: [links/commits/tickets]

OUTPUT:
- Format: [markdown/json/etc]
- Location: [where to write results]
- Definition of done: [checklist]

TIME: [X minutes hard limit]
```

---

## 4. Quick Reference: When to Spawn

| Scenario | Pattern | Max Agents |
|----------|---------|------------|
| Research multiple topics | Fan-out | 5 |
| Code review + fixes | Pipeline | 3 |
| Process 20 files | Map-reduce | 10 |
| Debug complex issue | Single agent | 1 |
| Urgent (< 5 min) | No spawn, direct | 0 |

---

## 5. Quality Standards

### Before Spawning Checklist
- [ ] Task is atomic (can't be reasonably split further)
- [ ] Context exceeds 50% of expected effort? Don't spawn.
- [ ] Success criteria are binary (pass/fail measurable)
- [ ] Output location is writable and won't conflict

### Monitoring
- Poll subagents ONCE at ~80% of timeout
- Kill if spinning (no progress > 30% of timeout)
- Capture partial results on timeout

---

## Remember

**Coordination overhead is real.** Every spawn costs ~10-20s in overhead. 
Use when parallelization saves >60s of wall-clock time.

**Clarity beats cleverness.** A simple sequential flow that's understood beats a complex parallel flow that fails silently.
