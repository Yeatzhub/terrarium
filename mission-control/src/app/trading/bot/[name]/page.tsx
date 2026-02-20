'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import { ArrowLeft, TrendingUp, TrendingDown, Play, Pause, AlertCircle, DollarSign, Activity } from 'lucide-react'

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

const BOT_CONFIG: Record<
  string,
  { name: string; icon: string; color: string; description: string; exchange: string }
> = {
  kraken: {
    name: 'Kraken Bot',
    icon: '🐙',
    color: 'purple',
    description: 'CEX trading bot for BTC, ETH, and major pairs',
    exchange: 'kraken',
  },
  toobit: {
    name: 'Toobit Bot',
    icon: '🔶',
    color: 'yellow',
    description: 'Perpetual futures trading with advanced strategies',
    exchange: 'toobit',
  },
  jupiter: {
    name: 'Jupiter Bot',
    icon: '🪐',
    color: 'pink',
    description: 'Solana DEX arbitrage and momentum trading',
    exchange: 'jupiter',
  },
  'pionex-xrp': {
    name: 'Pionex XRP',
    icon: '⚡',
    color: 'cyan',
    description: 'XRP COIN-M PERP futures with trend strategy',
    exchange: 'pionex',
  },
  'pionex-btc': {
    name: 'Pionex BTC',
    icon: '₿',
    color: 'orange',
    description: 'BTC aggressive breakout strategy',
    exchange: 'pionex',
  },
  'pionex-dca': {
    name: 'Pionex DCA',
    icon: '📊',
    color: 'indigo',
    description: 'Mean reversion with 3 safety levels',
    exchange: 'pionex',
  },
}

