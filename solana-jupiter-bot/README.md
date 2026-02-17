# Jupiter Solana Trading Bot

High-frequency DEX trading on Solana via Jupiter aggregator.

## Goal
Turn 1 SOL into 2 SOL as fast as possible using aggressive (but calculated) strategies.

**WARNING:** High risk of total loss. Educational purposes only.

---

## Strategies

### 1. Triangular Arbitrage (Recommended)
- Find price differences in circular trades
- Risk: Low (if executed correctly)
- Expected return: 0.5-2% per trade
- Timeline to double: 1-2 weeks

### 2. Momentum Chasing
- Buy trending tokens
- Risk: High
- Expected return: 10-50% per trade
- Timeline to double: Days (if lucky)

### 3. Range Trading
- Grid trading on SOL/USDC
- Risk: Medium
- Expected return: 10% over multiple trades
- Timeline to double: 2-4 weeks

---

## Quick Start

### 1. Paper Trading (No wallet needed)
```bash
# Install dependencies
pip install requests

# Run paper trading bot
python jupiter_bot.py --mode paper --strategy arbitrage --capital 1.0
```

### 2. Live Trading (Requires Solana wallet)
```bash
# Set wallet private key
export SOLANA_PRIVATE_KEY="your_private_key_here"

# Run live (DANGER - REAL FUNDS)
python jupiter_bot.py --mode live --strategy arbitrage --capital 1.0 --private-key $SOLANA_PRIVATE_KEY
```

---

## Analysis

See the doubling plan:
```bash
python strategies.py
```

Output includes:
- Available opportunities
- Realistic timelines
- Risk assessments
- Success probabilities

---

## Files

| File | Purpose |
|------|---------|
| `jupiter_api.py` | Jupiter API wrapper |
| `strategies.py` | Trading strategies + doubling plan |
| `jupiter_bot.py` | Main bot orchestrator |
| `README.md` | This file |

---

## Jupiter API

Uses Jupiter v6 API:
- Quote API: https://quote-api.jup.ag/v6
- Price API: https://price.jup.ag/v4
- Docs: https://station.jup.ag/docs/

---

## Risk Management

Even aggressive strategies have limits:
- Max 50% drawdown (stop trading)
- Max 0.3 SOL daily loss
- Max 50% of balance per trade
- Reserve 50% never traded

---

## Realistic Expectations

| Scenario | Timeline | Success Rate | Outcome |
|----------|----------|--------------|---------|
| Conservative | 2-4 weeks | 40-50% | Double 1 SOL |
| Aggressive | 2-3 days | 25% | Double or bust |
| Gambling | Hours | 10% | 10x or $0 |

**Most likely outcome:** Lose 30-50% of 1 SOL within first week.

---

## Wallet Setup

```bash
# Install Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Create wallet
solana-keygen new --outfile ~/jupiter-bot-wallet.json

# Get address
solana-keygen pubkey ~/jupiter-bot-wallet.json

# Fund with 1.1 SOL (1.0 for trading, 0.1 for gas)
# Use Faucet (devnet): solana airdrop 2 YOUR_ADDRESS --url devnet
# Or transfer from exchange

# Export private key for bot
cat ~/jupiter-bot-wallet.json
```

---

## Testing

Test on devnet first:
```bash
python jupiter_bot.py --mode paper --capital 1.0
```

Monitor for 24-48 hours before going live.

---

## Disclaimer

This is experimental software for educational purposes. Cryptocurrency trading carries substantial risk of loss. Never trade more than you can afford to lose completely.

**You will likely lose money.**
