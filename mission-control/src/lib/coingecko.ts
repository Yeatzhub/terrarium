// CoinGecko API Client with fallback
// Free tier: https://api.coingecko.com/api/v3

const API_BASE = 'https://api.coingecko.com/api/v3'

// Fallback prices when API is rate limited (updated Feb 20, 2026)
const FALLBACK_PRICES = {
  bitcoin: { usd: 67700, usd_24h_change: 1.2, usd_market_cap: 1340000000000 },
  ethereum: { usd: 2450, usd_24h_change: 0.8, usd_market_cap: 295000000000 },
  solana: { usd: 142, usd_24h_change: -1.5, usd_market_cap: 65000000000 },
  ripple: { usd: 1.42, usd_24h_change: 0.5, usd_market_cap: 82000000000 },
}

export interface Coin {
  id: string
  symbol: string
  name: string
  image: string
  current_price: number
  market_cap: number
  market_cap_rank: number
  price_change_24h: number
  price_change_percentage_24h: number
  sparkline_in_7d?: { price: number[] }
}

export interface SimplePrice {
  [coinId: string]: {
    usd: number
    usd_24h_change?: number
    usd_market_cap?: number
  }
}

// Cache for rate limiting
let cache: { data: any; timestamp: number } | null = null
const CACHE_TTL = 30 * 1000 // 30 seconds

async function fetchWithCache(url: string, options?: RequestInit): Promise<any> {
  // Check cache
  if (cache && Date.now() - cache.timestamp < CACHE_TTL) {
    return cache.data
  }

  try {
    const response = await fetch(url, options)
    if (!response.ok) {
      if (response.status === 429) {
        console.log('CoinGecko rate limited, using fallback')
        return FALLBACK_PRICES
      }
      throw new Error(`CoinGecko API error: ${response.status}`)
    }
    const data = await response.json()
    cache = { data, timestamp: Date.now() }
    return data
  } catch (error) {
    console.error('CoinGecko fetch error:', error)
    // Return fallback data on any error
    if (url.includes('simple/price')) {
      return FALLBACK_PRICES
    }
    if (cache) return cache.data
    return FALLBACK_PRICES
  }
}

export async function getTopCoins(limit: number = 20): Promise<Coin[]> {
  const url = `${API_BASE}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=${limit}&page=1&sparkline=true&price_change_percentage=24h`
  try {
    return await fetchWithCache(url)
  } catch (error) {
    // Return empty array if API fails
    return []
  }
}

export async function getSimplePrice(ids: string[]): Promise<SimplePrice> {
  const idsParam = ids.join(',')
  const url = `${API_BASE}/simple/price?ids=${idsParam}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true`
  return fetchWithCache(url)
}

export async function getCoinData(id: string): Promise<any> {
  const url = `${API_BASE}/coins/${id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false`
  try {
    return await fetchWithCache(url)
  } catch (error) {
    return null
  }
}

// Common crypto IDs for our bots
export const BOT_COIN_IDS = {
  bitcoin: 'bitcoin',
  ethereum: 'ethereum',
  solana: 'solana',
  ripple: 'ripple',  // XRP
  cardano: 'cardano',
  polkadot: 'polkadot',
  chainlink: 'chainlink',
  avalanche: 'avalanche-2',
  polygon: 'matic-network',
}

export async function getBotCoinPrices(): Promise<{
  btc: number
  eth: number
  sol: number
  xrp: number
  btcChange: number
  ethChange: number
  solChange: number
  xrpChange: number
}> {
  try {
    const prices = await getSimplePrice([
      BOT_COIN_IDS.bitcoin,
      BOT_COIN_IDS.ethereum,
      BOT_COIN_IDS.solana,
      BOT_COIN_IDS.ripple,
    ])

    return {
      btc: prices.bitcoin?.usd || FALLBACK_PRICES.bitcoin.usd,
      eth: prices.ethereum?.usd || FALLBACK_PRICES.ethereum.usd,
      sol: prices.solana?.usd || FALLBACK_PRICES.solana.usd,
      xrp: prices.ripple?.usd || FALLBACK_PRICES.ripple.usd,
      btcChange: prices.bitcoin?.usd_24h_change || FALLBACK_PRICES.bitcoin.usd_24h_change,
      ethChange: prices.ethereum?.usd_24h_change || FALLBACK_PRICES.ethereum.usd_24h_change,
      solChange: prices.solana?.usd_24h_change || FALLBACK_PRICES.solana.usd_24h_change,
      xrpChange: prices.ripple?.usd_24h_change || FALLBACK_PRICES.ripple.usd_24h_change,
    }
  } catch (error) {
    console.error('Error fetching bot coin prices:', error)
    return {
      btc: FALLBACK_PRICES.bitcoin.usd,
      eth: FALLBACK_PRICES.ethereum.usd,
      sol: FALLBACK_PRICES.solana.usd,
      xrp: FALLBACK_PRICES.ripple.usd,
      btcChange: FALLBACK_PRICES.bitcoin.usd_24h_change,
      ethChange: FALLBACK_PRICES.ethereum.usd_24h_change,
      solChange: FALLBACK_PRICES.solana.usd_24h_change,
      xrpChange: FALLBACK_PRICES.ripple.usd_24h_change,
    }
  }
}
