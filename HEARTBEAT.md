# HEARTBEAT.md

## Operating Schedule (America/Chicago — CDT/UTC-5)

| Time (CDT) | Time (UTC) | Task |
|------------|------------|------|
| 8:00 AM | 13:00 | Morning briefing: weather (Alexandria MN), bot status, today's tasks, one project idea |
| 9:00 PM | 02:00 | Daily improvement showcase - present autonomous work completed to improve workflows |
| 11:00 PM | 04:00 | End of day wrap up: accomplishments + tomorrow's priorities |

## Proactive Checks (every 30 min - 2 hours)

**Run these directly — do not spawn subagents (sandbox network issues).**

### Trading (Thor)
- [ ] Check Thor Docker container status
- [ ] Check TradingView webhook is receiving signals
- [ ] Monitor position and P&L

### System Health
- [ ] Check disk space (alert if >90%)
- [ ] Check OpenClaw gateway status
- [ ] Check thehub server (port 3000)
- [ ] Check ComfyUI (port 8188) — Bragi's design engine
- [ ] Check Hub sync queue (pending updates in updates.json)

### Calendar & Goals
- [ ] Check for overdue goals
- [ ] Check goals due today
- [ ] Alert on high-priority/critical goals

### Journal
- [ ] Note any significant changes made during session
- [ ] Add journal entry for: code changes, strategy updates, agent work

### Memory Maintenance
- [ ] Clean old memory files (>7 days)
- [ ] Check git status of workspace

---
If all checks pass, reply: HEARTBEAT_OK
If issues found, alert the user.