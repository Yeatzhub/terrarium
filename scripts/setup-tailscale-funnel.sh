#!/bin/bash
# Tailscale Funnel Configuration for Thor Webhook

# Reset current serve config
tailscale serve reset

# Route webhook paths to Caddy (port 80)
tailscale serve --bg /webhook/tradingview http://127.0.0.1:80
tailscale serve --bg /health http://127.0.0.1:80

# Route everything else to OpenClaw gateway (port 18789)
tailscale serve --bg / http://127.0.0.1:18789

echo "Tailscale Funnel configured!"
echo "Webhook URL: https://yeatzai.tailbf40f7.ts.net/webhook/tradingview"