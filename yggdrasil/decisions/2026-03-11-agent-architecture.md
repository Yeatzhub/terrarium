# Decision: Norse Pantheon Architecture

- **Date:** 2026-03-11
- **Type:** Architecture
- **Participants:** User, OpenClaw (main session)

## Context

Needed a structured agent hierarchy for autonomous trading operations targeting $200/day.

## Decision

Adopted Norse mythology naming convention for all agents:

| Norse Name | Role | Purpose |
|------------|------|---------|
| Heimdall | Coordinator | Delegates, monitors, escalates |
| Huginn | Scout | Market research |
| Tyr | Strategist | Strategy development, backtesting |
| Sindri | Smith | Bot implementation |
| Njord | Treasurer | Financial tracking (read-only) |
| Thor | Executor | Live trading execution |
| Mimir | Operator | Infrastructure |

## Key Constraints

1. **Thor** requires user approval to START any strategy
2. **Njord** is read-only until process proven
3. **Heimdall** can spawn subagents
4. Paper trading duration defined per strategy (default 7 days)
5. Circuit breakers defined per strategy by Tyr

## Communication Walls

- Treasury (Njord) isolated from code agents (Sindri)
- Execution (Thor) cannot change strategy (Tyr)
- Research (Huginn) cannot deploy or trade
- Code (Sindri) cannot access funds

## Implementation

- SKILL.md files created for all 7 agents
- Communication matrix enforced
- Learning directory structure established
- Yggdrasil shared knowledge index created

## Outcome

Foundation architecture complete. Ready for phased deployment:
- Phase 1: Heimdall + Huginn + Tyr + Mimir
- Phase 2: Sindri + Njord
- Phase 3: Thor (with paper trading)