# Hub Data & API Analysis Report

## Critical Issues Found

### 1. `/api/pionex-xrp` - BROKEN
- **Problem:** API reads `state.json` but bot writes to `state_mc.json`
- **Impact:** Dashboard shows no data for XRP bot
- **Fix:** Update path to `/storage/workspace/projects/trading/pionex/xrp/state_mc.json`

### 2. Field Name Mismatches
| Dashboard Expects | Bot State Provides | Fix |
|------------------|-------------------|-----|
| `marketState.price` | Not stored | Parse from logs |
| `position.entry_price` | `position.entry` | Rename field |
| `position.timestamp` | `position.open_time` | Rename field |
| Market indicators | Only in logs | Add to state file |

### 3. Path Issues for Sandbox
- Many APIs use `/home/yeatz/.openclaw/workspace/`
- Should use `/workspace/` for sandbox compatibility

## API Endpoints Status

| Endpoint | Status | Action Needed |
|----------|--------|---------------|
| `/api/pionex-xrp` | ❌ BROKEN | Fix state file path |
| `/api/hardware` | ⚠️ Verify | Check nvidia-smi works |
| `/api/llm-status` | ⚠️ Verify | Check Ollama on :11434 |
| `/api/agents` | ⚠️ Path fix | Remove hardcoded paths |
| `/api/tasks` | ⚠️ Path fix | Remove hardcoded paths |
| `/api/openclaw-status` | ⚠️ Verify | Check gateway :18789 |

## Implementation Priority

1. **HIGH:** Fix state file path (`state.json` → `state_mc.json`)
2. **HIGH:** Add market indicators to state or log parser
3. **MEDIUM:** Verify hardware/LLM APIs work
4. **MEDIUM:** Fix sandbox path issues
5. **LOW:** Standardize field names across frontend/backend

## Current Bot State (from state_mc.json)

```json
{
  "balance": 199.76,
  "position": {
    "side": "SHORT",
    "size": 289.36,
    "entry": 1.38237
  },
  "stats": {
    "total_trades": 0,
    "win_rate": 0,
    "total_pnl": 0
  }
}
```

## Live Market Data (from logs)

- Price: $1.3840
- MFI: 35.2 (bearish)
- WT1: -10.75, WT2: 2.98
- VWAP: -1.20
- Signal: SHORT (85% confidence)