export default function BotDetailPage() {
  const params = useParams()
  const botName = (params.name as string)?.toLowerCase() || ''
  
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [livePrices, setLivePrices] = useState({
    btc: 0,
    eth: 0,
    xrp: 0,
    sol: 0,
    btcChange: 0,
    ethChange: 0,
    xrpChange: 0,
    solChange: 0,
  })
  
  // Bot data
  const [krakenData, setKrakenData] = useState<PaperState | null>(null)
  const [toobitData, setToobitData] = useState<PaperState | null>(null)
  const [jupiterData, setJupiterData] = useState<JupiterState | null>(null)
  const [pionexXrpData, setPionexXrpData] = useState<any>(null)
  const [pionexBtcData, setPionexBtcData] = useState<any>(null)
  const [pionexDcaData, setPionexDcaData] = useState<any>(null)

  const config = BOT_CONFIG[botName]
  const isJupiter = botName === 'jupiter'
  const isPionex = botName.startsWith('pionex')
  
  // Get current data based on bot
  const currentData = botName === 'kraken' ? krakenData : botName === 'toobit' ? toobitData : null

  useEffect(() => {
    if (!config) return
    
    fetchData()
    fetchPrices()
    
    const interval = setInterval(() => {
      fetchData()
      fetchPrices()
    }, 30000)
    
    return () => clearInterval(interval)
  }, [botName])

  async function fetchPrices() {
    try {
      const res = await fetch('/api/coingecko?endpoint=bot-prices')
      if (res.ok) {
        const data = await res.json()
        setLivePrices({
          btc: data.btc || 0,
          eth: data.eth || 0,
          xrp: data.xrp || 0,
          sol: data.sol || 0,
          btcChange: data.btcChange || 0,
          ethChange: data.ethChange || 0,
          xrpChange: data.xrpChange || 0,
          solChange: data.solChange || 0,
        })
      }
    } catch (error) {
      console.error('Error fetching prices:', error)
    }
  }

  async function fetchData() {
    setLoading(true)
    try {
      if (isJupiter) {
        const jupiterRes = await fetch('/api/jupiter-data')
        if (jupiterRes.ok) {
          setJupiterData(await jupiterRes.json())
        }
      } else if (isPionex) {
        // Fetch Pionex data based on specific bot
        const endpoint = botName === 'pionex-xrp' ? '/api/pionex-xrp' : 
                        botName === 'pionex-btc' ? '/api/pionex-btc' : 
                        '/api/pionex-dca'
        const res = await fetch(endpoint)
        if (res.ok) {
          const data = await res.json()
          if (botName === 'pionex-xrp') {
            setPionexXrpData(data)
          } else if (botName === 'pionex-btc') {
            setPionexBtcData(data)
          } else {
            setPionexDcaData(data)
          }
        }
      } else {
        // Fetch CEX data
        const res = await fetch(`/api/trading-data?exchange=${botName}`)
        if (res.ok) {
          const data = await res.json()
          if (botName === 'kraken') {
            setKrakenData(data)
          } else {
            setToobitData(data)
          }
        }
      }
    } catch (err) {
      setError('Failed to load bot data')
    } finally {
      setLoading(false)
    }
  }

  if (!config) {
    return (
      <div className="min-h-screen bg-slate-900 text-white p-8">
        <div className="max-w-4xl mx-auto">
          <Link href="/trading" className="text-slate-400 hover:text-white mb-4 inline-flex items-center gap-2">
            <ArrowLeft className="w-4 h-4" /> Back to Trading
          </Link>
          <div className="bg-red-900/30 border border-red-700 rounded-xl p-8 text-center mt-8">
            <AlertCircle className="w-12 h-12 text-red-400 mx-auto mb-4" />
            <h1 className="text-2xl font-bold mb-2">Bot Not Found</h1>
            <p className="text-slate-400">The bot "{botName}" does not exist.</p>
          </div>
        </div>
      </div>
    )
  }

  const solPrice = livePrices.sol || 140
  const jupiterBalanceUsd = jupiterData ? jupiterData.balance_sol * solPrice : 0

  return (
    <div className="min-h-screen bg-slate-900 text-white p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link href="/trading" className="text-slate-400 hover:text-white mb-4 inline-flex items-center gap-2 transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back to Trading Overview
          </Link>
          
          <div className="flex items-center gap-4 mt-4">
            <span className="text-4xl">{config.icon}</span>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                {config.name}
              </h1>
              <p className="text-slate-400 mt-1">{config.description}</p>
            </div>
          </div>
        </div>

        {/* Live Prices Banner */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <PriceCard symbol="BTC" price={livePrices.btc} change={livePrices.btcChange} />
          <PriceCard symbol="ETH" price={livePrices.eth} change={livePrices.ethChange} />
          <PriceCard symbol="XRP" price={livePrices.xrp} change={livePrices.xrpChange} />
          <PriceCard symbol="SOL" price={livePrices.sol} change={livePrices.solChange} />
        </div>

        {loading ? (
          <div className="text-center py-20">
            <div className="animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-slate-400">Loading bot data...</p>
          </div>
        ) : error ? (
          <div className="bg-red-900/30 border border-red-700 rounded-xl p-6 text-center">
            <p className="text-red-400">{error}</p>
            <button onClick={fetchData} className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg">
              Retry
            </button>
          </div>
        ) : isJupiter && jupiterData ? (
          /* Jupiter View */
          <JupiterDetailView data={jupiterData} solPrice={solPrice} />
        ) : currentData ? (
          /* CEX Bot View */
          <CEXDetailView data={currentData} botName={botName} />
        ) : (
          <div className="bg-slate-800 rounded-xl p-8 text-center border border-slate-700">
            <Pause className="w-12 h-12 text-slate-500 mx-auto mb-4" />
            <p className="text-slate-400 mb-2">Bot not running</p>
            <p className="text-sm text-slate-500">
              Start the {config.name} to begin trading
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function PriceCard({ symbol, price, change }: { symbol: string; price: number; change: number }) {
  const isPositive = change >= 0
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
      <p className="text-slate-400 text-sm mb-1">{symbol}</p>
      <p className="text-xl font-bold font-mono">${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
      <div className={`flex items-center gap-1 mt-1 text-sm ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
        {isPositive ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
        <span>{isPositive ? '+' : ''}{change.toFixed(2)}%</span>
      </div>
    </div>
  )
}

function JupiterDetailView({ data, solPrice }: { data: JupiterState; solPrice: number }) {
  const balanceUsd = data.balance_sol * solPrice
  const initialUsd = data.initial_balance * solPrice
  const pnlUsd = data.pnl_sol * solPrice
  
  return (
    <div className="space-y-6">
      {/* Status Card */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-slate-400 text-sm mb-1">Status</p>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${data.status === 'active' ? 'bg-green-500 animate-pulse' : 'bg-yellow-500'}`}></div>
              <span className={`font-medium ${data.status === 'active' ? 'text-green-400' : 'text-yellow-400'}`}>
                {data.status === 'active' ? 'Running' : 'Stopped'}
              </span>
            </div>
          </div>
          <div className="text-right">
            <p className="text-slate-400 text-sm mb-1">Strategy</p>
            <p className="font-medium text-pink-400">{data.strategy?.toUpperCase() || 'ARBITRAGE'}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatBox label="Balance" value={`${data.balance_sol.toFixed(4)} SOL`} subValue={`≈ $${balanceUsd.toFixed(2)}`} />
          <StatBox label="P&L SOL" value={`${data.pnl_sol >= 0 ? '+' : ''}${data.pnl_sol.toFixed(4)}`} subValue={`≈ ${pnlUsd >= 0 ? '+' : ''}$${Math.abs(pnlUsd).toFixed(2)}`} isPositive={data.pnl_sol >= 0} />
          <StatBox label="Return %" value={`${data.pnl_pct >= 0 ? '+' : ''}${data.pnl_pct.toFixed(2)}%`} isPositive={data.pnl_pct >= 0} />
          <StatBox label="Trades" value={data.trades.toString()} />
        </div>
      </div>

      {/* Goal Progress */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <DollarSign className="w-5 h-5 text-cyan-400" />
          Goal: Double 1 SOL → 2 SOL
        </h2>
        <div className="w-full bg-slate-700 rounded-full h-4 mb-4">
          <div
            className="bg-gradient-to-r from-pink-500 to-purple-500 h-4 rounded-full transition-all"
            style={{ width: `${Math.min((data.balance_sol / 2) * 100, 100)}%` }}
          />
        </div>
        <div className="flex justify-between text-sm text-slate-400">
          <span>Start: 1.0 SOL</span>
          <span>Current: {data.balance_sol.toFixed(4)} SOL</span>
          <span>Goal: 2.0 SOL</span>
        </div>
      </div>
    </div>
  )
}

function CEXDetailView({ data, botName }: { data: PaperState; botName: string }) {
  const totalValue = data.balance + Object.values(data.positions).reduce((sum, pos) => sum + (pos.size * pos.entry_price), 0)
  const totalReturn = data.initial_balance > 0 ? ((totalValue / data.initial_balance) - 1) * 100 : 0

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatBox label="Balance" value={`$${data.balance.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`} />
        <StatBox 
          label="Total Value" 
          value={`$${totalValue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          subValue={totalReturn >= 0 ? `+${totalReturn.toFixed(2)}%` : `${totalReturn.toFixed(2)}%`}
          isPositive={totalReturn >= 0}
        />
        <StatBox 
          label="Realized P&L" 
          value={`$${data.realized_pnl.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`}
          isPositive={data.realized_pnl >= 0}
        />
        <StatBox label="Total Fees" value={`$${data.total_fees.toFixed(2)}`} />
      </div>

      {/* Positions */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" />
            Open Positions
          </h2>
          <span className="text-sm text-slate-400">{Object.keys(data.positions).length} active</span>
        </div>

        {Object.keys(data.positions).length === 0 ? (
          <div className="text-center py-8 text-slate-500">No open positions</div>
        ) : (
          <div className="space-y-3">
            {Object.values(data.positions).map((pos, i) => (
              <div key={i} className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-lg">{pos.symbol}</span>
                    <span className={`text-xs px-2 py-1 rounded ${pos.side === 'long' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
                      {pos.side.toUpperCase()}
                    </span>
                  </div>
                  <span className="text-slate-400 text-sm">
                    {new Date(pos.opened_at * 1000).toLocaleDateString()}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <p className="text-slate-500">Size</p>
                    <p className="font-mono">{pos.size.toFixed(6)}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Entry</p>
                    <p className="font-mono">${pos.entry_price.toFixed(2)}</p>
                  </div>
                  <div>
                    <p className="text-slate-500">Fees</p>
                    <p className="font-mono">${pos.fees.toFixed(2)}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Trades */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-cyan-400" />
            Recent Trades
          </h2>
          <span className="text-sm text-slate-400">{data.trades.length} total</span>
        </div>

        {data.trades.length === 0 ? (
          <div className="text-center py-8 text-slate-500">No trades yet</div>
        ) : (
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {[...data.trades].reverse().slice(0, 20).map((trade, i) => (
              <div key={i} className="flex items-center justify-between bg-slate-700/30 rounded-lg p-3 border border-slate-600/50">
                <div className="flex items-center gap-3">
                  <span className={`text-xs px-2 py-1 rounded font-medium ${
                    trade.side === 'buy' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                  }`}>
                    {trade.side.toUpperCase()}
                  </span>
                  <div>
                    <p className="font-medium">{trade.symbol}</p>
                    <p className="text-xs text-slate-400">
                      {new Date(trade.timestamp * 1000).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-mono text-sm">${trade.price.toFixed(2)}</p>
                  <p className="text-xs text-slate-400">{trade.size.toFixed(6)} @ {trade.type}</p>
                  {trade.pnl !== 0 && (
                    <p className={`text-xs ${trade.pnl > 0 ? 'text-green-400' : 'text-red-400'}`}>
                      P&L: {trade.pnl > 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatBox({ 
  label, 
  value, 
  subValue, 
  isPositive 
}: { 
  label: string; 
  value: string; 
  subValue?: string;
  isPositive?: boolean;
}) {
  return (
    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700 text-center">
      <p className="text-slate-400 text-sm mb-1">{label}</p>
      <p className="text-xl font-bold font-mono">{value}</p>
      {subValue && (
        <p className={`text-sm mt-1 ${isPositive ? 'text-green-400' : 'text-red-400'}`}>{subValue}</p>
      )}
    </div>
  )
}
