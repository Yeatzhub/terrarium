# Yggdrasil — World Tree

Shared knowledge index for the Norse pantheon.

## Purpose

Yggdrasil connects all agents. Decisions that span multiple agents are documented here.

## Structure

```
/storage/workspace/yggdrasil/
├── INDEX.md              # This file
└── decisions/
    ├── 2026-03-11-agent-architecture.md
    └── ...
```

## Cross-Agent Protocols

### Strategy → Implementation Flow

```
1. Huginn discovers opportunity
2. Tyr develops strategy → writes to /strategies/
3. Tyr hands off spec to Sindri
4. Sindri implements → tests → hands off to Mimir
5. Mimir deploys to staging
6. Njord reviews allocation
7. User approves live deployment
8. Thor executes with approved allocation
```

### Circuit Breaker Protocol

```
1. Njord detects limit breach OR Thor hits limit
2. Alert sent to Heimdall
3. Heimdall alerts user
4. User approves resume OR Tyr modifies strategy
5. If resume: Thor continues
6. If modify: restart flow from Tyr
```

### Daily Briefing Flow

```
Time: 8:00 AM (user's timezone)

Each agent reports to Heimdall:
- Huginn: Markets scanned, opportunities
- Tyr: Strategies in progress, backtest results
- Sindri: Code written, bugs fixed
- Njord: Balance snapshot, P&L
- Thor: Trades executed, positions held
- Mimir: System health, uptime

Heimdall consolidates → displays in Hub → optional Telegram
```

## Agent Communication Matrix

| From | To | Allowed |
|------|-----|---------|
| Heimdall | All | ✓ |
| Huginn | Tyr, Njord, Heimdall | ✓ |
| Tyr | Huginn, Sindri, Njord, Heimdall | ✓ |
| Sindri | Tyr, Mimir, Heimdall | ✓ |
| Njord | Thor, Huginn, Heimdall | ✓ |
| Thor | Njord, Mimir, Heimdall | ✓ |
| Mimir | Sindri, Thor, Heimdall | ✓ |

All other combinations blocked.

## Decision Archive

| Date | Decision | Agents | File |
|------|----------|--------|------|
| 2026-03-11 | Norse architecture established | All | `decisions/2026-03-11-agent-architecture.md` |

## Learning Protocol

Each agent maintains their own `learning/` folder:
- One concept per file
- Date-prefixed: `YYYY-MM-DD-topic.md`
- Cross-references: `[see Tyr:kill-zone-strategy]`

Yggdrasil indexes cross-agent knowledge, not individual agent learning.