# HEARTBEAT.md

## Operating Schedule

| Time | Task |
|------|------|
| 8:00 AM | Morning briefing: weather (Alexandria MN), bot status, today's tasks, one project idea |
| 9:00 PM | Daily improvement showcase - present autonomous work completed to improve workflows |
| 11:00 PM | End of day wrap up: accomplishments + tomorrow's priorities |

## Proactive Checks (every 30 min - 2 hours)

### Trading Bots
- [ ] Check if XRP bot is running
- [ ] Restart if crashed
- [ ] Alert if repeated crashes
- [ ] Monitor win rate and profitability

### System Health
- [ ] Check disk space (alert if >90%)
- [ ] Check OpenClaw gateway status
- [ ] Check thehub server (port 3000)

### Memory Maintenance
- [ ] Clean old memory files (>7 days)
- [ ] Check git status of workspace

## Weekly Audit (Sundays)

Run context bloat audit on: AGENTS.md, TOOLS.md, USER.md, MEMORY.md, HEARTBEAT.md, SOUL.md

For each file:
1. Move task-specific content → skills
2. Move historical content → memory/
3. Cut redundancy (one canonical location)
4. Compress (tables > paragraphs, bullets > prose)
5. Report before/after tokens

---
If all checks pass, reply: HEARTBEAT_OK
If issues found, alert the user.