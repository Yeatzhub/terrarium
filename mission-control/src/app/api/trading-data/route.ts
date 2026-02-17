import { NextRequest, NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const exchange = searchParams.get('exchange') || 'kraken'

  try {
    // Determine which state file to read
    const stateFile = exchange === 'toobit' 
      ? 'toobit_paper_state.json'
      : 'kraken_paper_state.json'
    
    // Look for the state file in btc-trading-bot directory
    const possiblePaths = [
      path.join(process.cwd(), '..', 'btc-trading-bot', stateFile),
      path.join(process.cwd(), '..', '..', 'btc-trading-bot', stateFile),
      path.join('/home/yeatz/.openclaw/workspace', 'btc-trading-bot', stateFile),
      path.join(process.cwd(), stateFile),
    ]

    let fileContent = null
    let foundPath = null

    for (const filePath of possiblePaths) {
      if (existsSync(filePath)) {
        fileContent = await readFile(filePath, 'utf-8')
        foundPath = filePath
        break
      }
    }

    if (!fileContent) {
      // Return default state if file doesn't exist yet
      return NextResponse.json({
        balance: 10000.0,
        initial_balance: 10000.0,
        realized_pnl: 0,
        total_fees: 0,
        positions: {},
        trades: [],
        timestamp: Date.now() / 1000,
        exchange,
        status: 'no_data'
      })
    }

    const data = JSON.parse(fileContent)
    
    return NextResponse.json({
      ...data,
      exchange,
      status: 'active'
    })

  } catch (error) {
    console.error('Error reading trading data:', error)
    return NextResponse.json(
      { error: 'Failed to read trading data' },
      { status: 500 }
    )
  }
}
