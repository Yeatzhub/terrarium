# Multi-Agent Coordination Patterns
*Synthesis Learning — 2026-02-20*

## 1. Task Decomposition Patterns

### Fan-Out Pattern
```
Parent Task → [Sub-agent A] [Sub-agent B] [Sub-agent C] → Aggregate Results
```
- Use when: Independent subtasks, parallel execution possible
- Implementation: Spawn sub-agents via `sessions_spawn`, poll with `subagents list`
- Timeout: Set `runTimeoutSeconds` per subtask + buffer for aggregation

### Pipeline Pattern
```
Stage 1 → Stage 2 → Stage 3 → Final Output
```
- Use when: Sequential dependencies, output of stage N feeds stage N+1
- Implementation: Chain via `sessions_send` to next agent, pass context explicitly
- Key: Each stage validates input before processing

### Map-Reduce Pattern
```
Data → [Shard 1] ... [Shard N] → [Reduce] → Result
```
- Use when: Large datasets, distributable workloads
- Implementation: Shard data in parent, spawn workers, collect via `sessions_history`

## 2. Dependency Management

### Explicit Contracts
Every inter-agent message must include:
```json
{
  "taskId": "uuid",
  "dependsOn": ["uuid-1", "uuid-2"],
  "deliverables": ["file.md", "analysis.json"],
  "checkpoint": true/false
}
```

### Checkpoint Protocol
- **When**: After expensive operations, before risky branches
- **How**: Write state to workspace, reference in `MEMORY.md`
- **Recovery**: Check `sessions_list` for status, resume from last checkpoint

### Deadlock Prevention
1. Always set `timeoutSeconds` on blocking operations
2. Use `subagents(action="kill")` for stuck processes
3. Implement exponential backoff on retries (max 3 attempts)

## 3. Context Handoff Protocols

### Structured Handoff
```markdown
## Handoff: Task Analysis → Code Generation

**Completed**:
- Architecture diagram: `docs/arch-2026-02-20.png`
- API contract: `contracts/api-v2.yaml`

**Context for Next Agent**:
- User preference: Fast iteration over perfection
- Risk areas: Database migrations (flagged)
- Skip: Authentication layer (already implemented)

**Success Criteria**:
- All endpoints return 200 in tests
- < 100ms response time for hot paths
```

### Minimal Viable Context
- **Include**: User intent, constraints, decisions made, file paths
- **Exclude**: Full conversation logs, implementation details (link instead)
- **Rule**: < 500 tokens per handoff; link to details in workspace

### State Persistence
- Short-term: `sessions_history` for recent context
- Medium-term: `memory/YYYY-MM-DD.md` for session notes
- Long-term: `MEMORY.md` for curated knowledge, `SKILL.md` for capabilities

## 4. Integration Testing

### Agent Contract Tests
```bash
# Verify sub-agent responds correctly to task type
openclaw sessions_spawn --task "TEST: Verify JSON output format" --agentId verifier
```

### End-to-End Validation
1. **Golden Path**: Happy flow with known-good inputs
2. **Error Injection**: Invalid inputs, timeouts, missing dependencies
3. **Load Test**: Multiple concurrent sub-agent spawns (monitor via `session_status`)

### Quality Gates
- All spawned tasks must complete within `timeoutSeconds`
- Output files must exist (verify with `read` before claiming success)
- Sub-agent results must be parsable (JSON validation)

## 5. Quality Standards

### Output Verification
| Check | Tool | Frequency |
|-------|------|-----------|
| File exists | `read` | Every file write |
| Format valid | JSON/YAML parse | Structured outputs |
| Links work | `web_fetch` | Documentation |
| Tests pass | `exec` | Code generation |

### Error Handling
- **Retry**: 3 attempts with exponential backoff
- **Escalate**: After retries fail, surface to user with full context
- **Log**: Write failures to `memory/` for pattern analysis

### Performance Budgets
- Sub-agent spawn: < 5s overhead
- Context handoff: < 500 tokens
- Total workflow: User-specified timeout (default 300s)

---

## Quick Reference: When to Use What

| Scenario | Pattern | Key Tool |
|----------|---------|----------|
| Parallel research | Fan-Out | `sessions_spawn` × N |
| Build pipeline | Pipeline | `sessions_send` chain |
| Large data processing | Map-Reduce | Shard + aggregate |
| Complex async workflow | State Machine | `cron` + checkpoints |
| User-facing real-time | Single Agent | Direct response |

---

*Next: Apply to workflow optimization for code review automation.*
