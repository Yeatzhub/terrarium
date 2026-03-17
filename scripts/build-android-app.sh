#!/bin/bash
# Daily Android app build script
# Runs at 6 AM CDT to check for changes and rebuild OpenClaw Android app

set -euo pipefail

# Android SDK configuration
export ANDROID_HOME=/home/spectre/.android/sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="/storage/workspace"
ANDROID_DIR="/storage/workspace/openclaw-repo/apps/android"
LOG_DIR="/storage/workspace/logs"
LOG_FILE="$LOG_DIR/android-build-$(date +%Y-%m-%d).log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== OpenClaw Android Build Started ==="

# Check for changes in the repo
cd "$ANDROID_DIR"

# Get current git status
GIT_STATUS=$(git status --porcelain 2>/dev/null || echo "not a git repo")
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
LAST_COMMIT=$(git log -1 --format="%h %s" 2>/dev/null || echo "no commits")

log "Branch: $CURRENT_BRANCH"
log "Last commit: $LAST_COMMIT"

# Pull latest changes if this is a git repo
if git remote -v 2>/dev/null | grep -q "origin"; then
    log "Checking for updates..."
    git fetch origin 2>&1 | tee -a "$LOG_FILE"
    
    LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "unknown")
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        log "Updates available, pulling..."
        git pull origin "$CURRENT_BRANCH" 2>&1 | tee -a "$LOG_FILE"
    else
        log "No updates needed."
    fi
fi

# Check if build is needed
LAST_BUILD=$(cat "$WORKSPACE/.last-android-build" 2>/dev/null || echo "1970-01-01")
TODAY=$(date +%Y-%m-%d)

if [ "$LAST_BUILD" = "$TODAY" ]; then
    log "Already built today. Skipping."
    log "=== Build Skipped ==="
    exit 0
fi

# Build the Android app
log "Starting build process..."

cd "$ANDROID_DIR"

# Clean previous build
log "Cleaning previous build..."
./gradlew clean 2>&1 | tee -a "$LOG_FILE" || {
    log "ERROR: Clean failed"
    exit 1
}

# Build debug APK
log "Building debug APK..."
./gradlew assembleDebug 2>&1 | tee -a "$LOG_FILE" || {
    log "ERROR: Build failed"
    exit 1
}

# Find the built APK
APK_PATH=$(find "$ANDROID_DIR/app/build/outputs/apk" -name "*.apk" -type f 2>/dev/null | head -1)

if [ -z "$APK_PATH" ]; then
    log "ERROR: No APK found after build"
    exit 1
fi

# Extract version from APK name or use date
VERSION=$(date +%Y.%-m.%-d)
APK_NAME="openclaw-${VERSION}-debug.apk"

log "Built APK: $APK_PATH"

# Copy to workspace root
cp "$APK_PATH" "$WORKSPACE/openclaw-android.apk"
log "Copied to: $WORKSPACE/openclaw-android.apk"

# Also copy to dist folder in projects/android
mkdir -p "$WORKSPACE/projects/android/spectre/dist"
cp "$APK_PATH" "$WORKSPACE/projects/android/spectre/dist/$APK_NAME"
log "Copied to: $WORKSPACE/projects/android/spectre/dist/$APK_NAME"

# Record build date
echo "$TODAY" > "$WORKSPACE/.last-android-build"

# Get APK size
APK_SIZE=$(du -h "$WORKSPACE/openclaw-android.apk" | cut -f1)
log "APK Size: $APK_SIZE"

log "=== Build Complete ==="

# Send notification to Telegram (optional - requires telegram CLI)
# telegram-cli -k -W -e "msg Yeatz 'OpenClaw Android app built: $APK_NAME ($APK_SIZE)'" 2>/dev/null || true

exit 0