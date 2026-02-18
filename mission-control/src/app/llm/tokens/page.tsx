'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { TrendingUp, DollarSign, Zap, Clock, ArrowLeft, BarChart3 } from 'lucide-react'

interface DailyUsage {
  date: string
  tokens: number
  cost: number
  provider: string
}

export default function LlmTokensPage() {
  const [usage, setUsage] = useState<DailyUsage[]>([
    { date: '2026-02-18', tokens: 450000, cost: 0, provider: 'P40' },
    { date: '2026-02-17', tokens: 620000, cost: 0, provider: 'P40' },
    { date: '2026-02-16', tokens: 380000, cost: 2.5, provider: 'Ollama Cloud' },
    { date: '2026-02-15', tokens: 290000, cost: 0, provider: 'P40' },
    { date: '2026-02-14', tokens: 510000, cost: 0, provider: 'P40' },
  ])

  const totalTokens = usage.reduce((sum, d) => sum + d.tokens, 0)
  const totalCost = usage.reduce((sum, d) => sum + d.cost, 0)
  const avgDaily = Math.round(totalTokens / usage.length)

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <Link href="/llm" className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
              Token Usage
            </h1>
            <p className="text-slate-400">Cost tracking & rate limits</p>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
            <div className="flex items-center gap-3 mb-2">
              <BarChart3 className="w-5 h-5 text-blue-400" />
              <span className="text-slate-400">Total Tokens (7 days)</span>
            </div>
            <p className="text-3xl font-bold">{totalTokens.toLocaleString()}</p>
            <p className="text-sm text-slate-500 mt-1">~{avgDaily.toLocaleString()}/day avg</p>
          </div>

          <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
            <div className="flex items-center gap-3 mb-2">
              <DollarSign className="w-5 h-5 text-green-400" />
              <span className="text-slate-400">Total Cost</span>
            </div>
            <p className="text-3xl font-bold text-emerald-400">${totalCost.toFixed(2)}</p>
            <p className="text-sm text-slate-500 mt-1">P40: $0 • Cloud: ${totalCost}</p>
          </div>

          <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
            <div className="flex items-center gap-3 mb-2">
              <Zap className="w-5 h-5 text-amber-400" />
              <span className="text-slate-400">NVIDIA Rate Limit</span>
            </div>
            <p className="text-3xl font-bold">9,847/<span className="text-lg text-slate-400">10K</span></p>
            <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden mt-3">
              <div className="h-full bg-amber-500 rounded-full" style={{ width: '98.5%' }} />
            </div>
          </div>
        </div>

        {/* Provider Breakdown */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-slate-400" />
            Daily Usage
          </h2>

          <div className="space-y-3">
            {usage.map((day) => (
              <div key={day.date} className="flex items-center justify-between py-3 border-b border-slate-800 last:border-0">
                <div className="flex items-center gap-4">
                  <span className="text-slate-400 w-24">{day.date}</span>
                  <span className="px-2 py-0.5 bg-slate-800 rounded text-xs text-slate-400">
                    {day.provider}
                  </span>
                </div>
                <div className="flex items-center gap-8">
                  <span className="text-slate-300">{day.tokens.toLocaleString()} tokens</span>
                  <span className={`font-mono w-16 text-right ${day.cost > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                    ${day.cost.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Cost Projection */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-slate-400" />
            Monthly Projection
          </h2>

          <div className="grid grid-cols-3 gap-6">
            <div className="text-center">
              <p className="text-slate-400 mb-1">P40 Local</p>
              <p className="text-2xl font-bold text-emerald-400">$0.00</p>
              <p className="text-sm text-slate-500">~15M tokens</p>
            </div>

            <div className="text-center">
              <p className="text-slate-400 mb-1">Ollama Cloud</p>
              <p className="text-2xl font-bold text-blue-400">~$15.00</p>
              <p className="text-sm text-slate-500">~500K tokens</p>
            </div>

            <div className="text-center">
              <p className="text-slate-400 mb-1">NVIDIA Overflow</p>
              <p className="text-2xl font-bold text-amber-400">~$5.00</p>
              <p className="text-sm text-slate-500">~1M tokens</p>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-slate-800 flex items-center justify-between">
            <span className="text-slate-400">Estimated Total</span>
            <span className="text-2xl font-bold">~$20.00/month</span>
          </div>
        </div>
      </div>
    </div>
  )
}
