# Complete Workflow Example

*End-to-end multi-agent workflow demonstrating all patterns*

---

## Scenario

Research market trends, analyze competitors, and generate a strategic report.

---

## Step 1: Plan and Decompose

### Dependency Map
```
[Research Market]
       ↓
┌──────┴──────┐
↓             ↓
[Analyze      [Gather
 Trends]      Competitors]
       ↓             ↓
       └──────┬──────┘
              ↓
        [Synthesize
           Report]
              ↓
        [Review &
          Polish]
```

### Task Breakdown
| Task | Duration | Depends On | Output |
|------|----------|------------|--------|
| Research Market | 10 min | — | `/tmp/market_data.json` |
| Analyze Trends | 8 min | Research | `/tmp/trends.md` |
| Gather Competitors | 8 min | Research | `/tmp/competitors.md` |
| Synthesize Report | 10 min | Trends + Competitors | `/tmp/draft_report.md` |
| Review & Polish | 5 min | Draft | `/output/final_report.md` |

---

## Step 2: Implement

### Phase 1: Research (Independent)
```python
# Spawn research agent
research_job = await sessions_spawn({
    "task": """Research current market trends in cloud computing.
    
Focus areas:
- Market size and growth rate
- Key technology trends
- Major player movements

Write structured output to /tmp/market_data.json with fields:
- market_size (string)
- growth_rate (string)
- trends (array of objects with name and description)
- player_movements (array)

Constraints: 10 minute time limit.""",
    "runTimeoutSeconds": 600,
    "cleanup": "success"
})

# Wait for completion
research_result = await poll_exponential(research_job["sessionKey"])
assert research_result["status"] == "completed"
assert os.path.exists("/tmp/market_data.json")
```

### Phase 2: Parallel Analysis (Depends on Research)
```python
# Check dependency before spawning dependents
if not os.path.exists("/tmp/market_data.json"):
    raise DependencyError("Research phase failed to produce output")

# Spawn two parallel analysis tasks
trends_job = await sessions_spawn({
    "task": """Analyze market trends from /tmp/market_data.json.

Write analysis to /tmp/trends.md including:
- Executive summary (3 bullets)
- Top 3 trends with implications
- Opportunity areas

Handoff context:
- Source data: /tmp/market_data.json
- Focus on AI/ML and edge computing trends
- Target audience: C-level execs""",
    "runTimeoutSeconds": 480
})

competitors_job = await sessions_spawn({
    "task": """Analyze competitors from /tmp/market_data.json.

Write competitor analysis to /tmp/competitors.md:
- Top 5 competitors overview
- Each competitor's recent moves
- Competitive positioning matrix

Handoff context:
- Source data: /tmp/market_data.json
- Compare against AWS, Azure, GCP primarily""",
    "runTimeoutSeconds": 480
})

# Wait for both in parallel
results = await asyncio.gather(
    poll_exponential(trends_job["sessionKey"]),
    poll_exponential(competitors_job["sessionKey"]),
    return_exceptions=True
)

# Handle partial failures
if isinstance(results[0], Exception):
    log.error(f"Trends analysis failed: {results[0]}")
    # Continue with competitors only
trends_ok = os.path.exists("/tmp/trends.md")
competitors_ok = os.path.exists("/tmp/competitors.md")

if not trends_ok and not competitors_ok:
    raise RuntimeError("Both analysis tasks failed")
```

### Phase 3: Synthesis (Depends on Both Analyses)
```python
# Verify dependencies
missing = []
for f in ["/tmp/trends.md", "/tmp/competitors.md"]:
    if not os.path.exists(f):
        missing.append(f)

if missing:
    # Graceful degradation: create minimal versions
    for f in missing:
        write(f, f"# Note: {f} unavailable\nSee raw data in /tmp/market_data.json")

# Spawn synthesis
synthesis_job = await sessions_spawn({
    "task": """Create strategic report from analyses.

Read:
- /tmp/trends.md - Market trend analysis
- /tmp/competitors.md - Competitive landscape

Write comprehensive report to /tmp/draft_report.md with:
1. Executive Summary (1 page)
2. Market Trends Analysis (2 pages)
3. Competitive Positioning (2 pages)
4. Strategic Recommendations (1 page)
5. Next Steps (bullet list)

Quality standards:
- Each section has clear headers
- Data citations from source documents
- Actionable recommendations
- Professional tone""",
    "runTimeoutSeconds": 600,
    "cleanup": "success"
})

synthesis_result = await poll_exponential(synthesis_job["sessionKey"])
```

