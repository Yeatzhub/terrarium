# Spectre Memory Vault

## Obsidian Setup for OpenClaw

### Installed Plugins

1. **Local REST API** (v3.5.0) - Enables HTTP access to notes
   - Endpoint: `https://127.0.0.1:27124/`
   - API Key: `openclaw-spectre-2026`
   - Allows OpenClaw agents to read/write notes programmatically

2. **Dataview** (v0.5.70) - Query notes like a database
   - Use `TABLE`, `LIST`, `TASK` queries
   - Example: `TABLE date, profit FROM "memory/trading" WHERE profit < 0`

3. **Periodic Notes** - Daily/weekly note templates
   - Daily notes stored in `memory/`
   - Format: `YYYY-MM-DD.md`

### Folder Structure

```
/storage/workspace/          (Vault root)
├── memory/
│   ├── YYYY-MM-DD.md       (Daily session notes)
│   ├── agents/              (Agent outputs)
│   └── trading/              (Trade logs)
├── agents/                  (Norse agent skill files)
├── projects/                (Project notes)
├── templates/               (Note templates)
└── .obsidian/               (Obsidian config)
```

### Starting Obsidian

```bash
/storage/workspace/start-obsidian.sh
```

Or manually:
```bash
~/Applications/Obsidian.AppImage --no-sandbox
```

Then open vault: `/storage/workspace`

### REST API Examples

```bash
# Check server status
curl -k https://127.0.0.1:27124/

# List all notes
curl -k -H "Authorization: Bearer openclaw-spectre-2026" \
  https://127.0.0.1:27124/vault/

# Read a note
curl -k -H "Authorization: Bearer openclaw-spectre-2026" \
  https://127.0.0.1:27124/vault/memory/2026-03-23.md

# Create/append to today's daily note
curl -k -X PATCH \
  -H "Authorization: Bearer openclaw-spectre-2026" \
  -H "Operation: append" \
  -H "Target-Type: heading" \
  -H "Target: Session Notes" \
  -H "Content-Type: text/plain" \
  --data "- Item added via REST API" \
  https://127.0.0.1:27124/vault/memory/2026-03-23.md

# Search notes
curl -k -X POST \
  -H "Authorization: Bearer openclaw-spectre-2026" \
  -H "Content-Type: application/vnd.olrapi.dataview.dql+txt" \
  --data "TABLE file.name, file.ctime FROM \"memory\" WHERE file.ctime >= date(today)" \
  https://127.0.0.1:27124/search/
```

### Agent Integration

OpenClaw agents can use the REST API to:
- Log trades to `memory/trading/YYYY-MM-DD.md`
- Update daily session notes
- Create strategy documents for Tyr
- Report infrastructure status via Mimir

---

**Setup Date:** 2026-03-23
**Obsidian Version:** 1.12.7