---
assigned_to: pixel
task_id: 1771462800003-toobit-live-ui
status: pending
created_at: 2026-02-19T01:05:00Z
started_at: null
completed_at: null
parent_task: synthesis-1771462800000-toobit-real-trading-bot
priority: high
---

# Task: Build Toobit Live Trading UI

**Objective:** Create real-time trading dashboard for Toobit bot at `/trading/bot/toobit/live`.

## Page Requirements

**URL:** `/trading/bot/toobit/live`
**Theme:** Mission Control dark (slate-950 background, cyan accents)

## Layout

### Header Section
- Title: "Toobit Live Trading"
- Subtitle: "Real-time position and P&L tracking"
- Back link to `/trading`
- Warning banner: "⚠️ Trading with real funds"

### Stats Cards Row
Show 4 cards side-by-side:
1. **Account Balance**
   - Current balance: `$XXX.XX`
   - Starting balance: `$100.00`
   - Net P&L: `+$XX.XX` (green) or `-$XX.XX` (red)
   - Progress to $200: Progress bar

2. **Active Position**
   - Pair: `BTCUSDT-PERP`
   - Side: `LONG` (green) or `SHORT` (red)
   - Size: `0.XXX BTC`
   - Entry: `$XX,XXX.XX`
   - Mark Price: `$XX,XXX.XX`
   - Unrealized P&L: `+$X.XX` or `-$X.XX`
   - ROE: `+X.XX%`

3. **Today's Performance**
   - Trades: `X`
   - Wins: `X` | Losses: `X`
   - Win Rate: `XX%`
   - Best Trade: `+$X.XX`
   - Worst Trade: `-$X.XX`

4. **Bot Status**
   - Status: `Running` (green), `Stopped` (gray), `Error` (red)
   - Runtime: `2h 15m`
   - Last trade: `3 minutes ago`
   - Connection: `Connected` (green dot)

### Main Content Area (2 columns)

**Left Column (60%):**

1. **Price Chart**
   - Use lightweight charting library (Chart.js or lightweight-charts)
   - Show price with entry/exit markers
   - Timeframe: 5min or 15min
   - Add position markers (triangles for entry/exit)

2. **Recent Trades Table**
   Columns: Time | Pair | Side | Size | Entry | Exit | P&L | Duration
   Show last 20 trades
   Color code: Green (profit), Red (loss)

**Right Column (40%):**

1. **Position Details**
   - Liquidation price
   - Margin used
   - Leverage
   - TP/SL levels (if set)

2. **Controls Panel**
   - Big button: `START BOT` (green) / `STOP BOT` (red)
   - Emergency: `CLOSE ALL POSITIONS` (red, needs confirmation)
   - Strategy settings (read-only for now)

3. **System Log**
   - Scrollable text area
   - Last 50 log lines from bot
   - Format: `[TIME] LEVEL: Message`
   - Show connection status, trades, errors

### Real-Time Updates

- Poll `/api/toobit-live` endpoint every 2 seconds
- Use React state management for data
- Show loading spinner on first load
- Smooth transitions for numbers updating

## API Integration

Create or update endpoint: `mission-control/src/app/api/toobit-live/route.ts`

Should return:
```json
{
  "status": "running",
  "balance": 105.45,
  "starting_balance": 100,
  "realized_pnl": 5.45,
  "unrealized_pnl": 2.30,
  "trades_today": 12,
  "wins": 8,
  "losses": 4,
  "position": {
    "pair": "BTCUSDT-PERP",
    "side": "LONG",
    "size": 0.05,
    "entry_price": 96300,
    "mark_price": 96500,
    "liquidation_price": 85000,
    "leverage": 10,
    "margin": 48.15,
    "unrealized_pnl": 10.00,
    "roe": 20.75
  },
  "recent_trades": [...],
  "logs": [...]
}
```

## Responsive Design

- Desktop: 2 columns
- Mobile: Single column, cards stack vertically
- Dark theme throughout
- Red/green indicators for P&L
- Animated transitions on data updates

## Safety Features in UI

- ⚠️ Prominent warning banner: "This bot trades with real money."
- Confirmation dialog on "Close All" button
- Show last error message if bot disconnected
- Gray out trading controls if bot stopped

## Output Files

- `mission-control/src/app/trading/bot/toobit/live/page.tsx`
- `mission-control/src/app/api/toobit-live/route.ts`

## Design Notes

Match existing Mission Control:
- Same color scheme (slate-950 bg, cyan-400 accents)
- Use Lucide icons
- Same card styling
- Same font (Inter)

---

*Delegated by Synthesis from: Build Real Toobit Trading Bot*