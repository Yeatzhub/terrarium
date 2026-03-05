# Human-in-the-Loop Patterns for Multi-Agent Systems

**Created:** 2026-02-22 16:20  
**Author:** Synthesis  
**Focus:** Approval gates, escalation protocols, and human-agent collaboration

---

## Why Humans Stay in the Loop

Agents excel at scale and speed. Humans excel at:
- **Judgment** - Nuanced decisions with incomplete info
- **Accountability** - Legal, ethical, financial responsibility
- **Creativity** - Novel solutions, edge cases
- **Trust** - Building confidence in autonomous systems

The trick is knowing *when* to pull humans in.

---

## The HITL Decision Framework

### Intervention Points

```
TASK FLOW:
[Input] → [Agent Processing] → [Human Gate?] → [Execute] → [Result]
                                    ↓
                    ┌───────────────┼───────────────┐
                    ↓               ↓               ↓
               LOW RISK        MEDIUM RISK       HIGH RISK
              (no gate)       (spot check)      (full review)
```

### Risk Level Matrix

| Risk Level | Criteria | Human Role |
|------------|----------|------------|
| **Low** | Internal, reversible, low cost | None (log only) |
| **Medium** | Limited scope, moderate cost | Spot check (5-10%) |
| **High** | External impact, costly, irreversible | Full review required |
| **Critical** | Financial, legal, safety | Approval + witness |

---

## Approval Gate Patterns

### Pattern 1: Pre-Action Approval

Before irreversible actions:

```markdown
AWAITING APPROVAL:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Action: Deploy to production
Agent: deploy_agent
Risk: HIGH (external, irreversible)

Summary:
  - 12 files changed
  - 3 new features
  - All tests passing

Changes:
  ✗ src/auth/oauth.ts (modified)
  ✗ src/middleware/session.ts (modified)  
  + src/utils/cache.ts (new)
  - src/deprecated/legacy.ts (deleted)

Rollback: git revert HEAD
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[APPROVE] [REJECT] [REQUEST CHANGES] [ESCALATE]
```

### Pattern 2: Batch Approval

Group similar actions for efficiency:

```markdown
BATCH APPROVAL REQUEST:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
3 actions requiring approval:

1. Send email to 15 users
   Template: "Welcome to Beta"
   Risk: MEDIUM

2. Update 47 documentation files
   Scope: Fix broken links
   Risk: LOW

3. Create git branch "feature/auth"
   Repository: main-app
   Risk: LOW

[APPROVE ALL] [REVIEW INDIVIDUALLY] [REJECT ALL]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Pattern 3: Delegated Authority

Allow trusted agents limited autonomy:

```yaml
# agent_authority.yaml
agents:
  coder_agent:
    autonomous_actions:
      - read_files
      - write_tests
      - lint_fixes
    requires_approval:
      - delete_files
      - git_push
      - install_packages
    max_budget_tokens: 100000
    
  deploy_agent:
    autonomous_actions:
      - build
      - test
    requires_approval:
      - deploy_staging
      - deploy_production
    allowed_environments:
      - staging
      # production needs explicit approval
```

---

## Escalation Protocols

### When to Escalate

```markdown
ESCALATION TRIGGERS:
━━━━━━━━━━━━━━━━━━━━
□ Agent confidence below 70%
□ Policy violation detected
□ Budget/time exceeded
□ 3+ retry failures
□ Unexpected output format
□ External dependency unavailable
□ User explicitly requested
□ Pattern matches known failure mode
━━━━━━━━━━━━━━━━━━━━
```

### Escalation Levels

```
Level 1: Agent → Fallback Agent
         "I can't handle this, routing to specialist"
         
Level 2: Agent → User (self-service)
         "I need your input: [question]"
         
Level 3: Agent → Admin (intervention)
         "I'm stuck, please review: [context]"
         
Level 4: Agent → Human + Pause
         "Critical issue, halting until resolved"
```

### Escalation Message Format

```markdown
## Escalation: [ESC_ID]

**Level:** [1-4]
**Agent:** [agent_id]
**Session:** [session_id]

### What Happened
[1-2 sentence summary]

### Agent Context
```
[last 3 actions]
current task
attempted solutions
```

### Why Escalated
[Specific trigger]

### Recommended Actions
1. [First suggestion]
2. [Alternative]

### Resume Commands
- `approve` - Continue with agent's recommendation
- `reject [reason]` - Stop and provide feedback
- `steer [direction]` - Guide agent differently
- `takeover` - Switch to manual mode
```

---

## Interaction Patterns

### Pattern 1: Clarification Request

When agent needs more information:

```markdown
CLARIFICATION NEEDED:
━━━━━━━━━━━━━━━━━━━━
Task: "Add authentication"
Ambiguity: Provider not specified

Options:
  A) OAuth (Google, GitHub, etc.)
  B) Email/password
  C) Magic links
  D) All of the above

Reply with letter or custom answer.
Timeout: 5 minutes (will use default: A)
━━━━━━━━━━━━━━━━━━━━
```

### Pattern 2: Progress Checkpoint

Periodic human visibility:

```markdown
PROGRESS UPDATE (25%):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task: Refactor API layer
Status: On track
Time: 8 min elapsed, ~24 min remaining

