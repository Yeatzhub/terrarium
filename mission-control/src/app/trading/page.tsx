'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { BarChart3, TrendingUp, TrendingDown, Play, Pause, AlertCircle, ArrowRight } from 'lucide-react'

interface Position {
  symbol: string
  side: string
  size: number
  entry_price: number
  fees: number
  opened_at: number
}

interface Trade {
  symbol: string
  side: string
  type: string
  size: number
  price: number
  value: number
  fees: number
  pnl: number
  timestamp: number
  datetime: string
}

interface PaperState {
  balance: number
  initial_balance: number
  realized_pnl: number
  total_fees: number
  positions: Record<string, Position>
  trades: Trade[]
  timestamp: number
  exchange: string
  status: string
}

interface JupiterState {
  balance_sol: number
  initial_balance: number
  pnl_sol: number
  pnl_pct: number
  trades: number
  strategy: string
  mode: string
  status: string
  timestamp: number
}

interface LivePrice {
  symbol: string
  name: string
  price: number
  change24h: number
}

const BOTS = [
  {
    id: 'kraken',
    name: 'Kraken Bot',
    icon: '🐙',
    color: 'purple',
    description: 'CEX trading for BTC, ETH pairs',
    exchange: 'kraken',
  },
  {
    id: 'toobit',
    name: 'Toobit Bot',
    icon: '🔶',
    color: 'yellow',
    description: 'Perpetual futures trading',
    exchange: 'toobit',
  },
  {
    id: 'jupiter',
    name: 'Jupiter Bot',
    icon: '🪐',
    color: 'pink',
    description: 'Solana DEX arbitrage',
    exchange: 'jupiter',
  },
]

