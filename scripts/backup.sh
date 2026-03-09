#!/bin/bash
# Workspace backup script - commits and pushes to GitHub
set -e
cd /storage/workspace
git add -A
if git diff --cached --quiet; then
  echo "No changes to commit"
  exit 0
fi
git commit -m "backup $(date -u +%Y-%m-%d_%H-%M-%S)"

# Get token from gh CLI
TOKEN=$(gh auth token)

# Push to remote (local main -> remote master)
git push https://x-access-token:${TOKEN}@github.com/Yeatzhub/openclaw-workspace-backup.git HEAD:master 2>&1 || {
  echo "Push failed, trying remote origin..."
  git push origin HEAD:master
}