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
