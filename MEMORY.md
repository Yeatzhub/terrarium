# MEMORY.md - Long-Term Memory

**Only load in main sessions.** Skip in shared contexts (Discord, groups).

## Trading Operation

- **Mission**: Algorithmic trading profits
- **Phase 1**: XRP bot on Pionex (Market Cipher v2)
- **Target**: $50/day (stretch)

**Assets:**
- `/storage/workspace/projects/trading/pionex/` - XRP bot
- `/storage/workspace/thehub/` - Next.js dashboard
- `/storage/workspace/projects/android/` - Spectre app (planning)

**Prefs:** Paper trading default, Pionex only, COIN-M futures, CoinGecko prices, autonomous execution

## System (Mar 2026)

| Component | Details |
|-----------|---------|
| GPU | Tesla P40 24GB |
| Models | qwen3-coder:30b, qwen3.5:35b, qwen3.5:27b |
| Storage | NVMe 256GB (boot), RAID0 3.6TB (/storage), 2×8TB WD Red (unused) |
| Network | Tailscale IP: 100.112.56.61 |
| Services | OpenClaw (18789), TheHub (3000), ComfyUI (8188), SearXNG (8082) |

## Recent Events

- **Mar 5**: Added 16GB swap on /storage/swapfile2 (fixes gateway OOM)
- **Mar 5**: Installed qwen3-coder:30b, removed qwen2.5-coder:32b
- **Mar 5**: Added Claude Code MCP for Ollama tools
- **Mar 2**: Tavily plugin installed, Market Cipher v2 strategy
- **Feb 28**: System hardening complete (UFW, fail2ban, SSH keys)

## Agent Learning Archive

See `memory/2026-02-agent-learning.md` — 47+ docs covering trading, Python, Android, UI patterns.