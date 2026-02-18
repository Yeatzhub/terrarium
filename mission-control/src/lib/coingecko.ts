// CoinGecko API Client
// Free tier: https://api.coingecko.com/api/v3

const API_BASE = 'https://api.coingecko.com/api/v3'

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
      throw new Error(`CoinGecko API error: ${response.status}`)
    }
    const data = await response.json()
    cache = { data, timestamp: Date.now() }
    return data
  } catch (error) {
    console.error('CoinGecko fetch error:', error)
    // Return cached data if available, even if expired
    if (cache) return cache.data
    throw error
  }
}

export async function getTopCoins(limit: number = 20): Promise<Coin[]> {
  const url = `${API_BASE}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=${limit}&page=1&sparkline=true&price_change_percentage=24h`
  return fetchWithCache(url)
}

export async function getSimplePrice(ids: string[]): Promise<SimplePrice> {
  const idsParam = ids.join(',')
  const url = `${API_BASE}/simple/price?ids=${idsParam}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true`
  return fetchWithCache(url)
}

export async function getCoinData(id: string): Promise<any> {
  const url = `${API_BASE}/coins/${id}?localization=false&tickers=false&market_data=true&community_data=false&developer_data=false`
  return fetchWithCache(url)
}

// Common crypto IDs for our bots
export const BOT_COIN_IDS = {
  bitcoin: 'bitcoin',
  ethereum: 'ethereum',
  solana: 'solana',
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
  btcChange: number
  ethChange: number
  solChange: number
}> {
  try {
    const prices = await getSimplePrice([
      BOT_COIN_IDS.bitcoin,
      BOT_COIN_IDS.ethereum,
      BOT_COIN_IDS.solana,
    ])
    
    return {
      btc: prices.bitcoin?.usd || 0,
      eth: prices.ethereum?.usd || 0,
      sol: prices.solana?.usd || 0,
      btcChange: prices.bitcoin?.usd_24h_change || 0,
      ethChange: prices.ethereum?.usd_24h_change || 0,
      solChange: prices.solana?.usd_24h_change || 0,
    }
  } catch (error) {
    console.error('Error fetching bot coin prices:', error)
    return {
      btc: 0,
      eth: 0,
      sol: 0,
      btcChange: 0,
      ethChange: 0,
      solChange: 0,
    }
  }
}
