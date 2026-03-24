#!/bin/bash
# Obsidian REST API Tunnel
# Forwards port 27125 (external) to 27124 (localhost)

TUNNEL_PORT=27125
TARGET_PORT=27124

# Kill existing tunnel
pkill -f "socat.*${TUNNEL_PORT}" 2>/dev/null

sleep 1

# Start tunnel
nohup socat TCP-LISTEN:${TUNNEL_PORT},fork,reuseaddr TCP:127.0.0.1:${TARGET_PORT} > /var/log/obsidian-tunnel.log 2>&1 &

echo "Obsidian tunnel running on port ${TUNNEL_PORT}"