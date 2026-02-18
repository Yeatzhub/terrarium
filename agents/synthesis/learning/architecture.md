# Trading System Architecture

A simple pipeline connecting market data to execution. **Price feeds** stream real-time data into a **signal generator**, which identifies entry/exit triggers. Valid signals pass to the **risk manager** for verification, then onward to **execution**.

## Data Flow

```
┌─────────────┐    ┌────────────────┐    ┌──────────────┐    ┌───────────┐
│ Price Feeds │───▶│ Signal Gener.  │───▶│  Risk Mgr    │───▶│ Execution │
└─────────────┘    └────────────────┘    └──────────────┘    └───────────┘
       │                     │                  │                  │
       │            ┌─────────┘                  │                  │
       │            ▼                             │                  │
       │       ┌──────────┐                       │                  │
       └──────▶│ Historic │                       │                  │
               │  Data    │                       │                  │
               └──────────┘                       │                  │
                                                  ▼                  │
                                            ┌──────────┐             │
                                            │  Block   │─────────────┘
                                            └──────────┘
```

## Risk Rules

1. **Position Sizing** — No single position exceeds 2% of total capital.
2. **Max Drawdown** — Trading halts if account drops 10% from peak.
3. **Daily Loss Limit** — All activity pauses after cumulative daily loss hits 5%.

These constraints prevent catastrophic losses and keep the system operational through adverse conditions.
