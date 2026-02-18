#!/bin/bash
# Real-time task watcher - SILENT VERSION
# Watches tasks/pending and executes immediately when tasks appear
# Zero output unless there's actual work

WORKSPACE="/home/yeatz/.openclaw/workspace"
PENDING_DIR="$WORKSPACE/tasks/pending"
IN_PROGRESS_DIR="$WORKSPACE/tasks/in-progress"
LOG_FILE="/tmp/task-watcher.log"

# Redirect all output to log file
exec 1>>"$LOG_FILE"
exec 2>>"$LOG_FILE"

echo "[$(date '+%H:%M:%S')] Starting real-time task watcher..."

# Ensure directories exist
mkdir -p "$PENDING_DIR" "$IN_PROGRESS_DIR"

# Process existing pending tasks first
for task_file in "$PENDING_DIR"/*.md; do
    [ -f "$task_file" ] || continue
    
    filename=$(basename "$task_file")
    
    # Skip test files and invalid files
    if [[ "$filename" == *"test"* ]] || ! head -1 "$task_file" | grep -q "^---"; then
        echo "[$(date '+%H:%M:%S')] Skipping invalid file: $filename"
        continue
    fi
    
    # Extract agent name
    AGENT_NAME=$(echo "$filename" | cut -d'-' -f1)
    
    # Move to in-progress
    cp "$task_file" "$IN_PROGRESS_DIR/$filename"
    sed -i 's/status: pending/status: in-progress/' "$IN_PROGRESS_DIR/$filename"
    date -Iseconds | xargs -I {} sed -i "s/started_at: null/started_at: {}/" "$IN_PROGRESS_DIR/$filename"
    rm "$task_file"
    
    echo "[$(date '+%H:%M:%S')] Queued task for $AGENT_NAME: $filename"
done

# Use inotifywait to watch for new files
if command -v inotifywait >/dev/null 2>&1; then
    inotifywait -m "$PENDING_DIR" -e create -e moved_to --format '%f' |
    while read filename; do
        [ -f "$PENDING_DIR/$filename" ] || continue
        
        # Skip test files and invalid files
        if [[ "$filename" != *.md ]] || [[ "$filename" == *"test"* ]]; then
            continue
        fi
        
        # Validate YAML frontmatter
        if ! head -1 "$PENDING_DIR/$filename" | grep -q "^---"; then
            echo "[$(date '+%H:%M:%S')] Skipping invalid file: $filename"
            continue
        fi
        
        # Extract agent name
        AGENT_NAME=$(echo "$filename" | cut -d'-' -f1)
        
        # Move to in-progress  
        cp "$PENDING_DIR/$filename" "$IN_PROGRESS_DIR/$filename"
        sed -i 's/status: pending/status: in-progress/' "$IN_PROGRESS_DIR/$filename"
        date -Iseconds | xargs -I {} sed -i "s/started_at: null/started_at: {}/" "$IN_PROGRESS_DIR/$filename"
        rm "$PENDING_DIR/$filename"
        
        echo "[$(date '+%H:%M:%S')] Queued task for $AGENT_NAME: $filename"
        
        # Spawn OpenClaw session for execution (silent)
        if command -v openclaw >/dev/null 2>&1; then
            openclaw run --file "$IN_PROGRESS_DIR/$filename" \
                --label "agent-$AGENT_NAME-task" \
                --timeout 600 \>> "$LOG_FILE" 2>&1 &
        fi
    done
else
    echo "[$(date '+%H:%M:%S')] inotifywait not installed. Using polling fallback."
    
    # Simple polling fallback
    while true; do
        for task_file in "$PENDING_DIR"/*.md; do
            [ -f "$task_file" ] || continue
            
            filename=$(basename "$task_file")
            
            # Skip test files
            if [[ "$filename" == *"test"* ]] || ! head -1 "$task_file" | grep -q "^---"; then
                continue
            fi
            
            AGENT_NAME=$(echo "$filename" | cut -d'-' -f1)
            
            cp "$task_file" "$IN_PROGRESS_DIR/$filename"
            sed -i 's/status: pending/status: in-progress/' "$IN_PROGRESS_DIR/$filename"
            date -Iseconds | xargs -I {} sed -i "s/started_at: null/started_at: {}/" "$IN_PROGRESS_DIR/$filename"
            rm "$task_file"
            
            echo "[$(date '+%H:%M:%S')] Queued task for $AGENT_NAME: $filename"
            
            if command -v openclaw >/dev/null 2>&1; then
                openclaw run --file "$IN_PROGRESS_DIR/$filename" \
                    --label "agent-$AGENT_NAME-task" \
                    --timeout 600 \>> "$LOG_FILE" 2>&1 &
            fi
        done
        sleep 5
    done
fi
