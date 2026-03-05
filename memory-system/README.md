# Memory System - Quick Reference

## Structure

```
/storage/workspace/memory-system/
├── HOT_MEMORY.md      # Always-loaded global rules
├── CONTEXT_MEMORY.md  # Project/domain-specific rules
├── ARCHIVE.md         # Inactive/stale patterns
├── CORRECTIONS.md     # Log of all corrections
├── MAINTENANCE.md     # Weekly review tracker
└── README.md          # This file
```

## How It Works

### 1. User Corrects Me
```
User: "No, do it this way..."
```
→ I log it in CORRECTIONS.md with context

### 2. Pattern Detection
If same correction appears 3 times:
→ I ask: "I've been corrected on X 3 times. Should this be a permanent rule?"
→ Options: Global / Domain / Project

### 3. Rule Application
When I apply a learned rule, I cite it:
```
Applying rule: HOT_MEMORY#paper-trading-default
"Paper trading default (live requires explicit YES)"
```

### 4. Weekly Maintenance
Every 7 days I:
- Deduplicate rules
- Move stale items to archive
- Send user a digest

## User Commands

| Command | Action |
|---------|--------|
| "forget X" | Delete X everywhere, confirm |
| "forget everything" | Wipe memory system, start fresh |
| "show memory" | Display current rules |
| "memory review" | Force maintenance review |

## Safety Rules

**NEVER store:**
- Passwords, tokens, API keys
- Financial account numbers or balances (personal)
- Health information
- Private info about other people
- Secrets of any kind

**ALWAYS ask before:**
- Making high-impact workflow changes
- Promoting a correction to permanent rule

## Current State

- Active global rules: 0
- Projects tracked: 2
- Domains tracked: 1
- Corrections logged: 0
- Status: **Fresh system, learning from you**