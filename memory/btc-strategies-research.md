# BTC Multiplication Strategies Research
Date: 2026-03-01

## Current BTC Market
- Price: $67,363
- 24h: +2.79%
- 7d: -0.88%
- 30d: -18.64%
- ATH: $126,080 (-46.6%)

## Research Findings

### 1. Funding Rate Arbitrage
- Hyperliquid BTC funding: 0.0000054 per 8h = ~0.06%/day = ~22% APY
- Strategy: Long spot + short perp = capture funding
- Risk: Funding can go negative, liquidation risk on short
- Capital efficiency: 40x leverage available on Hyperliquid

### 2. BTC Liquidity Provision
High APY pools (BTC pairs):
| Pool | APY | Chain | Project | TVL |
|------|-----|-------|---------|-----|
| USDC-cbBTC | 97-129% | Base | Uniswap/Aerodrome | $2.2M-$3.8M |
| WBTC-USDT | 78% | Arbitrum | Uniswap | $10.3M |
| SOL-cbBTC | 80% | Solana | Orca | $5.9M |
| WBTC-USDT | 2725%* | Ethereum | Supernova | $1.5M |

*Very high APY likely from incentives, may not be sustainable

Risk: Impermanent loss (IL) can exceed yield
Mitigation: Stable pairs reduce IL, volatile pairs increase it

### 3. BTC Lending (Low Risk, Low Reward)
| Protocol | APY | Asset | TVL |
|----------|-----|-------|-----|
| Fraxlend | 18.8% | WBTC | $2M |
| Merkl (Celo) | 33.3% | WBTC | $29K |
| Morpho | 0% | cbBTC | $2.5B |
| Aave | 0.004% | WBTC | $2.7B |
| Lombard LBTC | 0.38% | LBTC | $714M |

### 4. BTC Staking Protocols
- Lombard LBTC: 0.38% APY + potential points/airdrops
- Bedrock uniBTC: 3.3% APY (but it's ETH-based, not BTC)
- Babylon: Native BTC staking (points phase, mainnet not live for yields yet)

### 5. Delta-Neutral Strategies
- Ethena sUSDe: 3.6% APY (stablecoin, not BTC)
- Fusion by IPOR: 8.6% on WBTC (Ethereum)
- Strategy: Short perp + lend spot = delta neutral yield

## Top 3 Ideas for Fast BTC Multiplication

### Idea 1: Funding Rate Arbitrage on Hyperliquid
**APY: 15-40% (varies)**
**Risk: Medium**
- Long BTC spot (self-custody or exchange)
- Short BTC perp on Hyperliquid (partial hedge)
- Capture positive funding rates
- Current funding: 0.0054% per 8h = ~22% APY
- Can compound with leverage for higher returns

Pros:
- No impermanent loss
- Works in any market direction
- High capital efficiency

Cons:
- Funding can flip negative
- Liquidation risk on short position
- Need to monitor positions

### Idea 2: BTC Liquidity Provision on Base
**APY: 60-100%**
**Risk: Medium-High (IL)**

Best pools:
1. USDC-cbBTC on Uniswap V3 (Base): 97% APY, $2.2M TVL
2. USDC-cbBTC on Aerodrome Slipstream: 68-129% APY, $3.8M TVL

Strategy:
- Convert BTC to cbBTC (Coinbase wrapped BTC)
- Provide liquidity to USDC-cbBTC pool
- Reinvest fees

Pros:
- Very high yields
- cbBTC is fully backed 1:1
- Base has low fees

Cons:
- Impermanent loss if BTC moves significantly
- cbBTC centralization risk (Coinbase)
- Need to manage position actively (concentrated LP)

### Idea 3: WBTC Lending on Fraxlend + Points Farming
**APY: 18-33% + points/airdrops**
**Risk: Low-Medium**

Strategy:
- Deposit WBTC to Fraxlend (~18.8% APY)
- Or use Merkl on Celo (~33% APY, but lower liquidity)
- Stack points for potential airdrops

Pros:
- Simple, no IL
- Compound yields
- Low management overhead

Cons:
- Smart contract risk
- WBTC centralization (BitGo)
- Lower yields than LP

## Recommended Approach

For aggressive multiplication:
1. Start with Funding Rate Arb (50% allocation) - captures yield regardless of direction
2. Add BTC LP on Base (30% allocation) - high yield with manageable IL
3. Keep remainder in lending (20%) - stable base yield

Expected blended APY: 35-50%
Risk level: Medium
Time commitment: Daily monitoring

## Tools Needed
- Hyperliquid account (for funding arb)
- Base wallet (for LP)
- cbBTC/WBTC conversion path
- Position monitoring bot

## Next Steps
1. Set up Hyperliquid API access
2. Create Base wallet and get cbBTC
3. Build monitoring dashboard
4. Implement automated rebalancing