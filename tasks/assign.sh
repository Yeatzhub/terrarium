#!/bin/bash
# Assign a task to an agent
# Usage: ./assign.sh <agent-name> "Task description"

set -e

AGENT_NAME="$1"
TASK_DESCRIPTION="$2"
TASK_ID="$(date +%Y%m%d-%H%M%S)-$(openssl rand -hex 4 2>/dev/null || echo $RANDOM)"

if [ -z "$AGENT_NAME" ] || [ -z "$TASK_DESCRIPTION" ]; then
    echo "Usage: $0 <agent-name> \"Task description\""
    echo "Agents: pixel, ghost, oracle, synthesis"
    exit 1
fi

BASE_DIR="/home/yeatz/.openclaw/workspace/tasks"
mkdir -p "$BASE_DIR/pending"
mkdir -p "$BASE_DIR/in-progress"
mkdir -p "$BASE_DIR/completed"
mkdir -p "$BASE_DIR/failed"

TASK_FILE="$BASE_DIR/pending/${AGENT_NAME}-${TASK_ID}.md"

cat > "$TASK_FILE" << EOF
---
assigned_to: ${AGENT_NAME}
task_id: ${TASK_ID}
status: pending
created_at: $(date -Iseconds)
started_at: null
completed_at: null
---

# Task

${TASK_DESCRIPTION}

EOF

echo "✓ Task assigned to ${AGENT_NAME}"
echo "  Task ID: ${TASK_ID}"
echo "  File: ${TASK_FILE}"
echo ""
echo "To execute: ./agents/agent-runner.sh ${AGENT_NAME} ${TASK_FILE}"
