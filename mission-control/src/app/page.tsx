'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'

interface LLMStatus {
  currentModel: string
  contextWindow: number
  usage: {
    percentageUsed: number
  }
}

interface BotStatus {
  running: boolean
  balance: number
  trades: number
  pnl: number
}

export default function Dashboard() {
  const [llmStatus, setLlmStatus] = useState<LLMStatus | null>(null)
  const [botStatus, setBotStatus] = useState<BotStatus | null>(null)
  const [currentTime, setCurrentTime] = useState(new Date())
  const [isRefreshing, setIsRefreshing] = useState(false)

  useEffect(() => {
    // Update time every minute
    const timeInterval = setInterval(() => setCurrentTime(new Date()), 60000)
    
    // Initial fetch
    fetchData()
    
    // Set up interval for data refresh
    const dataInterval = setInterval(fetchData, 30000)
    
    return () => {
      clearInterval(timeInterval)
      clearInterval(dataInterval)
    }
  }, [])

  async function fetchData() {
    try {
      // Fetch LLM status
      const llmRes = await fetch('/api/llm-status', { cache: 'no-store' })
      if (llmRes.ok) {
        setLlmStatus(await llmRes.json())
      }
      
      // Fetch bot status from local file
      try {
        const botRes = await fetch('/api/jupiter-data', { cache: 'no-store' })
        if (botRes.ok) {
          const data = await botRes.json()
          setBotStatus({
            running: data.running || false,
            balance: data.balance || 1.0,
            trades: data.trades || 0,
            pnl: data.pnl || 0
          })
        }
      } catch {
        // Bot status not critical
      }
    } catch {
      // Silent fail
    }
  }

  async function handleRefresh() {
    setIsRefreshing(true)
    await fetchData()
    setTimeout(() => setIsRefreshing(false), 500)
  }

  const modelName = llmStatus?.currentModel?.split('/').pop() || 'Loading...'
  const modelShort = modelName.length > 15 ? modelName.slice(0, 15) + '…' : modelName

  // Quick actions - mobile-friendly oversized buttons
  const quickActions = [
    { href: '/trading', icon: '📈', label: 'Trading', color: 'bg-purple-600', desc: 'View P&L' },
    { href: '/notes', icon: '📝', label: 'Notes', color: 'bg-slate-700', desc: 'Quick jot' },
    { href: 'http://127.0.0.1:18789', icon: '🤖', label: 'OpenClaw', color: 'bg-blue-600', desc: 'Chat AI', external: true },
    { href: 'https://www.kraken.com/u/trade', icon: '⚡', label: 'Kraken', color: 'bg-orange-600', desc: 'Trade now', external: true },
  ]

  // Status cards data
  const statusCards = [
    {
      title: 'Jupiter Bot',
      icon: '🚀',
      status: botStatus?.running ? 'Running' : 'Idle',
      statusColor: botStatus?.running ? 'text-green-400' : 'text-yellow-400',
      href: '/trading',
      metrics: [
        { label: 'Balance', value: `${(botStatus?.balance || 1.0).toFixed(2)} SOL` },
        { label: 'Trades', value: String(botStatus?.trades || 0) },
        { label: 'P&L', value: `${(botStatus?.pnl || 0).toFixed(4)} SOL`, positive: (botStatus?.pnl || 0) >= 0 },
      ]
    },
    {
      title: 'P40 GPU',
      icon: '🖥️',
      status: 'Installed',
      statusColor: 'text-green-400',
      href: '/hardware',
      metrics: [
        { label: 'Temp', value: '43°C' },
        { label: 'Power', value: '192W' },
        { label: 'Load', value: '98%' },
      ]
    },
    {
      title: 'LLM',
      icon: '🧠',
      status: 'Active',
      statusColor: 'text-blue-400',
      href: '/llm/status',
      metrics: [
        { label: 'Model', value: modelShort },
        { label: 'Context', value: `${(llmStatus?.contextWindow || 0).toLocaleString()} tk` },
        { label: 'Usage', value: `${Math.round(llmStatus?.usage?.percentageUsed || 0)}%` },
      ]
    },
  ]

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Mobile Header */}
      <header className="sticky top-0 z-40 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 px-4 py-3 md:hidden">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🚀</span>
            <h1 className="text-lg font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              Mission Control
            </h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              className={`p-2 rounded-lg bg-slate-800 ${isRefreshing ? 'animate-spin' : ''}`}
              aria-label="Refresh"
            >
              <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
            <div className="text-right">
              <p className="text-[10px] text-slate-500 uppercase tracking-wider">{currentTime.toLocaleDateString('en-US', { weekday: 'short' })}</p>
              <p className="text-lg font-mono font-semibold">{currentTime.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })}</p>
            </div>
          </div>
        </div>
      </header>

      <div className="p-4 md:p-8 max-w-7xl mx-auto">
        {/* Desktop Header */}
        <div className="hidden md:block mb-8">
          <div className="flex items-center justify-between">
            <div>
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
            <button
              onClick={handleRefresh}
              className={`flex items-center gap-2 px-4 py-2 bg-slate-800 rounded-lg hover:bg-slate-700 transition-colors ${isRefreshing ? 'opacity-50' : ''}`}
            >
              <svg className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {/* Quick Actions - Mobile optimized */}
        <section className="mb-6">
          <h2 className="text-sm font-semibold mb-3 text-slate-400 uppercase tracking-wider md:text-base md:normal-case md:mb-4">
            ⚡ Quick Actions
          </h2>
          
          <div className="grid grid-cols-2 gap-3 md:flex md:flex-wrap md:gap-3">
            {quickActions.map((action) => {
              const content = (
                <>
                  <div className={`w-12 h-12 md:w-10 md:h-10 rounded-xl ${action.color} flex items-center justify-center text-2xl md:text-xl mb-2 md:mb-0 shadow-lg`}>
                    {action.icon}
                  </div>
                  <div className="text-left md:text-center">
                    <p className="font-semibold text-base md:text-sm">{action.label}</p>
                    <p className="text-xs text-slate-400 md:hidden">{action.desc}</p>
                  </div>
                </>
              )

              const className = `
                flex items-center gap-3 md:flex-col md:items-center md:justify-center
                p-3 md:px-4 md:py-3
                bg-slate-800 md:bg-slate-800/50
                rounded-xl md:rounded-lg
                border border-slate-700 md:border-0
                active:scale-98 md:hover:bg-slate-800
                transition-all
                md:text-center
                ${action.external ? 'opacity-90 hover:opacity-100' : ''}
              `

              if (action.external) {
                return (
                  <a
                    key={action.label}
                    href={action.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={className}
                  >
                    {content}
                  </a>
                )
              }

              return (
                <Link
                  key={action.label}
                  href={action.href}
                  className={className}
                >
                  {content}
                </Link>
              )
            })}
          </div>
        </section>

        {/* Status Cards - Mobile friendly */}
        <section className="mb-6">
          <h2 className="text-sm font-semibold mb-3 text-slate-400 uppercase tracking-wider md:hidden">
            📊 Systems
          </h2>
          
          <div className="grid gap-3 md:gap-4 md:grid-cols-2 lg:grid-cols-3">
            {statusCards.map((card) => (
              <Link
                key={card.title}
                href={card.href}
                className="block p-4 bg-slate-800 rounded-xl border border-slate-700 active:bg-slate-750 md:hover:border-slate-600 transition-all"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{card.icon}</span>
                    <h3 className="font-semibold text-lg">{card.title}</h3>
                  </div>
                  <span className={`text-sm font-medium ${card.statusColor}`}>
                    {card.status}
                  </span>
                </div>
                
                <div className="grid grid-cols-3 gap-2">
                  {card.metrics.map((metric) => (
                    <div key={metric.label} className="bg-slate-900/50 rounded-lg p-2">
                      <p className="text-[10px] text-slate-500 uppercase">{metric.label}</p>
                      <p className={`font-mono text-sm font-medium ${
                        'positive' in metric && metric.positive === false 
                          ? 'text-red-400' 
                          : 'positive' in metric && metric.positive 
                            ? 'text-green-400'
                            : 'text-white'
                      }`}>
                        {metric.value}
                      </p>
                    </div>
                  ))}
                </div>
              </Link>
            ))}
          </div>
        </section>

        {/* Recent Activity */}
        <section className="mb-6">
          <h2 className="text-sm font-semibold mb-3 text-slate-400 uppercase tracking-wider">
            📝 Recent Activity
          </h2>
          
          <div className="space-y-2">
            {[
              { time: 'Now', icon: '🚀', text: 'Jupiter Bot running (30+ min)', highlight: true },
              { time: '2m', icon: '🖥️', text: 'P40 GPU tested at 192W/43°C', highlight: true },
              { time: '30m', icon: '✅', text: 'Momentum strategy deployed' },
              { time: '1h', icon: '📝', text: 'Memory files committed' },
              { time: '3h', icon: '🤖', text: 'Qwen 2.5 32B loaded on GPU' },
            ].map((item, i) => (
              <div 
                key={i} 
                className={`flex items-center gap-3 p-3 rounded-xl ${item.highlight ? 'bg-slate-800/60 border border-slate-700/50' : ''}`}
              >
                <span className="w-8 h-8 bg-slate-800 rounded-lg flex items-center justify-center text-sm flex-shrink-0">
                  {item.icon}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">{item.text}</p>
                </div>
                <span className="text-xs text-slate-500 font-mono flex-shrink-0">{item.time}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Mobile-specific alert */}
        <section className="mb-20 md:mb-8">
          <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border border-blue-500/30 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">📱</span>
              <div>
                <h3 className="font-semibold text-blue-400">Mobile App Ready</h3>
                <p className="text-sm text-slate-400 mt-1">
                  Add to home screen for native app experience with offline support.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Footer spacer for mobile */}
        <footer className="text-center text-slate-600 text-xs pb-4 md:pb-0">
          Mission Control v2.0 • Mobile Optimized
        </footer>
      </div>
    </div>
  )
}
