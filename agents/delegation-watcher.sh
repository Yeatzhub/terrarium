#!/bin/bash
# Enhanced task watcher with Synthesis delegation
# Handles real tasks, training, and proper delegation

WORKSPACE="/home/yeatz/.openclaw/workspace"
PENDING_DIR="$WORKSPACE/tasks/pending"
TRAINING_DIR="$WORKSPACE/tasks/training"
IN_PROGRESS_DIR="$WORKSPACE/tasks/in-progress"
COMPLETED_DIR="$WORKSPACE/tasks/completed"
LOG_FILE="/tmp/task-watcher.log"

log() {
    echo "[$(date '+%H:%M:%S')] $1" >> "$LOG_FILE"
}

process_task() {
    local task_file="$1"
    local filename=$(basename "$task_file")
    
    # Skip invalid files
    if [[ "$filename" == *"test"* ]] || ! head -1 "$task_file" | grep -q "^---"; then
        log "Skipping invalid file: $filename"
        return
    fi
    
    local agent_name=$(echo "$filename" | cut -d'-' -f1)
    
    # Special handling for synthesis
    if [[ "$agent_name" == "synthesis" ]]; then
        handle_synthesis_task "$task_file" "$filename"
    else
        handle_regular_task "$task_file" "$filename" "$agent_name"
    fi
}

handle_synthesis_task() {
    local task_file="$1"
    local filename="$2"
    
    log "[SYNTHESIS] Processing: $filename"
    
    # Check if this is a delegation task
    if grep -q "# Task" "$task_file" && grep -i -E "(delegate|assign to|route to)" "$task_file" > /dev/null; then
        log "[SYNTHESIS] Delegation detected - parsing subtasks"
        
        # Parse and create subtasks for other agents
        # Look for patterns like "- [ ] Pixel: ..." or "Ghost: ..."
        grep -iE "^- \[ \] (Pixel|Ghost|Oracle):" "$task_file" | while read line; do
            sub_agent=$(echo "$line" | grep -oE "(Pixel|Ghost|Oracle)" | head -1 | tr '[:upper:]' '[:lower:]')
            sub_task=$(echo "$line" | sed 's/^- \[ \] [A-Za-z]*: *//')
            
            if [[ -n "$sub_agent" && -n "$sub_task" ]]; then
                create_subtask "$sub_agent" "$sub_task" "$filename"
            fi
        done
    fi
    
    # Move to in-progress
    cp "$task_file" "$IN_PROGRESS_DIR/$filename"
    sed -i 's/status: pending/status: in-progress/' "$IN_PROGRESS_DIR/$filename"
    date -Iseconds | xargs -I {} sed -i "s/started_at: null/started_at: {}/" "$IN_PROGRESS_DIR/$filename"
    rm "$task_file"
    
    log "[SYNTHESIS] Task queued: $filename"
}

create_subtask() {
    local agent="$1"
    local description="$2"
    local parent_task="$3"
    local task_id="$(date +%s)-$(cat /dev/urandom | tr -dc 'a-z0-9' | head -c 8)"
    
    cat > "$PENDING_DIR/${agent}-${task_id}.md" << EOF
---
assigned_to: $agent
task_id: $task_id
status: pending
created_at: $(date -Iseconds)
started_at: null
completed_at: null
parent_task: $parent_task
---

# Task

$description

*Delegated by Synthesis from: $parent_task*
EOF

    log "[DELEGATION] Created task for $agent: $description"
}

handle_regular_task() {
    local task_file="$1"
    local filename="$2"
    local agent="$3"
    
    log "[$agent] Processing: $filename"
    
    # Move to in-progress
    cp "$task_file" "$IN_PROGRESS_DIR/$filename"
    sed -i 's/status: pending/status: in-progress/' "$IN_PROGRESS_DIR/$filename"
    date -Iseconds | xargs -I {} sed -i "s/started_at: null/started_at: {}/" "$IN_PROGRESS_DIR/$filename"
    rm "$task_file"
    
    log "[$agent] Task queued: $filename"
}

# Check pending tasks
for task_file in "$PENDING_DIR"/*.md; do
    [ -f "$task_file" ] || continue
    process_task "$task_file"
done

# If no real tasks and it's Synthesis, check for training
if ! ls "$PENDING_DIR"/synthesis-*.md 2>/dev/null | grep -q .; then
    # Check for training tasks
    for training_file in "$TRAINING_DIR"/synthesis-*.md; do
        [ -f "$training_file" ] || continue
        
        filename=$(basename "$training_file")
        log "[TRAINING] Synthesis starting: $filename"
        
        # Move to pending to be processed
        cp "$training_file" "$PENDING_DIR/$filename"
        rm "$training_file"
        
        # Process immediately
        process_task "$PENDING_DIR/$filename"
    done
fi
