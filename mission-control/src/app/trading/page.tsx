'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

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
  message?: string
  fees?: {
    total_fees_sol: number
    total_gross_profit_sol: number
    total_net_profit_sol: number
    fee_efficiency_pct: number
  }
  performance?: {
    wins: number
    losses: number
    win_rate_pct: number
    avg_profit_sol: number
  }
  trade_history?: TradeHistory[]
}

interface TradeHistory {
  timestamp: string
  trade_id: number
  route: string
  gross_profit_sol: number
  jupiter_fees_sol: number
  gas_fees_sol: number
  slippage_sol: number
  total_fees_sol: number
  net_profit_sol: number
  balance_before_sol: number
  balance_after_sol: number
  strategy: string
  mode: string
  is_simulation: boolean
  profit_pct: number
}

export default function TradingPage() {
  const [krakenData, setKrakenData] = useState<PaperState | null>(null)
  const [toobitData, setToobitData] = useState<PaperState | null>(null)
  const [jupiterData, setJupiterData] = useState<JupiterState | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'kraken' | 'toobit' | 'jupiter'>('kraken')
  const [solPrice, setSolPrice] = useState<number>(140)

  useEffect(() => {
    fetchTradingData()
    fetchSolPrice()
    const interval = setInterval(() => {
      fetchTradingData()
      fetchSolPrice()
    }, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  async function fetchTradingData() {
    try {
      // Fetch Kraken paper state
      const krakenRes = await fetch('/api/trading-data?exchange=kraken')
      if (krakenRes.ok) {
        setKrakenData(await krakenRes.json())
      }

      // Fetch Toobit paper state
      const toobitRes = await fetch('/api/trading-data?exchange=toobit')
      if (toobitRes.ok) {
        setToobitData(await toobitRes.json())
      }

      // Fetch Jupiter data
      const jupiterRes = await fetch('/api/jupiter-data')
      if (jupiterRes.ok) {
        setJupiterData(await jupiterRes.json())
      }
    } catch (err) {
      setError('Failed to load trading data')
    } finally {
      setLoading(false)
    }
  }

  async function fetchSolPrice() {
    try {
      const res = await fetch('https://price.jup.ag/v4/price?ids=So11111111111111111111111111111111111111112')
      if (res.ok) {
        const data = await res.json()
        const price = data?.data?.['So11111111111111111111111111111111111111112']?.price
        if (price) setSolPrice(price)
      }
    } catch {
      // Fallback to cached price
    }
  }

  const currentData = activeTab === 'kraken' ? krakenData : activeTab === 'toobit' ? toobitData : null
  const jupiterCurrent = activeTab === 'jupiter'

  const totalValue = currentData 
    ? currentData.balance + Object.values(currentData.positions).reduce((sum, pos) => sum + (pos.size * pos.entry_price), 0) 
    : 0
  const totalReturn = currentData && currentData.initial_balance > 0 ? ((totalValue / currentData.initial_balance) - 1) * 100 : 0

  return (
    <main className="min-h-screen bg-slate-900 text-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-green-400 to-blue-500 bg-clip-text text-transparent">
              Trading Dashboard
            </h1>
            <p className="text-slate-400 mt-1">CEX + DEX positions & trade history</p>
            <p className="text-sm text-slate-500 mt-1">SOL Price: ${solPrice.toFixed(2)}</p>
          </div>
          <Link 
            href="/"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
          >
            ← Back to Mission Control
          </Link>
        </div>

        {/* Exchange Tabs */}
        <div className="flex gap-4 mb-6">
          <button
            onClick={() => setActiveTab('kraken')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'kraken' 
                ? 'bg-purple-600 text-white' 
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            🐙 Kraken (CEX)
          </button>
          <button
            onClick={() => setActiveTab('toobit')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'toobit' 
                ? 'bg-yellow-600 text-white' 
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            🔶 Toobit (CEX)
          </button>
          <button
            onClick={() => setActiveTab('jupiter')}
            className={`px-6 py-3 rounded-lg font-medium transition-colors ${
              activeTab === 'jupiter' 
                ? 'bg-pink-600 text-white' 
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700'
            }`}
          >
            🪐 Jupiter (DEX)
          </button>
        </div>

        {loading ? (
          <div className="text-center py-20">
            <div className="animate-spin w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
            <p className="text-slate-400">Loading trading data...</p>
          </div>
        ) : error ? (
          <div className="bg-red-900/30 border border-red-700 rounded-xl p-6 text-center">
            <p className="text-red-400">{error}</p>
            <button 
              onClick={fetchTradingData}
              className="mt-4 px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg"
            >
              Retry
            </button>
          </div>
        ) : jupiterCurrent ? (
          // Jupiter DEX View
          <JupiterView data={jupiterData} solPrice={solPrice} />
        ) : currentData ? (
          <>
            {/* Account Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <StatCard 
                label="Balance" 
                value={`$${currentData.balance.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}
                change={null}
                color="blue"
              />
              <StatCard 
                label="Total Value" 
                value={`$${totalValue.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}
                change={totalReturn >= 0 ? `+${totalReturn.toFixed(2)}%` : `${totalReturn.toFixed(2)}%`}
                color={totalReturn >= 0 ? 'green' : 'red'}
                positive={totalReturn >= 0}
              />
              <StatCard 
                label="Realized P&L" 
                value={`$${currentData.realized_pnl.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}
                change={currentData.realized_pnl >= 0 ? '+' : ''}
                color={currentData.realized_pnl >= 0 ? 'green' : 'red'}
                positive={currentData.realized_pnl >= 0}
              />
              <StatCard 
                label="Total Fees" 
                value={`$${currentData.total_fees.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}
                change={null}
                color="yellow"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Open Positions */}
              <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <span>📊</span> Open Positions
                  </h2>
                  <span className="text-sm text-slate-400">
                    {Object.keys(currentData.positions).length} active
                  </span>
                </div>

                {Object.keys(currentData.positions).length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    No open positions
                  </div>
                ) : (
                  <div className="space-y-3">
                    {Object.values(currentData.positions).map((pos, i) => (
                      <div key={i} className="bg-slate-700/50 rounded-lg p-4 border border-slate-600">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <span className="font-medium text-lg">{pos.symbol}</span>
                            <span className={`ml-2 text-xs px-2 py-1 rounded ${
                              pos.side === 'long' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                            }`}>
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
                  <h2 className="text-xl font-semibold flex items-center gap-2">
                    <span>📜</span> Trade History
                  </h2>
                  <span className="text-sm text-slate-400">
                    {currentData.trades.length} total
                  </span>
                </div>

                {currentData.trades.length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    No trades yet
                  </div>
                ) : (
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {[...currentData.trades].reverse().slice(0, 20).map((trade, i) => (
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

            {/* Summary Stats */}
            <div className="mt-6 bg-slate-800 rounded-xl p-6 border border-slate-700">
              <h2 className="text-xl font-semibold mb-4">Performance Summary</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <p className="text-slate-400 text-sm mb-1">Total Trades</p>
                  <p className="text-2xl font-bold">{currentData.trades.length}</p>
                </div>
                <div className="text-center">
                  <p className="text-slate-400 text-sm mb-1">Win Rate</p>
                  <p className="text-2xl font-bold">
                    {(() => {
                      const completed = currentData.trades.filter(t => t.side === 'sell' && t.pnl !== 0)
                      const wins = completed.filter(t => t.pnl > 0)
                      return completed.length > 0 ? `${((wins.length / completed.length) * 100).toFixed(1)}%` : '0%'
                    })()}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-slate-400 text-sm mb-1">Avg Trade</p>
                  <p className="text-2xl font-bold">
                    ${currentData.trades.length > 0 
                      ? (currentData.trades.reduce((sum, t) => sum + t.value, 0) / currentData.trades.length).toFixed(2)
                      : '0.00'}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-slate-400 text-sm mb-1">Total Fees</p>
                  <p className="text-2xl font-bold text-yellow-400">${currentData.total_fees.toFixed(2)}</p>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="bg-slate-800 rounded-xl p-8 text-center border border-slate-700">
            <p className="text-slate-400 mb-4">No trading data available</p>
            <p className="text-sm text-slate-500">
              Start the {activeTab} bot to generate paper trading data
            </p>
          </div>
        )}
      </div>
    </main>
  )
}

function JupiterView({ data, solPrice }: { data: JupiterState | null, solPrice: number }) {
  if (!data) {
    return (
      <div className="bg-slate-800 rounded-xl p-8 text-center border border-slate-700">
        <p className="text-slate-400">Loading Jupiter data...</p>
      </div>
    )
  }

  const balanceUsd = data.balance_sol * solPrice
  const initialUsd = data.initial_balance * solPrice
  const pnlUsd = data.pnl_sol * solPrice

  return (
    <>
      {/* Live SOL Price Banner */}
      <div className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 rounded-xl p-4 border border-purple-500/30 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <span className="text-3xl">◎</span>
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
            </div>
            <div>
              <p className="text-slate-400 text-sm">Live SOL Price</p>
              <p className="text-2xl font-bold text-white">${solPrice.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-slate-400 text-sm">Portfolio Value</p>
            <p className="text-xl font-bold text-green-400">${balanceUsd.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}</p>
          </div>
        </div>
      </div>

      {/* Jupiter Account Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <StatCard 
          label="SOL Balance" 
          value={`${data.balance_sol.toFixed(4)} SOL`}
          change={`≈ $${balanceUsd.toFixed(2)}`}
          color="blue"
        />
        <StatCard 
          label="Total Value" 
          value={`$${(balanceUsd).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`}
          change={data.pnl_pct >= 0 ? `+${data.pnl_pct.toFixed(2)}%` : `${data.pnl_pct.toFixed(2)}%`}
          color={data.pnl_pct >= 0 ? 'green' : 'red'}
          positive={data.pnl_pct >= 0}
        />
        <StatCard 
          label="P&L" 
          value={`${data.pnl_sol >= 0 ? '+' : ''}${data.pnl_sol.toFixed(4)} SOL`}
          change={`≈ ${pnlUsd >= 0 ? '+' : ''}$${Math.abs(pnlUsd).toFixed(2)}`}
          color={data.pnl_sol >= 0 ? 'green' : 'red'}
          positive={data.pnl_sol >= 0}
        />
        <StatCard 
          label="Strategy" 
          value={data.strategy.toUpperCase()}
          change={data.mode === 'paper' ? 'Paper Trading' : 'LIVE'}
          color="pink"
        />
      </div>

      {/* Jupiter Status */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 mb-6">
        <h2 className="text-xl font-semibold mb-4">🪐 Jupiter DEX Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-slate-700/50 rounded-lg p-4">
            <p className="text-slate-400 text-sm">Status</p>
            <p className={`text-lg font-medium ${data.status === 'active' ? 'text-green-400' : 'text-yellow-400'}`}>
              {data.status === 'active' ? '🟢 Active' : '⚠️ Not Running'}
            </p>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-4">
            <p className="text-slate-400 text-sm">Trades Executed</p>
            <p className="text-2xl font-bold">{data.trades}</p>
          </div>
          <div className="bg-slate-700/50 rounded-lg p-4">
            <p className="text-slate-400 text-sm">Mode</p>
            <p className="text-lg font-medium">{data.mode.toUpperCase()}</p>
          </div>
        </div>
        
        {/* Fee Breakdown */}
        {data.fees && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-700/30 rounded-lg p-3 text-center">
              <p className="text-slate-500 text-xs mb-1">Total Gross</p>
              <p className="text-green-400 font-mono">+{data.fees.total_gross_profit_sol.toFixed(6)} SOL</p>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-3 text-center">
              <p className="text-slate-500 text-xs mb-1">Total Fees</p>
              <p className="text-yellow-400 font-mono">-{data.fees.total_fees_sol.toFixed(6)} SOL</p>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-3 text-center">
              <p className="text-slate-500 text-xs mb-1">Fee Efficiency</p>
              <p className="text-pink-400 font-mono">{data.fees.fee_efficiency_pct.toFixed(2)}%</p>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-3 text-center">
              <p className="text-slate-500 text-xs mb-1">Net Profit</p>
              <p className={`font-mono ${data.fees.total_net_profit_sol >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {data.fees.total_net_profit_sol >= 0 ? '+' : ''}{data.fees.total_net_profit_sol.toFixed(6)} SOL
              </p>
            </div>
          </div>
        )}
        
        {/* Performance Stats */}
        {data.performance && (
          <div className="mt-4 grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="bg-slate-700/30 rounded-lg p-3 text-center">
              <p className="text-slate-500 text-xs mb-1">Win Rate</p>
              <p className="text-blue-400 font-bold">{data.performance.win_rate_pct.toFixed(1)}%</p>
              <p className="text-slate-600 text-xs">{data.performance.wins}W / {data.performance.losses}L</p>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-3 text-center">
              <p className="text-slate-500 text-xs mb-1">Avg Profit/Trade</p>
              <p className={`font-bold ${data.performance.avg_profit_sol >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {data.performance.avg_profit_sol >= 0 ? '+' : ''}{data.performance.avg_profit_sol.toFixed(6)} SOL
              </p>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-3 text-center">
              <p className="text-slate-500 text-xs mb-1">Total Return</p>
              <p className={`font-bold ${data.pnl_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {data.pnl_pct >= 0 ? '+' : ''}{data.pnl_pct.toFixed(2)}%
              </p>
            </div>
          </div>
        )}
        
        {data.message && (
          <div className="mt-4 p-4 bg-yellow-900/30 border border-yellow-700 rounded-lg">
            <p className="text-yellow-400 text-sm">{data.message}</p>
            <code className="block mt-2 text-xs bg-slate-800 p-2 rounded">
              cd solana-jupiter-bot && python jupiter_bot.py --mode paper --capital 1.0
            </code>
          </div>
        )}
      </div>

      {/* Trade History */}
      {data.trade_history && data.trade_history.length > 0 && (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center gap-2">
              <span>📜</span> Trade History
            </h2>
            <span className="text-sm text-slate-400">
              {data.trade_history.length} trades
            </span>
          </div>
          
          <div className="space-y-3 max-h-[400px] overflow-y-auto">
            {[...data.trade_history].reverse().slice(0, 20).map((trade, i) => {
              const date = new Date(trade.timestamp)
              const time = date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
              const emoji = trade.net_profit_sol > 0 ? '🟢' : trade.net_profit_sol < 0 ? '🔴' : '⚪'
              const simTag = trade.is_simulation ? '[SIM]' : ''
              
              return (
                <div key={i} className="bg-slate-700/40 rounded-lg p-4 border border-slate-600">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{emoji}</span>
                      <span className="text-sm text-slate-400">#{trade.trade_id.toString().padStart(4, '0')}</span>
                      <span className="text-sm font-mono text-slate-500">{time}</span>
                      {simTag && <span className="text-xs px-2 py-0.5 bg-purple-500/30 text-purple-400 rounded">{simTag}</span>}
                    </div>
                    <span className={`font-mono font-bold ${trade.net_profit_sol >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {trade.net_profit_sol >= 0 ? '+' : ''}{trade.net_profit_sol.toFixed(6)} SOL
                    </span>
                  </div>
                  
                  <div className="text-sm text-slate-400 mb-2">
                    Route: <span className="text-slate-300">{trade.route}</span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
                    <div className="bg-slate-800/50 rounded p-2">
                      <p className="text-slate-500">Gross</p>
                      <p className="text-green-400 font-mono">+{trade.gross_profit_sol.toFixed(6)}</p>
                    </div>
                    <div className="bg-slate-800/50 rounded p-2">
                      <p className="text-slate-500">Jupiter Fee</p>
                      <p className="text-yellow-400 font-mono">-{trade.jupiter_fees_sol.toFixed(6)}</p>
                    </div>
                    <div className="bg-slate-800/50 rounded p-2">
                      <p className="text-slate-500">Gas Fee</p>
                      <p className="text-orange-400 font-mono">-{trade.gas_fees_sol.toFixed(6)}</p>
                    </div>
                    <div className="bg-slate-800/50 rounded p-2">
                      <p className="text-slate-500">Slippage</p>
                      <p className="text-red-400 font-mono">-{trade.slippage_sol.toFixed(6)}</p>
                    </div>
                  </div>
                  
                  <div className="mt-2 text-xs text-slate-500">
                    Balance: {trade.balance_before_sol.toFixed(4)} → {trade.balance_after_sol.toFixed(4)} SOL
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Goal Progress */}
      <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
        <h2 className="text-xl font-semibold mb-4">🎯 Goal: Double 1 SOL → 2 SOL</h2>
        <div className="w-full bg-slate-700 rounded-full h-4 mb-4">
          <div 
            className="bg-gradient-to-r from-pink-500 to-purple-500 h-4 rounded-full transition-all duration-500"
            style={{ width: `${Math.min((data.balance_sol / 2) * 100, 100)}%` }}
          ></div>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">Start: 1.0 SOL</span>
          <span className="text-slate-400">Current: {data.balance_sol.toFixed(4)} SOL</span>
          <span className="text-slate-400">Goal: 2.0 SOL</span>
        </div>
        <p className="mt-4 text-sm text-slate-500">
          {data.balance_sol >= 2.0 
            ? '🎉 GOAL ACHIEVED!' 
            : `Need ${(2.0 - data.balance_sol).toFixed(4)} more SOL to reach goal`}
        </p>
      </div>
    </>
  )
}

function StatCard({ label, value, change, color, positive }: { 
  label: string
  value: string
  change: string | null
  color: 'blue' | 'green' | 'red' | 'yellow' | 'pink'
  positive?: boolean
}) {
  const colors = {
    blue: 'border-blue-500/30 bg-blue-500/10',
    green: 'border-green-500/30 bg-green-500/10',
    red: 'border-red-500/30 bg-red-500/10',
    yellow: 'border-yellow-500/30 bg-yellow-500/10',
    pink: 'border-pink-500/30 bg-pink-500/10'
  }

  return (
    <div className={`rounded-xl p-6 border ${colors[color]}`}>
      <p className="text-slate-400 text-sm mb-1">{label}</p>
      <p className="text-2xl font-bold">{value}</p>
      {change && (
        <p className={`text-sm mt-1 ${positive ? 'text-green-400' : color === 'pink' ? 'text-pink-400' : 'text-red-400'}`}>
          {change}
        </p>
      )}
    </div>
  )
}
