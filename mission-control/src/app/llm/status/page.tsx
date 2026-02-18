'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Server, Cloud, Cpu, Activity, CheckCircle2, XCircle, ArrowLeft, RefreshCw, Clock, Zap } from 'lucide-react'

interface ProviderStatus {
  id: string
  name: string
  type: 'local' | 'cloud'
  status: 'online' | 'offline' | 'degraded'
  latency: number
  models: string[]
  rateLimit?: string
}

export default function LlmStatusPage() {
  const [providers, setProviders] = useState<ProviderStatus[]>([
    {
      id: 'p40',
      name: 'P40 Local (Ollama)',
      type: 'local',
      status: 'online',
      latency: 50,
      models: ['qwen2.5:32b', 'phi4:latest', 'kimi-k2.5:cloud']
    },
    {
      id: 'nvidia',
      name: 'NVIDIA API',
      type: 'cloud',
      status: 'online',
      latency: 250,
      models: ['mistral-large-2', 'mistral-nemo-12b'],
      rateLimit: '10K req/month'
    }
  ])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  useEffect(() => {
    checkProviders()
    const interval = setInterval(checkProviders, 30000)
    return () => clearInterval(interval)
  }, [])

  const checkProviders = async () => {
    setLoading(true)
    try {
      // Check P40
      const start = Date.now()
      const ollamaRes = await fetch('http://localhost:11434/api/tags', { 
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      })
      const ollamaLatency = Date.now() - start
      
      const updated = [...providers]
      const p40Idx = updated.findIndex(p => p.id === 'p40')
      if (p40Idx >= 0) {
        updated[p40Idx] = {
          ...updated[p40Idx],
          status: ollamaRes.ok ? 'online' : 'offline',
          latency: ollamaRes.ok ? ollamaLatency : 0
        }
      }
      
      // Check NVIDIA (just key validation)
      const nvidiaIdx = updated.findIndex(p => p.id === 'nvidia')
      if (nvidiaIdx >= 0) {
        const hasKey = !!process.env.NVIDIA_API_KEY
        updated[nvidiaIdx] = {
          ...updated[nvidiaIdx],
          status: hasKey ? 'online' : 'degraded'
        }
      }
      
      setProviders(updated)
    } catch {
      // Keep current state
    } finally {
      setLoading(false)
      setLastUpdate(new Date())
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <CheckCircle2 className="w-5 h-5 text-emerald-400" />
      case 'degraded': return <Activity className="w-5 h-5 text-amber-400" />
      default: return <XCircle className="w-5 h-5 text-red-400" />
    }
  }

  const getLatencyColor = (ms: number) => {
    if (ms < 100) return 'text-emerald-400'
    if (ms < 500) return 'text-amber-400'
    return 'text-red-400'
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link href="/llm" className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                LLM Status
              </h1>
              <p className="text-slate-400">Provider Health & Availability</p>
            </div>
          </div>
          <button
            onClick={checkProviders}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Provider Cards */}
        <div className="grid gap-6">
          {providers.map((provider) => (
            <div key={provider.id} className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  {provider.type === 'local' ? (
                    <Server className="w-6 h-6 text-blue-400" />
                  ) : (
                    <Cloud className="w-6 h-6 text-purple-400" />
                  )}
                  <div>
                    <h2 className="text-lg font-semibold">{provider.name}</h2>
                    <p className="text-sm text-slate-400">{provider.type === 'local' ? 'On-Premise GPU' : 'Cloud API'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 px-3 py-1 bg-slate-800 rounded-full">
                  {getStatusIcon(provider.status)}
                  <span className={`text-sm capitalize ${
                    provider.status === 'online' ? 'text-emerald-400' : 
                    provider.status === 'degraded' ? 'text-amber-400' : 'text-red-400'
                  }`}>
                    {provider.status}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-slate-400 mb-1">
                    <Clock className="w-4 h-4" />
                    <span className="text-sm">Latency</span>
                  </div>
                  <p className={`text-lg font-bold ${getLatencyColor(provider.latency)}`}>
                    {provider.latency}ms
                  </p>
                </div>

                <div className="bg-slate-800 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-slate-400 mb-1">
                    <Cpu className="w-4 h-4" />
                    <span className="text-sm">Available Models</span>
                  </div>
                  <p className="text-lg font-bold">{provider.models.length}</p>
                </div>

                {provider.rateLimit && (
                  <div className="bg-slate-800 rounded-lg p-4">
                    <div className="flex items-center gap-2 text-slate-400 mb-1">
                      <Zap className="w-4 h-4" />
                      <span className="text-sm">Rate Limit</span>
                    </div>
                    <p className="text-lg font-bold">{provider.rateLimit}</p>
                  </div>
                )}
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {provider.models.map(model => (
                  <Link
                    key={model}
                    href="/llm/models"
                    className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-full text-sm transition-colors border border-slate-700"
                  >
                    {model}
                  </Link>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-slate-600 text-sm">
          <p>Last checked: {lastUpdate.toLocaleTimeString()}</p>
        </div>
      </div>
    </div>
  )
}
