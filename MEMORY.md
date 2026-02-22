# MEMORY.md - Long-Term Memory

**ONLY load in main sessions** (direct chats with your human). Do not load in shared contexts (Discord, group chats) for security.

## How to Use

This is your curated long-term memory — distilled essence, not raw logs.

**Write:**
- Significant events and decisions
- Things to remember about your human
- Lessons learned, opinions formed
- Preferences and patterns

**Maintain:**
- Review daily files periodically
- Update with distilled learnings
- Remove outdated info

Daily files (memory/YYYY-MM-DD.md) are raw notes; this is your curated wisdom.

## Memory

### Trading Operation (Feb 2026)
- **Mission**: Make money via algorithmic trading
- **Phase 1**: eBay sales for quick capital
- **Phase 2**: BTC trading bot (Kraken exchange, EMA+RSI strategy, paper trading)
- **Phase 3**: Android app (future)
- **Hardware**: P40 GPU for local inference

**Key Assets:**
- `btc-trading-bot/`: RSI strategy bot, webhook server, Kraken integration
- `polymarket_scanner.py`: Arbitrage detection for prediction markets
- `polymarket_paper_trader/`: **NEW** Automated paper trading bot for crypto Up/Down markets
  - Mean-reversion strategy (buy <0.40, sell >0.60)
  - $100 paper balance, $10 max per trade
  - Circuit breaker after 3 consecutive losses
  - Tracks P/L, win rate in portfolio.json
- `solana-jupiter-bot/`: Jupiter DEX trading bot (triangular arbitrage, momentum strategies)
- `thehub/`: Next.js dashboard for tracking (CEX + DEX + Prediction Markets)

**Preferences:**
- Paper trading default (live requires explicit "YES" confirmation)
- Delegate tasks to sub-agents without permission loops
- User manages overall direction, agents execute

**Technical Notes:**
- Kraken over Binance.US (geographic restrictions)
- TradingView webhooks on port 8080
- P40 GPU tracking: 9405508106245831259625
- Tailscale IP: 100.125.198.70

### P40 GPU Installation Complete (Feb 17, 2026)
- **Status**: Installed and operational
- **Drivers**: NVIDIA 570.211.01 server drivers
- **Cooling**: Noctua external fan, confirmed capable (42°C max under 192W load)
- **BIOS**: Intel HD 530 primary display, Above 4G Decoding enabled
- **Performance**: Qwen 2.5 32B runs at 98% GPU utilization, 21GB VRAM, 192W power peak
- **Fan Verdict**: Cooling exceeds requirements for 250W TDP
- **Models Available**: phi4 (9GB), Qwen 2.5 32B (19GB), Llama 3.1 70B downloading


### Trading Infrastructure Library Complete (Feb 20, 2026)
- **Status**: 47 learning docs created by agent subsystems (ghost, oracle, pixel, synthesis)
- **Purpose**: Complete trading system toolkit (risk management, position sizing, metrics, automation)

**Key Components Built:**
- **Risk Tools**: Position sizing (7 methods), risk of ruin calculator, correlation analyzer, volatility regime detector
- **Execution**: Trailing stop calculator (5 methods), market scanner (8 types), alert system (10 types), trade validator
- **Analytics**: PnL tracker, drawdown analyzer, backtest engine, trade journal, performance reporter
- **Infrastructure**: Session manager (persistent state), state machine, async patterns, circuit breakers
- **Strategy Education**: Order blocks, FVGs, liquidity sweeps, VWAP, kill zones, ATR, multi-timeframe hierarchy

**Location**: `agents/{ghost,oracle,pixel,synthesis}/learning/2026-02-20-*.md`

### Agent Learning Batch — Feb 21, 2026
Five new guides created overnight covering multi-agent coordination, Python patterns, Android architecture, trading risk, and UI design:

| Agent | Topic | File |
|-------|-------|------|
| Synthesis | Multi-Agent Coordination Patterns | `2026-02-21-0420-multi-agent-coordination.md` |
| Ghost | Frozen Dataclass + Validation | `2026-02-21-0423-dataclass-validation-pattern.md` |
| Nexus | Real-Time Trading Architecture (Android) | `2026-02-21-0441-realtime-trading-arch.md` |
| Oracle | Volatility Clustering (Risk/Sizing) | `2026-02-21-0453-volatility-clustering.md` |
| Pixel | CSS Glassmorphism Pattern | `2026-02-21-0524-css-glassmorphism-card.md` |

