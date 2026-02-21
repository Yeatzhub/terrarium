# Task Decomposition for Multi-Agent Systems

**Date:** 2026-02-21 04:20 PM  
**Topic:** Breaking down complex work into agent-sized chunks

---

## Why Decomposition Fails

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| Agent returns incomplete work | Task too broad | Narrow scope to single output |
| Agents step on each other | Overlapping responsibilities | Clear boundaries |
| Long running tasks | No checkpointing | Split into measurable stages |
| Inconsistent results | Ambiguous instructions | Concrete success criteria |

---

## The DECOMP Method

**D**etermine outcomes | **E**xtract subtasks | **C**hunk by complexity | **O**rder dependencies | **M**ake measurable | **P**repare handoffs

### Step 1: Determine Outcomes (5 min)

Define what "done" looks like before spawning.

```
Bad: "Analyze the data"
Good: "Output JSON with: mean, median, outliers (3σ), sample size"

Bad: "Write documentation"
Good: "Create README.md with: install steps, 3 examples, API ref"
```

**Success Criteria Template:**
```yaml
output_format: "json"
required_fields:
  - field: "mean"
    type: "number"
  - field: "summary"
    type: "string"
    max_length: 200
acceptance_test: "mean > 0 AND summary contains 'data'"
```

### Step 2: Extract Subtasks

Use these patterns to find natural splits:

**Pattern A: Data Splitting**
```
Input: 10,000 records
Subtask A: Process records 0-2,499
Subtask B: Process records 2,500-4,999
Subtask C: Process records 5,000-7,499
Subtask D: Process records 7,500-9,999
Subtask E: Merge results (depends on A-D)
```

**Pattern B: Pipeline Stages**
```
Stage 1: Extract raw data
Stage 2: Clean/normalize
Stage 3: Transform
Stage 4: Validate
Stage 5: Save
```

**Pattern C: Domain Separation**
```
Financial analysis → Agent A
Technical analysis → Agent B
Risk assessment → Agent C (needs A+B)
Executive summary → Agent D (needs A+B+C)
```

### Step 3: Chunk by Complexity

**The 5-15-60 Rule:**

| Task Type | Max Duration | Token Budget | Ideal Agent |
|-----------|-------------|--------------|-------------|
| Quick check | 5 min | 1K tokens | Any model |
| Standard task | 15 min | 3K tokens | Default model |
| Deep analysis | 60 min | 8K tokens | Capable model |

**If a task exceeds 60 min, it needs decomposition.**

### Step 4: Order Dependencies

Draw the graph:

```
     [Parse CSV]
    /     |     \
 [Sales] [Inventory] [Customers]
    \      |      /
     [Consolidate]
          |
     [Generate Report]
```

**Dependency Types:**
- **Hard:** B absolutely requires A's output (sequential)
- **Soft:** B can use A's output but has fallback (parallel with fallback)
- **None:** A and B independent (parallel)

**Optimization:** Maximize parallel edges, minimize hard dependencies.

### Step 5: Make Measurable

Each subtask needs:
1. **Input signature:** File path, format, size
2. **Processing limit:** Time, tokens, iterations
3. **Output schema:** Exact structure expected
4. **Quality gate:** Pass/fail check

**Example:**
```yaml
subtask:
  name: "Entity extraction"
  input: { path: "data/article.txt", max_size: "100KB" }
  limits: { time: "10m", tokens: 2000 }
  output: 
    format: "json"
    schema: { entities: [{ name: str, type: str, confidence: float }] }
  quality_gate: "count(entities) > 0 AND all(confidence > 0.5)"
```

### Step 6: Prepare Handoffs

Define what passes between agents:

```
Agent A ──[handoff.yaml + data.json]──→ Agent B
         
handoff.yaml contains:
- Source task id
- Output file reference
- Partial/total flag
- Next agent instructions
```

---

## Decomposition Patterns

### Pattern 1: Map-Reduce

**Use:** Distributed processing of homogeneous data

```
Input: Large dataset

Map Phase:
  Agent 1 → chunk-0.json
  Agent 2 → chunk-1.json
  Agent 3 → chunk-2.json

Reduce Phase:
  Agent 4 ← [chunk-0, chunk-1, chunk-2] → combined.json
```

**When to use:** Same operation on many items
**Max parallelism:** 10 agents (avoid rate limits)

