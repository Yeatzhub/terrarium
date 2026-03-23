# Agent Memory Folders

Each Norse agent writes to their dedicated folder:

| Agent | Folder | Content |
|-------|--------|---------|
| 📯 Heimdall | `memory/agents/heimdall/` | Daily briefings, coordination notes |
| 🦅 Huginn | `memory/agents/huginn/` | Market research, opportunity discoveries |
| ⚔️ Tyr | `memory/agents/tyr/` | Strategy documents, backtest results |
| 🔨 Sindri | `memory/agents/sindri/` | Code changes, deployment logs |
| 🌊 Njord | `memory/agents/njord/` | P&L reports, balance tracking |
| ⚡ Thor | `memory/agents/thor/` | Trade logs, execution notes |
| 🌳 Mimir | `memory/agents/mimir/` | System status, infrastructure updates |

## Usage via Obsidian REST API

```bash
# Mimir writes system status
obsidian write memory/agents/mimir/status.md --content "# System Status..."

# Thor appends trade log
obsidian append memory/trading/2026-03-23.md --heading "Trades" --content "- ENTRY..."

# Njord writes P&L
obsidian write memory/trading/pnl-daily.md --content "# Daily P&L..."
```

## Dataview Query Examples

```dataview
TABLE file.ctime, file.name
FROM "memory/agents/mimir"
WHERE file.ctime >= date(today)
```

```dataview
TABLE profit, pair
FROM "memory/trading"
WHERE profit < 0
SORT file.ctime DESC
```