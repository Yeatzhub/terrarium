import { NextRequest, NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'

interface BTCState {
  balance: number
  initial_balance: number
  realized_pnl: number
  unrealized_pnl: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  trades: any[]
  positions: Record<string, any>
  status: string
  consecutive_losses: number
  daily_pnl: number
  trades_today: number
}

async function getBTCState(): Promise<BTCState | null> {
  try {
    const statePath = path.join(
      process.env.HOME || '/home/yeatz',
      '.openclaw/workspace/btc-trading-bot/pionex/pionex_btc_state.json'
    )
    
    const data = await fs.readFile(statePath, 'utf-8')
    return JSON.parse(data)
  } catch {
    return null
  }
}

export async function GET() {
  const state = await getBTCState()
  
  if (!state) {
    return NextResponse.json({
      error: 'Bot state not found',
      status: 'not_initialized',
      balance: 0,
      realized_pnl: 0,
      trades: []
    })
  }
  
  const winRate = state.total_trades > 0 
    ? (state.winning_trades / state.total_trades * 100).toFixed(1)
    : '0.0'
  
  const currentPosition = Object.values(state.positions)[0] || null
  
  return NextResponse.json({
    symbol: 'BTC_USDT',
    marketType: 'USDT-M PERP',
    status: state.status,
    paperMode: true,
    
    balance: state.balance,
    initialBalance: state.initial_balance,
    realizedPnl: state.realized_pnl,
    unrealizedPnl: state.unrealized_pnl,
    totalPnl: state.realized_pnl + state.unrealized_pnl,
    
    totalTrades: state.total_trades,
    winningTrades: state.winning_trades,
    losingTrades: state.losing_trades,
    winRate: `${winRate}%`,
    
    position: currentPosition,
    recentTrades: state.trades.slice(-10).reverse(),
    consecutiveLosses: state.consecutive_losses,
    
    lastUpdated: new Date().toISOString()
  })
}

export async function POST(request: NextRequest) {
  const { action } = await request.json()
  
  const statePath = path.join(
    process.env.HOME || '/home/yeatz',
    '.openclaw/workspace/btc-trading-bot/pionex/pionex_btc_state.json'
  )
  
  try {
    const data = await fs.readFile(statePath, 'utf-8')
    const state: BTCState = JSON.parse(data)
    
    switch (action) {
      case 'reset':
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
        
      default:
        return NextResponse.json({ error: 'Unknown action' }, { status: 400 })
    }
  } catch {
    return NextResponse.json({ error: 'Failed to execute action' }, { status: 500 })
  }
}
