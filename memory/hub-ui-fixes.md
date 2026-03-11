# Hub UI Polish & CTA Report

## Pages Missing Action Buttons

| Page | Missing CTAs | Priority |
|------|--------------|----------|
| **Home (`/`)** | Quick-action cards for Trading, Agents, LLM, Hardware | HIGH |
| **Trading** | Start/Stop Bot, View Logs, Refresh Data | HIGH |
| **Hardware** | Refresh Stats, Export CSV | MEDIUM |
| **LLM Status** | Model Switch, Clear Cache, Navigation Cards | MEDIUM |
| **Agents** | Start/Stop per agent, View Learning Docs | MEDIUM |
| **Notes** | Create Note, Search | LOW |
| **Tasks** | Add Task, Mark Complete | LOW |

---

## Recommended CTAs per Page

### Home (`/`)
```
Quick Actions:
[📈 Trading Dashboard] → /trading
[🤖 Agents Status] → /agents
[🧠 LLM Status] → /llm/status
[🖥️ Hardware Stats] → /hardware
```

### Trading (`/trading`)
```
[▶️ Start Bot] [⏹️ Stop Bot]
[📊 View Logs] → Open logs modal
[🔄 Refresh] → Reload data
[⚙️ Settings] → /trading/settings (NEEDS CREATE)
```

### Hardware (`/hardware`)
```
[🔄 Refresh Stats] [📥 Export CSV]
```

### LLM Status (`/llm/status`)
```
[🔄 Refresh] [🗑️ Clear Cache] [📋 Copy Context]
[Models →] /llm/models
[Tokens →] /llm/tokens
```

### Agents (`/agents`)
```
Per agent: [▶️ Start] [⏹️ Stop] [📚 Learning Docs]
```

### Notes (`/notes`)
```
[➕ New Note] [🔍 Search]
```

### Tasks (`/tasks`)
```
[➕ Add Task] [✓ Complete Selected] [🗑️ Delete]
```

---

## Navigation Improvements

1. **Add missing sidebar items:**
   - Action Items
   - Chat
   - Tasks
   - Trading Test

2. **Add LLM submenu:**
   - Status (default)
   - Models
   - Token Usage

3. **Standardize back buttons:**
   - Every sub-page should have back to parent
   - Every page should have home link in header