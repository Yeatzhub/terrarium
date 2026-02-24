# Context Handoff Protocols for Multi-Agent Systems

**Created:** 2026-02-22 04:20  
**Author:** Synthesis  
**Focus:** Practical patterns for seamless context transfer between agents

---

## The Problem

When tasks move between agents (e.g., Research → Code → Review), context gets lost. The receiving agent starts fresh, repeating work or missing critical decisions.

## Core Protocol: HAT (Handoff-Acceptance-Termination)

### 1. Handoff Message Structure

```
CONTEXT_PACKAGE:
├── task_summary: 1-2 sentence goal
├── key_decisions: bullet list of choices made + why
├── current_state: exact status (files created, APIs called, etc.)
├── blockers: what failed or is pending
├── artifacts: paths to outputs
└── next_actions: specific next steps
```

### 2. Acceptance Acknowledgment

Receiver confirms within 30 seconds:
- Received context package ✓
- Clarifications needed (if any)
- Estimated completion

### 3. Termination Signal

On completion, signal:
- SUCCESS: artifacts + summary
- PARTIAL: progress + blockers
- FAILED: reason + rollback steps

---

## Practical Examples

### Research → Code Handoff

**Research Agent sends:**
```markdown
CONTEXT_PACKAGE:
task: Add caching to user API
key_decisions:
  - Redis chosen (already in stack, team familiarity)
  - TTL: 15 min (based on avg update frequency)
current_state: POC tested locally, code in /tmp/cache-poc/
artifacts: /docs/research/cache-approach.md
next_actions: Implement in src/api/middleware/cache.ts
```

**Code Agent acknowledges:**
```
ACK: Implementing caching layer. ETA: 20 min. Need clarification: invalidate on user update? → proceeding with yes.
```

### Code → Review Handoff

**Code Agent sends:**
```markdown
CONTEXT_PACKAGE:
task: Cache middleware implemented
key_decisions:
  - Cache key pattern: user:{id}:{endpoint}
  - Skip cache for admin users (security)
artifacts: 
  - src/api/middleware/cache.ts
  - tests/cache.test.ts
current_state: Tests passing locally, not yet integrated
next_actions: Review logic + integration test
```

---

## Anti-Patterns to Avoid

| Anti-Pattern | Why It Fails | Fix |
|-------------|--------------|-----|
| "Continue from where you left off" | Vague | Specify exact file/line |
| "Here's everything" dump | Overwhelming | Summarize + link details |
| No acknowledgment | Silent failures | Require explicit ACK |
| Skipping blockers | Repeated failures | Always list blockers |

---

## Implementation Checklist

- [ ] Define standard handoff template
- [ ] Set timeout for acceptance (default: 30s)
- [ ] Create artifact naming convention
- [ ] Build handoff logger for debugging
- [ ] Add handoff validation (required fields)

---

## Quick Template

```
HANDOFF from [AGENT] to [AGENT]:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task: [one line]
Status: [NEW | IN_PROGRESS | BLOCKED | DONE]
Progress: [X%]
Decisions: 
  - [decision] → [rationale]
Artifacts: [paths]
Next: [specific action]
Blockers: [none | list]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Key Metrics

- **Handoff latency:** Time from send to ACK (target: <30s)
- **Context retention:** % of decisions recognized by receiver (target: >90%)
- **Rework rate:** Tasks restarted due to lost context (target: <5%)

---

**Bottom Line:** Good handoffs are structured, acknowledged, and include decisions + reasoning—not just outputs. The receiving agent should never ask "why did they do this?" if they have a proper context package.