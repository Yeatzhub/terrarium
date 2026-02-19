import { NextRequest, NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

export const dynamic = 'force-dynamic'

// Path to bot state file
const STATE_PATH = path.join(process.cwd(), '..', 'btc-trading-bot', 'toobit_live_state.json')

export async function GET() {
  try {
    // Default response
    const defaultData = {
      status: 'stopped',
      paper_mode: true,
      balance: 100.0,
      initial_balance: 100.0,
      realized_pnl: 0.0,
      unrealized_pnl: 0.0,
      total_trades: 0,
      wins: 0,
      losses: 0,
      position: null,
      recent_trades: [],
      logs: ['Bot not running - waiting for data...'],
      timestamp: Date.now()
    }

    // Check if state file exists
    if (!existsSync(STATE_PATH)) {
      return NextResponse.json(defaultData)
    }

    // Read state file
    const content = await readFile(STATE_PATH, 'utf-8')
    const state = JSON.parse(content)

    // Get stats
    const stats = {
      status: 'running', // Would need to check if process is actually running
      paper_mode: state.paper_mode ?? true,
      balance: state.balance ?? 100.0,
      initial_balance: state.initial_balance ?? 100.0,
      realized_pnl: state.realized_pnl ?? 0.0,
      unrealized_pnl: state.unrealized_pnl ?? 0.0,
      total_trades: state.total_trades ?? 0,
      wins: state.wins ?? 0,
      losses: state.losses ?? 0,
      position: state.positions ? Object.values(state.positions)[0] : null,
      recent_trades: (state.trades || []).slice(-20).reverse(),
      logs: ['Connection established'],
      timestamp: Date.now()
    }

    return NextResponse.json(stats)

  } catch (error) {
    console.error('Error reading Toobit state:', error)
    return NextResponse.json(
      { error: 'Failed to read bot state', status: 'error' },
      { status: 500 }
    )
  }
}

// Webhook endpoint for bot to send updates
export async function POST(request: NextRequest) {
  try {
    const data = await request.json()
    
    // Bot sends status updates here
    // In production, this would update a shared state or database
    
    return NextResponse.json({ received: true })
  } catch (error) {
    return NextResponse.json(
      { error: 'Invalid webhook data' },
      { status: 400 }
    )
  }
}
