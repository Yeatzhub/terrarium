import { NextRequest, NextResponse } from 'next/server'
import {
  getTopCoins,
  getSimplePrice,
  getCoinData,
  getBotCoinPrices,
  BOT_COIN_IDS,
} from '@/lib/coingecko'

// Cache for Next.js fetch
export const dynamic = 'force-dynamic'
export const revalidate = 30 // Revalidate every 30 seconds

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams
  const endpoint = searchParams.get('endpoint') || 'prices'

  try {
    switch (endpoint) {
      case 'top': {
        const limit = parseInt(searchParams.get('limit') || '20')
        const coins = await getTopCoins(limit)
        return NextResponse.json({ coins, timestamp: Date.now() })
      }

      case 'simple': {
        const ids = searchParams.get('ids')?.split(',') || Object.keys(BOT_COIN_IDS)
        const prices = await getSimplePrice(ids)
        return NextResponse.json({ prices, timestamp: Date.now() })
      }

      case 'coin': {
        const id = searchParams.get('id')
        if (!id) {
          return NextResponse.json({ error: 'Coin ID required' }, { status: 400 })
        }
        const data = await getCoinData(id)
        return NextResponse.json({ coin: data, timestamp: Date.now() })
      }

      case 'bot-prices': {
        const prices = await getBotCoinPrices()
        return NextResponse.json({ ...prices, timestamp: Date.now() })
      }

      default:
        return NextResponse.json({ error: 'Invalid endpoint' }, { status: 400 })
    }
  } catch (error) {
    console.error('CoinGecko API error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch data from CoinGecko' },
      { status: 500 }
    )
  }
}
