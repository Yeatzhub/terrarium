#!/bin/bash
# GPU Temperature Alert - Notify if temp exceeds threshold

THRESHOLD=70
LOG_FILE="/storage/workspace/logs/gpu_temp.log"

mkdir -p "$(dirname "$LOG_FILE")"

# Get GPU temp
TEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader 2>/dev/null | tr -d ' C')

if [ -z "$TEMP" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Could not read GPU temp" >> "$LOG_FILE"
    exit 1
fi

TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

if [ "$TEMP" -ge "$THRESHOLD" ]; then
    # Log the alert
    echo "$TIMESTAMP ALERT: GPU temp is ${TEMP}°C (threshold: ${THRESHOLD}°C)" >> "$LOG_FILE"

    # Send notification via OpenClaw
    if command -v openclaw &> /dev/null; then
        openclaw notify --title "🔥 GPU Temperature Alert" --body "Tesla P40 at ${TEMP}°C (threshold: ${THRESHOLD}°C)" 2>/dev/null
    fi

    # Try to send to Discord webhook if configured
    if [ -n "$DISCORD_WEBHOOK_URL" ]; then
        curl -s -X POST "$DISCORD_WEBHOOK_URL" \
            -H "Content-Type: application/json" \
            -d "{\"content\": \"🔥 GPU Temp Alert: ${TEMP}°C (threshold: ${THRESHOLD}°C)\"}" \
            2>/dev/null
    fi

    # Also write to system log
    logger -t gpu_temp "ALERT: GPU temperature ${TEMP}°C exceeds threshold ${THRESHOLD}°C"

    exit 2  # Exit code 2 = alert triggered
fi

# Normal logging (every 10th check to reduce log spam)
if [ $(($(date +%s) % 600)) -lt 60 ]; then
    echo "$TIMESTAMP OK: GPU temp ${TEMP}°C" >> "$LOG_FILE"
fi

exit 0