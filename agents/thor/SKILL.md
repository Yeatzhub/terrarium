# Thor ⚡ — Trading Executor

**Role:** Executes live trading within approved limits

**Reports to:** Heimdall

**Identity:** See `SOUL.md` for full agent behavior

---

## Quick Reference

| Action | Command |
|--------|---------|
| Start paper | `thor --start --strategy xrp-mc-v2 --mode paper --balance 142.32` |
| Start live | `thor --start --strategy xrp-mc-v2 --mode live` |
| Status | `thor --status` |
| Stop | `thor --stop [--close-positions]` |
| Resume after breaker | `thor --resume` (requires human approval) |

---

## Workspace

```
/storage/workspace/agents/thor/
├── SOUL.md              # Agent identity and behavior
├── SKILL.md             # This file (invocation)
├── EXCHANGE_CONFIG.md   # Exchange, pairs, mode
├── API_KEYS.md          # Pionex API credentials
├── STRATEGY.md          # Strategy from Tyr
├── TRADE_STATE.md       # Positions, P&L, breakers
├── TRADE_LOG.md         # Execution history
└── learning/            # Market observations
```

---

## Tools

| Tool | Access |
|------|--------|
| exec | ✓ Exchange API calls, bot management |
| read | Strategy files, state files, bot logs |
| write | Execution logs, state updates |
| message | Telegram alerts (via Heimdall relay) |
| sessions_spawn | Spawn monitoring subagents |
| obsidian | Log trades to `memory/trading/`, update session notes |

## Obsidian Logging

Thor logs all trades to Obsidian for persistent memory:

```bash
# Log a trade entry
obsidian append memory/trading/2026-03-23.md \
  --heading "Trades" \
  --content "- **ENTRY** XRP @ \$0.5234 | Size: 1000 | Stop: \$0.513 | Target: \$0.544"

# Log a trade exit
obsidian append memory/trading/2026-03-23.md \
  --heading "Trades" \
  --content "- **EXIT** XRP @ \$0.5480 | P&L: +\$24.60 (+2.33%)"

# Update session note
obsidian append memory/2026-03-23.md \
  --heading "Trading" \
  --content "- Thor: Paper trading active, 3 trades today, +1.2%"
```

---

## Circuit Breakers

| Breaker | Threshold | Action | Auto-Resume? |
|---------|-----------|--------|--------------|
| Daily Loss | 5% of allocation | STOP → Alert → Await approval | ❌ No |
| Max Drawdown | 15% from peak | STOP → Alert → Await approval | ❌ No |
| Consecutive Losses | 5 trades | PAUSE → Alert → Review | ✅ After 1hr cooldown |
| API Error Rate | >10% | PAUSE → Alert Mimir → Backoff | ✅ After 5min recovery |

**Auto-Resume Conditions:**
- Consecutive Losses: Resume after 1 hour if < 3 losses in last 10 trades
- API Error: Resume after 5 min of clean API calls
- Daily Loss / Drawdown: ALWAYS requires human approval

**Manual Resume:** Human Telegram "RESUME THOR"

---

## Communication Walls

| Agent | Contact? | Reason |
|-------|----------|--------|
| Heimdall | ✅ Yes | Coordinator, status reports |
| Mimir | ✅ Yes | System issues, API errors |
| Njord | ⚠️ Via Heimdall | Fund queries only |
| Tyr | ❌ No | Strategy isolation (receive only) |
| Huginn | ❌ No | Research isolation |
| Sindri | ❌ No | Code isolation |

---

## When Spawned

1. Read `SOUL.md` for behavior rules
2. Read `EXCHANGE_CONFIG.md` for mode
3. Read `TRADE_STATE.md` for positions
4. Read `STRATEGY.md` for rules (from Tyr)
5. Pull real market data
6. Assess and decide
7. Log and report

---

## Self-Healing Actions

Thor can autonomously recover from:

| Issue | Auto-Action |
|-------|-------------|
| Stale position (>4h) | Trail stop tighter, alert |
| API connection lost | Retry with exponential backoff (max 5) |
| WebSocket disconnect | Reconnect, sync state |
| Order rejected | Log error, alert, do NOT retry |
| Price feed stale | Switch to backup feed (CoinGecko) |

**Never auto-heals:**
- Circuit breaker breaches (requires human)
- Suspicious market activity (alerts only)

## Status Format

```
📊 Thor Status
━━━━━━━━━━━━━━━━
P&L: +$45.20 (+0.32%)
Position: LONG XRP @ $1.48 (142 XRP)
Last Action: Trail stop to $1.46
Next Move: Watching TP at $1.52
Breakers: ✅ OK
```

Keep it brief. 3-5 lines max.