#!/bin/bash
# Morning Briefing - runs at 8 AM CDT (13:00 UTC)
# Sends daily briefing to user via Discord #alerts

set -euo pipefail

LOG="$HOME/.openclaw/logs/morning-briefing.log"
mkdir -p "$(dirname "$LOG")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG"
}

# Check if in quiet hours (11 PM - 8 AM CDT)
CURRENT_HOUR=$(date -u +%H | sed 's/^0//')
QUIET_START_UTC=4   # 11 PM CDT
QUIET_END_UTC=13   # 8 AM CDT

if [ $CURRENT_HOUR -ge $QUIET_START_UTC ] && [ $CURRENT_HOUR -lt $QUIET_END_UTC ]; then
    log "SKIPPED: Quiet hours (11 PM - 8 AM CDT)"
    exit 0
fi

log "=== Morning Briefing Started ==="

# Get system status
UPTIME=$(uptime -p 2>/dev/null || echo "unknown")
DISK_USAGE=$(df -h /storage --output=pcent 2>/dev/null | tail -1 | tr -d ' ')

# Check running services
GATEWAY_STATUS=$(openclaw gateway status 2>/dev/null | grep -i "running\|active" | head -1 || echo "unknown")
THEHUB_STATUS=$(curl -s http://localhost:3000/api/health 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "down")
XRP_BOT_COUNT=$(pgrep -c -f "bot_mc" 2>/dev/null || echo "0")

# Check calendar for today's goals
GOALS_TODAY=$(curl -s http://localhost:3000/api/calendar 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
goals = data.get('goals', [])
today = []
for g in goals:
    if g.get('status') in ['in-progress', 'not-started']:
        today.append(g.get('title', 'Untitled')[:30])
print(', '.join(today[:3]) if today else 'None')
" 2>/dev/null || echo "Unable to fetch")

# Get weather for Alexandria, MN
WEATHER=$(curl -s "https://api.open-meteo.com/v1/forecast?latitude=45.88&longitude=-95.38&current_weather=true&temperature_unit=fahrenheit" 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
cw = data.get('current_weather', {})
temp = cw.get('temperature', 'N/A')
wind = cw.get('windspeed', 'N/A')
print(f'{temp}°F, wind {wind} km/h')
" 2>/dev/null || echo "Weather unavailable")

# Build message
MESSAGE="🌅 Good morning, Yeatz!

📍 Weather (Alexandria, MN): $WEATHER

📊 System Status:
• Uptime: $UPTIME
• Disk: $DISK_USAGE used
• Gateway: $GATEWAY_STATUS
• The Hub: $THEHUB_STATUS
• XRP Bot: $XRP_BOT_COUNT instance(s) running

🎯 Today's Goals:
$GOALS_TODAY

💡 Project Idea: Review subagent architecture for better automation

Have a productive day!"

log "Sending briefing..."

# Send via Discord #alerts using OpenClaw
openclaw message send --channel discord --target 1486486418363650159 -m "$MESSAGE" 2>/dev/null

log "Briefing sent via Discord #alerts"

log "=== Morning Briefing Complete ==="
exit 0