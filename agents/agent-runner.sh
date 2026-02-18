#!/bin/bash
# Agent Runner - Wrapper for OpenClaw agent spawning
# Usage: ./agent-runner.sh <agent-name> <task-file>

set -e

AGENT_NAME="$1"
TASK_FILE="$2"

if [ -z "$AGENT_NAME" ] || [ -z "$TASK_FILE" ]; then
    echo "Usage: $0 <agent-name> <task-file>"
    echo "Example: $0 pixel tasks/pending/pixel-001.md"
    exit 1
fi

WORKSPACE="/home/yeatz/.openclaw/workspace"
AGENT_DIR="$WORKSPACE/agents/$AGENT_NAME"

if [ ! -d "$AGENT_DIR" ]; then
    echo "Error: Agent '$AGENT_NAME' not found at $AGENT_DIR"
    exit 1
fi

if [ ! -f "$TASK_FILE" ]; then
    echo "Error: Task file not found: $TASK_FILE"
    exit 1
fi

# Load agent SOUL.md for context
SOUL_FILE="$AGENT_DIR/SOUL.md"
AGENTS_FILE="$AGENT_DIR/AGENTS.md"

# Create a prompt that includes agent context + task
TEMP_PROMPT=$(mktemp)
cat > "$TEMP_PROMPT" << EOF
# Agent Context

You are $AGENT_NAME. Read your SOUL.md and AGENTS.md for your identity and capabilities:

$(cat "$SOUL_FILE" 2>/dev/null || echo "# No SOUL.md found")

$(cat "$AGENTS_FILE" 2>/dev/null || echo "# No AGENTS.md found")

---

# Your Task

$(cat "$TASK_FILE")

---

Execute this task as $AGENT_NAME. Save your work to the workspace and report completion.
EOF

# Execute task - since we can't spawn sub-agents directly, 
# we'll use the sessions_spawn tool through a temporary script
cd "$WORKSPACE"

# Create execution marker file to indicate this task is being processed
MARKER_FILE="/tmp/agent-$AGENT_NAME-$(basename $TASK_FILE).running"
touch "$MARKER_FILE"

# Log the execution request
echo "[$(date '+%H:%M:%S')] Agent $AGENT_NAME requested execution"
echo "Task: $TASK_FILE"
echo "Status: QUEUED_FOR_MANUAL_EXECUTION"

# For now, tasks need manual execution or cron-based processing
# This script prepares the task but doesn't auto-execute

echo ""
echo "═══════════════════════════════════════════"
echo "🤖 AGENT: $AGENT_NAME"
echo "📋 TASK: $(basename $TASK_FILE)"
echo "⏳ STATUS: Ready for execution"
echo "═══════════════════════════════════════════"
echo ""
echo "Task prepared. Execute via:"
echo "  openclaw agent --message \"$(cat $TEMP_PROMPT | head -c 200)...\" --label agent-$AGENT_NAME"
echo ""

# Cleanup
rm -f "$TEMP_PROMPT" "$MARKER_FILE"
