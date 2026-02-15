#!/bin/bash
# cleanup_old_memory.sh - Remove memory files older than 7 days

MEMORY_DIR="$HOME/.openclaw/workspace/memory"

if [ -d "$MEMORY_DIR" ]; then
    # Count files to be removed
    COUNT=$(find "$MEMORY_DIR" -name "*.md" -mtime +7 2>/dev/null | wc -l)
    
    if [ "$COUNT" -gt 0 ]; then
        echo "Removing $COUNT old memory files (7+ days)..."
        find "$MEMORY_DIR" -name "*.md" -mtime +7 -exec rm {} \;
        echo "Cleanup complete."
    else
        echo "No old memory files to remove."
    fi
else
    echo "Memory directory not found."
fi