Completed:
  ✓ Analyzed current structure
  ✓ Identified 12 endpoints to refactor
  ✓ Created migration plan

Next (26-50%):
  → Refactor auth endpoints
  → Write integration tests

On schedule? YES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Pattern 3: Confidence Report

Proactive uncertainty disclosure:

```markdown
CONFIDENCE REPORT:
━━━━━━━━━━━━━━━━━━━━
Task: Generate migration script
Overall: 78%

Breakdown:
  Syntax correctness: 95% ✓
  Handles edge cases: 70% ⚠️
  Performance optimal: 60% ⚠️
  Idempotent: 85% ✓

Uncertainties:
  - Large dataset handling untested
  - Index rebuild time estimated

Recommendation: Review output before running on production
━━━━━━━━━━━━━━━━━━━━
```

---

## Approval Workflow

### Standard Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Agent       │────→│ Approval    │────→│ Execute     │
│ Proposes    │     │ Queue       │     │ Action      │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    ↓             ↓
              [APPROVE]     [REJECT]
                    │             │
                    ↓             ↓
              Execute         Notify Agent
                               with reason
```

### Approval States

| State | Meaning | Next |
|-------|---------|------|
| PENDING | Waiting for human | → APPROVED / REJECTED / EXPIRED |
| APPROVED | Human approved | → Execute |
| REJECTED | Human declined | → Notify agent |
| EXPIRED | Timeout reached | → Default action or escalate |
| CANCELLED | Superseded | → End |

### Timeout Handling

```python
APPROVAL_CONFIG = {
    "default_timeout": 3600,  # 1 hour
    "escalation_timeout": 7200,  # 2 hours
    "expiry_action": "reject",  # or "approve" for low-risk
    "reminder_intervals": [600, 1800, 3600]  # 10min, 30min, 1hr
}

def handle_expiry(approval):
    if approval.risk == "LOW":
        return "approve_with_log"
    elif approval.risk == "MEDIUM":
        return "escalate_to_admin"
    elif approval.risk == "HIGH":
        return "reject_with_notification"
```

---

## Implementation Patterns

### Approval Store

```python
# Approval state management
class ApprovalStore:
    def __init__(self, db_path="approvals.json"):
        self.store = load_json(db_path)
    
    def create(self, action, context, risk_level):
        approval = {
            "id": generate_id(),
            "action": action,
            "context": context,
            "risk_level": risk_level,
            "state": "PENDING",
            "created": now(),
            "expires": now() + get_timeout(risk_level),
            "approver": None,
            "decision": None
        }
        self.store[approval["id"]] = approval
        return approval
    
    def approve(self, approval_id, approver):
        self.store[approval_id].update({
            "state": "APPROVED",
            "approver": approver,
            "decision": "approved",
            "decided_at": now()
        })
    
    def reject(self, approval_id, approver, reason):
        self.store[approval_id].update({
            "state": "REJECTED",
            "approver": approver,
            "decision": "rejected",
            "reason": reason,
            "decided_at": now()
        })
```

### Notification Channels

```markdown
ROUTING RULES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Risk: LOW      → Log only
Risk: MEDIUM   → Daily digest
Risk: HIGH     → Immediate notification
Risk: CRITICAL → Immediate + escalation chain

CHANNELS:
- Log: /var/log/approvals.log
- Digest: Email summary at 6pm
- Immediate: Slack #agent-approvals
- Escalation: SMS + Slack @channel
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Audit Trail

### Required Audit Fields

```json
{
  "approval_id": "apr_abc123",
  "action_type": "deploy",
  "agent_id": "deploy_agent",
  "risk_level": "HIGH",
  "created_at": "2026-02-22T16:20:00Z",
  "decided_at": "2026-02-22T16:25:00Z",
  "approver": "user@example.com",
  "decision": "approved",
  "context_hash": "sha256:...",
  "rejection_reason": null
}
```

### Audit Queries

```bash
# All approvals by user
cat audit.json | jq 'select(.approver == "user@example.com")'

# Rejected actions
cat audit.json | jq 'select(.decision == "rejected")'

# Actions by risk level
cat audit.json | jq 'group_by(.risk_level) | map({risk: .[0].risk_level, count: length})'
```

---

## Quick Reference

```markdown
HUMAN-IN-THE-LOOP CHEAT SHEET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LOW RISK:
  → No approval needed
  → Log for audit
  → Include in digest

MEDIUM RISK:
  → Spot check (5-10%)
  → Batch approvals allowed
  → 1 hour timeout

HIGH RISK:
  → Full review required
  → Individual approvals
  → 4 hour timeout
  → Reminder at 50%

CRITICAL:
  → Approval + witness
  → No timeout (must be explicit)
  → Full audit trail
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ESCALATE WHEN:
  □ Confidence < 70%
  □ 3+ failures
  □ Budget exceeded
  □ Policy violation

REJECTION = LEARNING:
  → Agent receives reason
  → Pattern added to avoid repeat
  → Metric tracked for improvement
```

---

## Bottom Line

Humans don't slow down agents—waiting for the wrong humans does:
1. **Classify risk** → Right approval level
2. **Batch intelligently** → Reduce interruptions
3. **Set timeouts** → Don't block forever
4. **Maintain audit** → Accountability trail
5. **Close the loop** → Rejections improve future behavior

The goal: Maximum autonomy with minimum surprises.