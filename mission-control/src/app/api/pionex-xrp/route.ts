import { NextRequest, NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'

interface XRPPosition {
  symbol: string
  side: string
  size: number
  entry_price: number
  stop_price: number
  target_price: number
  entry_time: string
  unrealized_pnl: number
}

interface XRPTrade {
  symbol: string
  side: string
  size: number
  entry_price: number
  exit_price: number
  pnl: number
  fees: number
  exit_reason: string
  closed_at: string
}

interface XRPState {
  balance: number
  initial_balance: number
  realized_pnl: number
  unrealized_pnl: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  trades: XRPTrade[]
  positions: Record<string, XRPPosition>
  status: string
  consecutive_losses: number
  daily_pnl: number
  trades_today: number
}

async function getXRPState(): Promise<XRPState | null> {
  try {
    const statePath = path.join(
      process.env.HOME || '/home/yeatz',
      '.openclaw/workspace/btc-trading-bot/pionex/pionex_xrp_state.json'
    )
    
    const data = await fs.readFile(statePath, 'utf-8')
    return JSON.parse(data)
  } catch {
    return null
  }
}

export async function GET() {
  const state = await getXRPState()
  
  if (!state) {
    return NextResponse.json({
      error: 'Bot state not found',
      status: 'not_initialized'
    }, { status: 404 })
  }
  
  // Calculate metrics
  const winRate = state.total_trades > 0 
    ? (state.winning_trades / state.total_trades * 100).toFixed(1)
    : '0.0'
  
  const profitFactor = state.losing_trades > 0
    ? (state.realized_pnl + (state.losing_trades * 10)) / (state.losing_trades * 10)
    : state.winning_trades > 0 ? '∞' : '0.0'
  
  const currentPosition = Object.values(state.positions)[0] || null
  
  return NextResponse.json({
    symbol: 'XRPUSD_PERP',
    marketType: 'COIN-M PERP',
    status: state.status,
    paperMode: true,
    
    // Balance
    balance: state.balance,
    initialBalance: state.initial_balance,
    realizedPnl: state.realized_pnl,
    unrealizedPnl: state.unrealized_pnl,
    totalPnl: state.realized_pnl + state.unrealized_pnl,
    
    // Performance
    totalTrades: state.total_trades,
    winningTrades: state.winning_trades,
    losingTrades: state.losing_trades,
    winRate: `${winRate}%`,
    profitFactor,
    
    // Current position
    position: currentPosition ? {
      side: currentPosition.side,
      size: currentPosition.size,
      entryPrice: currentPosition.entry_price,
      stopPrice: currentPosition.stop_price,
      targetPrice: currentPosition.target_price,
      unrealizedPnl: currentPosition.unrealized_pnl,
      entryTime: currentPosition.entry_time
    } : null,
    
    // Recent trades (last 10)
    recentTrades: state.trades.slice(-10).reverse(),
    
    // Safety
    consecutiveLosses: state.consecutive_losses,
    dailyPnl: state.daily_pnl,
    
    // Timestamp
    lastUpdated: new Date().toISOString()
  })
}

export async function POST(request: NextRequest) {
  const { action } = await request.json()
  
  const statePath = path.join(
    process.env.HOME || '/home/yeatz',
    '.openclaw/workspace/btc-trading-bot/pionex/pionex_xrp_state.json'
  )
  
  try {
    const data = await fs.readFile(statePath, 'utf-8')
    const state: XRPState = JSON.parse(data)
    
    switch (action) {
      case 'reset':
        // Reset to initial state
        state.balance = state.initial_balance
        state.realized_pnl = 0
        state.unrealized_pnl = 0
        state.total_trades = 0
        state.winning_trades = 0
        state.losing_trades = 0
        state.trades = []
        state.positions = {}
        state.consecutive_losses = 0
        state.daily_pnl = 0
        state.status = 'stopped'
        
        await fs.writeFile(statePath, JSON.stringify(state, null, 2))
        return NextResponse.json({ success: true, message: 'Bot reset' })
        
      case 'start':
        state.status = 'running'
        await fs.writeFile(statePath, JSON.stringify(state, null, 2))
        return NextResponse.json({ success: true, message: 'Bot started' })
        
      case 'stop':
        state.status = 'stopped'
        await fs.writeFile(statePath, JSON.stringify(state, null, 2))
        return NextResponse.json({ success: true, message: 'Bot stopped' })
        
      case 'reset_circuit_breaker':
        state.consecutive_losses = 0
        await fs.writeFile(statePath, JSON.stringify(state, null, 2))
        return NextResponse.json({ success: true, message: 'Circuit breaker reset' })
        
      default:
        return NextResponse.json({ error: 'Unknown action' }, { status: 400 })
    }
  } catch {
    return NextResponse.json({ error: 'Failed to execute action' }, { status: 500 })
  }
}
