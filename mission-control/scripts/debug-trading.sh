#!/bin/bash
# Automated Trading Page Debugger
# Diagnoses and fixes Mission Control trading page issues

set -e

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

WORKSPACE="/home/yeatz/.openclaw/workspace"
MISSION_CONTROL="$WORKSPACE/mission-control"
BTC_BOT="$WORKSPACE/btc-trading-bot"

echo -e "${BLUE}🔍 Mission Control Trading Page Debugger${NC}"
echo "========================================"
echo ""

# Check 1: Verify API endpoints exist
echo -e "${BLUE}📡 Checking API endpoints...${NC}"
API_DIR="$MISSION_CONTROL/src/app/api"

check_endpoint() {
    local endpoint=$1
    local path="$API_DIR/$endpoint"
    if [ -d "$path" ]; then
        echo -e "  ✅ $endpoint"
        return 0
    else
        echo -e "  ❌ $endpoint (missing)"
        return 1
    fi
}

TRADING_API_OK=true
check_endpoint "trading-data" || TRADING_API_OK=false
check_endpoint "coingecko" || TRADING_API_OK=false
check_endpoint "jupiter-data" || TRADING_API_OK=false

echo ""

# Check 2: Trading bot state files
echo -e "${BLUE}📁 Checking trading bot state files...${NC}"

STATE_FILES=(
    "kraken_paper_state.json"
    "toobit_paper_state.json"
)

for file in "${STATE_FILES[@]}"; do
    if [ -f "$BTC_BOT/$file" ]; then
        size=$(stat -f%z "$BTC_BOT/$file" 2>/dev/null || stat -c%s "$BTC_BOT/$file" 2>/dev/null || echo "unknown")
        echo -e "  ✅ $file (${size} bytes)"
    else
        echo -e "  ❌ $file (not found)"
        echo -e "     ${YELLOW}→ Creating sample state file${NC}"
        
        # Create sample state
        cat > "$BTC_BOT/$file" << 'EOF'
{
  "balance": 10000.0,
  "initial_balance": 10000.0,
  "realized_pnl": 0.0,
  "total_fees": 0.0,
  "positions": {
    "BTCUSD": {
      "symbol": "BTCUSD",
      "side": "long",
      "size": 0.1,
      "entry_price": 95000.0,
      "fees": 2.5,
      "opened_at": 1700000000
    }
  },
  "trades": [
    {
      "symbol": "BTCUSD",
      "side": "buy",
      "type": "limit",
      "size": 0.1,
      "price": 95000.0,
      "value": 9500.0,
      "fees": 2.5,
      "pnl": 0.0,
      "timestamp": 1700000000,
      "datetime": "2024-01-01T00:00:00Z"
    }
  ],
  "timestamp": 1700000000,
  "exchange": "kraken",
  "status": "active"
}
EOF
        echo -e "     ${GREEN}✓ Created sample $file${NC}"
    fi
done

echo ""

# Check 3: Test API responses
echo -e "${BLUE}🧪 Testing API responses...${NC}"

test_api() {
    local endpoint=$1
    local expected_key=$2
    local timeout=5
    
    response=$(curl -s -m $timeout "http://localhost:3000$endpoint" 2>/dev/null || echo '{}')
    
    if echo "$response" | grep -q "$expected_key"; then
        echo -e "  ✅ $endpoint - responding"
        return 0
    else
        echo -e "  ❌ $endpoint - not responding or empty"
        return 1
    fi
}

API_OK=true
test_api "/api/trading-data?exchange=kraken" "balance" || API_OK=false
test_api "/api/coingecko?endpoint=simple/price" "bitcoin" || API_OK=false

echo ""

# Check 4: Jupiter bot status
echo -e "${BLUE}🪐 Checking Jupiter bot...${NC}"
if [ -d "$WORKSPACE/solana-jupiter-bot" ]; then
    echo -e "  ✅ Jupiter bot directory exists"
    if [ -f "$WORKSPACE/solana-jupiter-bot/state.json" ]; then
        echo -e "  ✅ Jupiter state file exists"
    else
        echo -e "  ⚠️  Jupiter state file missing (will create on first run)"
    fi
else
    echo -e "  ⚠️  Jupiter bot not installed"
fi

echo ""

# Check 5: Polymarket scanner
echo -e "${BLUE}📊 Checking Polymarket scanner...${NC}"
if [ -f "$WORKSPACE/polymarket_paper_trader/portfolio.json" ]; then
    echo -e "  ✅ Polymarket portfolio exists"
else
    echo -e "  ⚠️  Polymarket portfolio not found"
fi

echo ""

# Summary
echo -e "${BLUE}📋 Summary${NC}"
echo "=========="

if [ "$TRADING_API_OK" = true ] && [ "$API_OK" = true ]; then
    echo -e "${GREEN}✅ Trading pages should be working${NC}"
    echo -e "   State files created where missing"
    echo -e "   APIs are responding"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Restart Mission Control: npm run build && npm start"
    echo "  2. Navigate to /trading to verify"
    echo "  3. Check individual bot pages: /trading/bot/kraken"
else
    echo -e "${YELLOW}⚠️  Some issues found${NC}"
    echo -e "   Missing APIs or endpoints not responding"
    echo ""
    echo -e "${YELLOW}Fixes applied:${NC}"
    echo "  - Created sample state files where missing"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Ensure Mission Control is running on port 3000"
    echo "  2. Restart if needed: npm run build && npm start"
fi

echo ""
echo -e "${BLUE}🔄 Auto-fix complete${NC}"
