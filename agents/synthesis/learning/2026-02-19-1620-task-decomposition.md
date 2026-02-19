# Task Decomposition Guide

*Breaking complex work into agent-ready pieces*

---

## 1. Decomposition Principles

### The 15-Minute Rule
> If an agent task takes >15 minutes, break it down further.

### Task Attributes
Each task should have:
- **Single outcome** — One clear deliverable
- **Bounded scope** — Can't grow infinitely
- **Testable completion** — Done is definable
- **No dependencies** — Or explicit about them
- **Fits in context** — Under 75% of token budget

---

## 2. Decomposition Patterns

### Pattern: Phase Gate
```
[Research] ──→ [Analyze] ──→ [Write] ──→ [Review]
   2h            1h            1h           0.5h
   ↓             ↓             ↓            ↓
  Data      Insights      Draft        Final
```
Each phase completes before next starts.

### Pattern: Work Stream
```
┌──────────┐
│ Research │──→ Topic A report
├──────────┤
│ Research │──→ Topic B report
├──────────┤
│ Research │──→ Topic C report
└──────────┘
         ↓
    [Merge]──→ Combined report
```
Multiple agents work in parallel, results combined.

### Pattern: Recursive Drill
```
[Analyze codebase]
      ↓
├─→ [Module A]
│      ↓
│   ├─→ [Function 1]
│   └─→ [Function 2]
│
└─→ [Module B]
       ↓
    ├─→ [Function 3]
    └─→ [Function 4]
```
Break until reach atomic tasks.

---

## 3. Task Sizing Guide

| Duration | Action |
|----------|--------|
| < 2 min | Do in main session |
| 2-15 min | Spawn with clear handoff |
| 15-60 min | Break into sub-tasks |
| > 60 min | Definitely needs decomposition |

---

## 4. Decomposition Checklist

Before spawning, verify:
- [ ] Task has one clear deliverable
- [ ] Expected output format defined
- [ ] Success criteria are testable
- [ ] Duration < 15 min (or further decomposed)
- [ ] Dependencies explicit
- [ ] Input files/references provided
- [ ] Error handling anticipated
- [ ] Cleanup strategy defined

---

## 5. Common Mistakes

| Mistake | Fix |
|---------|-----|
| "Fix the code" → vague | "Fix TypeError in parse_input() at line 47" |
| "Research everything" | "Research: market size, top 3 competitors, pricing" |
| "Write a report" | "Write 2-page exec summary, save to /output/" |
| Depends on unknown | List prerequisites explicitly |
| No output location | Specify exact file path |

---

## 6. Template

```markdown
**TASK:** [One sentence description]

**Inputs:**
- [File path or data source]

**Expected Output:**
- [File path] in [format]
- Contains: [specific elements]

**Success Criteria:**
- [ ] Criterion 1 (measurable)
- [ ] Criterion 2 (measurable)

**Constraints:**
- [Time limit]
- [Resource limits]
- [Must-nots]

**Dependencies:**
- [What must complete first]
- [What can run in parallel]

**On Failure:**
- [What to do if blocked]
```

---

## 7. Quick Decision Tree

```
Need to do work:
  └─→ < 2 minutes?
        └─→ YES → Do in main session
        └─→ NO  → Can it be single deliverable?
                      └─→ NO  → Decompose further
                      └─→ YES → Duration < 15 min?
                                    └─→ YES → Spawn with handoff
                                    └─→ NO  → Decompose into phases
```

---

*Generated: 2026-02-19 | Use: Before every task spawn*
