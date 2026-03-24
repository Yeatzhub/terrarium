---
name: obsidian
description: Read, write, and query notes in the Obsidian vault via REST API. Use for agent memory logging, trade journals, session notes, and Dataview queries.
homepage: https://obsidian.md
metadata: {"clawdbot":{"emoji":"📝","requires":{"bins":["obsidian"]}}}
---

# Obsidian - Note Management via REST API

Interact with the Obsidian vault via Local REST API plugin.

## Prerequisites

- Obsidian running with vault at `/storage/workspace`
- Local REST API plugin enabled (port 27124)
- API key configured in `.obsidian/plugins/local-rest-api/data.json`
- socat tunnel on port 27125 for Tailscale access

## Usage

### Read a Note

```bash
obsidian read memory/2026-03-23.md
```

### Create/Overwrite a Note

```bash
obsidian write memory/trading/trade-log.md --content "# Trade Log\n\nEntry: XRP @ $0.52"
```

### Append to a Heading

```bash
obsidian append memory/2026-03-23.md --heading "Session Notes" --content "- Checked bot status"
```

### Prepend to a Heading

```bash
obsidian prepend memory/2026-03-23.md --heading "Trading" --content "- Started paper trading"
```

### Patch Frontmatter

```bash
obsidian patch memory/trading/config.md --field status --value "active"
```

### List Notes in Folder

```bash
obsidian list memory/trading/
```

### Search (Dataview DQL)

```bash
obsidian query "TABLE file.name, profit FROM \"memory/trading\" WHERE profit < 0"
```

### Simple Search

```bash
obsidian search "XRP bot"
```

### Create Periodic Note

```bash
obsidian daily  # Today's daily note
obsidian weekly # This week's note
```

## API Details

- **Endpoint:** `https://100.112.56.61:27125` (Tailscale) or `https://127.0.0.1:27124` (localhost)
- **Auth:** Bearer token `openclaw-spectre-2026`
- **Certificate:** Self-signed (use `-k` flag with curl)

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/vault/{path}` | GET | Read note |
| `/vault/{path}` | PUT | Create/overwrite |
| `/vault/{path}` | PATCH | Append/prepend/replace section |
| `/vault/{path}` | DELETE | Delete note |
| `/vault/` | GET | List root |
| `/periodic/daily/` | GET/PUT | Today's daily note |
| `/search/` | POST | Dataview/JsonLogic query |
| `/search/simple/` | POST | Full-text search |

## Agent Integration Examples

### Thor - Log a Trade

```bash
obsidian append memory/trading/2026-03-23.md \
  --heading "Trades" \
  --content "- **ENTRY** XRP @ $0.5234 | Size: 1000 | Stop: $0.513 | Target: $0.544"
```

### Njord - Record P&L

```bash
obsidian write memory/trading/pnl-daily.md \
  --content "# Daily P&L\n\n## 2026-03-23\n- Balance: $142.19\n- Change: +$2.34 (+1.67%)\n- Trades: 3"
```

### Mimir - System Status

```bash
obsidian patch memory/agents/mimir/status.md \
  --field last_check \
  --value "2026-03-23T21:45:00Z"
```

### Heimdall - Daily Briefing

```bash
obsidian write memory/2026-03-23.md \
  --content "# Memory - 2026-03-23\n\n## Morning Briefing\n- Weather: 45°F, clear\n- Bot Status: Running\n- Priority: Review Thor circuit breakers"
```

### Huginn - Research Note

```bash
obsidian write memory/agents/huginn/research/xrp-market-analysis.md \
  --content "# XRP Market Analysis\n\n## 2026-03-23\n\nSentiment: Bullish\nVolume: +15% 24h\nKey levels: $0.50 support, $0.55 resistance"
```

## Dataview Query Examples

```dataview
// All losing trades
TABLE date, profit, pair
FROM "memory/trading"
WHERE profit < 0
SORT date DESC
```

```dataview
// Today's agent activity
TABLE file.name, file.ctime
FROM "memory/agents"
WHERE file.ctime >= date(today)
```

```dataview
// Recent session notes
LIST
FROM "memory"
WHERE file.ctime >= date(today) - dur(7 days)
SORT file.ctime DESC
```

---

**Location:** `/storage/workspace/skills/obsidian/`
**CLI:** `~/bin/obsidian` or `/storage/workspace/skills/obsidian/obsidian.sh`