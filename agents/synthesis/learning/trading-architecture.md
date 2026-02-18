# Trading System Architecture

**Owner:** Synthesis (Team Lead)  
**Purpose:** Unified architecture for Ghost (execution) and Oracle (strategy) agents  
**Version:** 1.0.0  
**Last Updated:** 2026-02-18

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           TRADING ECOSYSTEM ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│   │   Binance    │    │    Coinbase  │    │   Kraken     │  ← Exchange APIs │
│   │   WebSocket  │    │    REST/WS   │    │   REST/WS    │                  │
│   └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│          │                   │                   │                          │
│          └───────────────────┼───────────────────┘                          │
│                              │                                               │
│                    ┌─────────▼─────────┐                                    │
│                    │   DATA LAYER      │                                    │
│                    │  ┌─────────────┐  │    Tick Data, OHLCV, Order Book     │
│                    │  │ Message Bus │  │    ┌──────────────────────────┐    │
│                    │  │  (Redis)    │◄─┼────┤   Time-Series Database   │    │
│                    │  └─────────────┘  │    │      (TimescaleDB)       │    │
│                    └─────────┬─────────┘    └──────────────────────────┘    │
│                              │                                               │
│   ┌──────────────────────────┼──────────────────────────────────────┐        │
│   │              ORACLE AGENT (Strategy)              │           │        │
│   │  ┌───────────────────────▼────────────────────────┐  │           │        │
│   │  │           SIGNAL GENERATION ENGINE              │  │           │        │
│   │  │  ┌─────────────┐  ┌─────────────┐  ┌────────┐  │  │           │        │
│   │  │  │  Technical  │  │   ML Models │  │  Macro │  │  │           │        │
│   │  │  │  Indicators │  │ (LSTM/XGB)  │  │ Scanner│  │  │           │        │
│   │  │  └──────┬──────┘  └──────┬──────┘  └───┬────┘  │  │           │        │
│   │  │         └─────────────────┴─────────────┘       │  │           │        │
│   │  │                    │                           │  │           │        │
│   │  │         ┌────────────▼────────┐                  │  │           │        │
│   │  │         │   Signal Merger     │                  │  │           │        │
│   │  │         │ (Weighted Consensus)│                  │  │           │        │
│   │  │         └──────────┬──────────┘                  │  │           │        │
│   │  └────────────────────┼─────────────────────────────┘  │           │        │
│   │                       │                               │           │        │
│   │              ┌────────▼────────┐                      │           │        │
│   │              │ Signal Queue    │←─────────────────────┘           │        │
│   │              └────────┬────────┘                                  │        │
│   └───────────────────────┼───────────────────────────────────────────┘        │
│                           │                                                   │
│   ┌───────────────────────┼───────────────────────────────────────────┐        │
│   │           GHOST AGENT (Execution)                      │           │        │
│   │  ┌─────────────────────▼──────────────────────────────┐  │           │        │
│   │  │              EXECUTION ENGINE                       │  │           │        │
│   │  │  ┌────────────┐  ┌────────────┐  ┌────────────┐  │  │           │        │
│   │  │  │ Smart Order│  │  Position  │  │  Execution │  │  │           │        │
│   │  │  │  Router    │  │  Manager   │  │ Algorithms │  │  │           │        │
│   │  │  │ (TWAP/VWAP)│  │(Track/Size)│  │(Limit/Market)│  │  │           │        │
│   │  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  │  │           │        │
│   │  │        └───────────────┴───────────────┘          │  │           │        │
│   │  │                      │                             │  │           │        │
│   │  │             ┌────────▼────────┐                    │  │           │        │
│   │  │             │ Risk Filter     │◄──────────────────┐ │  │           │        │
│   │  │             │ (Pre-flight)    │                   │ │  │           │        │
│   │  │             └────────┬────────┘                   │ │  │           │        │
│   │  │                      │                            │ │  │           │        │
│   │  │             ┌────────▼────────┐                  │ │  │           │        │
│   │  │             │ Exchange Adapter  │                  │ │  │           │        │
│   │  │             │ (REST/WebSocket)  │                  │ │  │           │        │
│   │  │             └────────┬────────┘                  │ │  │           │        │
│   │  └──────────────────────┼──────────────────────────┘ │  │           │        │
│   │                         │                            │  │           │        │
│   └─────────────────────────┼────────────────────────────┘  │           │        │
│                             │                               │           │        │
│                    ┌────────▼────────┐                       │           │        │
│                    │  RISK CONTROL   │◄──────────────────────┘           │        │
│                    │     LAYER       │                                  │        │
│                    │ ┌─────────────┐ │                                  │        │
│                    │ │ Circuit     │ │                                  │        │
│                    │ │ Breakers    │ │                                  │        │
│                    │ │ Position    │ │                                  │        │
│                    │ │ Limits      │ │                                  │        │
│                    │ │ Drawdown    │ │                                  │        │
│                    │ └─────────────┘ │                                  │        │
│                    └────────┬────────┘                                  │        │
│                             │                                          │        │
│   ┌─────────────────────────▼─────────────────────────────────────────┐        │
│   │                    MONITORING & OBSERVABILITY                      │        │
│   │  ┌────────┐  ┌────────┐  ┌──────────┐  ┌────────────┐  ┌────────┐  │        │
│   │  │ Logging│  │ Metrics│  │  Alerts  │  │ Dashboard  │  │ Backtest│  │        │
│   │  │(Loki)  │  │(Prom. )│  │(PagerDuty│  │ (Grafana)  │  │  Engine │  │        │
│   │  └────────┘  └────────┘  └──────────┘  └────────────┘  └────────┘  │        │
│   └─────────────────────────────────────────────────────────────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Data Flow Architecture

### 2.1 Real-Time Price Feed Flow

```
Tick Data Flow:
================

Exchange ──► Collector ──► Normalizer ──► Message Bus ──► Consumers
    │           │              │              │
    │           │              │              ├──► Oracle (Signal Gen)
    │           │              │              ├──► Ghost (Execution)
    │           │              │              ├──► TimescaleDB (History)
    │           │              │              └──► Redis (Cache)
    │           │              │
    │           │              └─── Standardized Format (below)
    │           │
    │           └─── Rate Limiting, Connection Resilience
    │
    └─── WebSocket + REST Fallback

Standardized Data Schema:
-------------------------
{
  "symbol": "BTCUSDT",
  "exchange": "binance",
  "timestamp_ms": 1708234567890,
  "bid": 50123.45,
  "ask": 50124.10,
  "last": 50123.78,
  "volume_24h": 15234.56,
  "source": "spot",
  "latency_ms": 45
}
```

### 2.2 Signal → Execution Flow

```
Signal Flow Sequence:
=====================

Oracle                                      Ghost
------                                      -----
   │                                          │
   │  1. Signal Generated                     │
   │  {                                       │
   │    "signal_id": "sig_abc123",            │
   │    "strategy": "momentum_v2",            │
   │    "symbol": "BTCUSDT",                  │
   │    "action": "buy",                      │
   │    "confidence": 0.87,                   │
   │    "timestamp_ms": 1708234567890         │
   │  }                                       │
   │                                          │
   ├────────────────2. Publish───────────────►│  → Redis Stream
   │              to signal_queue             │
   │                                          │
   │                              3. Validate │
   │                         Confidence ≥ 0.7 │
   │                  Symbol in whitelist?    │
   │                          Drawdown OK?    │
   │                                          │
   │◄───────────────4. Ack/Nack───────────────┤
   │                                          │
   │                              5. Execute  │
   │                    Calculate position    │
   │                    Submit order via API  │
   │                                          │
   │  ◄─────────────6. Report────────────────┤
   │         Publish fill/cancel/reject     │
   │         to execution_result_queue        │

State Transitions:
==================

SIGNAL_GENERATED ──► SIGNAL_VALIDATED ──► ORDER_SUBMITTED ──► ORDER_FILLED
       │                    │                    │
       ▼                    ▼                    ▼
  SIGNAL_REJECTED    SIGNAL_EXPIRED       ORDER_CANCELLED
       │                                         │
       └─────────────────────────────────────────┘
          (Circuit breaker triggers)
```

---

## 3. Risk Management Layer

### 3.1 Position Sizing Algorithm

```python
# Kelly Criterion Modified for Crypto Volatility
def calculate_position_size(
    account_value: float,
    win_rate: float,           # Historical backtest accuracy
    avg_win: float,            # Average winning trade %
    avg_loss: float,          # Average losing trade %
    volatility_24h: float,      # From market data
    max_position_pct: float = 0.15  # Cap at 15% of account
) -> float:
    """
    Calculate position size using fractional Kelly with volatility adjustment.
    """
    # Kelly fraction: f = (bp - q) / b
    # where: b = avg_win/avg_loss, p = win_rate, q = 1-p
    
    if avg_loss == 0:
        return 0
    
    b = abs(avg_win / avg_loss)
    p = win_rate
    q = 1 - p
    
    kelly_fraction = (b * p - q) / b
    
    # Half-Kelly for safety
    safe_fraction = kelly_fraction * 0.5
    
    # Volatility adjustment (reduce size in high vol)
    vol_factor = max(0.25, 1.0 - volatility_24h)
    
    position_pct = safe_fraction * vol_factor
    
    # Hard caps
    position_pct = min(position_pct, max_position_pct)
    position_pct = max(position_pct, 0.01)  # Minimum 1%
    
    return account_value * position_pct
```

### 3.2 Circuit Breakers

```
┌────────────────────────────────────────────────────────────────┐
│                    CIRCUIT BREAKER HIERARCHY                    │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LEVEL 1: SYMBOL-LEVEL (Per trading pair)                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Trigger: Single symbol moves > 15% in 5 min             │   │
│  │ Action: Pause new orders for symbol, reduce position    │   │
│  │ Auto-reset: After 15 min or vol normalizes              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  LEVEL 2: AGENT-LEVEL (Ghost/Oracle process)                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Trigger: 3 consecutive failed executions OR 5% daily loss│   │
│  │ Action: Stop accepting signals, close existing positions   │   │
│  │ Auto-reset: Manual intervention required                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  LEVEL 3: ACCOUNT-LEVEL                                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Trigger: Daily loss > max_drawdown (configurable, 10%)   │   │
│  │ Action: Halt all trading, liquidate to stablecoins       │   │
│  │ Auto-reset: Manual + 24h cooling period + re-approval     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  LEVEL 4: SYSTEM-LEVEL                                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Trigger: Exchange API down > 10 min OR flash crash       │   │
│  │ Action: Emergency stop, notify operators                 │   │
│  │ Auto-reset: Never - requires manual reset                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

### 3.3 Drawdown Management

```python
# Max Drawdown Tracker
class DrawdownMonitor:
    def __init__(self, max_drawdown_pct: float = 10.0):
        self.max_drawdown_pct = max_drawdown_pct
        self.peak_value = 0.0
        self.current_value = 0.0
        self.drawdown_start_time: Optional[datetime] = None
        
    def update(self, current_value: float) -> dict:
        """Returns status and any circuit breaker triggers."""
        
        # Update peak
        if current_value > self.peak_value:
            self.peak_value = current_value
            self.drawdown_start_time = None
        
        self.current_value = current_value
        
        # Calculate drawdown
        drawdown_pct = ((self.peak_value - current_value) / self.peak_value) * 100
        
        status = {
            "peak": self.peak_value,
            "current": current_value,
            "drawdown_pct": drawdown_pct,
            "status": "normal",
            "action_required": None
        }
        
        # Decision tree
        if drawdown_pct >= self.max_drawdown_pct:
            status["status"] = "critical"
            status["action_required"] = "halt_and_liquidate"
        elif drawdown_pct >= self.max_drawdown_pct * 0.7:
            status["status"] = "warning"
            status["action_required"] = "reduce_position_sizes"
        elif drawdown_pct >= self.max_drawdown_pct * 0.5:
            status["status"] = "caution"
            status["action_required"] = "increase_monitoring"
            
        return status
```

---

## 4. Monitoring & Alerting Strategy

### 4.1 Metrics Collection

```
┌──────────────────────────────────────────────────────────────────┐
│                      METRICS CATEGORIES                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. MARKET DATA                                                 │
│     ├─ ticker_latency_ms: Time from exchange to normalized      │
│     ├─ price_stale_seconds: Time since last tick                │
│     ├─ spread_pct: (ask - bid) / mid                             │
│     └─ api_error_rate: Failed requests / total requests          │
│                                                                  │
│  2. SIGNAL METRICS (Oracle)                                      │
│     ├─ signals_generated_per_hour                                │
│     ├─ signal_confidence_distribution                            │
│     ├─ strategy_hit_rate: Predicted vs actual price movement     │
│     └─ signal_queue_depth: Pending signals waiting for Ghost     │
│                                                                  │
│  3. EXECUTION METRICS (Ghost)                                      │
│     ├─ orders_submitted_per_hour                                 │
│     ├─ fill_rate: Filled / submitted orders                      │
│     ├─ slippage: Expected price vs filled price                  │
│     ├─ execution_latency_ms: Signal received → order submitted │
│     └─ rejected_orders_count: By reason (insufficient funds,etc) │
│                                                                  │
│  4. RISK METRICS                                                  │
│     ├─ current_drawdown_pct                                      │
│     ├─ daily_pnl_usd                                             │
│     ├─ largest_single_position_pct                                 │
│     ├─ exposure_by_exchange                                        │
│     └─ circuit_breaker_triggers_per_day                            │
│                                                                  │
│  5. SYSTEM HEALTH                                                  │
│     ├─ cpu_usage_pct                                              │
│     ├─ memory_usage_pct                                           │
│     ├─ redis_queue_depth                                          │
│     ├─ database_connection_pool_utilization                       │
│     └─ last_checkpoint_age_ms                                     │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 4.2 Alerting Rules (Prometheus-style)

```yaml
# alerts.yml - Critical alerting thresholds

groups:
  - name: critical_alerts
    rules:
      
      # Market Data Issues
      - alert: StaleMarketData
        expr: time() - ticker_last_updated_seconds > 60
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "Market data stale for {{ $labels.symbol }}"
          runbook: "Check exchange WebSocket connection, fallback to REST"
      
      # Execution Issues
      - alert: HighRejectionRate
        expr: rate(orders_rejected_total[5m]) / rate(orders_submitted_total[5m]) > 0.1
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Order rejection rate > 10%"
          runbook: "Check balance, API rate limits, symbol restrictions"
      
      # Risk Alerts
      - alert: ApproachingMaxDrawdown
        expr: current_drawdown_pct > (max_drawdown_threshold_pct * 0.8)
        for: 0s
        labels:
          severity: critical
        annotations:
          summary: "Drawdown at {{ $value }}% (threshold: {{ $labels.threshold }}%)"
          runbook: "Reduce position sizes, consider hedging"
      
      - alert: CircuitBreakerTriggered
        expr: circuit_breaker_state == 1
        for: 0s
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker triggered at level {{ $labels.level }}"
          runbook: "Manual review required before re-enable"
      
      # System Health
      - alert: RedisQueueBacklog
        expr: redis_queue_depth > 100
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Signal queue backlog: {{ $value }} messages"
          runbook: "Check Ghost consumer health, scale if needed"
```

### 4.3 Logging Levels & Structure

```
Log Levels:
===========
ERROR   → Trading halts, balances critical, API failures    → Immediate alert
WARNING → Edge cases, retries, minor deviations             → Hourly digest
INFO    → Signals, fills, position changes                  → Dashboard only
DEBUG   → Detailed execution flow, calculations             → Stored 7 days

Structured Log Format:
=======================
{
  "timestamp": "2026-02-18T02:18:00.123Z",
  "level": "INFO",
  "source": "ghost",
  "component": "execution_engine",
  "event": "ORDER_FILLED",
  "trace_id": "abc123-xyz789",
  "data": {
    "order_id": "ord_def456",
    "signal_id": "sig_ghi789",
    "symbol": "BTCUSDT",
    "side": "buy",
    "quantity": 0.5,
    "price": 50123.45,
    "fee_usd": 2.50,
    "slippage_bps": 3
  },
  "metrics": {
    "execution_latency_ms": 45,
    "signal_to_fill_ms": 1234
  }
}
```

---

## 5. Scalability Design

### 5.1 Multi-Exchange Support

```
┌──────────────────────────────────────────────────────────────────┐
│                    EXCHANGE AGNOSTIC DESIGN                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Abstract Exchange Interface:
│  ----------------------------------------------------------------
│  
│  class ExchangeAdapter(ABC):
│      @abstractmethod
│      async def subscribe_tickers(self, symbols: List[str]): ...
│      
│      @abstractmethod
│      async def place_order(self, order: OrderRequest) -> Order: ...
│      
│      @abstractmethod
│      async def get_balances(self) -> Dict[str, Balance]: ...
│      
│      @abstractmethod
│      def normalize_ticker(self, raw: dict) -> Ticker: ...
│  
│                                                                  │
│  Adapter Implementations:
│  ----------------------------------------------------------------
│  
│  BinanceAdapter ──► binance-python library ──► Binance REST/WS
│  CoinbaseAdapter ──► cbpro / REST API ───────► Coinbase Pro
│  KrakenAdapter ──► krakenex library ──────────► Kraken API
│                                                                  │
│  Add New Exchange:
│  1. Implement ExchangeAdapter interface
│  2. Add exchange config to ~/.config/trading/exchanges/
│  3. Register in ExchangeFactory
│  4. Update market data collector to route symbols
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 5.2 Horizontal Scaling Architecture

```
Scale-Out Deployment:
=====================

┌─────────────────────────────────────────────────────────────────┐
│                          LOAD BALANCER                           │
│              (Routes by symbol hash or round-robin)               │
└────────────────────┬──────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬
        │            │            │
   ┌────▼───┐   ┌────▼───┐   ┌────▼───┐
   │Oracle-1│   │Oracle-2│   │Oracle-N│    ← Strategy Agents
   │BTC,ETH │   │SOL,ADA │   │(etc.)  │      (can scale per strategy)
   └───┬────┘   └───┬────┘   └───┬────┘
       │            │            │
       └────────────┼────────────┘
                    │
            ┌───────▼────────┐
            │   Redis        │  ← Shared state
            │   Cluster      │    (signals, positions, locks)
            └───────┬────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
   ┌────▼───┐  ┌────▼───┐  ┌────▼───┐
   │Ghost-1 │  │Ghost-2 │  │Ghost-N │    ← Execution Agents
   │Binance │  │Coinbase│  │Kraken  │      (can scale per exchange)
   └────────┘  └────────┘  └────────┘

State Management:
=================
- Signals: Redis Streams (ordered, persistent)
- Positions: Redis Hash (fast lookups)
- Locks: Redis Redlock (distributed locking)
- Config: Consul/etcd (service discovery)
```

### 5.3 Future Exchange Addition Checklist

```markdown
## Adding a New Exchange: Quick Reference

### Step 1: Research & Account Setup
- [ ] Review exchange API documentation
- [ ] Check trading pair availability vs target markets
- [ ] Create sandbox/testnet account
- [ ] Verify API rate limits and WebSocket capabilities
- [ ] Check for geographic restrictions

### Step 2: Adapter Development
- [ ] Implement `ExchangeAdapter` interface
- [ ] Add ticker normalization mapping
- [ ] Implement auth (API key, signature method)
- [ ] Add order types: market, limit, stop-limit
- [ ] Handle rate limiting with exponential backoff
- [ ] Add connection resilience (WebSocket auto-reconnect)

### Step 3: Testing
- [ ] Unit tests with mocked responses
- [ ] Integration tests on sandbox
- [ ] Paper trading validation (1 week minimum)
- [ ] Latency benchmarking vs existing exchanges
- [ ] Error injection testing (network failures, rate limits)

### Step 4: Deployment
- [ ] Add exchange config to shared config store
- [ ] Update monitoring dashboards
- [ ] Configure alerts for new exchange errors
- [ ] Document in runbook
- [ ] Update circuit breaker rules for new exchange
```

---

## 6. Quick Reference: File Locations

| Component | Path | Owner |
|-----------|------|-------|
| Architecture | `~/.openclaw/workspace/agents/synthesis/learning/trading-architecture.md` | Synthesis |
| Shared Libraries | `~/.openclaw/workspace/agents/synthesis/learning/shared-libs.md` | Synthesis |
| Config Schema | `~/.openclaw/workspace/config/trading-config-schema.json` | Synthesis |
| Exchange Adapters | `~/.openclaw/workspace/agents/ghost/adapters/` | Ghost |
| Strategy Code | `~/.openclaw/workspace/agents/oracle/strategies/` | Oracle |
| Database Migrations | `~/.openclaw/workspace/db/migrations/` | Shared |
| Monitoring Rules | `~/.openclaw/workspace/config/alerts/` | Synthesis |

---

## 7. Communication Contracts

### Inter-Agent Message Format

```json
{
  "version": "1.0.0",
  "message_type": "signal|execution|status|alert",
  "trace_id": "uuid-for-tracing",
  "sender": "oracle|ghost|synthesis",
  "timestamp_ms": 1708234567890,
  "payload": { }
}
```

| Message Type | Channel | Producer | Consumer |
|--------------|---------|----------|----------|
| `signal` | `trading:signals:queue` | Oracle | Ghost |
| `execution_update` | `trading:execution:events` | Ghost | Oracle, Dashboard |
| `risk_alert` | `trading:risk:alerts` | Ghost | Synthesis, PagerDuty |
| `heartbeat` | `trading:health:checks` | All | Monitoring |

---

**Next Steps:**
1. Ghost: Review Execution Engine section, implement adapters
2. Oracle: Review Signal Generation flow, integrate with Message Bus
3. Synthesis: Set up Redis cluster, Prometheus/Grafana stack
