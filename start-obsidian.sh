#!/bin/bash
# Start Obsidian with the workspace vault
# OpenClaw Memory System
export OBSIDIAN_VAULT="/storage/workspace"
~/Applications/Obsidian.AppImage --no-sandbox --appimage-extract-and-run "$OBSIDIAN_VAULT" &
echo "Obsidian started. Vault: $OBSIDIAN_VAULT"
echo "Local REST API will be available at: https://127.0.0.1:27124/"
echo "API Key: openclaw-spectre-2026"