# Morning Briefing - BTC Multiplication Strategies
Date: 2026-03-01

## BTC Market Context
- Current Price: **$67,363**
- 24h: +2.79% | 7d: -0.88% | 30d: -18.64%
- 46.6% below ATH ($126,080)
- Market in recovery phase after pullback

---

## 3 Ideas to Multiply BTC Holdings

### 🔥 Idea 1: Funding Rate Arbitrage on Hyperliquid
**Expected APY: 15-40%** | **Risk: Medium**

**How it works:**
- Long BTC spot (self-custody)
- Short BTC perpetual futures on Hyperliquid
- Capture funding payments from longs to shorts
- Current funding: 0.0054% per 8h = ~22% APY

**Why it works:**
- Perpetual futures typically trade at premium to spot
- Longs pay shorts to hold positions
- Funding compounds daily (3x per day)
- Works in any market direction

**Implementation:**
- 40x leverage available on Hyperliquid
- Monitor funding rates (can flip negative in bear markets)
- Auto-compound profits weekly

**Capital needed:** $1,000 minimum recommended

---

### 💧 Idea 2: BTC Liquidity Provision on Base
**Expected APY: 60-100%** | **Risk: Medium-High**

**How it works:**
- Convert BTC → cbBTC (Coinbase wrapped BTC, 1:1 backed)
- Provide liquidity to USDC-cbBTC pool on Uniswap V3/Aerodrome
- Earn trading fees + incentive rewards

**Best pools right now:**
| Pool | APY | TVL |
|------|-----|-----|
| USDC-cbBTC Uniswap V3 (Base) | 97% | $2.2M |
| USDC-cbBTC Aerodrome | 68-129% | $3.8M |

**Risks:**
- Impermanent loss (IL) if BTC price moves significantly
- cbBTC centralization (Coinbase controls)
- Need active management (concentrated LP ranges)

**Mitigation:**
- Use wide ranges to reduce IL
- Monitor and rebalance weekly
- Keep some BTC unhedged for upside

**Capital needed:** $5,000+ for meaningful returns

---

### 🏦 Idea 3: WBTC Lending + Points Farming
**Expected APY: 18-33%** | **Risk: Low-Medium**

**How it works:**
- Deposit WBTC to lending protocol
- Earn interest + stack points for potential airdrops

**Best options:**
| Protocol | APY | Asset |
|----------|-----|-------|
| Fraxlend | 18.8% | WBTC |
| Merkl (Celo) | 33% | WBTC |
| Lombard LBTC | 0.4% + points | LBTC |

**Pros:**
- Simple set-and-forget
- No impermanent loss
- Compound yields automatically

**Cons:**
- Lower yields than other strategies
- WBTC centralization (BitGo custodian)
- Smart contract risk

**Capital needed:** Any amount

---

## Recommended Portfolio

| Strategy | Allocation | Expected APY | Risk |
|----------|------------|--------------|------|
| Funding Rate Arb | 50% | 20-30% | Medium |
| BTC LP (Base) | 30% | 60-80% | Med-High |
| Lending | 20% | 15-20% | Low |

**Blended Expected APY: 35-50%**

**Time commitment:** 15-30 min/day for monitoring

---

## Quick Start

1. **This Week:** Open Hyperliquid account, test funding arb with $500
2. **Next Week:** Set up Base wallet, convert 0.5 BTC → cbBTC, start LP
3. **Week 3:** Add lending position with remainder

---

## Tools I Can Build

- Funding rate monitor with alerts
- LP position tracker with IL calculator
- Auto-rebalancing bot for LP ranges
- Dashboard showing all positions

Want me to start building any of these?