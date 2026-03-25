# MEMORY.md - Long-Term Memory

**Only load in main sessions.** Skip in shared contexts (Discord, groups).

## Trading Operation

- **Mission**: Algorithmic trading profits
- **Phase 1**: XRP bot on Pionex (Market Cipher v2)
- **Target**: $200/day

**Assets:**
- `/storage/workspace/projects/trading/pionex/` - XRP bot
- `/storage/workspace/thehub/` - Next.js dashboard
- `/storage/workspace/projects/android/` - Spectre app (planning)

**Prefs:** Paper trading default, Pionex only, COIN-M futures, CoinGecko prices, autonomous execution

---

## Norse Pantheon Agents

Eight-agent architecture for autonomous trading operations:

| Agent | Role | Purpose |
|-------|------|---------|
| 📯 Heimdall | Coordinator | Delegates tasks, monitors health, escalates to user |
| 🦅 Huginn | Scout | Market research, opportunity discovery |
| ⚔️ Tyr | Strategist | Strategy development, backtesting, risk parameters |
| 🔨 Sindri | Smith | Bot implementation from Tyr's specs |
| 🔨 Brokkr | Builder | Android APK builds, deployment to Hub |
| 🌊 Njord | Treasurer | Read-only fund tracking, P&L reports |
| ⚡ Thor | Executor | Live trading within circuit breakers |
| 🌳 Mimir | Operator | Infrastructure, The Hub, system monitoring |

**Communication Walls:**
- Treasury (Njord) ↔ isolated from code agents (Sindri)
- Execution (Thor) ↔ cannot change strategy (Tyr)
- Research (Huginn) ↔ cannot deploy or trade

**Location:** `/storage/workspace/agents/{heimdall,huginn,tyr,sindri,njord,thor,mimir}/SKILL.md`

---

## Risk Management

**XRP Bot v2.1 — Circuit Breakers:**

| Breaker | Threshold | Action |
|---------|-----------|--------|
| Daily Loss | 5% of allocation | STOP trading, alert |
| Max Drawdown | 15% from peak | STOP, await approval |
| Consecutive Losses | 5 trades | PAUSE, review strategy |
| API Error Rate | >10% | PAUSE, alert Mimir |

**Stop-Loss / Take-Profit:**
- Stop-loss: 2% from entry
- Take-profit: 4% from entry (2:1 R:R)
- Trailing stop: Activates at +2% profit, trails at 1.5%

**Paper Trade Validation:** 7 days minimum, >50% win rate, <15% drawdown

**Location:** `/storage/workspace/projects/trading/strategies/xrp-market-cipher-v2.md`

---

## Infrastructure (Mar 2026)

| Component | Details |
|-----------|---------|
| GPU | Tesla P40 24GB |
| Models | qwen3-coder:30b, qwen3.5:35b, qwen3.5:27b |
| Storage | NVMe 256GB (boot), RAID0 3.6TB (/storage), 2×8TB WD Red (unused) |
| Network | Tailscale IP: 100.112.56.61 |
| Services | OpenClaw (18789), TheHub (3000), ComfyUI (8188), SearXNG (8082) |

---

## Tracking Systems

**Calendar:** `/calendar` on The Hub — Goals, deadlines, milestones
**Journal:** `/journal` on The Hub — Daily changes, decisions, learnings
**Notes:** "note:" prefix in chat adds to implementation queue
**QMD Search:** 75 workspace files indexed for semantic search

---

## System (Contact)

- **Telegram:** 8464154608 (bot: @AISpectre_bot)
- **Timezone:** America/Chicago (CDT/UTC-5)

---

## Events

See `memory/2026-03-events.md` for recent events.

## Agent Learning Archive

See `memory/2026-02-agent-learning.md` — 47+ docs covering trading, Python, Android, UI patterns.