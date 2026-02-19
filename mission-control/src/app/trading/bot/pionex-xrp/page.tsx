'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { ArrowLeft, RefreshCw, Play, Square, AlertTriangle } from 'lucide-react'

interface XRPBotData {
  symbol: string
  marketType: string
  status: string
  paperMode: boolean
  balance: number
  initialBalance: number
  realizedPnl: number
  unrealizedPnl: number
  totalPnl: number
  totalTrades: number
  winningTrades: number
  losingTrades: number
  winRate: string
  profitFactor: string
  position: {
    side: string
    size: number
    entryPrice: number
    stopPrice: number
    targetPrice: number
    unrealizedPnl: number
    entryTime: string
  } | null
  recentTrades: Array<{
    side: string
    size: number
    entry_price: number
    exit_price: number
    pnl: number
    exit_reason: string
    closed_at: string
  }>
  consecutiveLosses: number
  dailyPnl: number
  lastUpdated: string
}

export default function PionexXRPPage() {
  const [data, setData] = useState<XRPBotData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionLoading, setActionLoading] = useState(false)

  const fetchData = async () => {
    try {
      const res = await fetch('/api/pionex-xrp')
      if (!res.ok) throw new Error('Failed to fetch')
      const json = await res.json()
      setData(json)
    } catch {
      setError('Bot not running or state file missing')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    const interval = setInterval(fetchData, 30000)
    return () => clearInterval(interval)
  }, [])

  const handleAction = async (action: string) => {
    setActionLoading(true)
    try {
      const res = await fetch('/api/pionex-xrp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      })
      if (res.ok) {
        fetchData()
      }
    } catch (err) {
      console.error(err)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen bg-slate-900 text-white p-8 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-2 border-cyan-500 border-t-transparent rounded-full" />
      </main>
    )
  }

  if (error || !data) {
    return (
      <main className="min-h-screen bg-slate-900 text-white p-8">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-4 mb-6">
            <Link href="/trading" className="p-2 hover:bg-slate-800 rounded-lg">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <h1 className="text-2xl font-bold">Pionex XRP COIN-M PERP</h1>
          </div>
          
          <div className="bg-slate-800/50 rounded-xl p-8 text-center">
            <p className="text-slate-400 mb-4">{error || 'Bot not initialized'}</p>
            <button
              onClick={() => handleAction('start')}
              disabled={actionLoading}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg font-medium flex items-center gap-2 mx-auto"
            >
              <Play className="w-4 h-4" />
              Initialize Bot
            </button>
          </div>
        </div>
      </main>
    )
  }

  const isRunning = data.status === 'running'
  const isCircuitBroken = data.consecutiveLosses >= 3

  return (
    <main className="min-h-screen bg-slate-900 text-white p-4 md:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-6">
          <Link href="/trading" className="p-2 hover:bg-slate-800 rounded-lg">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold">Pionex XRP COIN-M PERP</h1>
            <p className="text-slate-400 text-sm">
              {data.symbol} • {data.marketType} • {data.paperMode ? '🧪 Paper' : '🔴 Live'}
            </p>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <button
              onClick={fetchData}
              className="p-2 hover:bg-slate-800 rounded-lg"
              disabled={loading}
            >
              <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
            </button>
            {isRunning ? (
              <button
                onClick={() => handleAction('stop')}
                disabled={actionLoading}
                className="px-3 py-2 bg-red-600/80 hover:bg-red-700 rounded-lg text-sm font-medium flex items-center gap-2"
              >
                <Square className="w-4 h-4" />
                Stop
              </button>
            ) : (
              <button
                onClick={() => handleAction('start')}
                disabled={actionLoading}
                className="px-3 py-2 bg-cyan-600 hover:bg-cyan-700 rounded-lg text-sm font-medium flex items-center gap-2"
              >
                <Play className="w-4 h-4" />
                Start
              </button>
            )}
          </div>
        </div>

        {/* Alerts */}
        {isCircuitBroken && (
          <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mb-6 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            <div>
              <p className="font-medium text-red-400">Circuit Breaker Active</p>
              <p className="text-sm text-slate-400">{data.consecutiveLosses} consecutive losses</p>
            </div>
            <button
              onClick={() => handleAction('reset_circuit_breaker')}
              disabled={actionLoading}
              className="ml-auto px-3 py-1 bg-red-600/80 hover:bg-red-700 rounded text-sm"
            >
              Reset
            </button>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {/* Balance */}
          <div className="bg-slate-800/50 rounded-xl p-4">
            <p className="text-slate-400 text-sm">Balance (XRP)</p>
            <p className="text-2xl font-bold">{data.balance.toFixed(4)}</p>
            <p className={`text-sm ${data.totalPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {data.totalPnl >= 0 ? '+' : ''}{data.totalPnl.toFixed(4)} XRP
            </p>
          </div>

          {/* Win Rate */}
          <div className="bg-slate-800/50 rounded-xl p-4">
            <p className="text-slate-400 text-sm">Win Rate</p>
            <p className="text-2xl font-bold">{data.winRate}</p>
            <p className="text-sm text-slate-400">
              {data.winningTrades}W / {data.losingTrades}L
            </p>
          </div>

          {/* Total Trades */}
          <div className="bg-slate-800/50 rounded-xl p-4">
            <p className="text-slate-400 text-sm">Total Trades</p>
            <p className="text-2xl font-bold">{data.totalTrades}</p>
            <p className="text-sm text-slate-400">
              Daily: {data.dailyPnl.toFixed(4)} XRP
            </p>
          </div>

          {/* Status */}
          <div className="bg-slate-800/50 rounded-xl p-4">
            <p className="text-slate-400 text-sm">Status</p>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-green-500 animate-pulse' : 'bg-slate-500'}`} />
              <p className="text-xl font-bold capitalize">{data.status}</p>
            </div>
            <p className="text-sm text-slate-400">
              {data.consecutiveLosses} consec. losses
            </p>
          </div>
        </div>

        {/* Position & Trades */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Current Position */}
          <div className="bg-slate-800/50 rounded-xl p-4">
            <h2 className="text-lg font-semibold mb-4">Current Position</h2>
            {data.position ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Side</span>
                  <span className={`font-medium ${data.position.side === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                    {data.position.side === 'BUY' ? 'LONG' : 'SHORT'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Size</span>
                  <span className="font-medium">{data.position.size.toFixed(2)} XRP</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Entry</span>
                  <span className="font-medium">${data.position.entryPrice.toFixed(4)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Stop</span>
                  <span className="font-medium text-red-400">${data.position.stopPrice.toFixed(4)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">Target</span>
                  <span className="font-medium text-green-400">${data.position.targetPrice.toFixed(4)}</span>
                </div>
                <div className="flex items-center justify-between pt-3 border-t border-slate-700">
                  <span className="text-slate-400">Unrealized P&L</span>
                  <span className={`font-bold ${data.position.unrealizedPnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {data.position.unrealizedPnl >= 0 ? '+' : ''}{data.position.unrealizedPnl.toFixed(4)} XRP
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8">No open position</p>
            )}
          </div>

          {/* Recent Trades */}
          <div className="bg-slate-800/50 rounded-xl p-4">
            <h2 className="text-lg font-semibold mb-4">Recent Trades</h2>
            {data.recentTrades.length > 0 ? (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                {data.recentTrades.map((trade, i) => (
                  <div key={i} className="bg-slate-700/30 rounded-lg p-3 text-sm">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`font-medium ${trade.side === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.side === 'BUY' ? 'LONG' : 'SHORT'}
                      </span>
                      <span className={`font-bold ${trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(4)} XRP
                      </span>
                    </div>
                    <div className="text-slate-400 text-xs space-y-1">
                      <div className="flex justify-between">
                        <span>{trade.size.toFixed(2)} XRP</span>
                        <span className="capitalize">{trade.exit_reason}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>${trade.entry_price.toFixed(4)} → ${trade.exit_price.toFixed(4)}</span>
                        <span>{new Date(trade.closed_at).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8">No trades yet</p>
            )}
          </div>
        </div>

        {/* Last Updated */}
        <p className="text-slate-500 text-sm mt-6 text-center">
          Last updated: {new Date(data.lastUpdated).toLocaleString()}
        </p>
      </div>
    </main>
  )
}
