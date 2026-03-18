# Learning Template

Every learning file should follow this structure:

```markdown
# Learning: [Short Title - What was discovered/fixed]

**Date:** YYYY-MM-DD
**Agent:** [Which agent wrote this]
**Type:** discovery | error | success | optimization | decision
**Risk:** low | medium | high
**Status:** proposed | approved | implemented | archived

## What Happened
[One paragraph description of the event/discovery]

## Context
[Background, environment, why it matters]

## Key Insight
[The core learning - what's the takeaway]

## Proposed Action
[What should be done about it - be specific]

## Implementation
[If approved, how was it implemented]

## Files Affected
[List of files that were changed]

## Tags
[space-separated tags for searchability]
```

---

## Example

```markdown
# Learning: XRP VPN Disconnection Pattern

**Date:** 2026-03-17
**Agent:** Thor
**Type:** error
**Risk:** medium
**Status:** implemented

## What Happened
Bot lost VPN connection 3 times in 24 hours, causing trade failures.

## Context
Dubai VPN container restarts unexpectedly. Bot continued running but couldn't reach Pionex API.

## Key Insight
VPN health check must be added to Mimir's service monitor with auto-restart.

## Proposed Action
Add VPN container health check to Mimir. Restart on failure.

## Implementation
- Added `/scripts/vpn-health-check.sh`
- Added cron job every 5 minutes
- Mimir monitors and restarts

## Files Affected
- `/scripts/vpn-health-check.sh` (new)
- `/storage/workspace/agents/mimir/SKILL.md` (updated)

## Tags
vpn xrp bot connectivity infrastructure
```