# OpenClaw Operations Overview

## Infrastructure Stack

```
┌─────────────────────────────────────────────────────────────┐
│                        HOST (yeatzai)                       │
│                    Tailscale: 100.112.56.61                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                 OPENCLAW GATEWAY                        │  │
│  │                    Port 18789                            │  │
│  │                                                         │  │
│  │   Main Agent (runs on HOST, not Docker)               │  │
│  │   └── Coordinates all subagents                        │  │
│  │                                                         │  │
│  │   Norse Pantheon Agents:                                │  │
│  │   ├── Heimdall 📯 Coordinator                           │  │
│  │   ├── Huginn 🦅 Scout                                  │  │
│  │   ├── Tyr ⚔️ Strategist                                │  │
│  │   ├── Sindri 🔨 Smith                                  │  │
│  │   ├── Njord 🌊 Treasurer                                │  │
│  │   ├── Thor ⚡ Executor (sandbox: off)                   │  │
│  │   └── Mimir 🌳 Operator (sandbox: off)                 │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                   THE HUB                               │  │
│  │                   Port 3000                             │  │
│  │   Dashboard, Agents, Calendar, Trading                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                   XRP BOT                               │  │
│  │              runs on HOST directly                      │  │
│  │              uses VPN via localhost:1080                │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │              DOCKER CONTAINERS                           │  │
│  │                                                         │  │
│  │   surfshark-dubai (WireGuard VPN)                       │  │
│  │   └── localhost:1080 → Dubai IP                         │  │
│  │                                                         │  │
│  │   openclaw-sbx-agent-* (Isolated sandboxes)            │  │
│  │   ├── Cron jobs                                         │  │
│  │   └── Subagents (when sandbox != off)                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                   OLLAMA                                │  │
│  │              localhost:11434                            │  │
│  │   qwen3.5:27b, qwen3-coder:30b, qwen3.5:35b            │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent Architecture

### Norse Pantheon (7 Agents)

| Agent | Role | Sandbox | Model | Can Do |
|-------|------|---------|-------|--------|
| 📯 **Heimdall** | Coordinator | default | cloud | Briefings, alerts, coordination |
| 🦅 **Huginn** | Scout | default | cloud | Market research, web search |
| ⚔️ **Tyr** | Strategist | default | cloud | Strategy, backtesting |
| 🔨 **Sindri** | Smith | default | cloud | Code implementation |
| 🌊 **Njord** | Treasurer | default | cloud | Balance tracking (read-only) |
| ⚡ **Thor** | Executor | **off** | cloud | Trade execution, VPN access |
| 🌳 **Mimir** | Operator | **off** | cloud | Infrastructure, The Hub |

### Sandbox Modes

| Mode | Where | Can Reach |
|------|-------|-----------|
| `default` | Docker container | Internet ✅, Host services ❌ |
| `off` | Host (your machine) | Everything ✅ |

### Model Assignments

| Used By | Model | Cost |
|---------|-------|------|
| Cron jobs | ollama-cloud/glm-5:cloud | Paid |
| Subagents | ollama-cloud/glm-5:cloud | Paid |
| Main agent | ollama-cloud/glm-5:cloud | Paid |
| Fallback | ollama-local/qwen3.5:27b | Free |

---

## Cron Jobs

### Status Overview

| Job | Schedule | Status | Issue |
|-----|----------|--------|-------|
| mimir-service-monitor | Every 5min | ✅ OK | — |
| workspace-backup | Every 2h | ✅ OK | — |
| heimdall-health-check | Hourly | ❌ Error | Sandbox + local model |
| morning-briefing | 8 AM | ❌ Error | Fixed script, needs model fix |
| daily-checkin | 9 PM | ❌ Error | Sandbox + local model |
| end-of-day | 11 PM | ❌ Error | Sandbox + local model |
| security-audit | 6 AM | ❌ Error | Sandbox + local model |
| security-fix | 6:30 AM | ❌ Error | Sandbox + local model |
| api-key-audit | 7 AM | ❌ Error | Sandbox + local model |
| cron-health-monitor | 7:30 AM | ❌ Error | Sandbox + local model |

### Why They Fail

```
Cron Job (sandbox: default, Docker)
    └── Uses ollama-local/qwen model
        └── Docker can't reach host's Ollama
            └── FAILS
```

### What Works

```
Cron Job (sandbox: default, Docker)
    └── Uses ollama-cloud/glm-5:cloud
        └── Cloud API, no local access needed
            └── SUCCESS
```

---

## Trading Operation

### XRP Bot (Market Cipher v2.1)

```
Location: /storage/workspace/projects/trading/pionex/xrp/
Status: RUNNING (2 instances - should be 1)
Mode: Paper trading
Balance: 142.32 XRP
VPN: surfshark-dubai (Dubai) - WORKING
```

**Flow:**
```
XRP Bot (Python script)
    └── Runs on HOST
        └── Uses ENV: SOCKS_PROXY_HOST=127.0.0.1, SOCKS_PROXY_PORT=1080
            └── Connects through WireGuard container
                └── Routes through Dubai IP
                    └── Accesses Pionex API ✅
```

**Strategy:** Market Cipher v2.1 (not RSI Momentum yet)

---

## Current Issues

### Critical

1. **Multiple bot instances** - `xrp-bot.sh` doesn't properly kill old processes
2. **Cron jobs failing** - Using `ollama-local` in Docker sandbox

### Fixed Today

1. ✅ Morning briefing script created
2. ✅ Workspace backup working
3. ✅ Norse theme for The Hub
4. ✅ Android app build automated
5. ✅ VPN confirmed working
6. ✅ Bot management script created

### Needs Attention

1. ❌ Fix bot multiple instances
2. ❌ Update cron jobs to use `glm-5:cloud`
3. ❌ Create Thor's SOUL.md
4. ❌ Add Pionex API keys for Thor

---

## File Locations

```
/storage/workspace/
├── agents/
│   ├── heimdall/SKILL.md
│   ├── huginn/SKILL.md
│   ├── tyr/SKILL.md
│   ├── sindri/SKILL.md
│   ├── njord/SKILL.md
│   ├── thor/SKILL.md
│   └── mimir/SKILL.md
├── projects/
│   └── trading/
│       ├── pionex/xrp/bot_mc_v2_1.py
│       └── strategies/
│           ├── rsi-momentum-reversal.md
│           └── orderbook-imbalance-scalp.md
├── thehub/ (Next.js dashboard)
├── scripts/
│   ├── xrp-bot.sh
│   ├── build-android-app.sh
│   └── morning-briefing.sh
└── MEMORY.md
```

---

## Config Files

```
~/.openclaw/
├── openclaw.json         # Main config
└── agents/
    ├── main/
    ├── heimdall/
    ├── huginn/
    ├── tyr/
    ├── sindri/
    ├── njord/
    ├── thor/
    └── mimir/
        ├── agent.json     # Agent-specific config
        └── settings.json  # Memory/skills
```

---

## Quick Reference

### To Start XRP Bot
```bash
/storage/workspace/projects/trading/pionex/xrp/xrp-bot.sh start
```

### To Check Bot Status
```bash
/storage/workspace/projects/trading/pionex/xrp/xrp-bot.sh status
```

### To Check Cron Jobs
```bash
openclaw cron list
```

### To View The Hub
```
http://localhost:3000/          # Dashboard (Valhalla)
http://localhost:3000/agents   # The Pantheon
http://localhost:3000/calendar # Seasons
```

### To View OpenClaw Dashboard
```
http://localhost:18789/
```