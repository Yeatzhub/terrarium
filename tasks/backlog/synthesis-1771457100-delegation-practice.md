---
assigned_to: synthesis
task_id: 1771457100-delegation-practice
status: failed
created_at: 2026-02-18T23:25:00Z
started_at: 2026-02-18T17:36:28-06:00
completed_at: null
type: training
difficulty: medium
---

# Training Task: Multi-Agent Coordination Practice

Practice proper task delegation by coordinating a multi-agent workflow.

## Objective
Create a "Learning Documentation System" that combines skills from all agents.

## Your Role (Synthesis)
Design the system architecture and coordinate the implementation.

## Delegation Plan

- [ ] **Ghost**: Create Python script to scan `agents/*/learning/` folders and generate index.json with metadata (agent, topic, date, file size)
- [ ] **Pixel**: Design a web dashboard component to display the learning index with search/filter by agent and date
- [ ] **Oracle**: Analyze which topics are most common and suggest a tagging/categorization system for trading-related learnings

## Requirements

### Ghost's Backend Script
- Scan all agent learning directories
- Extract frontmatter metadata
- Generate JSON index with file locations
- Include last modified timestamps

### Pixel's UI Component  
- React component for `/agents/learning` page
- Filter by agent (synthesis, ghost, pixel, oracle)
- Filter by date range
- Sort by recency
- Responsive grid layout

### Oracle's Analysis
- Count topics by category (code, trading, ui, architecture)
- Suggest tags based on content analysis
- Propose learning path recommendations

## Success Criteria
- All three subtasks completed
- System works end-to-end
- Documentation created explaining the handoff protocol

## Output
Create a file: `agents/synthesis/learning/2026-02-18-delegation-practice.md` documenting:
1. How you decomposed the task
2. What information you provided to each agent
3. How you verified their work
4. Lessons learned about coordination

---

*This is a training exercise. Focus on delegation patterns, not perfection.*
