#!/bin/bash
# OpenClaw Android Automated Build Script
# Builds APK with custom changes and deploys to The Hub
# Designed for fully automated nightly builds

set -euo pipefail

# === Configuration ===
ANDROID_HOME=/home/spectre/.android/sdk
ANDROID_DIR="/storage/workspace/openclaw-repo/apps/android"
HUB_PUBLIC="/storage/workspace/thehub/public"
VERSION_FILE="/storage/workspace/android-version.json"
LOG_DIR="/storage/workspace/logs/android-builds"
WORKSPACE="/storage/workspace"

# Custom changes files (tracked for stash/pop)
CUSTOM_FILES=(
    "apps/android/app/build.gradle.kts"
    "apps/android/app/src/main/AndroidManifest.xml"
    "apps/android/app/src/main/java/ai/openclaw/app/MainViewModel.kt"
    "apps/android/app/src/main/java/ai/openclaw/app/ui/SettingsSheet.kt"
    "apps/android/app/src/main/res/mipmap-hdpi/ic_launcher.png"
    "apps/android/app/src/main/res/mipmap-hdpi/ic_launcher_foreground.png"
    "apps/android/app/src/main/res/mipmap-mdpi/ic_launcher.png"
    "apps/android/app/src/main/res/mipmap-mdpi/ic_launcher_foreground.png"
    "apps/android/app/src/main/res/mipmap-xhdpi/ic_launcher.png"
    "apps/android/app/src/main/res/mipmap-xhdpi/ic_launcher_foreground.png"
    "apps/android/app/src/main/res/mipmap-xxhdpi/ic_launcher.png"
    "apps/android/app/src/main/res/mipmap-xxhdpi/ic_launcher_foreground.png"
    "apps/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher.png"
    "apps/android/app/src/main/res/mipmap-xxxhdpi/ic_launcher_foreground.png"
    "apps/android/app/src/main/res/values/colors.xml"
    "apps/android/app/src/main/res/xml/file_paths.xml"
)

# Ensure directories exist
mkdir -p "$LOG_DIR"

# === Logging ===
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H%M%S)
LOG_FILE="$LOG_DIR/build-$DATE-$TIME.log"

log() {
    local level="$1"; shift
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] $*" tee -a "$LOG_FILE"
}

log "INFO" "=== OpenClaw Android Build Started ==="

# === Step 1: Pull Latest Changes ===
log "INFO" "Checking for upstream updates..."

cd "$WORKSPACE/openclaw-repo"

# Fetch latest
git fetch origin main 2>&1 | tee -a "$LOG_FILE"

# Check for updates
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)

if [ "$LOCAL" != "$REMOTE" ]; then
    log "INFO" "Updates available. Pulling..."
    
    # Stash any local changes
    if git diff --quiet && git diff --cached --quiet; then
        log "INFO" "No local changes to stash"
        STASHED=false
    else
        log "INFO" "Stashing local changes..."
        git stash push -m "auto-stash-$DATE-$TIME" 2>&1 | tee -a "$LOG_FILE"
        STASHED=true
    fi
    
    # Pull
    git pull origin main 2>&1 | tee -a "$LOG_FILE"
    
    # Restore stashed changes
    if [ "$STASHED" = true ]; then
        log "INFO" "Restoring stashed changes..."
        git stash pop 2>&1 | tee -a "$LOG_FILE" || {
            log "WARN" "Conflict detected, resolving..."
            # Accept ours for build.gradle.kts version conflicts
            if [ -f "apps/android/app/build.gradle.kts" ]; then
                # Check for merge conflicts
                if grep -q "<<<<<<" "apps/android/app/build.gradle.kts" 2>/dev/null; then
                    log "INFO" "Resolving build.gradle.kts conflicts..."
                    # Take our version (keep stash version)
                    git checkout --theirs "apps/android/app/build.gradle.kts" 2>/dev/null || true
                    git add "apps/android/app/build.gradle.kts"
                fi
            fi
            # Continue anyway - build.gradle.kts will be updated in step 2
        }
    fi
else
    log "INFO" "Already up to date"
fi

# === Step 2: Check New Commits ===
LAST_BUILD=$(cat "$WORKSPACE/.last-android-build" 2>/dev/null || echo "1970-01-01")
TODAY=$(date +%Y-%m-%d)

# Get commits since last build
if [ "$LAST_BUILD" != "1970-01-01" ]; then
    SINCE="--since=$LAST_BUILD"
else
    SINCE="--since=1 week ago"
fi

NEW_COMMITS=$(git log $SINCE --oneline -- apps/android/ 2>/dev/null | head -20)
COMMIT_COUNT=$(echo "$NEW_COMMITS" | grep -c . || echo "0")

if [ "$COMMIT_COUNT" -eq 0 ] && [ "$LAST_BUILD" = "$TODAY" ]; then
    log "INFO" "No new commits and already built today. Skipping."
    log "INFO" "=== Build Skipped ==="
    exit 0
fi

log "INFO" "Found $COMMIT_COUNT new commits since $LAST_BUILD:"
echo "$NEW_COMMITS" | tee -a "$LOG_FILE"

# === Step 3: Update Version ===
log "INFO" "Updating version..."