### Agent Learning Batch — Feb 21, 2026 (Morning)
Three more guides covering testing patterns, logging infrastructure, and trading strategy:

| Agent | Topic | File |
|-------|-------|------|
| Synthesis | Integration Test Examples for Multi-Agent Systems | `2026-02-21-0620-integration-test-examples.md` |
| Ghost | Structured Logging with Context Propagation | `2026-02-21-0623-structured-logging.md` |
| Oracle | Multi-Timeframe Confluence (Timing/Structure) | `2026-02-21-0624-multi-timeframe-confluence.md` |

### Agent Learning Batch — Feb 21, 2026 (Mid-Day)
Five more guides covering position sizing, scroll animations, UI components, trading indicators, and workflow optimization:

| Agent | Topic | File |
|-------|-------|------|
| Ghost | Position Sizer v2 (CSV batch + safety caps) | `2026-02-21-0723-position-sizer-v2.md` |
| Ghost | Trade Journal P&L Analyzer CLI | `2026-02-21-0823-trade-journal-analyzer.md` |
| Pixel | CSS Scroll-Driven Animations | `2026-02-21-0724-css-scroll-driven-animations.md` |
| Nexus | Jetpack Compose Sparkline Component | `2026-02-21-0741-compose-sparkline-component.md` |
| Oracle | Stochastic RSI Indicator Use Case | `2026-02-21-0753-stochastic-rsi-use-case.md` |
| Synthesis | Workflow Optimization (TBD) | `2026-02-21-0820-workflow-optimization.md` |
| Ghost | Async Retry Pattern with Exponential Backoff | `2026-02-21-0923-async-retry-pattern.md` |

### Agent Learning Batch — Feb 21, 2026 (Afternoon/Evening)
Five more guides covering risk management, order blocks, UX patterns, Android testing, and quality standards:

| Agent | Topic | File |
|-------|-------|------|
| Synthesis | Quality Standards & Production Readiness | `2026-02-21-1022-quality-standards.md` |
| Ghost | Risk-of-Ruin Calculator CLI | `2026-02-21-1023-risk-of-ruin-calculator.md` |
| Pixel | UX Skeleton Screens Pattern | `2026-02-21-0925-ux-skeleton-screens.md` |
| Nexus | Android Architecture Testing Guide | `2026-02-21-1041-android-architecture-testing.md` |
| Oracle | Order Blocks (Market Structure) | `2026-02-21-0925-order-blocks.md` |

### Agent Learning Batch — Feb 21, 2026 (Evening)
Two more guides covering drawdown analysis and UI components:

| Agent | Topic | File |
|-------|-------|------|
| Ghost | Drawdown Analyzer CLI | `2026-02-21-1123-drawdown-analyzer.md` |
| Pixel | Component Button System | `2026-02-21-1127-component-button-system.md` |

### Agent Learning Batch — Feb 21, 2026 (Afternoon)
Three more guides covering live P&L tracking, Bollinger Band strategy, and integration testing:

| Agent | Topic | File |
|-------|-------|------|
| Ghost | Live P&L Tracker | `2026-02-21-1223-live-pnl-tracker.md` |
| Oracle | Bollinger Band Squeeze Strategy | `2026-02-21-1225-bollinger-band-squeeze.md` |
| Synthesis | Integration Test Examples (Additional) | `2026-02-21-1220-integration-test-examples.md` |

### Agent Learning Batch — Feb 21, 2026 (Afternoon/Evening)
Six more guides covering async patterns, CSS, Kotlin Flow, market structure, and pre-trade checklists:

| Agent | Topic | File |
|-------|-------|------|
| Ghost | Async Context Manager Pattern | `2026-02-21-1323-async-context-managers.md` |
| Ghost | Pre-Trade Checklist | `2026-02-21-1423-pre-trade-checklist.md` |
| Pixel | CSS Container Queries | `2026-02-21-1324-css-container-queries.md` |
| Nexus | Kotlin Coroutines & Flow Patterns | `2026-02-21-1341-kotlin-coroutines-flow-patterns.md` |
| Oracle | Liquidity Sweeps | `2026-02-21-1353-liquidity-sweeps.md` |
| Synthesis | Context Handoff Protocols | `2026-02-21-1420-context-handoff-protocols.md` |

### Agent Learning Batch — Feb 21, 2026 (Late Afternoon)
Three more guides covering regime detection, ATR use case, and form validation:

