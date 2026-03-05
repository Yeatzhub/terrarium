# Research Queue

Ideas to investigate when time permits. Add items freely, review when ready.

---

## Queue

### 2026-03-02: ZeroClaw - Rust OpenClaw Alternative
**Added**: 2026-03-02
**Priority**: Medium
**Status**: Queued

**What**: Lightweight AI assistant framework in Rust, alternative to OpenClaw.

**Key specs**:
- 3.4 MB binary, ~5 MB RAM, <10ms startup
- 22+ AI providers, 7 channels
- MIT licensed, 532 tests passing
- OpenClaw-compatible (SOUL.md, skills, memory format)

**Why interesting**:
- Could run on edge devices (Pi, etc.)
- 99% less memory than OpenClaw
- Security-first design (allowlists, autonomy levels)
- Rust trait system for extensibility

**Questions to explore**:
- How mature is the Telegram channel?
- Can it run existing OpenClaw skills?
- Migration path from OpenClaw?
- Performance on P40 server?
- Active development velocity?

**Links**:
- https://github.com/zeroclaw-labs/zeroclaw
- https://zeroclaw.org/
- https://zeroclaw.net/

---

## Template for New Items

```
### YYYY-MM-DD: [Title]
**Added**: YYYY-MM-DD
**Priority**: Low/Medium/High
**Status**: Queued / Researching / Done

**What**: Brief description

**Why interesting**: Why we care

**Questions to explore**:
- Question 1?
- Question 2?

**Links**:
- URL 1
- URL 2
```

---

### 2026-03-02: OpenClaw on Android - Deep Dive
**Added**: 2026-03-02
**Priority**: High
**Status**: Done

**What**: Running OpenClaw on Android phones via Termux or postmarketOS

#### Option 1: Termux (Recommended)
**No root required** - Runs OpenClaw directly in Termux with compatibility patches

**Key Project**: `github.com/AidanPark/openclaw-android`
- One-command installer: `curl -fsSL https://raw.githubusercontent.com/AidanPark/openclaw-android/main/bootstrap.sh | bash && source ~`
- No proot-distro needed (saves 700MB-1GB)
- Patches Android's bionic libc issues automatically
- ~50MB overhead vs 1-2GB for proot approach

**How it works**:
1. Patches `os.networkInterfaces()` crash (Android Error 13)
2. Creates compatibility shims for native modules
3. Sets up `NODE_OPTIONS` to preload patches
4. Bypasses systemd requirements
5. Handles Termux path differences

**Requirements**:
- Android 7.0+ (Android 10+ recommended)
- ~500MB free storage
- Termux from F-Droid (NOT Play Store - outdated)
- Disable battery optimization for Termux
- Stay Awake mode for 24/7 operation
- Charge limit to 80% for battery health

**Key issues**:
- Android 12+ "Phantom Process Killer" kills background processes
- Fix: Disable via ADB from within Termux
- Must run `openclaw gateway` in foreground or tmux

**Alternative Termux method** (older):
- Uses proot-distro + Ubuntu
- More overhead but better compatibility
- Guide: `sagartamang.com/blog/openclaw-on-android-termux`

#### Option 2: Android Node App (Official)
**Companion app** - Not standalone, requires separate Gateway

**What it is**:
- Official OpenClaw Android app from docs
- Pairs to a Gateway running on another machine (your server)
- Exposes device capabilities: camera, location, SMS, notifications
- Uses mDNS/NSD discovery on same LAN or manual connection

**Setup**:
1. Run Gateway on master machine (your server)
2. Android app discovers Gateway via mDNS or manual host:port
3. Approve pairing via CLI: `openclaw nodes approve <requestId>`
4. Node exposes `camera.*`, `screen.*`, `location.*`, `sms.*`, `canvas.*`

**Use case**: Give your server access to phone's sensors remotely

#### Option 3: postmarketOS on OnePlus
**Full Linux** - Replace Android with minimal Linux

**Verified working**: OnePlus 6 + postmarketOS + OpenClaw
- Blog: `abhisaha.com/blog/openclaw-deploys-openclaw-on-phone`
- SXMO desktop (< 200MB)
- SSH + Tailscale for remote access
- Agent deployed OpenClaw via SSH

**postmarketOS supported devices**:
- OnePlus 6 (enchilada)
- OnePlus 6T (fajita)
- PinePhone, Librem 5, etc.
- Many other Android devices

**Setup**:
1. Install postmarketOS (replaces Android)
2. Configure SSH and Tailscale
3. Install Node.js and OpenClaw
4. Fix nftables firewall (`chain input { policy drop; }` blocks port 18789)
5. Run Gateway on port 18789

**Pros**:
- Full Linux environment
- No Android restrictions
- Better for 24/7 server use
- Can run other services (n8n, etc.)

**Cons**:
- Wipes Android (dual boot possible but complex)
- Limited device support
- May have hardware issues (GPS, modem, etc.)

#### Termux vs postmarketOS Comparison

| Aspect | Termux | postmarketOS |
|--------|--------|--------------|
| Setup | 1 command | Flash custom OS |
| Android apps | Still work | Gone |
| Storage | ~500MB | ~2GB+ |
| Performance | Native speed | Native speed |
| Background | Phantom killer issues | No issues |
| Firewall | Android managed | iptables/nftables |
| Hardware | All sensors | May have gaps |
| 24/7 uptime | Requires Stay Awake + tmux | Native daemon |

#### Key Commands (Termux)

```bash
# Install (one command)
curl -fsSL https://raw.githubusercontent.com/AidanPark/openclaw-android/main/bootstrap.sh | bash && source ~

# Setup
openclaw onboard

# Run gateway (in separate tab/tmux)
openclaw gateway

# Update
oa --update

# Uninstall
oa --uninstall

# Disable phantom process killer (Android 12+)
adb shell "/settings put global settings_enable_monitor_phantom_procs 0"
```

#### Additional AI Tools Working on Termux

After installing OpenClaw patches:
- Claude Code: `npm i -g @anthropic-ai/claude-code`
- Gemini CLI: `npm i -g @google/gemini-cli`
- Codex CLI: `npm i -g @openai/codex`

#### Security Note
- Run on factory-reset phone with no personal accounts
- Isolate from personal data
- Use dedicated accounts for any services
- OpenClaw has security concerns - don't expose to public internet

---

## Completed

(Move finished research here with summary)