### Pattern 2: Branch-Merge

**Use:** Different analyses on same input

```
Input: document.txt

Branch:
  ├─ Agent A (sentiment) → sentiment.json
  ├─ Agent B (entities) → entities.json
  └─ Agent C (topics) → topics.json

Merge:
  Agent D ← [sentiment, entities, topics] → analysis-full.json
```

**When to use:** Need multiple perspectives
**Key:** Ensure branches don't overlap in work

### Pattern 3: Iterative Refinement

**Use:** Quality improvement through rounds

```
Round 1: Agent A → draft (v1)
Round 2: Agent B → review + edits (v2)
Round 3: Agent A → final polish (v3)
```

**Max rounds:** 3 (diminishing returns after)
**Alternative:** Parallel drafts → ranking → combine best

### Pattern 4: Specialist Routing

**Use:** Different task types need different skills

```
Router Agent:
  Input task → Analyze type
  
  Type A → Specialist A
  Type B → Specialist B
  Type C → Specialist C
  
All outputs → Aggregator
```

**Example:** Support ticket routing → Billing/Technical/Sales agents

### Pattern 5: Checkpoint Pipeline

**Use:** Long tasks that might fail mid-way

```
Stage 1: Agent A → checkpoint-1.json (5 min)
Stage 2: Agent B → checkpoint-2.json (10 min)
Stage 3: Agent C → final.json (3 min)

On failure: Resume from last checkpoint
```

**Best for:** Reliable recovery, debugging long flows

---

## Anti-Patterns to Avoid

### ❌ The God Task

```
Bad: "Build me a website"
Good: 
  1. Design database schema (Agent A)
  2. Create API endpoints (Agent B, depends on A)
  3. Build frontend (Agent C, parallel to B if API mocked)
  4. Write tests (Agent D, depends on B+C)
```

### ❌ The Chatty Coordinator

```
Bad: Coordinator polling 20x/second
Good: 
  - Spawn agents with timeouts
  - Check every 5-10 seconds
  - Use push notifications when possible
```

### ❌ Over-Granularity

```
Bad: 50 agents for 50 lines of code
Good:
  - 1 agent per file (if files <200 lines)
  - 1 agent per component
  - Batch tiny tasks: 1 agent processes 10 small items
```

### ❌ Hidden Dependencies

```
Bad: Agent B assumes Agent A cleaned data
Good:
  - Handoff file explicitly states: "This data is validated"
  - Agent B validates anyway (defensive)
```

---

## The 5-Minute Decomposition Exercise

Take any task and run through these questions:

1. **What single output file proves completion?**
2. **Can I split this into before/middle/after?**
3. **Are there natural data chunks?**
4. **Which parts can run simultaneously?**
5. **What's the longest any subtask should take?** (If >15 min, split)
6. **What does each stage need from the previous?**

**Example:**
```
Task: "Analyze customer feedback"

1. Output: sentiment-report.json
2. Split: Extract → Analyze → Summarize
3. Chunks: Per-product feedback files
4. Parallel: Each product analyzed independently
5. Max time: 10 min per product (chunk if larger)
6. Needs: Clean text → Scores → Aggregated summary
```

---

## Decomposition Decision Tree

```
Start
  │
  ├─ Task has clear sequential steps? → Pipeline pattern
  │
  ├─ Processing large homogeneous data? → Map-Reduce
  │
  ├─ Need multiple perspectives on same input? → Branch-Merge
  │
  ├─ Quality critical, needs refinement? → Iterative
  │
  ├─ Different types need different skills? → Specialist Router
  │
  └─ Long running, failure risk? → Checkpoint Pipeline
```

---

## Quick Reference: Task Size Guide

| If task is... | Decomposition | Agent Count |
|--------------|---------------|-------------|
| <5 min, single file | Don't split | 1 |
| 5-15 min, 2-3 stages | Pipeline | 2-3 |
| 15-60 min, complex | Checkpoint pipeline | 3-5 |
| Large dataset | Map-reduce | 5-10 |
| Needs multiple analysis types | Branch-merge | 3-4 + 1 aggregator |
| Mixed skill requirements | Specialist router | 1 + N specialists |

---

**Related:** See `context-handoff-protocols.md` for how decomposed tasks communicate; `workflow-optimization.md` for making them fast.
