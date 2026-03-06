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

## Completed

### 2026-03-02: OpenClaw on Android - Deep Dive
**Completed**: 2026-03-02

**Summary**: Researched running OpenClaw on Android via Termux, postmarketOS, or Android Node App.

**Key findings**:
- Termux method works with compatibility patches
- postmarketOS offers full Linux but wipes Android
- Android Node App requires separate Gateway

**Status**: Ready to implement when needed
