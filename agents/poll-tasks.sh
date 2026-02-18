#!/bin/bash
# Auto-polling script for agents
# Checks for pending tasks and executes them

set -e

AGENT_NAME="$1"
if [ -z "$AGENT_NAME" ]; then
    echo "Usage: $0 <agent-name>"
    exit 1
fi

WORKSPACE="/home/yeatz/.openclaw/workspace"
PENDING_DIR="$WORKSPACE/tasks/pending"
IN_PROGRESS_DIR="$WORKSPACE/tasks/in-progress"
COMPLETED_DIR="$WORKSPACE/tasks/completed"
FAILED_DIR="$WORKSPACE/tasks/failed"
AGENT_DIR="$WORKSPACE/agents/$AGENT_NAME"

# Ensure directories exist
mkdir -p "$IN_PROGRESS_DIR" "$COMPLETED_DIR" "$FAILED_DIR"

# Find pending tasks for this agent
PENDING_TASKS=$(find "$PENDING_DIR" -name "${AGENT_NAME}-*.md" -type f 2>/dev/null || true)

if [ -z "$PENDING_TASKS" ]; then
    # No tasks found - silent exit
    exit 0
fi

# Process first pending task (one at a time)
TASK_FILE=$(echo "$PENDING_TASKS" | head -1)
TASK_BASENAME=$(basename "$TASK_FILE")

echo "[$AGENT_NAME] Processing task: $TASK_BASENAME"

# Extract task ID
TASK_ID=$(echo "$TASK_BASENAME" | sed 's/.*-//' | sed 's/.md$//')

# Move to in-progress
cp "$TASK_FILE" "$IN_PROGRESS_DIR/$TASK_BASENAME"
sed -i 's/status: pending/status: in-progress/' "$IN_PROGRESS_DIR/$TASK_BASENAME"
date -Iseconds | xargs -I {} sed -i "s/started_at: null/started_at: {}/" "$IN_PROGRESS_DIR/$TASK_BASENAME"
rm "$TASK_FILE"

# Load agent context
SOUL_FILE="$AGENT_DIR/SOUL.md"
AGENTS_FILE="$AGENT_DIR/AGENTS.md"

if [ ! -f "$SOUL_FILE" ]; then
    echo "Error: SOUL.md not found for $AGENT_NAME"
    exit 1
fi

# Execute via OpenClaw if available
if command -v openclaw >/dev/null 2>&1; then
    # Create a temporary task file with full context
    TEMP_TASK=$(mktemp)
    cat > "$TEMP_TASK" << EOF
You are $AGENT_NAME. Read your SOUL.md and AGENTS.md to understand your role.

$(cat "$SOUL_FILE" 2>/dev/null)
$(cat "$AGENTS_FILE" 2>/dev/null)

---

# Your Task

$(cat "$IN_PROGRESS_DIR/$TASK_BASENAME" | tail -n +1)

---

Execute this task as $AGENT_NAME:
1. Save any files to the workspace as needed
2. Commit your changes with git
3. Move the task to completed when done: $COMPLETED_DIR

Report completion when done.
EOF

    # Note: OpenClaw sessions spawn only supports 'main' agent
    # This script is designed to be called by cron which creates system events
    # The task will be processed by the main agent via cron-triggered system events
    echo "[$AGENT_NAME] Task queued. It will be processed by the system agent."
    rm -f "$TEMP_TASK"
    
    # Return to pending for next cron cycle
    mv "$IN_PROGRESS_DIR/$TASK_BASENAME" "$PENDING_DIR/"
    sed -i 's/status: in-progress/status: pending/' "$PENDING_DIR/$TASK_BASENAME"
    echo "[$AGENT_NAME] Task ready for system processing: $TASK_BASENAME"
else
    # Fallback: Just use agent-runner.sh
    cd "$WORKSPACE"
    ./agents/agent-runner.sh "$AGENT_NAME" "$IN_PROGRESS_DIR/$TASK_BASENAME" || {
        echo "[$AGENT_NAME] Task failed: $TASK_BASENAME"
        mv "$IN_PROGRESS_DIR/$TASK_BASENAME" "$FAILED_DIR/"
        sed -i 's/status: in-progress/status: failed/' "$FAILED_DIR/$TASK_BASENAME"
        exit 1
    }
fi
