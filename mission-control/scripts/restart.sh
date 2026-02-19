#!/bin/bash
# Automated Mission Control Restart with Port Cleanup

PORT=3000

echo "🔄 Restarting Mission Control..."

# Kill processes on port 3000
echo "📡 Clearing port $PORT..."
for pid in $(lsof -ti:$PORT 2>/dev/null); do
    echo "  Killing PID $pid"
    kill -9 $pid 2>/dev/null
done

# Wait for port to clear
sleep 2

# Double check
if ss -tlnp | grep -q ":$PORT"; then
    echo "❌ Port $PORT still in use, force killing..."
    fuser -k $PORT/tcp 2>/dev/null || true
    sleep 2
fi

echo "🏗️  Rebuilding..."
cd ~/.openclaw/workspace/mission-control
npm run build 2>&1 | tail -10

echo "🚀 Starting server..."
npm start 2>&1