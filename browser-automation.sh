#!/bin/bash
# Mission Control Browser Automation Script
# Uses Playwright + Xvfb for headless browser control

set -e

# Configuration
BASE_URL="http://100.125.198.70:3000"
OUTPUT_DIR="/tmp/mc-screenshots"
VIRTUAL_DISPLAY=":99"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Helper: Run command with virtual display
with_display() {
    xvfb-run --server-num=99 --server-args="-screen 0 1920x1080x24 -ac +extension GLX +render -noreset" "$@"
}

# Screenshot any page
screenshot() {
    local path=$1
    local output_name=$2
    local viewport=${3:-"1920,1080"}
    
    echo "📸 Screenshot: $path"
    with_display npx playwright screenshot \
        --browser=chromium \
        --viewport-size="$viewport" \
        --full-page \
        "${BASE_URL}${path}" \
        "${OUTPUT_DIR}/${output_name}.png"
    echo "✅ Saved: ${OUTPUT_DIR}/${output_name}.png"
}

# Screenshot mobile viewport
screenshot_mobile() {
    local path=$1
    local output_name=$2
    
    echo "📱 Mobile screenshot: $path"
    with_display npx playwright screenshot \
        --browser=chromium \
        --viewport-size="375,812" \
        --full-page \
        "${BASE_URL}${path}" \
        "${OUTPUT_DIR}/${output_name}-mobile.png"
    echo "✅ Saved: ${OUTPUT_DIR}/${output_name}-mobile.png"
}

# Capture all main pages
screenshot_all() {
    echo "📸 Capturing all Mission Control pages..."
    
    screenshot "/" "dashboard"
    screenshot "/trading" "trading"
    screenshot "/trading/bot/toobit/live" "toobit-live"
    screenshot "/agents" "agents"
    screenshot "/tasks" "tasks"
    screenshot "/action-items" "action-items"
    
    echo ""
    echo "✅ All screenshots saved to: $OUTPUT_DIR"
    ls -lh "$OUTPUT_DIR"
}

# Capture mobile versions
screenshot_all_mobile() {
    echo "📱 Capturing mobile versions..."
    
    screenshot_mobile "/" "dashboard"
    screenshot_mobile "/trading" "trading"
    screenshot_mobile "/trading/bot/toobit/live" "toobit-live"
    screenshot_mobile "/agents" "agents"
    
    echo ""
    echo "✅ Mobile screenshots saved to: $OUTPUT_DIR"
}

# PDF export
pdf() {
    local path=$1
    local output_name=$2
    
    echo "📄 PDF: $path"
    with_display npx playwright pdf \
        --browser=chromium \
        "${BASE_URL}${path}" \
        "${OUTPUT_DIR}/${output_name}.pdf"
    echo "✅ Saved: ${OUTPUT_DIR}/${output_name}.pdf"
}

# Open browser interactively (requires actual display)
open_browser() {
    local path=$1
    
    if [ -n "$DISPLAY" ]; then
        echo "🌐 Opening browser..."
        npx playwright open --browser=chromium "${BASE_URL}${path}"
    else
        echo "⚠️  No DISPLAY available. Use VNC or X11 forwarding."
        echo "Alternative: screenshot the page instead"
    fi
}

# Test specific element (requires JavaScript evaluation)
test_element() {
    local path=$1
    local selector=$2
    
    echo "🧪 Testing element: $selector on $path"
    
    cat > /tmp/test-element.js << 'EOF'
const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    await page.goto(process.argv[2]);
    
    const element = await page.$(process.argv[3]);
    if (element) {
        console.log('✅ Element found');
        const text = await element.textContent();
        console.log('Text:', text?.substring(0, 100));
        const visible = await element.isVisible();
        console.log('Visible:', visible);
    } else {
        console.log('❌ Element not found');
    }
    
    await browser.close();
})();
EOF

    with_display node /tmp/test-element.js "${BASE_URL}${path}" "$selector"
}

# Monitor page for changes
monitor() {
    local path=$1
    local interval=${2:-60}
    local duration=${3:-3600}
    
    echo "📊 Monitoring $path for changes..."
    echo "Interval: ${interval}s, Duration: ${duration}s"
    
    local prev_hash=""
    local end_time=$(($(date +%s) + duration))
    local counter=0
    
    while [ $(date +%s) -lt $end_time ]; do
        counter=$((counter + 1))
        local output="${OUTPUT_DIR}/monitor-${counter}.png"
        
        with_display npx playwright screenshot \
            --browser=chromium \
            --viewport-size="1920,1080" \
            "${BASE_URL}${path}" \
            "$output" 2>/dev/null
        
        local hash=$(md5sum "$output" 2>/dev/null | cut -d' ' -f1)
        
        if [ "$hash" != "$prev_hash" ]; then
            echo "🔄 Change detected at $(date '+%H:%M:%S')"
            cp "$output" "${OUTPUT_DIR}/monitor-latest.png"
            prev_hash="$hash"
        fi
        
        sleep "$interval"
    done
    
    echo "✅ Monitoring complete"
}

# Help
show_help() {
    echo "Mission Control Browser Automation"
    echo ""
    echo "Usage: ./browser-automation.sh <command> [args]"
    echo ""
    echo "Commands:"
    echo "  screenshot <path> <name> [viewport]  - Screenshot specific page"
    echo "  screenshot_mobile <path> <name>      - Mobile viewport screenshot"
    echo "  screenshot_all                       - All main pages (desktop)"
    echo "  screenshot_all_mobile                - All main pages (mobile)"
    echo "  pdf <path> <name>                    - Export page as PDF"
    echo "  open <path>                          - Open browser (requires display)"
    echo "  test <path> <selector>               - Test element exists"
    echo "  monitor <path> [interval] [duration] - Monitor page for changes"
    echo "  help                                 - Show this help"
    echo ""
    echo "Examples:"
    echo "  ./browser-automation.sh screenshot /trading trading-desktop"
    echo "  ./browser-automation.sh screenshot_mobile /agents agents-mobile"
    echo "  ./browser-automation.sh screenshot_all"
    echo "  ./browser-automation.sh monitor /trading/bot/toobit/live 30 600"
    echo ""
    echo "Output directory: $OUTPUT_DIR"
}

# Main command handler
case "${1:-help}" in
    screenshot)
        screenshot "$2" "$3" "$4"
        ;;
    screenshot_mobile)
        screenshot_mobile "$2" "$3"
        ;;
    screenshot_all)
        screenshot_all
        ;;
    screenshot_all_mobile)
        screenshot_all_mobile
        ;;
    pdf)
        pdf "$2" "$3"
        ;;
    open)
        open_browser "$2"
        ;;
    test)
        test_element "$2" "$3"
        ;;
    monitor)
        monitor "$2" "${3:-60}" "${4:-3600}"
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
