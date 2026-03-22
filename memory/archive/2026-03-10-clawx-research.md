# ClawX Research — Morning Briefing

## What is ClawX?

**ClawX** is a desktop GUI for OpenClaw — transforms CLI-based AI orchestration into a native desktop experience.

- **Repo:** https://github.com/ValueCell-ai/ClawX
- **Website:** https://clawx.com.cn
- **License:** MIT
- **Status:** Active development (v0.1.24-alpha.9 released today Mar 10)
- **Languages:** English, 中文, 日本語

## Key Features

| Feature | Description |
|---------|-------------|
| **One-click install** | No terminal, no YAML, guided setup wizard |
| **Chat interface** | Multi-canvas, markdown rendering, message history |
| **Multi-channel** | Configure/monitor multiple AI channels independently |
| **Cron scheduler** | Visual task scheduling, define triggers/intervals |
| **Skill marketplace** | Browse, install, manage skills from GUI |
| **Auto gateway mgmt** | Lifecycle handled automatically |
| **Proxy support** | Built-in proxy for China/network-restricted users |
| **Native keychain** | Secure credential storage |

## Why It Matters for Yeatz

1. **Current setup:** You use the web Control UI (Tailscale) or Telegram
2. **ClawX alternative:** Native desktop app with more features:
   - Built-in cron scheduler (no manual crontab editing)
   - Skill marketplace GUI (browse ClawHub visually)
   - Multi-channel dashboard
   - System tray integration

3. **Trade-offs:**
   - Pro: Better UX, visual config, skill browsing
   - Con: Another Electron app (heavier than web UI)
   - Con: Still alpha (pre-release quality)

## Latest Release Info

**Version:** v0.1.24-alpha.9 (released Mar 10, 2026 03:42 UTC)
**Download count:** ~350+ total (growing fast)
**Release cadence:** Multiple releases per day (very active)

### Downloads for Linux x64

```
# AppImage (recommended)
https://github.com/ValueCell-ai/ClawX/releases/download/v0.1.24-alpha.9/ClawX-0.1.24-alpha.9-linux-x86_64.AppImage

# Debian/Ubuntu
https://github.com/ValueCell-ai/ClawX/releases/download/v0.1.24-alpha.9/ClawX-0.1.24-alpha.9-linux-amd64.deb

# RPM
https://github.com/ValueCell-ai/ClawX/releases/download/v0.1.24-alpha.9/ClawX-0.1.24-alpha.9-linux-x86_64.rpm
```

### Install on Ubuntu

```bash
# AppImage method
wget https://github.com/ValueCell-ai/ClawX/releases/download/v0.1.24-alpha.9/ClawX-0.1.24-alpha.9-linux-x86_64.AppImage
chmod +x ClawX-*.AppImage
./ClawX-0.1.24-alpha.9-linux-x86_64.AppImage

# Or .deb method
wget https://github.com/ValueCell-ai/ClawX/releases/download/v0.1.24-alpha.9/ClawX-0.1.24-alpha.9-linux-amd64.deb
sudo apt install ./ClawX-0.1.24-alpha.9-linux-amd64.deb
```

### Dependencies (Ubuntu 24.04)

```bash
# For AppImage
sudo apt install libfuse2t64

# For .deb
sudo apt install libgtk-3-0t64 libnotify4t64 libxss1t64
```

## Architecture

ClawX embeds OpenClaw directly — **no separate installation needed**:
- **Single-process mode:** Gateway runs inside app
- **IPC bridge:** Renderer ↔ Main process ↔ OpenClaw
- **Strict upstream sync:** Always matches official OpenClaw releases

## Developer Mode

Settings → Advanced → Developer Mode exposes:
- Raw config editing
- HTTP/HTTPS/SOCKS proxy overrides
- Advanced gateway settings

## Community

- **Discord:** https://discord.com/invite/84Kex3GGAh
- **Issues:** https://github.com/ValueCell-ai/ClawX/issues

## Recommendation

**Try it.** Download the AppImage, run it alongside your current setup. It won't interfere with your existing OpenClaw installation (uses its own embedded runtime).

If useful, could replace the Tailscale web UI for daily desktop work. Keep Telegram channel for mobile away-from-desk usage.

---

*Research completed: 2026-03-10 07:26 UTC*