#!/bin/bash
# Reminder: Review Subagents at 7 PM CDT (00:00 UTC)
# Sends Telegram notification

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

curl -s -X POST "https://api.telegram.org/bot8621394908:AAEDXUoihhq48gQ06EG5pzIO2DHZdUaYdn0/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{\"chat_id\": \"8464154608\", \"text\": \"$MESSAGE\"}" > /dev/null 2>&1