#!/bin/bash
# check-graphics.sh - Scan Android project for missing graphics

PROJECT="${1:-terrarium}"
PROJECT_DIR="/storage/workspace/projects/android/$PROJECT"
ASSETS_DIR="$PROJECT_DIR/assets"
REQUIREMENTS_FILE="$ASSETS_DIR/graphics-requirements.json"

# Standard Android graphics requirements
declare -A REQUIRED_GRAPHICS=(
    ["mipmap-mdpi/icon.png"]="48x48"
    ["mipmap-hdpi/icon.png"]="72x72"
    ["mipmap-xhdpi/icon.png"]="96x96"
    ["mipmap-xxhdpi/icon.png"]="144x144"
    ["mipmap-xxxhdpi/icon.png"]="192x192"
    ["banners/play_store.png"]="1024x500"
    ["splash/splash.png"]="1080x1920"
    ["notification/mdpi/notification.png"]="24x24"
    ["notification/hdpi/notification.png"]="36x36"
    ["notification/xhdpi/notification.png"]="48x48"
)

# Initialize requirements
MISSING=()
COMPLETE=()

# Check each required graphic
for path in "${!REQUIRED_GRAPHICS[@]}"; do
    full_path="$ASSETS_DIR/$path"
    if [ -f "$full_path" ]; then
        COMPLETE+=("{\"path\": \"$path\", \"size\": \"${REQUIRED_GRAPHICS[$path]}\"}")
    else
        MISSING+=("{\"path\": \"$path\", \"size\": \"${REQUIRED_GRAPHICS[$path]}\", \"status\": \"missing\"}")
    fi
done

# Output summary
echo "=== Graphics Check for $PROJECT ==="
echo "Complete: ${#COMPLETE[@]} graphics"
echo "Missing: ${#MISSING[@]} graphics"

if [ ${#MISSING[@]} -gt 0 ]; then
    echo ""
    echo "Missing graphics:"
    for item in "${MISSING[@]}"; do
        echo "  - $item"
    done
    echo ""
    echo "Post to #graphics: 'Bragi needed for $PROJECT:'"
    for item in "${MISSING[@]}"; do
        path=$(echo "$item" | jq -r '.path')
        echo "  - $path"
    done
fi

# Update requirements file
if [ ${#MISSING[@]} -gt 0 ]; then
    exit 1  # Graphics needed
else
    exit 0  # All graphics present
fi