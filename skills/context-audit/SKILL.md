---
name: context-audit
description: Audit and reduce always-loaded context bloat. Use when asked to run context audit, weekly audit, or clean up workspace files (AGENTS.md, TOOLS.md, USER.md, MEMORY.md, HEARTBEAT.md, SOUL.md).
---

# Context Bloat Audit

Reduce token bloat in always-loaded workspace files.

## Files to Audit

- `/storage/workspace/AGENTS.md`
- `/storage/workspace/TOOLS.md`
- `/storage/workspace/USER.md`
- `/storage/workspace/MEMORY.md`
- `/storage/workspace/HEARTBEAT.md`
- `/storage/workspace/SOUL.md`

## Process

For each file:

1. **Move to skills**: If instructional/procedural and task-specific → extract to a skill
2. **Move to memory**: If historical/factual → move to `memory/YYYY-MM.md`
3. **Cut redundancy**: Same info in multiple files → one canonical location
4. **Compress**: Tables > paragraphs, bullets > prose
5. **Report**: Before/after token estimate + what moved where

## Token Rules

- **SOUL.md**: Identity, behavior — minimal changes
- **AGENTS.md**: Boot sequence, references — keep lean
- **USER.md**: User prefs — essential only
- **MEMORY.md**: Trading info, system specs — static facts
- **HEARTBEAT.md**: Schedule, checks — what runs when
- **TOOLS.md**: APIs, tools — env-specific notes

## Output Format

```
## [FILE].md
Before: X tokens
After: Y tokens
Saved: Z tokens

Changes:
- [What was moved where]
- [What was compressed]
```

## Goal

Minimize always-loaded context so runtime rules have maximum weight.