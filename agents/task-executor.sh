#!/bin/bash
# Task Executor - Processes pending tasks and executes via OpenClaw
WORKSPACE="/home/yeatz/.openclaw/workspace"
PENDING_DIR="$WORKSPACE/tasks/pending"
TRAINING_DIR="$WORKSPACE/tasks/training"
IN_PROGRESS_DIR="$WORKSPACE/tasks/in-progress"
COMPLETED_DIR="$WORKSPACE/tasks/completed"
FAILED_DIR="$WORKSPACE/tasks/failed"
LOG_FILE="/tmp/task-watcher.log"
AGENTS_DIR="$WORKSPACE/agents"

log() {
    echo "[$(date '+%H:%M:%S')] $1" >> "$LOG_FILE"
}

move_completed() {
    local task_file="$1"
    local filename=$(basename "$task_file")
    sed -i 's/status: in-progress/status: completed/' "$task_file"
    date -Iseconds | xargs -I {} sed -i "s/completed_at: null/completed_at: {}/" "$task_file"
    mv "$task_file" "$COMPLETED_DIR/"
    log "[COMPLETED] $filename"
}

move_failed() {
    local task_file="$1"
    local filename=$(basename "$task_file")
    sed -i 's/status: in-progress/status: failed/' "$task_file"
    mv "$task_file" "$FAILED_DIR/"
    log "[FAILED] $filename"
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
    log "[DELEGATION] Created task for $agent"
}

process_task() {
    local task_file="$1"
    local filename=$(basename "$task_file")
    
    # Skip invalid
    if [[ "$filename" == *"test"* ]] || ! head -1 "$task_file" | grep -q "^---"; then
        log "Skipping invalid: $filename"
        return
    fi
    
    local agent_name=$(echo "$filename" | cut -d'-' -f1)
    
    log "[$agent_name] Processing: $filename"
    
    # Move to in-progress
    local IN_PROGRESS_FILE="$IN_PROGRESS_DIR/$filename"
    cp "$task_file" "$IN_PROGRESS_FILE"
    sed -i 's/status: pending/status: in-progress/' "$IN_PROGRESS_FILE"
    date -Iseconds | xargs -I {} sed -i "s/started_at: null/started_at: {}/" "$IN_PROGRESS_FILE"
    rm "$task_file"
    
    # Handle delegation for synthesis
    if [[ "$agent_name" == "synthesis" ]]; then
        # Check for delegation markers
        local DELEGATION_COUNT=0
        DELEGATION_COUNT=$(grep -cE "^- \[ \] \*\*[A-Za-z]+\*\*:" "$IN_PROGRESS_FILE" 2>/dev/null || true)
        
        if [ "${DELEGATION_COUNT:-0}" -gt 0 ] 2>/dev/null; then
            
            # Parse delegation - match "- [ ] **Agent**: task"
            grep -E "^- \[ \] \*\*[A-Za-z]+\*\*:" "$IN_PROGRESS_FILE" 2>/dev/null | while read line; do
                local SUB_AGENT=$(echo "$line" | grep -oE "\*\*[A-Za-z]+\*\*" | head -1 | tr -d '*' | tr '[:upper:]' '[:lower:]')
                local SUB_TASK=$(echo "$line" | sed -E 's/^- \[ \] \*\*[A-Za-z]+\*\*:\s*//')
                
                if [[ -n "$SUB_AGENT" && -n "$SUB_TASK" ]]; then
                    create_subtask "$SUB_AGENT" "$SUB_TASK" "$filename"
                fi
            done
        fi
    fi
    
    # Mark for execution - since we can't directly spawn agents,
    # we prepare the task and rely on the main agent (me) to execute
    log "[$agent_name] Task ready for execution: $filename"
    
    # For tasks that need immediate execution, we create a notification
    echo ""
    echo "═══════════════════════════════════════════════"
    echo "🎯 TASK READY FOR EXECUTION"
    echo "Agent: $agent_name"
    echo "Task: $filename"
    echo "Location: $IN_PROGRESS_FILE"
    echo "═══════════════════════════════════════════════"
    echo ""
}

# Ensure directories exist
mkdir -p "$PENDING_DIR" "$TRAINING_DIR" "$IN_PROGRESS_DIR" "$COMPLETED_DIR" "$FAILED_DIR"

log "=== Task Processor Starting ==="

# Move training to pending if no real tasks
if ! ls "$PENDING_DIR"/*.md 2>/dev/null | grep -q .; then
    if ls "$TRAINING_DIR"/synthesis-*.md 2>/dev/null | grep -q .; then
        log "[TRAINING] Moving training to pending"
        for training in "$TRAINING_DIR"/synthesis-*.md; do
            [ -f "$training" ] || continue
            filename=$(basename "$training")
            mv "$training" "$PENDING_DIR/$filename"
            log "[TRAINING] Queued: $filename"
        done
    fi
fi

# Process all pending tasks
TASK_COUNT=0
for task_file in "$PENDING_DIR"/*.md; do
    [ -f "$task_file" ] || continue
    process_task "$task_file"
    TASK_COUNT=$((TASK_COUNT + 1))
done

log "=== Processed $TASK_COUNT tasks ==="
