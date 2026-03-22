#!/bin/bash
# Build and deploy OpenClaw Android APK
# Usage: ./build-android-apk.sh [version]

set -e

REPO_DIR="/storage/workspace/openclaw-repo/apps/android"
HUB_PUBLIC="/storage/workspace/thehub/public"
VERSION_FILE="/storage/workspace/android-version.json"

# Get current date
DATE=$(date +%Y.%-m.%-d)
DATE_CODE=$(date +%Y%m%d)

# Determine version
if [ -n "$1" ]; then
    VERSION="$1"
else
    VERSION="$DATE"
fi

# Convert version to versionCode (YYYYMMDDnn format)
# Input: YYYY.M.D or YYYY.M.D.n
# Output: YYYYMMDDnn (e.g., 2026.3.22.1 -> 2026032201)
parse_version() {
    local v="$1"
    # Extract parts: YYYY.M.D[.n]
    local year=$(echo "$v" | cut -d. -f1)
    local month=$(echo "$v" | cut -d. -f2)
    local day=$(echo "$v" | cut -d. -f3)
    local patch=$(echo "$v" | cut -d. -f4)
    
    # Default patch to 0 if not provided
    [ -z "$patch" ] && patch=0
    
    # Pad month and day to 2 digits
    month=$(printf "%02d" "$month")
    day=$(printf "%02d" "$day")
    patch=$(printf "%02d" "$patch")
    
    echo "${year}${month}${day}${patch}"
}
VERSION_CODE=$(parse_version "$VERSION")

echo "Building OpenClaw Android APK v$VERSION (versionCode: $VERSION_CODE)"

# Update version in build.gradle.kts
echo "Updating version numbers..."
sed -i "s/versionCode = [0-9]*/versionCode = $VERSION_CODE/" "$REPO_DIR/app/build.gradle.kts"
sed -i "s/versionName = \"[^\"]*\"/versionName = \"$VERSION\"/" "$REPO_DIR/app/build.gradle.kts"

# Also update the output filename version
sed -i "s/val versionName = \"[^\"]*\"/val versionName = \"$VERSION\"/" "$REPO_DIR/app/build.gradle.kts"

# Build APK
echo "Building APK..."
cd "$REPO_DIR"
export ANDROID_HOME=~/.android/sdk
./gradlew clean assembleDebug --no-daemon

# Verify build
echo "Verifying build..."
OUTPUT_METADATA="$REPO_DIR/app/build/outputs/apk/debug/output-metadata.json"
if [ ! -f "$OUTPUT_METADATA" ]; then
    echo "ERROR: Build failed - no output metadata found"
    exit 1
fi

# Check version in output matches expected
BUILT_VERSION=$(grep -o '"versionName": "[^"]*"' "$OUTPUT_METADATA" | cut -d'"' -f4)
if [ "$BUILT_VERSION" != "$VERSION" ]; then
    echo "WARNING: Built version ($BUILT_VERSION) doesn't match expected ($VERSION)"
fi

# Find APK
APK_FILE=$(find "$REPO_DIR/app/build/outputs/apk" -name "*.apk" -type f | head -1)
if [ ! -f "$APK_FILE" ]; then
    echo "ERROR: No APK found"
    exit 1
fi

# Get APK size
APK_SIZE=$(stat -c%s "$APK_FILE")

echo "Deploying APK ($APK_SIZE bytes)..."
cp "$APK_FILE" "$HUB_PUBLIC/openclaw.apk"

# Get recent commits for changelog
echo "Generating changelog..."
cd /storage/workspace/openclaw-repo
CHANGELOG=$(git log --since="7 days ago" --oneline -- apps/android/ | head -5 | sed 's/^/    "/;s/$/",/' | sed '$ s/,$//')

# Update version file
cat > "$VERSION_FILE" << EOF
{
  "versionCode": $VERSION_CODE,
  "versionName": "$VERSION",
  "buildDate": "$(date +%Y-%m-%d)",
  "apkPath": "/openclaw.apk",
  "size": $APK_SIZE,
  "changelog": [
$CHANGELOG
  ]
}
EOF

echo ""
echo "✅ Build complete!"
echo "   Version: $VERSION"
echo "   VersionCode: $VERSION_CODE"
echo "   APK: $HUB_PUBLIC/openclaw.apk"
echo "   Size: $APK_SIZE bytes"
echo ""
echo "Test: curl -s http://localhost:3000/api/app-version | python3 -m json.tool"