# Thor - API Credentials

## Pionex API

**Configuration file:** `/storage/workspace/projects/trading/pionex/api_config.py`

```
API_KEY: 9pHT15WJ...RJ3f
API_SECRET: pcehCTdp...sc9b
ACCOUNT_TYPE: spot
```

**⚠️ Current Status:** READ-ONLY
- ✅ Read account balance
- ✅ Read order history
- ❌ Place orders (needs write permission)
- ❌ Cancel orders (needs write permission)

**For Live Trading:**
1. Create new API key with "Trade" permission in Pionex
2. Update `api_config.py` with new credentials

## Telegram Notifications

Thor sends trade alerts via Telegram through Heimdall relay.

**Channel:** Configured in OpenClaw (`openclaw.json`)

---

*Last updated: 2026-03-24*