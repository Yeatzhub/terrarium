---
name: android-update
description: Build and deploy OpenClaw Android app APK updates to The Hub. Use when asked to "update the Android app", "build a new APK", "deploy the latest Android app", or "check for Android app updates". Handles checking commits, building APK, versioning, and deployment.
---

# Android App Update

Build and deploy the OpenClaw Android app from the latest source.

## Workflow

1. **Check for new commits** in `apps/android/` directory
2. **Update version numbers** in `build.gradle.kts` (increment patch)
3. **Build APK** using Gradle
4. **Deploy** to The Hub's public directory
5. **Update version info** in `android-version.json`

## Key Paths

| Path | Purpose |
|------|---------|
| `/storage/workspace/openclaw-repo/apps/android` | Android app source |
| `/storage/workspace/thehub/public/openclaw.apk` | Deployed APK |
| `/storage/workspace/android-version.json` | Version metadata for OTA |
| `/storage/workspace/thehub/src/app/api/app-version/route.ts` | OTA API endpoint |

## Version Scheme

- **Format**: `YYYY.MM.DD{n}` (e.g., `2026.3.22.1`)
- **versionCode**: `YYYYMMDDnn` (e.g., `2026032201`)
- Increment the patch number (`n` or `nn`) on same-day builds

## Build Commands

```bash
# Check current version
grep -E "versionCode|versionName" /storage/workspace/openclaw-repo/apps/android/app/build.gradle.kts | head -5

# Update version (example: set to 2026.3.22)
sed -i 's/versionCode = [0-9]*/versionCode = 2026032200/' /storage/workspace/openclaw-repo/apps/android/app/build.gradle.kts
sed -i 's/versionName = "[^"]*"/versionName = "2026.3.22"/' /storage/workspace/openclaw-repo/apps/android/app/build.gradle.kts

# Build APK
cd /storage/workspace/openclaw-repo/apps/android
export ANDROID_HOME=~/.android/sdk
./gradlew clean assembleDebug --no-daemon

# Verify build
cat app/build/outputs/apk/debug/output-metadata.json

# Deploy APK
cp app/build/outputs/apk/debug/openclaw-*.apk /storage/workspace/thehub/public/openclaw.apk
```

## Update android-version.json

After deploying, update the version metadata:

```json
{
  "versionCode": 2026032200,
  "versionName": "2026.3.22",
  "buildDate": "2026-03-22",
  "apkPath": "/openclaw.apk",
  "size": <file size in bytes>,
  "changelog": [
    "commit message 1",
    "commit message 2"
  ]
}
```

## OTA Update Flow

1. App calls `GET /api/app-version?current=<installed_version>`
2. API returns version info with `updateAvailable: true/false`
3. If update available, app downloads from `externalDownloadUrl` or `downloadUrl`
4. App uses FileProvider + `ACTION_VIEW` intent to install

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Build fails | Check `ANDROID_HOME` is set, SDK installed |
| Version not updating | Clean build: `./gradlew clean assembleDebug` |
| OTA not working | Check `android-version.json` has correct versionCode |
| App shows update after install | versionCode in APK must match versionCode in API |

## Quick Commands

```bash
# Get current APK info
curl -s http://localhost:3000/api/app-version | python3 -m json.tool

# Get recent Android commits
cd /storage/workspace/openclaw-repo && git log --since="7 days ago" --oneline -- apps/android/ | head -10

# Check APK file size
ls -la /storage/workspace/thehub/public/openclaw.apk
```