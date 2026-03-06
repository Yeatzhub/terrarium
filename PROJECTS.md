# PROJECTS.md - Active Projects Tracker

Last updated: 2026-03-06

## Active Projects

| Project | Status | Priority | Description |
|---------|--------|----------|-------------|
| Trading Bot | 🔴 Stopped | HIGH | XRP adaptive strategy on Pionex (bot crashed) |
| TheHub Dashboard | 🟡 In Progress | MEDIUM | Next.js monitoring dashboard |
| Android App (Spectre) | 🔴 Planning | LOW | React Native companion app |

---

## 1. Trading Bot (Pionex XRP)

**Status:** 🔴 Stopped (needs restart)  
**Priority:** HIGH  
**Location:** /storage/workspace/projects/trading/pionex/xrp/

### Current State
- **Balance:** $98.44 USD (paper trading)
- **Initial:** $100.00
- **Trades:** 7 total (4 wins, 3 losses)
- **Strategy:** Adaptive (regime-switching: trend + mean reversion)
- **Paper Trading:** ✅ Enabled

### Key Components
- bot_mc.py - Market Cipher v2 strategy (current)
- bot.py - Legacy adaptive strategy
- state.json - Persistent state
- shared/adaptive_strategy.py - Strategy logic

### Circuit Breaker
- **Limit:** 3 consecutive losses (triggered)
- **Reset:** Manual or auto on restart

### Recent Trades
| Date | Side | PnL | Exit Reason |
|------|------|-----|-------------|
| Mar 5 | BUY | -$1.51 | stop loss |
| Mar 5 | BUY | +$0.01 | stop loss |
| Mar 5 | BUY | +$0.70 | stop loss |
| Mar 5 | SELL | -$1.56 | stop loss |
| Mar 5 | SELL | -$0.47 | conviction_lost |

### Issues
- Bot stopped after 3rd consecutive loss (Mar 5, 13:26 UTC)
- venv was bloated (8.2GB) — rebuilt to 161MB

### Next Steps
- [ ] Restart bot
- [ ] Monitor win rate
- [ ] Consider live trading when consistent

---

## 2. TheHub Dashboard

**Status:** 🟡 In Progress  
**Priority:** MEDIUM  
**Location:** /storage/workspace/thehub/

### Current State
- Prod server: port 3000 (running)
- Tailscale: https://yeatzai.tailbf40f7.ts.net

### Features
- ✅ OpenClaw status monitoring
- ✅ Trading bot dashboard
- ✅ Services health checks

### Next Steps
- [ ] Add real-time bot logs
- [ ] Mobile responsive improvements

---

## 3. Android App (Spectre)

**Status:** 🔴 Planning  
**Priority:** LOW  
**Location:** /storage/workspace/projects/android/

### Architecture
- React Native + Expo
- Mirror TheHub features

### Next Steps
- [ ] Scaffold project with Expo
- [ ] Implement auth flow
- [ ] Add bot monitoring screens

---

## Completed Projects

| Project | Completed | Notes |
|---------|-----------|-------|
| System Hardening | Feb 28, 2026 | UFW, SSH keys, Fail2ban |
| P40 GPU Install | Feb 17, 2026 | Cooling confirmed working |
| Venv Cleanup | Mar 6, 2026 | Reduced from 8.2GB to 161MB |
| ComfyUI Setup | Feb 25, 2026 | SDXL running on port 8188 |

---

## Priority Definitions

- **HIGH:** Daily monitoring, revenue impacting
- **MEDIUM:** Weekly progress, operational efficiency
- **LOW:** As time permits, future planning

## Status Definitions

- 🟢 **Active:** Running, monitored, daily work
- 🟡 **In Progress:** Actively developing
- 🔴 **Stopped/Halted:** Not running, needs attention
- 🔴 **Planning:** Not started, architecture phase
- ✅ **Completed:** Finished and stable
