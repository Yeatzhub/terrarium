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

# Use OpenClaw to run the agent
cd "$WORKSPACE"

# Option 1: Use openclaw CLI if available
if command -v openclaw >/dev/null 2>&1; then
    openclaw run --file "$TEMP_PROMPT" --label "agent-$AGENT_NAME-$(date +%s)"
else
    # Option 2: Direct API call to gateway
    curl -s -X POST http://localhost:18789/api/v1/run \
        -H "Content-Type: application/json" \
        -d "{\"prompt\":$(cat "$TEMP_PROMPT" | jq -R -s .),\"label\":\"agent-$AGENT_NAME\",\"workspace\":\"$WORKSPACE\"}" 2>/dev/null || echo "API call failed"
fi

# Cleanup
rm -f "$TEMP_PROMPT"

echo ""
echo "Agent $AGENT_NAME completed task: $TASK_FILE"
