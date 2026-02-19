# Portfolio Risk Monitor

**Ghost Learning Entry** | 2026-02-18 21:23 | Multi-Exchange Risk Aggregation

---

## Problem

Multiple trading bots (BTC/Kraken, Solana/Jupiter, Polymarket) run independently. Each has its own risk controls, but **total portfolio exposure is invisible**:
- Correlated positions across bots amplify risk
- No unified stop-loss for "portfolio down 10%"
- Manual checking of 3+ dashboards = delayed response

## Solution

A unified risk monitor that aggregates exposure across all bots and enforces portfolio-level limits.

---

## Core Architecture

```python
"""
portfolio_risk_monitor.py
Aggregates risk across multiple trading bots with circuit breaker capability
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    NORMAL = "normal"
    ELEVATED = "elevated"  # 50% of max risk used
    CRITICAL = "critical"  # 75% of max risk used
    BREACH = "breach"      # Limit exceeded


@dataclass
class Position:
    """Normalized position from any exchange"""
    source: str           # 'kraken', 'jupiter', 'polymarket'
    symbol: str
    side: str            # 'long' or 'short'
    size: float          # Base currency amount
    entry_price: float
    current_price: float
    unrealized_pnl: float
    margin_used: float   # In USD
    leverage: float = 1.0
    
    @property
    def notional(self) -> float:
        return abs(self.size * self.current_price)
    
    @property
    def pnl_pct(self) -> float:
        if self.entry_price == 0:
            return 0
        return (self.current_price - self.entry_price) / self.entry_price * (1 if self.side == 'long' else -1)


@dataclass  
class RiskLimits:
    """Portfolio-level risk constraints"""
    max_total_notional: float = 50000.0      # $50k max exposure
    max_margin_used: float = 10000.0         # $10k margin max
    max_drawdown_pct: float = 10.0           # Stop all at 10% loss
    max_correlation_exposure: float = 0.6    # 60% max in correlated assets
    max_single_position_pct: float = 0.25    # 25% max in one position
    
    # Per-source limits
    max_per_source: Dict[str, float] = field(default_factory=lambda: {
        'kraken': 20000.0,
        'jupiter': 15000.0,
        'polymarket': 10000.0
    })


@dataclass
class RiskSnapshot:
    """Current risk state across all positions"""
    timestamp: datetime
    positions: List[Position]
    total_notional: float
    total_margin: float
    total_unrealized_pnl: float
    drawdown_pct: float
    risk_level: RiskLevel
    
    # Breakdown by source
    source_exposure: Dict[str, float]
    
    # Correlated exposure (BTC + ETH + SOL considered correlated crypto)
    crypto_exposure: float


class PortfolioRiskMonitor:
    """
    Aggregates positions from multiple bots and enforces portfolio limits.
    
    Usage:
        monitor = PortfolioRiskMonitor(RiskLimits())
        
        # Register position sources
        monitor.register_source('kraken', kraken_position_fetcher)
        monitor.register_source('jupiter', jupiter_position_fetcher)
        
        # Start monitoring
        await monitor.start_monitoring(interval_seconds=30)
        
        # Check if trading allowed
        if monitor.can_open_position('kraken', 'BTC/USD', 0.1):
            execute_trade()
    """
    
    def __init__(self, limits: RiskLimits, start_equity: float = 100000.0):
        self.limits = limits
        self.start_equity = start_equity
        self.positions: List[Position] = []
        self.sources: Dict[str, Callable[[], List[Position]]] = {}
        self.running = False
        self.current_snapshot: Optional[RiskSnapshot] = None
        self._callbacks: List[Callable[[RiskSnapshot], None]] = []
        
        # Circuit breaker state
        self.circuit_breaker_triggered = False
        self.circuit_breaker_time: Optional[datetime] = None
        self.cooldown_minutes = 30
        
    def register_source(
        self, 
        name: str, 
        fetcher: Callable[[], List[Position]]
    ) -> None:
        """Register a position source (e.g., Kraken fetcher)"""
        self.sources[name] = fetcher
        logger.info(f"Registered source: {name}")
        
    def on_risk_change(self, callback: Callable[[RiskSnapshot], None]) -> None:
        """Register callback for risk level changes"""
        self._callbacks.append(callback)
        
    async def start_monitoring(self, interval_seconds: int = 30) -> None:
        """Start the monitoring loop"""
        self.running = True
        logger.info(f"Starting risk monitor (interval: {interval_seconds}s)")
        
        while self.running:
            try:
                await self._update_positions()
                await self._evaluate_risk()
                await asyncio.sleep(interval_seconds)
            except Exception as e:
                logger.error(f"Monitor error: {e}")
                await asyncio.sleep(5)
                
    def stop(self) -> None:
        """Stop monitoring"""
        self.running = False
        
    async def _update_positions(self) -> None:
        """Fetch positions from all registered sources"""
        all_positions = []
        
        for source_name, fetcher in self.sources.items():
            try:
                positions = fetcher()
                all_positions.extend(positions)
                logger.debug(f"{source_name}: {len(positions)} positions")
            except Exception as e:
                logger.error(f"Failed to fetch from {source_name}: {e}")
                
        self.positions = all_positions
        
    async def _evaluate_risk(self) -> None:
        """Calculate risk metrics and check limits"""
        snapshot = self._calculate_snapshot()
        self.current_snapshot = snapshot
        
        # Check circuit breaker
        if snapshot.risk_level == RiskLevel.BREACH:
            self._trigger_circuit_breaker("Risk limit breached")
        elif snapshot.drawdown_pct >= self.limits.max_drawdown_pct:
            self._trigger_circuit_breaker(f"Max drawdown reached: {snapshot.drawdown_pct:.2f}%")
            
        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(snapshot)
            except Exception as e:
                logger.error(f"Callback error: {e}")
                
    def _calculate_snapshot(self) -> RiskSnapshot:
        """Calculate current risk snapshot"""
        total_notional = sum(p.notional for p in self.positions)
        total_margin = sum(p.margin_used for p in self.positions)
        total_pnl = sum(p.unrealized_pnl for p in self.positions)
        
        current_equity = self.start_equity + total_pnl
        drawdown_pct = (self.start_equity - current_equity) / self.start_equity * 100
        
        # Source breakdown
        source_exposure: Dict[str, float] = {}
        for p in self.positions:
            source_exposure[p.source] = source_exposure.get(p.source, 0) + p.notional
            
        # Crypto exposure (simplified correlation model)
        crypto_symbols = {'BTC', 'ETH', 'SOL', 'WBTC', 'stETH'}
        crypto_exposure = sum(
            p.notional for p in self.positions 
            if any(sym in p.symbol for sym in crypto_symbols)
        )
        
        # Determine risk level
        risk_level = self._determine_risk_level(
            total_notional, total_margin, drawdown_pct, 
            source_exposure, crypto_exposure
        )
        
        return RiskSnapshot(
            timestamp=datetime.now(),
            positions=self.positions.copy(),
            total_notional=total_notional,
            total_margin=total_margin,
            total_unrealized_pnl=total_pnl,
            drawdown_pct=drawdown_pct,
            risk_level=risk_level,
            source_exposure=source_exposure,
            crypto_exposure=crypto_exposure
        )
        
    def _determine_risk_level(
        self, 
        notional: float,
        margin: float,
        drawdown: float,
        source_exposure: Dict[str, float],
        crypto_exposure: float
    ) -> RiskLevel:
        """Determine overall risk level"""
        
        # Check absolute limits
        if notional > self.limits.max_total_notional:
            return RiskLevel.BREACH
        if margin > self.limits.max_margin_used:
            return RiskLevel.BREACH
        if drawdown >= self.limits.max_drawdown_pct:
            return RiskLevel.BREACH
            
        # Check per-source limits
        for source, exposure in source_exposure.items():
            max_for_source = self.limits.max_per_source.get(source, float('inf'))
            if exposure > max_for_source:
                return RiskLevel.BREACH
                
        # Check correlation exposure
        if crypto_exposure > self.limits.max_correlation_exposure * notional:
            return RiskLevel.CRITICAL
            
        # Check utilization levels
        notional_util = notional / self.limits.max_total_notional
        margin_util = margin / self.limits.max_margin_used
        
        if notional_util > 0.75 or margin_util > 0.75 or drawdown > 7:
            return RiskLevel.CRITICAL
        elif notional_util > 0.5 or margin_util > 0.5 or drawdown > 5:
            return RiskLevel.ELEVATED
            
        return RiskLevel.NORMAL
        
    def _trigger_circuit_breaker(self, reason: str) -> None:
        """Trigger portfolio circuit breaker"""
        if self.circuit_breaker_triggered:
            return
            
        self.circuit_breaker_triggered = True
        self.circuit_breaker_time = datetime.now()
        logger.critical(f"CIRCUIT BREAKER TRIGGERED: {reason}")
        
        # Notify all callbacks
        if self.current_snapshot:
            for callback in self._callbacks:
                try:
                    callback(self.current_snapshot)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
                    
    def reset_circuit_breaker(self) -> bool:
        """Reset circuit breaker after cooldown"""
        if not self.circuit_breaker_triggered:
            return True
            
        if self.circuit_breaker_time:
            elapsed = datetime.now() - self.circuit_breaker_time
            if elapsed < timedelta(minutes=self.cooldown_minutes):
                remaining = self.cooldown_minutes - elapsed.total_seconds() / 60
                logger.warning(f"Circuit breaker active: {remaining:.1f} min remaining")
                return False
                
        self.circuit_breaker_triggered = False
        self.circuit_breaker_time = None
        logger.info("Circuit breaker reset")
        return True
        
    def can_open_position(
        self, 
        source: str, 
        symbol: str, 
        size: float,
        price: float
    ) -> bool:
        """Check if new position can be opened"""
        
        if self.circuit_breaker_triggered:
            return False
            
        if not self.current_snapshot:
            return True  # No data yet, allow with caution
            
        notional = size * price
        
        # Check total notional
        if self.current_snapshot.total_notional + notional > self.limits.max_total_notional:
            logger.warning(f"Position rejected: would exceed total notional limit")
            return False
            
        # Check per-source limit
        current_source = self.current_snapshot.source_exposure.get(source, 0)
        max_source = self.limits.max_per_source.get(source, float('inf'))
        if current_source + notional > max_source:
            logger.warning(f"Position rejected: would exceed {source} limit")
            return False
            
        # Check single position limit
        position_notional = sum(
            p.notional for p in self.positions 
            if p.symbol == symbol and p.source == source
        )
        total_position = position_notional + notional
        max_single = self.limits.max_total_notional * self.limits.max_single_position_pct
        if total_position > max_single:
            logger.warning(f"Position rejected: would exceed single position limit")
            return False
            
        return True
        
    def get_status(self) -> Dict:
        """Get current status for dashboard/alerts"""
        if not self.current_snapshot:
            return {"status": "initializing"}
            
        snap = self.current_snapshot
        return {
            "timestamp": snap.timestamp.isoformat(),
            "risk_level": snap.risk_level.value,
            "circuit_breaker": self.circuit_breaker_triggered,
            "total_notional": snap.total_notional,
            "total_margin": snap.total_margin,
            "unrealized_pnl": snap.total_unrealized_pnl,
            "drawdown_pct": snap.drawdown_pct,
            "positions_count": len(snap.positions),
            "source_exposure": snap.source_exposure,
            "crypto_exposure": snap.crypto_exposure,
            "limits": {
                "max_notional": self.limits.max_total_notional,
                "max_margin": self.limits.max_margin_used,
                "max_drawdown": self.limits.max_drawdown_pct
            },
            "utilization": {
                "notional": snap.total_notional / self.limits.max_total_notional,
                "margin": snap.total_margin / self.limits.max_margin_used if self.limits.max_margin_used > 0 else 0
            }
        }
```

