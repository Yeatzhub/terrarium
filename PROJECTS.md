# PROJECTS.md - Active Projects Tracker

Last updated: 2026-03-01

## Active Projects

| Project | Status | Priority | Description |
|---------|--------|----------|-------------|
| Trading Bot | 🟢 Active | HIGH | XRP adaptive strategy on Pionex |
| TheHub Dashboard | 🟡 In Progress | MEDIUM | Next.js monitoring dashboard |
| postmarketOS Build | 🔴 On Hold | LOW | OnePlus 6T Linux phone |
| Android App (Spectre) | 🔴 Planning | LOW | React Native companion app |

---

## 1. Trading Bot (Pionex XRP)

**Status:** 🟢 Active - Paper Trading  
**Priority:** HIGH  
**Location:** `/storage/workspace/projects/trading/pionex/xrp/`

### Current State
- **Balance:** 204.22 XRP
- **Trades:** 34 total
- **Strategy:** Adaptive (regime-switching: trend + mean reversion)
- **Paper Trading:** ✅ Enabled

### Key Components
- `bot.py` - Main trading loop
- `state.json` - Persistent state (balance, trades, circuit breaker)
- `shared/adaptive_strategy.py` - Strategy logic

### Circuit Breaker
- **Limit:** 3 consecutive losses
- **Reset:** Manual (needs code fix for auto-reset)
- **Volatility Filter:** ADX must be ≥ 15

### Recent Issues
- Circuit breaker stuck issue (needs auto-reset timer)
- Pionex API connectivity (resolved by using direct API)

### Next Steps
- [ ] Add auto-reset for circuit breaker (60 min cooldown)
- [ ] Monitor win rate improvement
- [ ] Consider live trading when consistent profits

---

## 2. TheHub Dashboard

**Status:** 🟡 In Progress  
**Priority:** MEDIUM  
**Location:** `/home/yeatz/.openclaw/workspace/thehub/`

### Current State
- Dev server: port 3001 (running)
- Prod server: port 3000 (needs start)
- Tailscale HTTPS: https://yeatzai.tailbf40f7.ts.net

### Features
- ✅ OpenClaw status monitoring
- ✅ Trading bot dashboard
- ✅ Services health checks
- ✅ AI team overview
- 🚧 Device flasher (WebUSB issues on Windows)
- 📝 Projects overview (needs implementation)

### Next Steps
- [ ] Add projects overview page
- [ ] Fix systemd services for auto-start
- [ ] Add real-time bot logs
- [ ] Mobile responsive improvements

---

## 3. postmarketOS Build (OnePlus 6T)

**Status:** 🔴 On Hold  
**Priority:** LOW  
**Location:** `/home/yeatz/.openclaw/workspace/projects/postmarketos-build/`

### Current State
- Images downloaded: boot.img (26MB), rootfs.img (2.1GB)
- WebUSB flasher blocked on Windows (driver issues)
- Images ready at: `thehub/public/builds/`

### Blockers
- Windows WebUSB permissions
- Need fastboot CLI method instead

### Next Steps
- [ ] Use fastboot CLI on Windows
- [ ] Flash boot.img to boot partition
- [ ] Flash rootfs.img to userdata
- [ ] Test boot into postmarketOS

---

## 4. Android App (Spectre)

**Status:** 🔴 Planning  
**Priority:** LOW  
**Location:** `/home/yeatz/.openclaw/workspace/projects/android/spectre/`

### Architecture
- React Native + Expo
- Mirror TheHub features (trading, bot status)
- Push notifications for alerts

### Next Steps
- [ ] Scaffold project with Expo
- [ ] Implement auth flow
- [ ] Add bot monitoring screens
- [ ] Integrate with TheHub API

---

## Completed Projects

| Project | Completed | Notes |
|---------|-----------|-------|
| System Hardening | Feb 28, 2026 | UFW, SSH keys, Fail2ban |
| P40 GPU Install | Feb 17, 2026 | Cooling confirmed working |
| ComfyUI Setup | Feb 25, 2026 | SDXL running on port 8188 |

---

## Priority Definitions

- **HIGH:** Daily monitoring, revenue impacting
- **MEDIUM:** Weekly progress, operational efficiency
- **LOW:** As time permits, future planning

## Status Definitions

- 🟢 **Active:** Running, monitored, daily work
- 🟡 **In Progress:** Actively developing
- 🔴 **On Hold:** Blocked or deprioritized
- 🔴 **Planning:** Not started, architecture phase
- ✅ **Completed:** Finished and stable