#!/bin/bash
#
# sync-hub-updates.sh
# Processes pending updates from The Hub update queue
# Called by Mimir as part of inter-agent coordination
#

set -euo pipefail

# Paths
UPDATES_FILE="/storage/workspace/thehub/api/updates.json"
LOG_FILE="/storage/workspace/agents/mimir/hub-sync.log"
HUB_DATA_DIR="/storage/workspace/thehub/api"

# Ensure directories exist
mkdir -p "$(dirname "$LOG_FILE")"
mkdir -p "$HUB_DATA_DIR"

# Logging function
log() {
    local level="$1"
    local message="$2"
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "[$timestamp] [$level] $message" >> "$LOG_FILE"
}

# Initialize updates file if missing
if [[ ! -f "$UPDATES_FILE" ]]; then
    echo '{"pending": []}' > "$UPDATES_FILE"
    log "INFO" "Initialized empty updates.json"
fi

# Process APK version update
process_apk_update() {
    local update="$1"
    local version
    version=$(echo "$update" | jq -r '.version // "unknown"')
    local changelog
    changelog=$(echo "$update" | jq -r '.changelog // ""')
    
    log "INFO" "Processing APK update to version $version"
    
    # Update the version file
    echo "{\"version\": \"$version\", \"updated\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\"}" \
        > "$HUB_DATA_DIR/apk-version.json"
    
    log "SUCCESS" "APK version updated to $version"
    return 0
}

# Process asset refresh
process_asset_refresh() {
    local update="$1"
    local asset_type
    asset_type=$(echo "$update" | jq -r '.asset_type // "unknown"')
    local asset_id
    asset_id=$(echo "$update" | jq -r '.asset_id // "unknown"')
    
    log "INFO" "Processing asset refresh for $asset_type/$asset_id"
    
    # Touch the assets manifest to trigger refresh signal
    touch "$HUB_DATA_DIR/.assets_refresh"
    
    log "SUCCESS" "Asset refresh signaled for $asset_type/$asset_id"
    return 0
}

# Process status change
process_status_change() {
    local update="$1"
    local service
    service=$(echo "$update" | jq -r '.service // "unknown"')
    local new_status
    new_status=$(echo "$update" | jq -r '.new_status // "unknown"')
    local old_status
    old_status=$(echo "$update" | jq -r '.old_status // "unknown"')
    
    log "INFO" "Processing status change for $service: $old_status -> $new_status"
    
    # Update the status file
    local status_file="$HUB_DATA_DIR/services-status.json"
    
    if [[ -f "$status_file" ]]; then
        # Update existing status entry
        local temp_file
        temp_file=$(mktemp)
        jq --arg svc "$service" --arg status "$new_status" \
            '.[$svc] = $status' "$status_file" > "$temp_file" \
            && mv "$temp_file" "$status_file"
    else
        # Create new status file
        echo "{\"$service\": \"$new_status\"}" > "$status_file"
    fi
    
    log "SUCCESS" "Status updated for $service: $new_status"
    return 0
}

# Main processing
main() {
    log "INFO" "Starting hub sync process"
    
    # Check for pending updates
    local pending_count
    pending_count=$(jq '.pending | length' "$UPDATES_FILE" 2>/dev/null || echo "0")
    
    if [[ "$pending_count" -eq 0 ]]; then
        log "INFO" "No pending updates"
        exit 0
    fi
    
    log "INFO" "Found $pending_count pending updates"
    
    local processed=0
    local failed=0
    
    # Process each update
    local updates
    updates=$(jq -c '.pending[]' "$UPDATES_FILE")
    
    while IFS= read -r update; do
        local update_type
        update_type=$(echo "$update" | jq -r '.type // "unknown"')
        
        case "$update_type" in
            "apk_update")
                if process_apk_update "$update"; then
                    ((processed++))
                else
                    log "ERROR" "Failed to process APK update"
                    ((failed++))
                fi
                ;;
            "asset_refresh")
                if process_asset_refresh "$update"; then
                    ((processed++))
                else
                    log "ERROR" "Failed to process asset refresh"
                    ((failed++))
                fi
                ;;
            "status_change")
                if process_status_change "$update"; then
                    ((processed++))
                else
                    log "ERROR" "Failed to process status change"
                    ((failed++))
                fi
                ;;
            *)
                log "WARN" "Unknown update type: $update_type"
                ((failed++))
                ;;
        esac
    done <<< "$updates"
    
    # Clear processed updates from queue
    echo '{"pending": []}' > "$UPDATES_FILE"
    
    log "INFO" "Cleared update queue"
    log "SUCCESS" "Processed: $processed, Failed: $failed"
    
    # Exit with failure code if any updates failed
    if [[ "$failed" -gt 0 ]]; then
        log "ERROR" "Completed with errors"
        exit 1
    fi
    
    exit 0
}

main "$@"