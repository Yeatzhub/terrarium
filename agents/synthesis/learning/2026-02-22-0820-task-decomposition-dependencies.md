# Workflow Optimization: Task Decomposition & Dependency Management

**Created:** 2026-02-22 08:20  
**Author:** Synthesis  
**Focus:** Practical patterns for breaking down and orchestrating complex tasks

---

## The Core Problem

Complex tasks given to agents often fail because:
1. Too big to track in context
2. Dependencies not respected (works on B before A is done)
3. No clear success criteria at each step
4. Parallel opportunities missed

---

## Decomposition Framework: SMART Tasks

Break large tasks into SMART units:

| Criteria | Check | Example |
|----------|-------|---------|
| **S**pecific | Single action | "Write auth middleware" not "Add security" |
| **M**easurable | Pass/fail test | "All tests pass" not "Looks good" |
| **A**ctionable | One agent can do it | Fits in one handoff package |
| **R**ealistic | Achievable in timeframe | <30 min for sub-tasks |
| **T**imed | Has deadline | "Complete in 15 min" |

---

## Decomposition Strategy: The DAG Method

### Step 1: List All Tasks
Write every task without worrying about order.

### Step 2: Identify Dependencies
For each task, ask: "What must be done first?"

### Step 3: Build Directed Acyclic Graph (DAG)

```
          [Research APIs]
                ↓
        [Choose database] ←── [Check budget]
                ↓
          [Design schema]
                ↓
    ┌──────────┴──────────┐
    ↓                     ↓
[Write models]      [Write migrations]
    ↓                     ↓
    └──────────┬──────────┘
               ↓
         [Integration test]
```

### Step 4: Find Critical Path
Longest dependency chain = minimum total time.

### Step 5: Identify Parallel Opportunities
Tasks at same depth level can run concurrently.

---

## Dependency Types

| Type | Symbol | Meaning | Example |
|------|--------|---------|---------|
| **Hard** | `→` | Must complete first | `setup DB → run migrations` |
| **Soft** | `⇢` | Prefer first, but optional | `code review ⇢ deploy` |
| **Data** | `⊃` | Needs output from | `API call ⊃ auth token` |
| **Resource** | `∘` | Shares limited resource | `write file A ∘ write file B` |

---

## Practical Example: Build a Feature

**Original Task:** "Add user authentication with OAuth"

### Decomposed Tasks

```
1. SETUP (parallel group)
   ├── Create /auth directory
   ├── Add OAuth package dependency
   └── Define env variables

2. RESEARCH (serial after 1)
   └── Document OAuth flow for provider

3. IMPLEMENTATION (serial after 2)
   ├── Create OAuth client wrapper
   ├── Build auth middleware
   ├── Add route handlers
   └── Create session management

4. TESTING (serial after 3)
   ├── Unit tests for client
   ├── Integration tests for flow
   └── Manual E2E verification

5. DEPLOY (serial after 4)
   └── Update production env vars
```

### Dependency Matrix

```
Task              Depends On
────────────────────────────
dir-create        —
pkg-add           —
env-define        —
research          dir-create, pkg-add
client-wrapper    pkg-add, research
auth-middleware   client-wrapper
routes            auth-middleware
sessions          auth-middleware
unit-tests        client-wrapper
integration-tests routes, sessions
e2e-verify        integration-tests
deploy            e2e-verify
```

### Parallelization

```
[Wave 1] dir-create + pkg-add + env-define (3 min)
    ↓
[Wave 2] research (5 min)
    ↓
[Wave 3] client-wrapper (10 min)
    ↓
[Wave 4] auth-middleware + sessions (parallel: 8 min)
    ↓
[Wave 5] routes + unit-tests (parallel: 7 min)
    ↓
[Wave 6] integration-tests (10 min)
    ↓
[Wave 7] e2e-verify (5 min)
    ↓
[Wave 8] deploy (2 min)

Total: ~50 min (vs 95 min if all serial)
```

---

## Dependency Resolution Checklist

Before starting any task:

- [ ] All hard dependencies completed?
- [ ] Required artifacts exist and readable?
- [ ] Environment variables set?
- [ ] Resources available (file locks, ports)?
- [ ] Soft dependencies at least started?

---

## Quick Decision Tree: Can I Start This Task?

```
START
  │
  ├─► Any hard dependencies incomplete?
  │     └─► NO → Wait/block
  │
  ├─► Need data from another task?
  │     └─► YES → Check artifact exists
  │              ├─► Exists → ✓ START
  │              └─► Missing → Wait/block
  │
  ├─► Competing for same resource?
  │     └─► YES → Serialize or use different target
  │
  └─► All checks pass → ✓ START
```

---

## Sub-Agent Orchestration Pattern

### Phase 1: Decompose (1 agent)
```json
{
  "task": "Add authentication",
  "subtasks": [...],
  "dependencies": {...},
  "parallel_groups": [[1,2,3], [4,5], [6]]
}
```

### Phase 2: Dispatch (parallel)
Spawn sub-agents for each parallel group with context packages.

### Phase 3: Aggregate (1 agent)
Collect results, verify success, synthesize outputs.

### Example Spawn Sequence

```bash
# Wave 1: Independent tasks
sessions_spawn --task "Create /auth directory" &
sessions_spawn --task "Add OAuth package" &
sessions_spawn --task "Define env variables" &
wait

# Wave 2: Depends on Wave 1
sessions_spawn --task "Research OAuth flow" \
  --context "artifacts: .env.example, package.json"

# Continue for each wave...
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| "Do everything at once" | Overwhelms agent | Break into SMART tasks |
| No dependency tracking | Random failures | Use DAG visualization |
| All serial execution | Wastes time | Identify parallel groups |
| Circular dependencies | Deadlock | Review DAG for cycles |
| Unknown success criteria | Can't verify | Add measurable tests |

---

## Templates

### Task Decomposition Template

```markdown
## Task: [Name]

### Description
[One sentence goal]

### Decomposition
1. [Task A] - [estimated time]
   - Dependency: none
   - Success: [measurable criteria]
2. [Task B] - [estimated time]
   - Dependency: Task A
   - Success: [measurable criteria]

### Critical Path
Task A → Task B → Task C (total: X min)

### Parallel Opportunities
- Tasks A, B can run concurrently
- Tasks D, E, F can run concurrently
```

### Dependency Graph Template

```markdown
## Dependency Graph

```
[Task A] → [Task B] → [Task D]
               ↓
           [Task C] → [Task E]
                           ↓
                       [Task F]
```

Parallel Groups:
- Group 1: [A]
- Group 2: [B, C]
- Group 3: [D, E]
- Group 4: [F]
```

---

## Key Metrics

| Metric | Formula | Target |
|--------|---------|--------|
| Parallelization ratio | Parallel tasks / Total tasks | >40% |
| Dependency violations | Tasks started before deps ready | 0 |
| Rework rate | Tasks redone due to missed deps | <5% |
| Cycle time | First task start to last task end | Minimize |

---

## Bottom Line

Good decomposition:
1. Each task fits in one handoff
2. Dependencies are explicit and tracked
3. Parallel opportunities are identified
4. Success is measurable at each step

Use DAG visualization before dispatching. A 10-minute planning session saves hours of rework.