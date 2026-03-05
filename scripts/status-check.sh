#!/bin/bash
# Hourly Status Check - Run via cron
# Logs to /tmp/status-check.log

LOG="/tmp/status-check.log"
ALERT_LOG="/home/yeatz/.openclaw/workspace/memory/status-alerts.log"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') STATUS CHECK ===" >> "$LOG"

ALERTS=()

# OpenClaw Gateway
if curl -s -o /dev/null -w "%{http_code}" http://localhost:18789/status 2>/dev/null | grep -q "200"; then
    echo "✅ OpenClaw Gateway: ONLINE" >> "$LOG"
else
    echo "❌ OpenClaw Gateway: OFFLINE" >> "$LOG"
    ALERTS+=("OpenClaw Gateway OFFLINE")
fi

# The Hub
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/openclaw-status 2>/dev/null | grep -q "200"; then
    echo "✅ The Hub: ONLINE" >> "$LOG"
else
    echo "❌ The Hub: OFFLINE" >> "$LOG"
    ALERTS+=("The Hub OFFLINE")
fi

# SearXNG
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/search?q=test\&format=json 2>/dev/null | grep -q "200"; then
    echo "✅ SearXNG: ONLINE" >> "$LOG"
else
    echo "❌ SearXNG: OFFLINE" >> "$LOG"
    ALERTS+=("SearXNG OFFLINE")
fi

# Ollama
if curl -s http://localhost:11434/api/tags 2>/dev/null | grep -q "models"; then
    echo "✅ Ollama: ONLINE" >> "$LOG"
else
    echo "❌ Ollama: OFFLINE" >> "$LOG"
    ALERTS+=("Ollama OFFLINE")
fi

# Trading Bots
for bot in xrp btc sol eth; do
    STATE="/home/yeatz/.openclaw/workspace/trading-bots/pionex/$bot/state.json"
    # Check for process running from that bot's directory
    PID=$(ps aux | grep "[p]ython.*bot.py" | grep "pionex/$bot" | awk '{print $2}')
    if [ -n "$PID" ]; then
        BALANCE=$(jq -r '.balance' "$STATE" 2>/dev/null)
        TRADES=$(jq -r '.total_trades' "$STATE" 2>/dev/null)
        echo "✅ $bot Bot: RUNNING (pid=$PID, Balance: $BALANCE, Trades: $TRADES)" >> "$LOG"
    else
        echo "⚠️  $bot Bot: STOPPED (no process)" >> "$LOG"
        ALERTS+=("$bot Bot stopped")
    fi
done

# GPU Status (if nvidia-smi available)
if command -v nvidia-smi &> /dev/null; then
    GPU_TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null | head -1)
    GPU_UTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null | head -1)
    VRAM_USED=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null | head -1)
    VRAM_TOTAL=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>/dev/null | head -1)
    echo "🌡️  GPU (P40): ${GPU_TEMP}°C | ${GPU_UTIL}% util | ${VRAM_USED}/${VRAM_TOTAL} MB VRAM" >> "$LOG"
fi

# Summary
echo "" >> "$LOG"
if [ ${#ALERTS[@]} -gt 0 ]; then
    echo "🚨 ALERTS: ${ALERTS[*]}" >> "$LOG"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ${ALERTS[*]}" >> "$ALERT_LOG"
fi
echo "========================================" >> "$LOG"

# Keep log under 100 lines
tail -100 "$LOG" > "${LOG}.tmp" && mv "${LOG}.tmp" "$LOG"