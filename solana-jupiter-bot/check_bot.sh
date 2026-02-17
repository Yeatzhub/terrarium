#!/bin/bash
# Quick bot status check

echo "🚀 Jupiter Momentum Bot Status"
echo "=============================="
echo ""

# Check if running
if pgrep -f "jupiter_momentum_bot" > /dev/null 2>&1; then
    echo "✅ Bot is RUNNING"
    PID=$(pgrep -f "jupiter_momentum_bot" | head -1)
    echo "   PID: $PID"
else
    echo "❌ Bot is NOT running"
fi

echo ""

# Show current state
if [ -f jupiter_momentum_state.json ]; then
    echo "📊 Account:"
    jq -r '"   Balance: \(.balance) SOL
   P&L: \(.pnl_sol) SOL (\(.pnl_pct)%)
   Trades: \(.wins + .losses) (\(.wins)W / \(.losses)L)
   Open Positions: \(.open_positions | length)"' jupiter_momentum_state.json 2>/dev/null || echo "   Loading state..."
    
    echo ""
    
    OPEN=$(jq -r '.open_positions | length' jupiter_momentum_state.json 2>/dev/null)
    if [ "$OPEN" -gt 0 ] 2>/dev/null; then
        echo "🎯 Open Positions:"
        jq -r '.open_positions[] | "   #\(.trade_id) \(.token) \(.direction) | Entry: $\(.entry_price) | Stop: $\(.stop_loss_price) | Target: $\(.take_profit_price)"' jupiter_momentum_state.json 2>/dev/null
    fi
else
    echo "⏳ Building price history..."
fi

echo ""
echo "=============================="
echo "Last log entry:"
tail -1 bot.log 2>/dev/null || echo "   No log yet"