# Generate version: YYYY.MM.DD.N (N = build number for day)
PATCH=1
while [ -f "$VERSION_FILE" ]; do
    EXISTING=$(jq -r '.versionName' "$VERSION_FILE" 2>/dev/null || echo "")
    if [ "${EXISTING%%.*}" = "${TODAY%%-*}" ]; then
        # Same day, increment patch
        PATCH=$(( ${EXISTING##*.} + 1 ))
        break
    fi
    break
done

VERSION_NAME="$TODAY.$PATCH"
VERSION_CODE=$(echo "$TODAY" | tr -d '-')$(printf "%02d" $PATCH)

log "INFO" "Version: $VERSION_NAME (code: $VERSION_CODE)"

# Update build.gradle.kts
GRADLE_FILE="apps/android/app/build.gradle.kts"
sed -i "s/versionCode = [0-9]*/versionCode = $VERSION_CODE/" "$GRADLE_FILE"
sed -i "s/versionName = \"[^\"]*\"/versionName = \"$VERSION_NAME\"/" "$GRADLE_FILE"

# Also update the output filename version
if grep -q 'val versionName = output.versionName' "$GRADLE_FILE" 2>/dev/null; then
    sed -i "s/val versionName = output.versionName.orNull ?: \"[^\"]*\"/val versionName = \"$VERSION_NAME\"/" "$GRADLE_FILE"
fi

log "INFO" "Version updated in build.gradle.kts"

# === Step 4: Build APK ===
log "INFO" "Building APK (Play flavor)..."

cd "$ANDROID_DIR"
export ANDROID_HOME

# Clean
./gradlew clean 2>&1 | tee -a "$LOG_FILE" || {
    log "ERROR" "Clean failed"
    exit 1
}

# Build ThirdParty Debug variant (full features: SMS, call log, etc.)
./gradlew assembleThirdPartyDebug --no-daemon 2>&1 | tee -a "$LOG_FILE" || {
    log "ERROR" "Build failed"
    exit 1
}

# Find APK (ThirdParty flavor)
APK_PATH=$(find "$ANDROID_DIR/app/build/outputs/apk/thirdParty/debug" -name "*.apk" -type f 2>/dev/null | head -1)

if [ -z "$APK_PATH" ]; then
    log "ERROR" "No APK found after build"
    exit 1
fi

log "INFO" "Built: $(basename $APK_PATH)"

# === Step 5: Deploy to The Hub ===
log "INFO" "Deploying to The Hub..."

cp "$APK_PATH" "$HUB_PUBLIC/openclaw.apk"
APK_SIZE=$(stat -c%s "$HUB_PUBLIC/openclaw.apk")

log "INFO" "APK deployed: $(du -h $HUB_PUBLIC/openclaw.apk | cut -f1)"

# === Step 6: Update Version JSON ===
log "INFO" "Updating version metadata..."

# Build changelog from commits
CHANGELOG=$(git log $SINCE --format='- %s' -- apps/android/ 2>/dev/null | head -10 | jq -Rs 'split("\n") | map(select(length > 0)) | map(ltrimstr("- "))' 2>/dev/null || echo "[]")

# If no commits, use default
if [ "$CHANGELOG" = "[]" ] || [ -z "$CHANGELOG" ]; then
    CHANGELOG='["Automated build"]'
fi

# Add custom changes note if they exist
CUSTOM_NOTE=""
if [ -d "$ANDROID_DIR/app/src/main/java/ai/openclaw/app/update" ]; then
    CUSTOM_NOTE="\"OTA update support enabled\""
fi

# Create version JSON
cat > "$VERSION_FILE" << EOF
{
  "versionCode": $VERSION_CODE,
  "versionName": "$VERSION_NAME",
  "buildDate": "$TODAY",
  "apkPath": "/openclaw.apk",
  "size": $APK_SIZE,
  "changelog": $CHANGELOG
}
EOF

# Add custom note if present
if [ -n "$CUSTOM_NOTE" ]; then
    jq ".changelog = [\"OTA update support enabled\"] + .changelog" "$VERSION_FILE" > "$VERSION_FILE.tmp" && mv "$VERSION_FILE.tmp" "$VERSION_FILE"
fi

log "INFO" "Version metadata updated: $VERSION_FILE"

# Record build date
echo "$TODAY" > "$WORKSPACE/.last-android-build"

# === Step 7: Rebuild The Hub (optional) ===
log "INFO" "Checking if The Hub needs rebuild..."

# Check if API files changed
if find "$WORKSPACE/thehub/src/app/api" -newer "$WORKSPACE/.last-android-build" -type f 2>/dev/null | grep -q .; then
    log "INFO" "API files changed, rebuilding The Hub..."
    cd "$WORKSPACE/thehub"
    npm run build 2>&1 | tee -a "$LOG_FILE" || {
        log "WARN" "The Hub build failed, continuing anyway"
    }
    # The Hub should auto-restart with its own process manager
else
    log "INFO" "The Hub build not needed"
fi

# === Step 8: Notify (optional) ===
# Uncomment to enable notifications
# if command -v telegram-cli &>/dev/null; then
#     telegram-cli -k -W -e "msg Yeatz 'Android build complete: v$VERSION_NAME ($APK_SIZE bytes)'" 2>/dev/null || true
# fi

# === Done ===
log "INFO" "=== Build Complete ==="
log "INFO" "Version: $VERSION_NAME"
log "INFO" "APK: $HUB_PUBLIC/openclaw.apk"
log "INFO" "Download: http://localhost:3000/download"

# Output version for callers
echo "{\"version\": \"$VERSION_NAME\", \"size\": $APK_SIZE, \"apk\": \"$HUB_PUBLIC/openclaw.apk\"}"

exit 0