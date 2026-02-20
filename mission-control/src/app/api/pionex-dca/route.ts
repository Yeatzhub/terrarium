import { NextRequest, NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'

interface DCAPosition {
  entries: Array<{
    price: number
    size: number
    timestamp: string
  }>
  total_size: number
  average_price: number
  safety_level: number
  unrealized_pnl: number
}

interface DCAState {
  balance: number
  initial_balance: number
  realized_pnl: number
  total_trades: number
  winning_trades: number
  losing_trades: number
  current_position: DCAPosition | null
  trade_history: any[]
  status: string
  symbol: string
  direction: string
  max_safety_level: number
}

async function getDCAState(): Promise<DCAState | null> {
  try {
    const statePath = path.join(
      process.env.HOME || '/home/yeatz',
      '.openclaw/workspace/btc-trading-bot/pionex/dca_state.json'
    )
    
    const data = await fs.readFile(statePath, 'utf-8')
    return JSON.parse(data)
  } catch {
    return null
  }
}

export async function GET() {
  const state = await getDCAState()
  
  if (!state) {
    return NextResponse.json({
      error: 'Bot state not found',
      status: 'not_initialized',
      balance: 100,
      realized_pnl: 0,
      total_trades: 0
    })
  }
  
  const winRate = state.total_trades > 0 
    ? (state.winning_trades / state.total_trades * 100).toFixed(1)
    : '0.0'
  
  return NextResponse.json({
    symbol: state.symbol || 'XRP_USDT',
    strategy: 'DCA Reversal',
    direction: state.direction || 'LONG',
    status: state.status || 'running',
    paperMode: true,
    
    balance: state.balance,
    initialBalance: state.initial_balance,
    realizedPnl: state.realized_pnl,
    totalPnl: state.realized_pnl,
    
    totalTrades: state.total_trades,
    winningTrades: state.winning_trades,
    losingTrades: state.losing_trades,
    winRate: `${winRate}%`,
    
    position: state.current_position ? {
      entries: state.current_position.entries,
      totalSize: state.current_position.total_size,
      averagePrice: state.current_position.average_price,
      safetyLevel: state.current_position.safety_level,
      unrealizedPnl: state.current_position.unrealized_pnl
    } : null,
    
    maxSafetyLevel: state.max_safety_level || 3,
    recentTrades: state.trade_history?.slice(-10).reverse() || [],
    
    lastUpdated: new Date().toISOString()
  })
}

export async function POST(request: NextRequest) {
  const { action } = await request.json()
  
  const statePath = path.join(
    process.env.HOME || '/home/yeatz',
    '.openclaw/workspace/btc-trading-bot/pionex/dca_state.json'
  )
  
  try {
    const data = await fs.readFile(statePath, 'utf-8')
    const state: DCAState = JSON.parse(data)
    
    switch (action) {
      case 'reset':
        state.balance = state.initial_balance
        state.realized_pnl = 0
        state.total_trades = 0
        state.winning_trades = 0
        state.losing_trades = 0
        state.current_position = null
        state.trade_history = []
        state.status = 'stopped'
        
        await fs.writeFile(statePath, JSON.stringify(state, null, 2))
        return NextResponse.json({ success: true, message: 'DCA Bot reset' })
        
      case 'start':
        state.status = 'running'
        await fs.writeFile(statePath, JSON.stringify(state, null, 2))
        return NextResponse.json({ success: true, message: 'DCA Bot started' })
        
      case 'stop':
        state.status = 'stopped'
        await fs.writeFile(statePath, JSON.stringify(state, null, 2))
        return NextResponse.json({ success: true, message: 'DCA Bot stopped' })
        
      case 'close_position':
        if (state.current_position) {
          state.current_position = null
          await fs.writeFile(statePath, JSON.stringify(state, null, 2))
          return NextResponse.json({ success: true, message: 'Position closed' })
        }
        return NextResponse.json({ error: 'No position to close' }, { status: 400 })
        
      default:
        return NextResponse.json({ error: 'Unknown action' }, { status: 400 })
    }
  } catch {
    return NextResponse.json({ error: 'Failed to execute action' }, { status: 500 })
  }
}
