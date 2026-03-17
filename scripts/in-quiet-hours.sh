#!/bin/bash
# Check if current time is within quiet hours
# Returns 0 (true) if in quiet hours, 1 (false) otherwise
# Usage: in-quiet-hours && echo "Quiet" || echo "Active"

# Quiet hours: 11 PM - 8 AM CDT (04:00 - 13:00 UTC)
QUIET_START_UTC=4
QUIET_END_UTC=13

CURRENT_HOUR=$(date -u +%H | sed 's/^0//')

if [ $CURRENT_HOUR -ge $QUIET_START_UTC ] && [ $CURRENT_HOUR -lt $QUIET_END_UTC ]; then
    exit 0  # In quiet hours
else
    exit 1  # Not in quiet hours
fi