| Agent | Topic | File |
|-------|-------|------|
| Ghost | Regime Detector | `2026-02-21-1523-regime-detector.md` |
| Oracle | ATR Use Case | `2026-02-21-1526-atr-use-case.md` |
| Pixel | UX Form Validation Patterns | `2026-02-21-1528-ux-form-validation-patterns.md` |

### Agent Learning Batch — Feb 21, 2026 (Late Afternoon/Evening)
Six more guides covering decomposition, MC validation, Room DB, and market structure:

| Agent | Topic | File |
|-------|-------|------|
| Synthesis | Task Decomposition Patterns | `2026-02-21-1620-task-decomposition.md` |
| Ghost | Monte Carlo Backtest Validator | `2026-02-21-1623-mc-validator.md` |
| Nexus | Room Database Advanced Patterns | `2026-02-21-1641-room-database-patterns.md` |
| Oracle | BOS vs ChoCH Market Structure | `2026-02-21-1653-bos-choch-structure.md` |
| Pixel | CSS Grid Subgrid Pattern | `2026-02-21-1726-css-grid-subgrid.md` |

### Agent Learning Batch — Feb 21, 2026 (Evening)
Three more guides covering integration tests, SL/TP calculator, and VWAP:

| Agent | Topic | File |
|-------|-------|------|
| Synthesis | Integration Test Examples | `2026-02-21-1820-integration-test-examples.md` |
| Ghost | SL/TP Calculator CLI | `2026-02-21-1823-sl-tp-calculator.md` |
| Oracle | VWAP Use Case | `2026-02-21-1825-vwap-use-case.md` |

### Agent Learning Batch — Feb 21, 2026 (Evening)
Three more guides covering error handling, CSS text wrapping, and expectancy:

| Agent | Topic | File |
|-------|-------|------|
| Ghost | Error Classification & Handling Pattern | `2026-02-21-1923-error-handling-pattern.md` |
| Pixel | CSS Text Wrap Balance | `2026-02-21-1924-css-text-wrap-balance.md` |
| Oracle | Trading Expectancy | `2026-02-21-1953-expectancy-edge.md` |

### Agent Learning Batch — Feb 21, 2026 (Late Evening)
Two more guides covering dependency management:

| Agent | Topic | File |
|-------|-------|------|
| Synthesis | Dependency Management | `2026-02-21-2020-dependency-management.md` |
| Ghost | Daily Summary | `2026-02-21-summary.md` |

### Agent Learning Batch — Feb 21, 2026 (Night)
Three more guides covering config management, FVGs, and UI components:

| Agent | Topic | File |
|-------|-------|------|
| Ghost | Configuration Management Pattern | `2026-02-21-2023-config-management.md` |
| Oracle | Fair Value Gaps (FVG) | `2026-02-21-2125-fair-value-gaps.md` |
| Pixel | Toggle Switch Component | `2026-02-21-2126-component-toggle-switch.md` |

### Agent Learning Batch — Feb 21, 2026 (Night)
Synthesis quality standards guide:

| Agent | Topic | File |
|-------|-------|------|
| Synthesis | Quality Standards & Production Readiness | `2026-02-21-2220-quality-standards.md` |

### Agent Learning Batch — Feb 21, 2026 (Late Night)
Two more guides covering async retry patterns and Hilt DI:

| Agent | Topic | File |
|-------|-------|------|
| Ghost | Async Retry Pattern v2 | `2026-02-21-2123-async-retry-v2.md` |
| Nexus | Hilt Dependency Injection Patterns | `2026-02-21-2241-hilt-dependency-injection-patterns.md` |
| Oracle | CCI Use Case | `2026-02-21-2253-cci-use-case.md` |

### Agent Learning Batch — Feb 21, 2026 (Late Night)
Ghost trade report generator:

| Agent | Topic | File |
|-------|-------|------|
| Ghost | Trade Report Generator | `2026-02-21-2223-trade-report-generator.md` |
| Pixel | Empty State UX Pattern | `2026-02-21-2325-ux-empty-states.md` |

### Agent Learning — Feb 22, 2026
Ghost quick reference for Python trading patterns:

| Agent | Topic | File |
|-------|-------|------|
| Ghost | Quick Reference: Python Trading Patterns | `2026-02-22-0023-quick-reference.md` |
| Oracle | Pivot Points | `2026-02-22-0024-pivot-points.md` |
| Synthesis | Workflow Optimization Patterns | `2026-02-22-0020-workflow-optimization-patterns.md` |
| Ghost | Rate Limiter Pattern | `2026-02-22-0123-rate-limiter.md` |
