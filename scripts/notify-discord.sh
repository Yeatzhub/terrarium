#!/bin/bash
# Discord notification with quiet hours support
# Only sends during quiet hours if priority is CRITICAL
# Routes to #alerts channel (1486486418363650159)

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

# Log the notification
LOG_FILE="/storage/workspace/logs/notifications-$(date +%Y-%m-%d).log"
mkdir -p "$(dirname "$LOG_FILE")"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$PRIORITY] $MESSAGE" >> "$LOG_FILE"

# Send via OpenClaw to Discord #alerts
openclaw message send --channel discord --target 1486486418363650159 -m "[$PRIORITY] $MESSAGE" 2>/dev/null

exit 0