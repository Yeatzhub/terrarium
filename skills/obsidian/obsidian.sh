#!/bin/bash
# Obsidian REST API wrapper
# Interact with Obsidian vault via Local REST API plugin

set -e

OBSIDIAN_HOST="https://100.112.56.61:27125"
VAULT_ROOT="/storage/workspace"
DATA_FILE="$VAULT_ROOT/.obsidian/plugins/local-rest-api/data.json"

# Get API key from config
get_api_key() {
    if [[ -f "$DATA_FILE" ]]; then
        grep -o '"apiKey"[[:space:]]*:[[:space:]]*"[^"]*"' "$DATA_FILE" | cut -d'"' -f4
    else
        echo "openclaw-spectre-2026"
    fi
}

API_KEY=$(get_api_key)

# Common curl options
curl_opts="-k -s -H \"Authorization: Bearer $API_KEY\""

# Commands
cmd_read() {
    local path="$1"
    curl -k -s -H "Authorization: Bearer $API_KEY" \
        "${OBSIDIAN_HOST}/vault/${path}"
}

cmd_write() {
    local path="$1"
    local content="$2"
    curl -k -s -X PUT \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: text/markdown" \
        --data "$content" \
        "${OBSIDIAN_HOST}/vault/${path}"
}

cmd_append() {
    local path="$1"
    local heading="$2"
    local content="$3"
    curl -k -s -X PATCH \
        -H "Authorization: Bearer $API_KEY" \
        -H "Operation: append" \
        -H "Target-Type: heading" \
        -H "Target: $heading" \
        -H "Content-Type: text/plain" \
        --data "$content" \
        "${OBSIDIAN_HOST}/vault/${path}"
}

cmd_prepend() {
    local path="$1"
    local heading="$2"
    local content="$3"
    curl -k -s -X PATCH \
        -H "Authorization: Bearer $API_KEY" \
        -H "Operation: prepend" \
        -H "Target-Type: heading" \
        -H "Target: $heading" \
        -H "Content-Type: text/plain" \
        --data "$content" \
        "${OBSIDIAN_HOST}/vault/${path}"
}

cmd_patch() {
    local path="$1"
    local field="$2"
    local value="$3"
    curl -k -s -X PATCH \
        -H "Authorization: Bearer $API_KEY" \
        -H "Operation: replace" \
        -H "Target-Type: frontmatter" \
        -H "Target: $field" \
        -H "Content-Type: application/json" \
        --data "\"$value\"" \
        "${OBSIDIAN_HOST}/vault/${path}"
}

cmd_list() {
    local path="${1:-}"
    curl -k -s -H "Authorization: Bearer $API_KEY" \
        "${OBSIDIAN_HOST}/vault/${path}" | jq -r '.files[]? // .name? // .'
}

cmd_query() {
    local dql="$1"
    curl -k -s -X POST \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/vnd.olrapi.dataview.dql+txt" \
        --data "$dql" \
        "${OBSIDIAN_HOST}/search/"
}

cmd_search() {
    local query="$1"
    curl -k -s -X POST \
        -H "Authorization: Bearer $API_KEY" \
        "https://127.0.0.1:27124/search/simple/?query=$(echo "$query" | sed 's/ /+/g')"
}

cmd_daily() {
    curl -k -s -H "Authorization: Bearer $API_KEY" \
        "${OBSIDIAN_HOST}/periodic/daily/"
}

cmd_weekly() {
    curl -k -s -H "Authorization: Bearer $API_KEY" \
        "${OBSIDIAN_HOST}/periodic/weekly/"
}

cmd_status() {
    curl -k -s "${OBSIDIAN_HOST}/" | jq . || curl -k -s "${OBSIDIAN_HOST}/"
}

# Usage
usage() {
    cat << EOF
Obsidian REST API wrapper

Usage:
    obsidian read <path>                    Read a note
    obsidian write <path> --content <text>  Create/overwrite note
    obsidian append <path> --heading <h> --content <text>  Append to heading
    obsidian prepend <path> --heading <h> --content <text> Prepend to heading
    obsidian patch <path> --field <f> --value <v>          Patch frontmatter
    obsidian list [path]                    List notes in folder
    obsidian query "<DQL>"                  Dataview query
    obsidian search "<text>"                Full-text search
    obsidian daily                          Get today's daily note
    obsidian weekly                         Get this week's note
    obsidian status                         Check API status

Examples:
    obsidian read memory/2026-03-23.md
    obsidian append memory/2026-03-23.md --heading "Session Notes" --content "- Item"
    obsidian query 'TABLE file.name FROM "memory" WHERE file.ctime >= date(today)'
EOF
}

# Parse args
if [[ $# -eq 0 ]]; then
    usage
    exit 1
fi

command="$1"
shift

case "$command" in
    read)
        cmd_read "$1"
        ;;
    write)
        path="$1"; shift
        content=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --content) content="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        cmd_write "$path" "$content"
        ;;
    append)
        path="$1"; shift
        heading=""
        content=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --heading) heading="$2"; shift 2 ;;
                --content) content="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        cmd_append "$path" "$heading" "$content"
        ;;
    prepend)
        path="$1"; shift
        heading=""
        content=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --heading) heading="$2"; shift 2 ;;
                --content) content="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        cmd_prepend "$path" "$heading" "$content"
        ;;
    patch)
        path="$1"; shift
        field=""
        value=""
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --field) field="$2"; shift 2 ;;
                --value) value="$2"; shift 2 ;;
                *) shift ;;
            esac
        done
        cmd_patch "$path" "$field" "$value"
        ;;
    list)
        cmd_list "$1"
        ;;
    query)
        cmd_query "$1"
        ;;
    search)
        cmd_search "$1"
        ;;
    daily)
        cmd_daily
        ;;
    weekly)
        cmd_weekly
        ;;
    status)
        cmd_status
        ;;
    -h|--help|help)
        usage
        ;;
    *)
        echo "Unknown command: $command"
        usage
        exit 1
        ;;
esac