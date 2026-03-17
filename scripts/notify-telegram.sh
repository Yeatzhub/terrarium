#!/bin/bash
# Telegram notification with quiet hours support
# Only sends during quiet hours if priority is CRITICAL

# Time constants (America/Chicago = CDT = UTC-5)
QUIET_START=23  # 11 PM CDT = 04:00 UTC
QUIET_END=8     # 8 AM CDT = 13:00 UTC

# Check if we're in quiet hours (UTC)
CURRENT_HOUR=$(date -u +%H | sed 's/^0//')

# Convert to CDT for comparison
CURRENT_HOUR_CDT=$(( (CURRENT_HOUR - 5 + 24) % 24 ))

IN_QUIET_HOURS=0
if [ $CURRENT_HOUR_CDT -ge $QUIET_START ] || [ $CURRENT_HOUR_CDT -lt $QUIET_END ]; then
    IN_QUIET_HOURS=1
fi

# Check priority (CRITICAL, HIGH, MEDIUM, LOW, default MEDIUM)
PRIORITY="${1:-MEDIUM}"
MESSAGE="$2"

if [ -z "$MESSAGE" ]; then
    echo "Usage: $0 <priority> <message>"
    echo "Priority: CRITICAL, HIGH, MEDIUM, LOW"
    exit 1
fi

# If in quiet hours and not critical, skip
if [ $IN_QUIET_HOURS -eq 1 ] && [ "$PRIORITY" != "CRITICAL" ]; then
    LOG_FILE="/storage/workspace/logs/notifications-$(date +%Y-%m-%d).log"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [QUIET-HOURS] Suppressed ($PRIORITY): $MESSAGE" >> "$LOG_FILE"
    exit 0
fi

# Send via OpenClaw message tool or direct Telegram API
# This would need to integrate with OpenClaw's message system
# For now, log to file
LOG_FILE="/storage/workspace/logs/notifications-$(date +%Y-%m-%d).log"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$PRIORITY] $MESSAGE" >> "$LOG_FILE"

# If we had direct Telegram integration:
# curl -s "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
#   -d "chat_id=${CHAT_ID}" \
#   -d "text=${MESSAGE}" \
#   -d "parse_mode=HTML" \
#   > /dev/null

exit 0