'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Play, Pause, AlertCircle, TrendingUp, ArrowRight } from 'lucide-react'

interface Bot {
  id: string
  name: string
  icon: string
  type: 'kraken' | 'toobit' | 'jupiter'
  status: 'running' | 'stopped' | 'error'
  pnl?: string
}

interface PaperState {
  balance: number
  initial_balance: number
  realized_pnl: number
  total_fees: number
  trades: { timestamp: number }[]
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
}

const statusConfig = {
  running: { icon: Play, color: 'text-emerald-400', bg: 'bg-emerald-500/20' },
  stopped: { icon: Pause, color: 'text-slate-400', bg: 'bg-slate-500/20' },
  error: { icon: AlertCircle, color: 'text-rose-400', bg: 'bg-rose-500/20' }
}

const typeLabels: Record<string, { label: string; icon: string; href: string }> = {
  jupiter: { label: 'Jupiter', icon: '🪐', href: '/trading/bot/jupiter' },
  kraken: { label: 'Kraken', icon: '🐙', href: '/trading/bot/kraken' },
  toobit: { label: 'Toobit', icon: '🔶', href: '/trading/bot/toobit' },
}

export default function BotStatus() {
  const [bots, setBots] = useState<Bot[]>([
    { id: '1', name: 'Jupiter Momentum', icon: '🪐', type: 'jupiter', status: 'stopped', pnl: '0.0000 SOL' },
    { id: '2', name: 'Kraken Paper', icon: '🐙', type: 'kraken', status: 'stopped', pnl: '$0.00' },
    { id: '3', name: 'Toobit Futures', icon: '🔶', type: 'toobit', status: 'stopped', pnl: '$0.00' },
  ])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchBotData()
    const interval = setInterval(fetchBotData, 30000)
    return () => clearInterval(interval)
  }, [])

  async function fetchBotData() {
    try {
      const [jupiterRes, krakenRes, toobitRes] = await Promise.all([
        fetch('/api/jupiter-data'),
        fetch('/api/trading-data?exchange=kraken'),
        fetch('/api/trading-data?exchange=toobit'),
      ])

      let jupiterData: JupiterState | null = null
      let krakenData: PaperState | null = null
      let toobitData: PaperState | null = null

      if (jupiterRes.ok) jupiterData = await jupiterRes.json()
      if (krakenRes.ok) krakenData = await krakenRes.json()
      if (toobitRes.ok) toobitData = await toobitRes.json()

      const updatedBots: Bot[] = [
        {
          id: '1',
          name: 'Jupiter Momentum',
          icon: '🪐',
          type: 'jupiter',
          status: jupiterData?.status === 'active' ? 'running' : 'stopped',
          pnl: jupiterData ? `${jupiterData.pnl_sol >= 0 ? '+' : ''}${jupiterData.pnl_sol.toFixed(4)} SOL` : '0.0000 SOL',
        },
        {
          id: '2',
          name: 'Kraken Paper',
          icon: '🐙',
          type: 'kraken',
          status: krakenData?.status === 'active' ? 'running' : 'stopped',
          pnl: krakenData ? `$${krakenData.realized_pnl.toFixed(2)}` : '$0.00',
        },
        {
          id: '3',
          name: 'Toobit Futures',
          icon: '🔶',
          type: 'toobit',
          status: toobitData?.status === 'active' ? 'running' : 'stopped',
          pnl: toobitData ? `$${toobitData.realized_pnl.toFixed(2)}` : '$0.00',
        },
      ]

      setBots(updatedBots)
    } catch (error) {
      console.error('Error fetching bot data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800">
          <h2 className="text-lg font-semibold">Trading Bots</h2>
        </div>
        <div className="p-6 text-center">
          <div className="animate-pulse space-y-3">
            <div className="h-16 bg-slate-800 rounded-lg"></div>
            <div className="h-16 bg-slate-800 rounded-lg"></div>
            <div className="h-16 bg-slate-800 rounded-lg"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Trading Bots</h2>
        <Link href="/trading" className="text-sm text-cyan-400 hover:text-cyan-300 transition-colors">
          View All
        </Link>
      </div>

      <div className="divide-y divide-slate-800/50">
        {bots.map((bot) => {
          const config = statusConfig[bot.status]
          const typeInfo = typeLabels[bot.type]
          const Icon = config.icon

          return (
            <Link key={bot.id} href={typeInfo.href || '/trading'}>
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 hover:bg-slate-800/50 transition-colors cursor-pointer group">
                <div className="flex items-center gap-4">
                  <div className={`rounded-lg p-2 ${config.bg}`}>
                    <Icon className={`h-5 w-5 ${config.color}`} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{bot.icon}</span>
                      <h3 className="font-semibold text-white group-hover:text-cyan-400 transition-colors">{bot.name}</h3>
                    </div>
                    <p className="text-xs text-slate-400">{typeInfo.label}</p>
                  </div>
                </div>

                <div className="flex items-center gap-6 sm:gap-8">
                  <div className="text-right">
                    <p className="text-xs text-slate-500">Status</p>
                    <p className={`text-sm font-medium capitalize ${bot.status === 'running' ? 'text-emerald-400' : 'text-slate-400'}`}>
                      {bot.status}
                    </p>
                  </div>

                  {bot.pnl && (
                    <div className="text-right">
                      <p className="text-xs text-slate-500">P&L</p>
                      <div className="flex items-center gap-1">
                        <TrendingUp className="h-3 w-3 text-slate-400" />
                        <p className="text-sm font-medium text-slate-300">{bot.pnl}</p>
                      </div>
                    </div>
                  )}

                  <ArrowRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
                </div>
              </div>
            </Link>
          )
        })}
      </div>

      {bots.every(b => b.status === 'stopped') && (
        <div className="px-6 py-4 bg-slate-800/50 border-t border-slate-800">
          <p className="text-sm text-slate-400 text-center">
            No bots currently running. Start a bot to begin trading.
          </p>
        </div>
      )}
    </div>
  )
}
