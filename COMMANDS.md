# Commands

User can issue these commands via Telegram:

## Thor (Trading Executor)

| Command | Action |
|---------|--------|
| `thor status` | Show XRP bot status, position, PnL, circuit breakers |
| `thor stop` | Stop trading bot |
| `thor start` | Start trading bot (paper mode) |
| `thor resume` | Resume after circuit breaker trip |

### Thor Status Response
When user sends "thor status":
1. Read `/storage/workspace/projects/trading/pionex/xrp/state_mc.json`
2. Check if bot process is running: `pgrep -f bot_mc_v2_1.py`
3. Read last 10 lines of `/storage/workspace/projects/trading/pionex/xrp/logs/bot_mc_v2.log`
4. Format response:
```
📊 XRP Bot Status
━━━━━━━━━━━━━━━━
Position: [LONG/SHORT/FLAT] @ $X.XXXX
Balance: XXX.XX XRP
PnL: $XX.XX (±X.XX%)
Circuit Breakers: ✅ OK / ⚠️ TRIPPED
Bot Process: 🟢 Running / 🔴 Stopped
Last Signal: [LONG/SHORT/HOLD] @ $X.XXXX
Daily Trades: X/X wins
```

### Thor Stop
When user sends "thor stop":
1. Kill bot process: `pkill -f bot_mc_v2_1.py`
2. Confirm stopped
3. Read final state
4. Report: "🛑 Bot stopped. Position: [status]"

### Thor Start
When user sends "thor start":
1. Start bot: `cd /storage/workspace/projects/trading/pionex/xrp && source ../venv/bin/activate && nohup python bot_mc_v2_1.py --mode paper ...`
2. Confirm running
3. Report: "🟢 Bot started in paper mode"

### Thor Resume
When user sends "thor resume" (after circuit breaker):
1. Check if breaker is why bot stopped
2. Confirm user approval
3. Clear breaker state
4. Start bot

## Other Agents

| Command | Agent | Action |
|---------|-------|--------|
| `heimdall status` | Heimdall | System health overview |
| `mimir status` | Mimir | Infrastructure status |
| `huginn scan` | Huginn | Market research |
| `njord balance` | Njord | Treasury balance report |

## System Commands

| Command | Action |
|---------|--------|
| `status` / `/status` | OpenClaw status card |
| `heartbeat` | Run heartbeat checks |
| `help` | List available commands |