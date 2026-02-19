#!/bin/bash
# Browser automation script using Playwright CLI

# Screenshot any URL
screenshot() {
    local url=$1
    local output=$2
    npx playwright screenshot --browser=chromium --full-page "$url" "$output"
    echo "Screenshot saved: $output"
}

# Screenshot with mobile viewport
screenshot_mobile() {
    local url=$1
    local output=$2
    npx playwright screenshot --browser=chromium --viewport-size="375,812" "$url" "$output"
    echo "Mobile screenshot saved: $output"
}

# Open browser interactively
open_browser() {
    local url=$1
    npx playwright open --browser=chromium "$url"
}

# Run automated test
run_test() {
    local test_file=$1
    npx playwright test "$test_file"
}

# PDF export
pdf() {
    local url=$1
    local output=$2
    npx playwright pdf --browser=chromium "$url" "$output"
    echo "PDF saved: $output"
}

# Usage examples:
echo "Browser Automation Commands:"
echo "  ./browser.sh screenshot URL output.png"
echo "  ./browser.sh screenshot_mobile URL output.png"
echo "  ./browser.sh open_browser URL"
echo "  ./browser.sh pdf URL output.pdf"

# Execute command if arguments provided
if [ $# -gt 0 ]; then
    "$@"
fi
