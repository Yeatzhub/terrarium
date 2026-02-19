'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { 
  ArrowLeft, 
  Play, 
  Square, 
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Activity,
  DollarSign,
  Target,
  Clock,
  Wifi,
  WifiOff
} from 'lucide-react'

interface Position {
  symbol: string
  side: 'LONG' | 'SHORT'
  size: number
  entry_price: number
  stop_loss: number
  take_profit: number
  unrealized_pnl: number
}

interface Trade {
  symbol: string
  side: string
  size: number
  entry_price: number
  exit_price?: number
  pnl: number
  closed_at: string
}

interface BotData {
  status: string
  paper_mode: boolean
  balance: number
  initial_balance: number
  realized_pnl: number
  unrealized_pnl: number
  total_trades: number
  wins: number
  losses: number
  position: Position | null
  recent_trades: Trade[]
  logs: string[]
  timestamp: number
}

export default function ToobitLivePage() {
  const [data, setData] = useState<BotData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showCloseConfirm, setShowCloseConfirm] = useState(false)

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch('/api/toobit-live')
      if (!res.ok) throw new Error('Failed to fetch')
      const json = await res.json()
      setData(json)
      setError(null)
    } catch (err) {
      setError('Connection lost')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 2000)
    return () => clearInterval(interval)
  }, [fetchData])

  const handleStart = async () => {
    try {
      await fetch('/api/toobit-live', { method: 'POST', body: JSON.stringify({ action: 'start' }) })
      fetchData()
    } catch (err) {
      console.error('Failed to start bot:', err)
    }
  }

  const handleStop = async () => {
    try {
      await fetch('/api/toobit-live', { method: 'POST', body: JSON.stringify({ action: 'stop' }) })
      fetchData()
    } catch (err) {
      console.error('Failed to stop bot:', err)
    }
  }

  const handleCloseAll = async () => {
    try {
      await fetch('/api/toobit-live', { method: 'POST', body: JSON.stringify({ action: 'emergency_close' }) })
      setShowCloseConfirm(false)
      fetchData()
    } catch (err) {
      console.error('Failed to close positions:', err)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-slate-400">Loading Toobit Live Trading...</p>
        </div>
      </div>
    )
  }

  const balance = data?.balance ?? 100
  const initial = data?.initial_balance ?? 100
  const totalPnl = (data?.realized_pnl ?? 0) + (data?.unrealized_pnl ?? 0)
  const winRate = data?.total_trades ? (data.wins / data.total_trades * 100).toFixed(1) : '0.0'
  const progress = ((balance - initial) / initial * 100)

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <div className="border-b border-slate-800 bg-slate-950/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link 
                href="/trading" 
                className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                  Toobit Live Trading
                </h1>
                <p className="text-slate-400 text-sm">Real-time position and P&L tracking</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {!data?.paper_mode && (
                <span className="px-3 py-1 bg-red-500/20 text-red-400 border border-red-500/30 rounded-full text-xs font-medium flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" />
                  LIVE MONEY
                </span>
              )}
              <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors text-sm">
                Settings
              </button>
            </div>
          </div>

          {/* Warning Banner */}
          <div className="mt-4 p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-400 flex-shrink-0" />
            <p className="text-amber-200 text-sm">
              ⚠️ Warning: This bot trades with real money on Toobit. All trades are real and funds are at risk.
            </p>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Current Position Banner */}
        {data?.position && (
          <div className={`rounded-xl p-4 mb-6 border ${data.position.side === 'LONG' ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'} animate-pulse`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className={`p-3 rounded-full ${data.position.side === 'LONG' ? 'bg-green-500/20' : 'bg-red-500/20'}`}>
                  {data.position.side === 'LONG' ? (
                    <TrendingUp className={`w-8 h-8 ${data.position.side === 'LONG' ? 'text-green-400' : 'text-red-400'}`} />
                  ) : (
                    <TrendingDown className="w-8 h-8 text-red-400" />
                  )}
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`text-2xl font-bold ${data.position.side === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                      {data.position.side} POSITION
                    </span>
                    <span className="px-2 py-0.5 bg-slate-800 rounded text-xs text-slate-400">
                      ACTIVE
                    </span>
                  </div>
                  <p className="text-slate-400 text-sm">
                    {data.position.size.toFixed(4)} BTC @ ${data.position.entry_price.toLocaleString()} 
                    • Leverage: 10x
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className={`text-3xl font-bold ${data.position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {data.position.unrealized_pnl >= 0 ? '+' : ''}${data.position.unrealized_pnl.toFixed(2)}
                </p>
                <p className="text-xs text-slate-400">Unrealized P&L</p>
              </div>
            </div>
            
            {/* Target/Stop Bar */}
            <div className="mt-4 grid grid-cols-3 gap-2 text-center text-sm">
              <div className="bg-slate-900/50 rounded-lg p-2">
                <p className="text-slate-500 text-xs">Stop Loss</p>
                <p className="text-red-400 font-medium">${data.position.stop_loss.toLocaleString()}</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-2">
                <p className="text-slate-500 text-xs">Entry</p>
                <p className="text-slate-300 font-medium">${data.position.entry_price.toLocaleString()}</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-2">
                <p className="text-slate-500 text-xs">Take Profit</p>
                <p className="text-green-400 font-medium">${data.position.take_profit.toLocaleString()}</p>
              </div>
            </div>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {/* Account Balance */}
          <div className="rounded-xl p-4 border border-cyan-500/30 bg-cyan-500/5">
            <div className="flex items-center gap-2 text-cyan-400 mb-2">
              <DollarSign className="w-4 h-4" />
              <span className="text-sm font-medium">Account Balance</span>
            </div>
            <p className="text-2xl font-bold">${balance.toFixed(2)}</p>
            <p className="text-xs text-slate-400 mt-1">Started: ${initial.toFixed(2)}</p>
            <div className="mt-3">
              <div className="flex justify-between text-xs text-slate-400 mb-1">
                <span>Progress to $200</span>
                <span>{progress.toFixed(1)}%</span>
              </div>
              <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-cyan-500 to-green-500 transition-all"
                  style={{ width: `${Math.min(Math.max(progress, 0), 100)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Active Position */}
          <div className="rounded-xl p-4 border border-slate-700 bg-slate-900/50">
            <div className="flex items-center gap-2 text-slate-400 mb-2">
              <Activity className="w-4 h-4" />
              <span className="text-sm font-medium">Active Position</span>
            </div>
            {data?.position ? (
              <>
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-lg font-bold ${data.position.side === 'LONG' ? 'text-green-400' : 'text-red-400'}`}>
                    {data.position.side}
                  </span>
                  <span className="text-xs text-slate-400">{data.position.size.toFixed(4)} BTC</span>
                </div>
                <p className="text-sm text-slate-400">Entry: ${data.position.entry_price.toLocaleString()}</p>
                <p className={`text-sm font-medium ${data.position.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  Unrealized: ${data.position.unrealized_pnl.toFixed(2)}
                </p>
              </>
            ) : (
              <div className="flex flex-col items-center justify-center py-2">
                <span className="text-2xl mb-1">⏳</span>
                <p className="text-slate-500 text-sm">Waiting for signal...</p>
              </div>
            )}
          </div>

          {/* Performance */}
          <div className="rounded-xl p-4 border border-slate-700 bg-slate-900/50">
            <div className="flex items-center gap-2 text-slate-400 mb-2">
              <Target className="w-4 h-4" />
              <span className="text-sm font-medium">Today's Performance</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-slate-500">Trades:</span>
                <span className="ml-1 font-medium">{data?.total_trades ?? 0}</span>
              </div>
              <div>
                <span className="text-slate-500">Win Rate:</span>
                <span className="ml-1 font-medium">{winRate}%</span>
              </div>
              <div>
                <span className="text-slate-500">Wins:</span>
                <span className="ml-1 text-green-400">{data?.wins ?? 0}</span>
              </div>
              <div>
                <span className="text-slate-500">Losses:</span>
                <span className="ml-1 text-red-400">{data?.losses ?? 0}</span>
              </div>
            </div>
          </div>

          {/* Bot Status */}
          <div className="rounded-xl p-4 border border-slate-700 bg-slate-900/50">
            <div className="flex items-center gap-2 text-slate-400 mb-2">
              <Activity className="w-4 h-4" />
              <span className="text-sm font-medium">Bot Status</span>
            </div>
            <div className="flex items-center gap-2 mb-2">
              {(data?.status === 'running') ? (
                <>
                  <Wifi className="w-4 h-4 text-green-400" />
                  <span className="text-green-400 font-medium">Running</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-4 h-4 text-slate-500" />
                  <span className="text-slate-500 font-medium">Stopped</span>
                </>
              )}
            </div>
            <p className="text-xs text-slate-500">
              Last update: {data?.timestamp ? new Date(data.timestamp).toLocaleTimeString() : '-'}
            </p>
            <p className="text-xs text-slate-500">
              Mode: {data?.paper_mode ? 'Paper Trading' : 'LIVE'}
            </p>
          </div>
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Charts & Trades */}
          <div className="lg:col-span-2 space-y-6">
            {/* Price Chart Placeholder */}
            <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-cyan-400" />
                Price Chart
              </h2>
              <div className="h-64 flex items-center justify-center bg-slate-800/50 rounded-lg">
                <p className="text-slate-500">Price chart integration coming soon</p>
              </div>
            </div>

            {/* Recent Trades */}
            <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-6">
              <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Clock className="w-5 h-5 text-cyan-400" />
                Recent Trades
              </h2>
              {data?.recent_trades && data.recent_trades.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-slate-500 border-b border-slate-800">
                        <th className="text-left py-2">Time</th>
                        <th className="text-left">Side</th>
                        <th className="text-right">Size</th>
                        <th className="text-right">Entry</th>
                        <th className="text-right">P&L</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recent_trades.slice(0, 10).map((trade, i) => (
                        <tr key={i} className="border-b border-slate-800/50 last:border-0">
                          <td className="py-3 text-slate-400">
                            {new Date(trade.closed_at).toLocaleTimeString()}
                          </td>
                          <td className={trade.side === 'LONG' ? 'text-green-400' : 'text-red-400'}>
                            {trade.side}
                          </td>
                          <td className="text-right">{trade.size.toFixed(4)}</td>
                          <td className="text-right">${trade.entry_price.toLocaleString()}</td>
                          <td className={`text-right ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                            {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">No trades yet</p>
              )}
            </div>
          </div>

          {/* Right Column - Controls & Info */}
          <div className="space-y-6">
            {/* Position Details */}
            <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-6">
              <h2 className="text-lg font-semibold mb-4">Position Details</h2>
              {data?.position ? (
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Liquidation Price</span>
                    <span className="text-red-400">Calculated...</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Margin Used</span>
                    <span>${(data.position.size * data.position.entry_price / 10).toFixed(2)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Leverage</span>
                    <span>10x</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Stop Loss</span>
                    <span className="text-red-400">${data.position.stop_loss.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Take Profit</span>
                    <span className="text-green-400">${data.position.take_profit.toLocaleString()}</span>
                  </div>
                </div>
              ) : (
                <p className="text-slate-500 text-center py-4">No open position</p>
              )}
            </div>

            {/* Controls */}
            <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-6">
              <h2 className="text-lg font-semibold mb-4">Controls</h2>
              <div className="space-y-3">
                {data?.status === 'running' ? (
                  <button
                    onClick={handleStop}
                    className="w-full py-3 bg-red-500/20 hover:bg-red-500/30 border border-red-500/50 text-red-400 rounded-lg transition-colors flex items-center justify-center gap-2"
                  >
                    <Square className="w-4 h-4" />
                    Stop Bot
                  </button>
                ) : (
                  <button
                    onClick={handleStart}
                    className="w-full py-3 bg-green-500/20 hover:bg-green-500/30 border border-green-500/50 text-green-400 rounded-lg transition-colors flex items-center justify-center gap-2"
                  >
                    <Play className="w-4 h-4" />
                    Start Bot
                  </button>
                )}
                
                <button
                  onClick={() => setShowCloseConfirm(true)}
                  className="w-full py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2"
                >
                  <AlertTriangle className="w-4 h-4" />
                  Emergency Close All
                </button>
              </div>
            </div>

            {/* System Log */}
            <div className="rounded-xl border border-slate-700 bg-slate-900/50 p-6">
              <h2 className="text-lg font-semibold mb-4">System Log</h2>
              <div className="h-48 overflow-y-auto bg-slate-950 rounded-lg p-3 text-xs font-mono space-y-1">
                {data?.logs?.map((log, i) => (
                  <p key={i} className="text-slate-400">
                    [{new Date().toLocaleTimeString()}] {log}
                  </p>
                )) || <p className="text-slate-600">Waiting for logs...</p>}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Emergency Close Confirmation */}
      {showCloseConfirm && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 rounded-xl p-6 max-w-md w-full border border-red-500/50">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="w-8 h-8 text-red-500" />
              <h3 className="text-xl font-bold text-red-400">Emergency Close</h3>
            </div>
            <p className="text-slate-300 mb-6">
              This will immediately close ALL open positions and cancel all orders. 
              This cannot be undone.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowCloseConfirm(false)}
                className="flex-1 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleCloseAll}
                className="flex-1 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
              >
                Close All Positions
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
