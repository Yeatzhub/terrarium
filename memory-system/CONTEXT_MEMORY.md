# CONTEXT MEMORY - Project/Domain Rules

> Rules specific to projects, domains, or work modes.
> Active when working in that context.

---

## Projects

### trading
- **Path**: `/storage/workspace/projects/trading/`
- **Priority**: HIGHEST - funds all projects
- **Goal**: Steady profits from XRP bot
- **Current State**:
  - Balance: 185.26 XRP (started 200, down 14.74)
  - Trades: 55
  - Win rate: ~30%
  - Position: SHORT
- **Active Improvements**:
  - Stricter entry filters (ADX ≥ 30, Z ≥ 4.0)
  - Trailing stops (0.5% profit threshold)
  - Realistic fees (0.25% round-trip)
- **Rules**:
  - Paper trading default (live requires explicit "YES")
  - Pionex only for CEX trading
  - Single XRP bot until performance validated
- **Added**: 2026-02-26

### thehub
- **Path**: `/storage/workspace/thehub/`
- **Rules**:
  - Only XRP bot page (BTC/SOL/ETH deleted)
- **Added**: 2026-02-26

---

## Domains

### crypto-trading
- **Rules**:
  - Track profit goal: 0-100 XRP gain (from 200 XRP start)
  - Fee simulation: 0.25% round-trip (Pionex rates)
- **Added**: 2026-02-26

---

## Index
- Projects tracked: 2
- Domains tracked: 1
- Last updated: 2026-02-26