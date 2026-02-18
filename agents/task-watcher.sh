#!/bin/bash
# Real-time task watcher
WORKSPACE="/home/yeatz/.openclaw/workspace"
PENDING_DIR="$WORKSPACE/tasks/pending"
TRAINING_DIR="$WORKSPACE/tasks/training"
LOG_FILE="/tmp/task-watcher.log"
EXECUTOR="$WORKSPACE/agents/task-executor.sh"

log_msg() {
    echo "[$(date '+%H:%M:%S')] $1" >> "$LOG_FILE"
}

# Initial run
log_msg "Starting task watcher..."
log_msg "Running initial task scan..."
"$EXECUTOR" >> "$LOG_FILE" 2>&1

# Watch for file changes
if command -v inotifywait >/dev/null 2>&1; then
    log_msg "Using inotifywait for monitoring..."
    
    inotifywait -m "$PENDING_DIR" "$TRAINING_DIR" \
        -e create -e moved_to --format '%w%f' 2>&1 |
    while read filepath; do
        [ -f "$filepath" ] || continue
        
        filename=$(basename "$filepath")
        
        # Skip non-md files and test files
        if [[ "$filename" != *.md ]] || [[ "$filename" == *"test"* ]]; then
            continue
        fi
        
        log_msg "New file: $filename"
        
        # Run executor
        "$EXECUTOR" >> "$LOG_FILE" 2>&1
        
        log_msg "Execution cycle done"
    done
else
    log_msg "Using polling fallback..."
    while true; do
        "$EXECUTOR" >> "$LOG_FILE" 2>&1
        sleep 10
    done
fi