export default function TradingPage() {
  const [loading, setLoading] = useState(true)
  const [krakenData, setKrakenData] = useState<PaperState | null>(null)
  const [toobitData, setToobitData] = useState<PaperState | null>(null)
  const [jupiterData, setJupiterData] = useState<JupiterState | null>(null)
  const [livePrices, setLivePrices] = useState<LivePrice[]>([])

  useEffect(() => {
    fetchAllData()
    fetchLivePrices()

    const interval = setInterval(() => {
      fetchAllData()
      fetchLivePrices()
    }, 30000) // Refresh every 30s

    return () => clearInterval(interval)
  }, [])

  async function fetchLivePrices() {
    try {
      const res = await fetch('/api/coingecko?endpoint=bot-prices')
      if (res.ok) {
        const data = await res.json()
        setLivePrices([
          { symbol: 'BTC', name: 'Bitcoin', price: data.btc || 0, change24h: data.btcChange || 0 },
          { symbol: 'ETH', name: 'Ethereum', price: data.eth || 0, change24h: data.ethChange || 0 },
          { symbol: 'SOL', name: 'Solana', price: data.sol || 0, change24h: data.solChange || 0 },
        ])
      }
    } catch (error) {
      console.error('Error fetching live prices:', error)
    }
  }

  async function fetchAllData() {
    try {
      const [krakenRes, toobitRes, jupiterRes] = await Promise.all([
        fetch('/api/trading-data?exchange=kraken'),
        fetch('/api/trading-data?exchange=toobit'),
        fetch('/api/jupiter-data'),
      ])

      if (krakenRes.ok) setKrakenData(await krakenRes.json())
      if (toobitRes.ok) setToobitData(await toobitRes.json())
      if (jupiterRes.ok) setJupiterData(await jupiterRes.json())

    } catch (err) {
      console.error('Failed to load trading data:', err)
    } finally {
      setLoading(false)
    }
  }

  const getBotData = (botId: string): { status: 'active' | 'inactive'; pnl: string; trades: number } => {
    switch (botId) {
      case 'kraken':
        return {
          status: krakenData?.status === 'active' ? 'active' : 'inactive',
          pnl: krakenData ? `$${krakenData.realized_pnl.toFixed(2)}` : '$0.00',
          trades: krakenData?.trades?.length || 0,
        }
      case 'toobit':
        return {
          status: toobitData?.status === 'active' ? 'active' : 'inactive',
          pnl: toobitData ? `$${toobitData.realized_pnl.toFixed(2)}` : '$0.00',
          trades: toobitData?.trades?.length || 0,
        }
      case 'jupiter':
        const jupiterPnl = jupiterData?.pnl_sol || 0
        const solPrice = livePrices.find(p => p.symbol === 'SOL')?.price || 140
        return {
          status: jupiterData?.status === 'active' ? 'active' : 'inactive',
          pnl: `${jupiterPnl >= 0 ? '+' : ''}${jupiterPnl.toFixed(4)} SOL (~$${(jupiterPnl * solPrice).toFixed(2)})`,
          trades: jupiterData?.trades || 0,
        }
      default:
        return { status: 'inactive', pnl: '$0.00', trades: 0 }
    }
  }

  return (
    <main className="min-h-screen bg-slate-900 text-white p-4 md:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent">
              Trading Dashboard
            </h1>
            <p className="text-slate-400 mt-1">CEX and DEX trading bots overview</p>
          </div>
          <Link
            href="/"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
          >
            ← Back to Mission Control
          </Link>
        </div>

        {/* Live Prices Ticker */}
        <LivePriceTicker prices={livePrices} />

        {/* Summary Stats */}
        <SummaryStats
          krakenData={krakenData}
          toobitData={toobitData}
          jupiterData={jupiterData}
          solPrice={livePrices.find(p => p.symbol === 'SOL')?.price || 140}
        />

        {/* Bot Cards */}
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-cyan-400" />
            Active Trading Bots
          </h2>

          {loading ? (
            <div className="text-center py-12">
              <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
              <p className="text-slate-400">Loading bot data...</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {BOTS.map((bot) => {
                const data = getBotData(bot.id)
                return (
                  <BotCard
                    key={bot.id}
                    bot={bot}
                    status={data.status}
                    pnl={data.pnl}
                    trades={data.trades}
                  />
                )
              })}
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <QuickActions />
      </div>
    </main>
  )
}

function LivePriceTicker({ prices }: { prices: LivePrice[] }) {
  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700 mb-6 overflow-hidden">
      <div className="flex items-center gap-6 overflow-x-auto scrollbar-hide">
        {prices.map((coin) => {
          const isPositive = coin.change24h >= 0
          return (
            <div key={coin.symbol} className="flex items-center gap-3 flex-shrink-0">
              <div className="flex flex-col">
                <span className="text-sm font-medium text-slate-300">{coin.name}</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-bold text-lg">
                    ${coin.price.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                  </span>
                  <span className={`text-xs flex items-center gap-0.5 ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
                    {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                    {isPositive ? '+' : ''}{coin.change24h.toFixed(2)}%
                  </span>
                </div>
              </div>
              {prices.indexOf(coin) < prices.length - 1 && (
                <div className="w-px h-10 bg-slate-700 mx-2"></div>
              )}
            </div>
          )
        })}
        {prices.length === 0 && (
          <div className="text-slate-500 text-sm">Loading live prices...</div>
        )}
      </div>
    </div>
  )
}

function SummaryStats({ krakenData, toobitData, jupiterData, solPrice }: {
  krakenData: PaperState | null
  toobitData: PaperState | null
  jupiterData: JupiterState | null
  solPrice: number
}) {
  const totalBalance = (krakenData?.balance || 0) + (toobitData?.balance || 0) + ((jupiterData?.balance_sol || 0) * solPrice)
  const totalPnl = (krakenData?.realized_pnl || 0) + (toobitData?.realized_pnl || 0) + ((jupiterData?.pnl_sol || 0) * solPrice)
  const totalTrades = (krakenData?.trades?.length || 0) + (toobitData?.trades?.length || 0) + (jupiterData?.trades || 0)
  const activeBots = [krakenData, toobitData, jupiterData].filter(d => d?.status === 'active').length

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <StatCard label="Total Balance" value={`$${totalBalance.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} color="blue" />
      <StatCard label="Total P&L" value={`$${totalPnl.toLocaleString('en-US', { minimumFractionDigits: 2 })}`} change={null} color={totalPnl >= 0 ? 'green' : 'red'} positive={totalPnl >= 0} />
      <StatCard label="Total Trades" value={totalTrades.toString()} color="purple" />
      <StatCard label="Active Bots" value={`${activeBots}/3`} color="cyan" />
    </div>
  )
}

function BotCard({ bot, status, pnl, trades }: {
  bot: typeof BOTS[0]
  status: 'active' | 'inactive'
  pnl: string
  trades: number
}) {
  const colorClasses: Record<string, { bg: string; border: string; text: string; hover: string }> = {
    purple: { bg: 'bg-purple-500/10', border: 'border-purple-500/30', text: 'text-purple-400', hover: 'hover:border-purple-500/60' },
    yellow: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/30', text: 'text-yellow-400', hover: 'hover:border-yellow-500/60' },
    pink: { bg: 'bg-pink-500/10', border: 'border-pink-500/30', text: 'text-pink-400', hover: 'hover:border-pink-500/60' },
  }

  const colors = colorClasses[bot.color]

  return (
    <Link href={`/trading/bot/${bot.id}`}>
      <div className={`bg-slate-800 rounded-xl p-6 border ${colors.border} ${colors.hover} transition-all cursor-pointer group`}>
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{bot.icon}</span>
            <div>
              <h3 className="font-semibold text-white group-hover:text-cyan-400 transition-colors">{bot.name}</h3>
              <p className="text-sm text-slate-400">{bot.description}</p>
            </div>
          </div>
          <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full ${status === 'active' ? 'bg-green-500/20' : 'bg-slate-700'}`}>
            <div className={`w-2 h-2 rounded-full ${status === 'active' ? 'bg-green-400 animate-pulse' : 'bg-slate-500'}`}></div>
            <span className="text-xs font-medium capitalize">{status}</span>
          </div>
        </div>

        <div className={`grid grid-cols-2 gap-4 p-4 rounded-lg ${colors.bg}`}>
          <div>
            <p className="text-slate-500 text-xs mb-1">P&L</p>
            <p className="font-mono text-sm font-medium">{pnl}</p>
          </div>
          <div>
            <p className="text-slate-500 text-xs mb-1">Trades</p>
            <p className="font-mono text-sm font-medium">{trades}</p>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2 text-sm text-slate-400 group-hover:text-cyan-400 transition-colors">
          <span>View Details</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </div>
      </div>
    </Link>
  )
}

function StatCard({ label, value, change, color, positive }: {
  label: string
  value: string
  change: string | null
  color: string
  positive?: boolean
}) {
  const colors: Record<string, string> = {
    blue: 'border-blue-500/30 bg-blue-500/10',
    green: 'border-green-500/30 bg-green-500/10',
    red: 'border-red-500/30 bg-red-500/10',
    purple: 'border-purple-500/30 bg-purple-500/10',
    yellow: 'border-yellow-500/30 bg-yellow-500/10',
    cyan: 'border-cyan-500/30 bg-cyan-500/10',
  }

  return (
    <div className={`rounded-xl p-4 border ${colors[color] || colors.blue}`}>
      <p className="text-slate-400 text-sm mb-1">{label}</p>
      <p className="text-xl font-bold">{value}</p>
      {change && (
        <p className={`text-sm mt-1 ${positive ? 'text-green-400' : 'text-red-400'}`}>{change}</p>
      )}
    </div>
  )
}

function QuickActions() {
  const actions = [
    { label: 'View All Trades', href: '/trading/history', color: 'blue' },
    { label: 'Bot Settings', href: '/trading/settings', color: 'purple' },
    { label: 'API Configuration', href: '/trading/api-keys', color: 'cyan' },
  ]

  return (
    <div className="mt-8">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <Play className="w-5 h-5 text-green-400" />
        Quick Actions
      </h2>
      <div className="flex flex-wrap gap-4">
        {actions.map((action) => (
          <Link
            key={action.label}
            href={action.href}
            className={`px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg hover:bg-slate-700 transition-colors text-sm`}
          >
            {action.label}
          </Link>
        ))}
      </div>
    </div>
  )
}
