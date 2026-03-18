# Norse Continuous Learning

## Overview

A self-improvement capability for the Norse pantheon that analyzes runtime history, identifies improvement opportunities, and proposes changes for human approval.

**Key Difference from Capability Evolver:**
- Collaborative (uses Norse agents)
- Human-in-the-loop for code changes
- No external dependencies (no EvoMap)
- Memory-based learning (no self-modification)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    HEIMDALL (Coordinator)                   │
│   - Scans agent learning/ directories                      │
│   - Identifies patterns, failures, improvements            │
│   - Generates daily learning report                        │
│   - Proposes changes to user                                │
├─────────────────────────────────────────────────────────────┤
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              LEARNING PIPELINE                          ││
│  │  1. Analyze → 2. Propose → 3. Review → 4. Implement   ││
│  └─────────────────────────────────────────────────────────┘│
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              AGENT LEARNING DIRS                        ││
│  │  agents/huginn/learning/*.md                           ││
│  │  agents/tyr/learning/*.md                               ││
│  │  agents/sindri/learning/*.md                            ││
│  │  agents/njord/learning/*.md                             ││
│  │  agents/thor/learning/*.md                              ││
│  │  agents/mimir/learning/*.md                             ││
│  └─────────────────────────────────────────────────────────┘│
│                         ↓                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              IMPLEMENTATION                             ││
│  │  Sindri → code changes                                  ││
│  │  Mimir → infrastructure                                 ││
│  │  Tyr → strategy updates                                ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Phases

### Phase 1: Analyze (Daily)

**Agent:** Heimdall
**Schedule:** 8 AM CDT (morning briefing)

**What it does:**
1. Scan all `agents/*/learning/*.md` files
2. Look for patterns:
   - Repeated errors
   - Failed tasks
   - Successful solutions
   - Optimization opportunities
3. Identify learning opportunities
4. Store in `memory/learning-YYYY-MM-DD.md`

**Example analysis:**
```markdown
# Learning Analysis - 2026-03-18

## Patterns Found

### Huginn Learning
- Discovered: RSI patterns in XRP correlate with volume
- Source: agents/huginn/learning/2026-03-18-rsi-volume.md
- Significance: Could improve XRP bot strategy

### Thor Learning
- Error: Multiple VPN disconnections (3 occurrences)
- Source: agents/thor/learning/2026-03-18-vpn-disconnect.md
- Significance: Need VPN health check in Mimir

### Sindri Learning
- Success: Reduced bot startup time by 40%
- Source: agents/sindri/learning/2026-03-18-startup-optimize.md
- Significance: Good - no action needed

## Proposed Improvements
1. [HIGH] Add VPN health check to Mimir
2. [MEDIUM] Update XRP strategy with RSI-volume correlation
3. [LOW] Document startup optimization

## Approval Needed
- Strategy update requires user approval
- Infrastructure changes auto-apply if <5% risk
```

---

### Phase 2: Propose (Daily)

**Agent:** Heimdall
**Output:** Telegram message with proposals

**Proposal format:**
```
🌅 Daily Learning Analysis

📊 Patterns: 3 found
🔴 Issues: 1 (VPN disconnections)
✅ Improvements: 1 (startup time)

📈 Proposed Actions:

[1] HIGH: Add VPN health check
    Risk: Low
    Impact: Prevents trading downtime
    → /approve vpn-health

[2] MEDIUM: Update XRP strategy with RSI-volume
    Risk: Medium
    Impact: Better trade signals
    → /approve rsi-strategy

[3] Document startup optimization
    Risk: None
    Status: Already applied

Reply with /approve <id> to proceed.
```

---

### Phase 3: Review (Interactive)

**Agent:** User
**Action:** Approve or reject proposals

**Approval commands:**
- `/approve all` - Apply all proposals
- `/approve <id>` - Apply specific proposal
- `/reject <id>` - Reject proposal
- `/defer <id>` - Defer to later

**Risk thresholds:**
- **Auto-apply** (no approval needed):
  - Documentation changes
  - Log cleanup
  - Memory maintenance
  
- **Needs approval:**
  - Code changes
  - Strategy updates
  - Infrastructure changes
  - New dependencies

- **Always rejected:**
  - Self-modification of core agents
  - External API calls without approval
  - Removing safety checks

---

### Phase 4: Implement

**Agents:** Sindri (code), Mimir (infra), Tyr (strategy)

**Implementation flow:**
```
User approves → Heimdall delegates:
  - Code changes → Sindri
  - Infrastructure → Mimir
  - Strategy → Tyr
  - Updates → MEMORY.md
```

**After implementation:**
1. Agent writes to `learning/YYYY-MM-DD-implementation.md`
2. Heimdall verifies in next morning's analysis
3. Learning is archived in `memory/archive/`

---

## Learning File Format

### Directory Structure
```
agents/
├── heimdall/
│   └── learning/
│       └── 2026-03-18-coordination-patterns.md
├── huginn/
│   └── learning/
│       └── 2026-03-18-market-discovery.md
├── tyr/
│   └── learning/
│       └── 2026-03-18-strategy-backtest.md
├── sindri/
│   └── learning/
│       └── 2026-03-18-code-patterns.md
├── njord/
│   └── learning/
│       └── 2026-03-18-balance-analysis.md
├── thor/
│   └── learning/
│       └── 2026-03-18-execution-log.md
└── mimir/
    └── learning/
        └── 2026-03-18-infrastructure.md
```

### Learning File Template
```markdown
# Learning: [Short Title]
Date: YYYY-MM-DD
Agent: [agent name]
Type: discovery | error | success | optimization

## What Happened
[Description of what occurred or was discovered]

## Context
[Relevant context, environment, timing]

## Impact
[How this affects the operation]

## Proposed Action
[What should be done about it]

## Risk Level
[low | medium | high]

## Status
[proposed | approved | implemented | archived]
```

---

## Implementation Checklist

### Files to Create
```
/storage/workspace/agents/heimdall/learning/
  └── (daily learning files generated by Heimdall)

/storage/workspace/memory/
  └── learning-YYYY-MM-DD.md (daily analysis)

/storage/workspace/memory/archive/
  └── learning-YYYY-MM-DD.md (archived after implementation)
```

### SKILL.md Updates

**Heimdall SKILL.md** - Add learning scanning:
```markdown
## Continuous Learning

### Daily Analysis (8 AM CDT)
1. Scan all agents/*/learning/*.md
2. Identify patterns and improvements
3. Generate learning-YYYY-MM-DD.md
4. Send proposals to Telegram

### Learning Categories
- **Error Pattern**: 3+ similar errors across agents
- **Success Pattern**: Repeated success worth documenting
- **Optimization**: Performance improvement data
- **Discovery**: New insight from Huginn/Tyr
```

### Cron Job
```bash
# learning-analysis.sh - runs at 8 AM CDT
# Scans learning dirs, proposes improvements
```

---

## Comparison to Capability Evolver

| Feature | Capability Evolver | Norse Learning |
|---------|-------------------|-----------------|
| Self-modification | ✅ Yes | ❌ No (human approval required) |
| External API | ✅ EvoMap Hub | ❌ None |
| Human approval | Optional | Required for code/strategy |
| Architecture | Single agent | Collaborative (7 Norse agents) |
| Memory | GEP protocol | Simple markdown files |
| Risk | Higher | Lower |
| Transparency | Code-based | Memory-based (readable) |

---

## Example Usage

### Agent Creates Learning File

**Huginn discovers something:**
```markdown
# Learning: RSI-Volume Correlation in XRP
Date: 2026-03-18
Agent: Huginn
Type: discovery

## What Happened
RSI(14) crosses above 30 only lead to profitable trades when volume > 1.5x average.

## Context
Analyzed 50 XRP trades over 7 days. 23 trades with RSI crosses.
Volume filter would have filtered out 18 unprofitable trades.

## Impact
Could improve XRP bot win rate by ~15%.

## Proposed Action
Update XRP strategy to include volume filter on RSI signals.

## Risk Level
low

## Status
proposed
```

### Heimdall Analyzes

**Morning briefing:**
```
🌅 Learning Analysis - 2026-03-18

📊 1 pattern found from Huginn

📈 [1] MEDIUM: Add volume filter to RSI strategy
    Impact: +15% win rate
    Risk: Low
    → /approve rsi-volume
```

### User Approves

```
User: /approve rsi-volume
```

### Heimdall Delegates

```
/approved: rsi-volume
→ Delegating to Tyr for strategy update
→ Tyr will update /storage/workspace/projects/trading/strategies/rsi-momentum-reversal.md
→ Sindri will implement in bot code
```

---

## Safety Guarantees

1. **No self-modification** - Agents can't modify their own SKILL.md files
2. **Human gatekeeper** - All code/strategy changes require approval
3. **Transparent learning** - All learning stored in readable markdown
4. **Rollback capability** - Git tracks all changes
5. **Risk classification** - Each proposal has risk level
6. **Memory bounds** - Learning files >7 days archived

---

## Next Steps

Want me to:

1. **Create the cron job** for daily learning analysis?
2. **Update Heimdall's SKILL.md** to include learning pipeline?
3. **Create the learning directory structure**?
4. **Build the approval flow** in Telegram?