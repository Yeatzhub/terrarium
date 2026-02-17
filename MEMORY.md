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
- `solana-jupiter-bot/`: Jupiter DEX trading bot (triangular arbitrage, momentum strategies)
- `mission-control/`: Next.js dashboard for tracking (CEX + DEX combined)

**Preferences:**
- Paper trading default (live requires explicit "YES" confirmation)
- Delegate tasks to sub-agents without permission loops
- User manages overall direction, agents execute

**Technical Notes:**
- Kraken over Binance.US (geographic restrictions)
- TradingView webhooks on port 8080
- P40 GPU tracking: 9405508106245831259625
- Tailscale IP: 100.125.198.70