### Phase 4: Review (Depends on Synthesis)
```python
review_job = await sessions_spawn({
    "task": """Review and polish /tmp/draft_report.md.

Tasks:
- Check for clarity and flow
- Fix any grammar/spelling
- Ensure all sections present
- Verify formatting consistent
- Add Table of Contents

Write final polished report to /output/final_report.md

Quality gate:
- Must be suitable for executive presentation
- No placeholder text""",
    "runTimeoutSeconds": 300
})

review_result = await poll_exponential(review_job["sessionKey"])
assert os.path.exists("/output/final_report.md"), "Final report not created"
```

---

## Step 3: Error Handling

### Retry Logic
```python
async def resilient_research(task, max_retries=2):
    for attempt in range(max_retries + 1):
        try:
            job = await sessions_spawn(task)
            result = await poll_exponential(job["sessionKey"], max_wait=600)
            if result["status"] == "completed":
                return result
            raise RuntimeError(f"Status: {result['status']}")
        except Exception as e:
            if attempt == max_retries:
                raise
            log.warning(f"Attempt {attempt + 1} failed, retrying...")
            await asyncio.sleep(2 ** attempt)
```

### Circuit Breaker for Dependencies
```python
class WorkflowState:
    def __init__(self):
        self.completed = set()
        self.failed = set()
    
    def can_proceed(self, dependencies):
        for dep in dependencies:
            if dep in self.failed:
                return False, f"Dependency {dep} failed"
            if dep not in self.completed:
                return False, f"Dependency {dep} incomplete"
        return True, None

# Usage
state = WorkflowState()
can_go, reason = state.can_proceed(["research", "trends"])
if not can_go:
    raise WorkflowBlockedError(reason)
```

---

## Step 4: Validation

### Output Verification
```python
def validate_final_report(path="/output/final_report.md"):
    assert os.path.exists(path), f"Missing: {path}"
    
    content = read(path)
    
    # Required sections
    required = [
        "Executive Summary",
        "Market Trends",
        "Competitive",
        "Recommendations",
        "Next Steps"
    ]
    
    missing = [s for s in required if s not in content]
    if missing:
        raise ValidationError(f"Missing sections: {missing}")
    
    # Length check
    word_count = len(content.split())
    if word_count < 500:
        raise ValidationError(f"Report too short: {word_count} words")
    
    # No placeholder text
    if "TODO" in content or "FIXME" in content:
        raise ValidationError("Contains placeholder text")
    
    return True

# Run validation
try:
    validate_final_report()
    print("✓ Final report validated")
except ValidationError as e:
    print(f"✗ Validation failed: {e}")
```

---

## Step 5: Cleanup

```python
# Preserve final output, remove intermediates
intermediate_files = [
    "/tmp/market_data.json",
    "/tmp/trends.md",
    "/tmp/competitors.md",
    "/tmp/draft_report.md"
]

for f in intermediate_files:
    if os.path.exists(f):
        os.remove(f)
        log.info(f"Cleaned up: {f}")

# Verify final output remains
assert os.path.exists("/output/final_report.md")
print("✓ Workflow complete, artifacts preserved")
```

---

## Summary

### What This Demonstrates
| Pattern | Location |
|---------|----------|
| Task Decomposition | 5-phase breakdown |
| Dependency Management | Research → Parallel → Merge → Review |
| Context Handoff | Each spawn has explicit inputs/outputs |
| Parallel Execution | Trends + Competitors simultaneously |
| Error Handling | Retry logic, graceful degradation |
| Validation | Output verification before completion |
| Cleanup | Intermediate files removed |

### Key Takeaways
1. **Plan dependencies first** — Draw the map before coding
2. **Parallelize where possible** — Trends and competitors don't block each other
3. **Validate at boundaries** — Check files exist before using
4. **Handle failures gracefully** — Continue with partial data if possible
5. **Clean up as you go** — Don't leave temp files scattered

---

*Generated: 2026-02-19 | Use: Reference template for building workflows*
