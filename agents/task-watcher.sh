#!/bin/bash
# Real-time task watcher using inotify
# Watches tasks/pending and executes immediately when tasks appear

WORKSPACE="/home/yeatz/.openclaw/workspace"
PENDING_DIR="$WORKSPACE/tasks/pending"

echo "Starting real-time task watcher..."
echo "Watching: $PENDING_DIR"
echo "Press Ctrl+C to stop"

# Ensure directory exists
mkdir -p "$PENDING_DIR"

# Use inotifywait to watch for new files
if command -v inotifywait >/dev/null 2>&1; then
    inotifywait -m "$PENDING_DIR" -e create -e moved_to --format '%f' |
    while read filename; do
        if [[ "$filename" == *.md ]] && [[ "$filename" != *"test"* ]]; then
            # Validate task file has proper frontmatter
            if head -1 "$PENDING_DIR/$filename" | grep -q "^---"; then
                # Extract agent name from filename (synthesis-xyz.md -> synthesis)
                AGENT_NAME=$(echo "$filename" | cut -d'-' -f1)
                
                echo ""
                echo "═══ 🎯 TASK DETECTED ══════════════"
                echo "Agent: $AGENT_NAME"
                echo "File: $filename"
                echo "Time: $(date '+%H:%M:%S')"
                echo "═══════════════════════════════════"
                echo ""
                
                # Execute the task
                "$WORKSPACE/agents/poll-tasks.sh" "$AGENT_NAME"
            else
                echo "⚠️  Skipping invalid task file: $filename (no YAML frontmatter)"
            fi
        fi
    done
else
    echo "Error: inotifywait not installed. Install with: sudo apt-get install inotify-tools"
    exit 1
fi
