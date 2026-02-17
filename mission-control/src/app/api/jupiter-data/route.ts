import { NextRequest, NextResponse } from 'next/server'
import { readFile } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const endpoint = searchParams.get('endpoint') || 'status'

  try {
    // Check for Jupiter bot state file
    const possiblePaths = [
      path.join(process.cwd(), '..', 'solana-jupiter-bot', 'jupiter_state.json'),
      path.join(process.cwd(), '..', '..', 'solana-jupiter-bot', 'jupiter_state.json'),
      path.join('/home/yeatz/.openclaw/workspace', 'solana-jupiter-bot', 'jupiter_state.json'),
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
      // Return default state if Jupiter bot not running yet
      return NextResponse.json({
        status: 'not_initialized',
        balance_sol: 1.0,
        initial_balance: 1.0,
        pnl_sol: 0,
        pnl_pct: 0,
        trades: 0,
        strategy: 'arbitrage',
        mode: 'paper',
        timestamp: Date.now() / 1000,
        message: 'Jupiter bot not started - run: python jupiter_bot.py --mode paper --capital 1.0'
      })
    }

    const data = JSON.parse(fileContent)
    
    return NextResponse.json({
      ...data,
      status: 'active'
    })

  } catch (error) {
    console.error('Error reading Jupiter data:', error)
    return NextResponse.json(
      { 
        status: 'error',
        error: 'Failed to read Jupiter bot data',
        balance_sol: 1.0,
        initial_balance: 1.0,
        pnl_sol: 0,
        trades: 0
      },
      { status: 500 }
    )
  }
}