---

## Integration Example

```python
# integrate_with_bots.py
"""Connect the risk monitor to existing trading bots"""

import asyncio
import json
from portfolio_risk_monitor import PortfolioRiskMonitor, RiskLimits, Position

# Fetchers for each bot

def fetch_kraken_positions() -> List[Position]:
    """Fetch from BTC trading bot state"""
    try:
        with open('/home/yeatz/.openclaw/workspace/btc-trading-bot/state.json') as f:
            state = json.load(f)
            
        positions = []
        for pos in state.get('positions', []):
            positions.append(Position(
                source='kraken',
                symbol=pos['symbol'],
                side='long' if pos['size'] > 0 else 'short',
                size=abs(pos['size']),
                entry_price=pos['entry_price'],
                current_price=pos['current_price'],
                unrealized_pnl=pos['unrealized_pnl'],
                margin_used=pos.get('margin', 0),
                leverage=pos.get('leverage', 1.0)
            ))
        return positions
    except Exception as e:
        logger.error(f"Kraken fetch failed: {e}")
        return []

def fetch_jupiter_positions() -> List[Position]:
    """Fetch from Solana Jupiter bot state"""
    try:
        with open('/home/yeatz/.openclaw/workspace/solana-jupiter-bot/state.json') as f:
            state = json.load(f)
            
        positions = []
        for pos in state.get('active_positions', []):
            positions.append(Position(
                source='jupiter',
                symbol=pos['token'],
                side='long',
                size=pos['size'],
                entry_price=pos['entry_price'],
                current_price=pos['current_price'],
                unrealized_pnl=pos['unrealized_pnl'],
                margin_used=pos.get('value_usd', 0) * 0.1,  # 10% margin approx
                leverage=1.0
            ))
        return positions
    except Exception as e:
        logger.error(f"Jupiter fetch failed: {e}")
        return []

# Alert callback
def on_risk_change(snapshot):
    """Send alert when risk changes"""
    if snapshot.risk_level.value in ['critical', 'breach']:
        logger.critical(
            f"RISK ALERT: {snapshot.risk_level.value.upper()} | "
            f"DD: {snapshot.drawdown_pct:.2f}% | "
            f"Notional: ${snapshot.total_notional:,.0f}"
        )
        # Add Telegram/Discord alert here
        
# Setup and run
async def main():
    limits = RiskLimits(
        max_total_notional=50000.0,
        max_margin_used=10000.0,
        max_drawdown_pct=10.0,
        max_correlation_exposure=0.6
    )
    
    monitor = PortfolioRiskMonitor(limits, start_equity=50000.0)
    monitor.register_source('kraken', fetch_kraken_positions)
    monitor.register_source('jupiter', fetch_jupiter_positions)
    monitor.on_risk_change(on_risk_change)
    
    # Start monitoring (runs forever)
    await monitor.start_monitoring(interval_seconds=30)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Key Design Decisions

1. **Normalized Position dataclass** — All exchanges normalized to common format. No exchange-specific logic in risk calculations.

2. **Source registration pattern** — Each bot provides a fetcher function. No direct dependencies on bot internals.

3. **Circuit breaker with cooldown** — Prevents immediate re-entry after stop. Forces manual review.

4. **Correlation exposure tracking** — BTC/ETH/SOL treated as correlated basket. Prevents "diversified" positions that all move together.

5. **Async monitoring loop** — Non-blocking position updates. Fetchers can use async I/O without blocking risk calculations.

---

## Usage in Trading Bots

```python
# In your trading bot, before opening a position:

from portfolio_risk_monitor import monitor  # shared instance

def open_position(self, symbol: str, size: float, price: float):
    # Check with risk monitor first
    if not monitor.can_open_position('kraken', symbol, size, price):
        logger.warning(f"Trade blocked by risk monitor: {symbol}")
        return False
        
    # Proceed with trade...
    return self.execute_trade(symbol, size, price)
```

---

## Next Steps

1. **Add to btc-trading-bot** — Integrate `can_open_position()` check before order execution
2. **Add to solana-jupiter-bot** — Same integration pattern
3. **Create dashboard** — Simple web view of `get_status()` output
4. **Add Telegram alerts** — Critical/breach notifications to your phone
5. **Backtest correlation model** — Verify crypto exposure assumptions with historical data

---

**File location:** `agents/ghost/learning/2026-02-18-2123-portfolio-risk-monitor.md`
**Lines of code:** ~350 (implementation) + ~100 (integration)
**Immediate utility:** HIGH — protects against portfolio-level drawdowns
