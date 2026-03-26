#!/bin/bash
# Reminder: Review Subagents at 7 PM CDT (00:00 UTC)
# Sends Discord notification to #alerts

MESSAGE="⏰ 7 PM CDT Reminder

Review Subagents Architecture:
• Heimdall (Coordinator)
• Huginn (Scout)
• Tyr (Strategist)
• Sindri (Smith)
• Njord (Treasurer)
• Thor (Executor)
• Mimir (Operator)

Decide: Agent separation vs single-bot setup.
Reply with 'done' when complete."

# Send via OpenClaw to Discord #alerts
openclaw message send --channel discord --target 1486486418363650159 -m "$MESSAGE" 2>/dev/null