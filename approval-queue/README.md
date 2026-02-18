# Job Approval Queue System

## Purpose
Queue for tasks requiring user approval before execution.

## How It Works

1. **Agent completes task** → Creates a request in queue
2. **User reviews** → Approves or rejects
3. **On approval** → Agent executes final step

## Queue Location
`~/.openclaw/workspace/approval-queue/`

## File Format
Each request is a JSON file: `YYYY-MM-DD-HHMMSS-agent-task-id.json`

```json
{
  "id": "2026-02-18-034515-ghost-deploy",
  "timestamp": "2026-02-18T03:45:15Z",
  "agent": "ghost",
  "task": "Deploy trading bot to production",
  "requester": "synthesis",
  "description": "Jupiter momentum bot has passed paper trading. Ready for live deployment with $100 test capital.",
  "files_changed": [
    "bots/jupiter_momentum_bot.py",
    "config/live_config.yaml"
  ],
  "risk_level": "medium",
  "estimated_impact": "May lose up to $100 if strategy fails",
  "approvals_needed": ["user"],
  "status": "pending",
  "auto_execute_on_approval": true
}
```

## Status Values
- `pending` - Awaiting review
- `approved` - User approved, ready to execute
- `rejected` - User rejected, do not execute
- `executed` - Action completed

## Risk Levels
- `low` - Documentation, read-only analysis, learning materials
- `medium` - Code changes, configuration updates, test deployments
- `high` - Live trading, money at risk, irreversible actions
- `critical` - Large capital deployment, system changes

## Approval Commands

Check queue:
```bash
ls ~/.openclaw/workspace/approval-queue/ | grep pending
```

Approve (user):
```bash
# Edit file, change status to "approved"
# System automatically notifies agent to execute
```

Reject:
```bash
# Edit file, change status to "rejected"
# System notifies agent of rejection with reason
```

## Auto-Queue Rules

These actions **automatically** create approval requests:

| Action | Risk Level | Approver |
|--------|-----------|----------|
| Live trading deployment | high | user |
| Capital allocation >$500 | critical | user |
| Database schema changes | medium | user |
| Production config changes | medium | user |
| New exchange integration | high | user |
| Git push to main | low | auto (no approval) |

## No-Approval Actions (Auto-Execute)
These run without approval:
- Paper trading only
- Documentation
- Learning/research
- Test files
- Local development
- Read-only analysis

## Notification
When items are added to queue:
- Telegram notification to user
- Dashboard badge shows count
- Summary in daily report

## Current Queue Status