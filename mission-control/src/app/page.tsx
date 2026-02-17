'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'

interface LLMStatus {
  currentModel: string
  availableModels: string[]
  contextWindow: number
  loadedModels: Array<{
    name: string
    model: string
    size: number
  }>
  usage: {
    totalTokens: number
    maxTokens: number
    remainingTokens: number
    percentageUsed: number
  }
  timestamp: number
}

interface AgentStatus {
  name: string
  status: 'running' | 'idle' | 'error'
  description: string
}

interface HardwareItem {
  name: string
  status: 'delivered' | 'in-transit' | 'pending' | 'installed'
  eta?: string
}

export default function Dashboard() {
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null)
  const [currentTime, setCurrentTime] = useState(new Date())

  useEffect(() => {
    // Update time every minute
    const timeInterval = setInterval(() => setCurrentTime(new Date()), 60000)
    
    // Fetch LLM status
    fetchLLMStatus()
    const llmInterval = setInterval(fetchLLMStatus, 30000)
    
    return () => {
      clearInterval(timeInterval)
      clearInterval(llmInterval)
    }
  }, [])

  async function fetchLLMStatus() {
    try {
      const res = await fetch('/api/llm-status')
      if (res.ok) {
        setLlmStatus(await res.json())
      }
    } catch {
      // Failed to fetch
    }
  }

  const quickActions = [
    { href: '/tasks', label: '📋 Tasks', color: 'bg-slate-700 hover:bg-slate-600' },
    { href: '/notes', label: '📝 Notes', color: 'bg-slate-700 hover:bg-slate-600' },
    { href: '/trading', label: '📈 Trading', color: 'bg-purple-600 hover:bg-purple-500' },
    { href: 'http://127.0.0.1:18789', label: '🤖 OpenClaw', external: true, color: 'bg-blue-600 hover:bg-blue-500' },
    { href: 'http://100.125.198.70:8080', label: '🔍 SearXNG', external: true, color: 'bg-slate-600 hover:bg-slate-500' },
    { href: 'https://www.kraken.com/u/trade', label: '📈 Kraken', external: true, color: 'bg-orange-600 hover:bg-orange-500' },
    { href: 'https://www.tradingview.com/chart/', label: '📊 TradingView', external: true, color: 'bg-cyan-600 hover:bg-cyan-500' },
    { href: 'http://100.125.198.70:3000', label: '🌐 Tailscale', external: true, color: 'bg-slate-600 hover:bg-slate-500' },
  ]

  const activeAgents: AgentStatus[] = [
    { name: 'BTC Webhook', status: 'running', description: 'Flask + paper trading' },
    { name: 'Polymarket Scanner', status: 'running', description: 'Arbitrage detection' },
    { name: 'eBay Phase 1', status: 'running', description: 'Photo + listing prep' },
  ]

  const hardwareItems: HardwareItem[] = [
    { name: 'Tesla P40 GPU', status: 'in-transit', eta: 'Soon' },
    { name: 'Noctua Fan + Riser', status: 'delivered' },
    { name: 'WD Red 8TB (x2)', status: 'pending' },
    { name: 'i7-7700K CPU', status: 'pending' },
  ]

  const recentActivity = [
    { time: 'Today', text: 'Polymarket arbitrage scanner deployed' },
    { time: 'Today', text: 'Mission Control UI reorganized' },
    { time: 'Today', text: '3 active sub-agents deployed' },
    { time: 'Feb 16', text: 'P40 GPU delivery tracking updated' },
    { time: 'Feb 13', text: 'Telegram bot @zorinclawbot paired' },
  ]

  const modelName = llmStatus?.currentModel?.split('/').pop() || 'Loading...'

  return (
    <div className="p-4 md:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          Dashboard
        </h1>
        <p className="text-slate-400 mt-1">
          {currentTime.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
          })}
        </p>
      </div>

      {/* Quick Actions */}
      <section className="mb-8">
        <h2 className="text-lg font-semibold mb-4 text-slate-300 flex items-center gap-2">
          <span>⚡</span> Quick Actions
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
          {quickActions.map((action) => (
            action.external ? (
              <a
                key={action.label}
                href={action.href}
                target="_blank"
                rel="noopener noreferrer"
                className={`text-center px-3 py-3 ${action.color} rounded-lg transition-colors font-medium text-sm`}
              >
                {action.label}
              </a>
            ) : (
              <Link
                key={action.label}
                href={action.href}
                className={`text-center px-3 py-3 ${action.color} rounded-lg transition-colors font-medium text-sm`}
              >
                {action.label}
              </Link>
            )
          ))}
        </div>
      </section>

      {/* Summary Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        
        {/* Trading Summary */}
        <Link href="/trading" className="group">
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 hover:border-purple-500/50 hover:bg-slate-800/80 transition-all duration-300 h-full">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">📈</span>
                <div>
                  <h3 className="font-semibold text-lg">Trading</h3>
                  <p className="text-sm text-slate-400">Active Positions</p>
                </div>
              </div>
              <span className="text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Exchanges</span>
                <span className="font-mono">3 Active</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Strategy</span>
                <span className="font-mono">Paper Trading</span>
              </div>
              <div className="flex items-center gap-2 mt-3">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                <span className="text-xs text-green-400">Kraken, Toobit, Jupiter</span>
              </div>
            </div>
          </div>
        </Link>

        {/* Hardware Summary */}
        <Link href="/hardware/deliveries" className="group">
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 hover:border-cyan-500/50 hover:bg-slate-800/80 transition-all duration-300 h-full">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">🖥️</span>
                <div>
                  <h3 className="font-semibold text-lg">Hardware</h3>
                  <p className="text-sm text-slate-400">Deliveries & Status</p>
                </div>
              </div>
              <span className="text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">In Transit</span>
                <span className="font-mono text-yellow-400">1</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Delivered</span>
                <span className="font-mono text-green-400">1</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Pending</span>
                <span className="font-mono text-slate-400">2</span>
              </div>
              <div className="mt-3 pt-3 border-t border-slate-700">
                <p className="text-xs text-slate-400">Next: Tesla P40 GPU</p>
              </div>
            </div>
          </div>
        </Link>

        {/* Agents Summary */}
        <Link href="/agents/active" className="group">
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 hover:border-blue-500/50 hover:bg-slate-800/80 transition-all duration-300 h-full">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">🤖</span>
                <div>
                  <h3 className="font-semibold text-lg">Agents</h3>
                  <p className="text-sm text-slate-400">Active Sub-agents</p>
                </div>
              </div>
              <span className="text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
            </div>
            <div className="space-y-2">
              {activeAgents.map((agent) => (
                <div key={agent.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></span>
                    <span className="text-sm">{agent.name}</span>
                  </div>
                  <span className="text-xs text-blue-400">{agent.status}</span>
                </div>
              ))}
              <div className="mt-3 pt-3 border-t border-slate-700 flex justify-between">
                <span className="text-xs text-slate-400">Total Agents</span>
                <span className="text-sm font-mono">{activeAgents.length}</span>
              </div>
            </div>
          </div>
        </Link>

        {/* LLM Status Summary */}
        <Link href="/llm/status" className="group">
          <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 hover:border-pink-500/50 hover:bg-slate-800/80 transition-all duration-300 h-full">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <span className="text-3xl">🧠</span>
                <div>
                  <h3 className="font-semibold text-lg">LLM</h3>
                  <p className="text-sm text-slate-400">Model & Tokens</p>
                </div>
              </div>
              <span className="text-pink-400 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
            </div>
            <div className="space-y-2">
              <div className="bg-slate-700/50 rounded p-2">
                <p className="text-xs text-slate-400 mb-1">Active Model</p>
                <p className="font-mono text-sm text-pink-400 truncate" title={modelName}>
                  {modelName.length > 20 ? modelName.slice(0, 20) + '...' : modelName}
                </p>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-slate-400">Context</span>
                <span className="font-mono">{llmStatus?.contextWindow?.toLocaleString() || '--'} tk</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-1.5 mt-2">
                <div 
                  className="bg-gradient-to-r from-pink-500 to-purple-500 h-1.5 rounded-full"
                  style={{ width: `${Math.min(llmStatus?.usage?.percentageUsed || 0, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </Link>

        {/* System Stats Summary */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 h-full">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-3xl">📊</span>
            <div>
              <h3 className="font-semibold text-lg">System Stats</h3>
              <p className="text-sm text-slate-400">Quick Overview</p>
            </div>
          </div>
          <div className="space-y-3">
            <StatRow label="BTC Price" value="$67,871" />
            <StatRow label="RSI" value="43.82" />
            <StatRow label="Memory Files" value="3" />
            <StatRow label="Git Commits" value="7" />
          </div>
        </div>

        {/* Running Services */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 h-full">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-3xl">🟢</span>
            <div>
              <h3 className="font-semibold text-lg">Services</h3>
              <p className="text-sm text-slate-400">Running Processes</p>
            </div>
          </div>
          <div className="space-y-2">
            {[
              { name: 'Mission Control', port: '3000', status: 'online' },
              { name: 'SearXNG', port: '8082', status: 'online' },
              { name: 'Trading Webhook', port: '8081', status: 'online' },
            ].map((service) => (
              <div key={service.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className={`w-2 h-2 rounded-full ${
                    service.status === 'online' ? 'bg-green-500' : 'bg-yellow-500'
                  }`}></span>
                  <span>{service.name}</span>
                </div>
                <span className="text-xs text-slate-500">:{service.port}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 md:col-span-2 lg:col-span-2 xl:col-span-2">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-3xl">📝</span>
            <div>
              <h3 className="font-semibold text-lg">Recent Activity</h3>
              <p className="text-sm text-slate-400">Latest Updates</p>
            </div>
          </div>
          <div className="space-y-3">
            {recentActivity.map((item, i) => (
              <div key={i} className="flex items-start gap-3 text-sm">
                <span className="text-slate-500 text-xs whitespace-nowrap w-16">{item.time}</span>
                <span className="text-slate-300">{item.text}</span>
              </div>
            ))}
          </div>        </div>
      </div>

      {/* Alerts Section */}
      <section className="mt-8">
        <h2 className="text-lg font-semibold mb-4 text-slate-300 flex items-center gap-2">
          <span>🔔</span> Alerts
        </h2>
        <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-xl p-4 flex items-start gap-3">
          <span className="text-yellow-500 text-xl">⚠️</span>
          <div>
            <p className="font-medium text-yellow-400">Hardware Delivery Expected</p>
            <p className="text-sm text-slate-400 mt-1">
              Tesla P40 GPU in transit. Verify PSU wattage (250W required) before installation.
            </p>
            <a 
              href="https://tools.usps.com/go/TrackConfirmAction?tLabels=9405508106245831259625"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-block mt-2 text-sm text-blue-400 hover:text-blue-300"
            >
              Track Package →
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-12 text-center text-slate-500 text-sm">
        Mission Control v1.2 • Built with Next.js • {currentTime.getFullYear()}
      </footer>
    </div>
  )
}

function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-slate-400 text-sm">{label}</span>
      <span className="font-mono font-medium">{value}</span>
    </div>
  )
}
