#!/bin/bash
# Obsidian startup script for headless operation
# Uses Xvfb virtual display

export DISPLAY=:99
cd /home/spectre/Applications/obsidian-extracted/squashfs-root

# Start Xvfb if not running
if ! pgrep -f "Xvfb :99" > /dev/null; then
    Xvfb :99 -screen 0 1920x1080x24 -ac &
    sleep 2
fi

# Start Obsidian
./obsidian --no-sandbox --disable-gpu &

echo "Obsidian started on display :99"
echo "REST API: https://127.0.0.1:27124"