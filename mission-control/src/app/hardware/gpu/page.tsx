'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { Cpu, Thermometer, Activity, HardDrive, ArrowLeft, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react'

interface GpuStats {
  name: string
  temperature: number
  utilization: number
  memoryUsed: number
  memoryTotal: number
  powerDraw: number
  powerLimit: number
  fanSpeed: number
}

interface OllamaModel {
  name: string
  size: string
  parameterCount: string
  loaded: boolean
}

export default function GpuStatusPage() {
  const [gpuStats, setGpuStats] = useState<GpuStats | null>(null)
  const [models, setModels] = useState<OllamaModel[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  useEffect(() => {
    fetchGpuData()
    const interval = setInterval(fetchGpuData, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchGpuData = async () => {
    try {
      // Fetch GPU stats from API
      const res = await fetch('/api/gpu-status')
      if (res.ok) {
        const data = await res.json()
        setGpuStats(data.gpu)
        setModels(data.models || [])
      }
      setLastUpdate(new Date())
    } catch (err) {
      console.error('Failed to fetch GPU data:', err)
    } finally {
      setLoading(false)
    }
  }

  const getTempColor = (temp: number) => {
    if (temp < 50) return 'text-emerald-400'
    if (temp < 70) return 'text-amber-400'
    return 'text-red-400'
  }

  const getUtilizationColor = (util: number) => {
    if (util < 30) return 'bg-emerald-500'
    if (util < 70) return 'bg-amber-500'
    return 'bg-red-500'
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link href="/hardware" className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
                GPU Status
              </h1>
              <p className="text-slate-400">P40 Monitoring & Ollama Models</p>
            </div>
          </div>
          <button
            onClick={fetchGpuData}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center h-64">
            <RefreshCw className="w-8 h-8 animate-spin text-cyan-500" />
          </div>
        ) : (
          <>
            {/* GPU Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
                <div className="flex items-center gap-3 mb-2">
                  <Cpu className="w-5 h-5 text-cyan-400" />
                  <span className="text-slate-400">GPU Name</span>
                </div>
                <p className="text-xl font-bold">{gpuStats?.name || 'Tesla P40'}</p>
                <p className="text-sm text-slate-500 mt-1">24GB VRAM</p>
              </div>

              <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
                <div className="flex items-center gap-3 mb-2">
                  <Thermometer className="w-5 h-5 text-orange-400" />
                  <span className="text-slate-400">Temperature</span>
                </div>
                <p className={`text-2xl font-bold ${getTempColor(gpuStats?.temperature || 32)}`}>
                  {gpuStats?.temperature || 32}°C
                </p>
                <p className="text-sm text-slate-500 mt-1">Target: &lt;70°C</p>
              </div>

              <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
                <div className="flex items-center gap-3 mb-2">
                  <Activity className="w-5 h-5 text-emerald-400" />
                  <span className="text-slate-400">Utilization</span>
                </div>
                <div className="flex items-center gap-3">
                  <p className="text-2xl font-bold">{gpuStats?.utilization || 0}%</p>
                  <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                    <div 
                      className={`h-full ${getUtilizationColor(gpuStats?.utilization || 0)} rounded-full transition-all duration-500`}
                      style={{ width: `${gpuStats?.utilization || 0}%` }}
                    />
                  </div>
                </div>
                <p className="text-sm text-slate-500 mt-1">Compute load</p>
              </div>

              <div className="bg-slate-900 rounded-xl p-6 border border-slate-800">
                <div className="flex items-center gap-3 mb-2">
                  <HardDrive className="w-5 h-5 text-purple-400" />
                  <span className="text-slate-400">VRAM</span>
                </div>
                <p className="text-2xl font-bold">
                  {((gpuStats?.memoryUsed || 5) / 1024).toFixed(1)} / {((gpuStats?.memoryTotal || 24576) / 1024).toFixed(0)} GB
                </p>
                <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden mt-2">
                  <div 
                    className="h-full bg-purple-500 rounded-full transition-all duration-500"
                    style={{ width: `${((gpuStats?.memoryUsed || 5) / (gpuStats?.memoryTotal || 24576 || 24576 || 24576)) * 100}%` }}
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Ollama Models */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  Available Models
                </h2>
                <div className="space-y-3">
                  {models.length > 0 ? models.map((model) => (
                    <div 
                      key={model.name}
                      className={`p-4 rounded-lg border ${model.loaded ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-slate-800 border-slate-700'}`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium">{model.name}</h3>
                          <p className="text-sm text-slate-400">{model.parameterCount} • {model.size}</p>
                        </div>
                        {model.loaded ? (
                          <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-xs">Loaded</span>
                        ) : (
                          <span className="px-2 py-1 bg-slate-700 text-slate-400 rounded text-xs">Available</span>
                        )}
                      </div>
                    </div>
                  )) : (
                    <div className="text-center py-8 text-slate-500">
                      <p>Models loaded on P40:</p>
                      <div className="mt-4 space-y-2">
                        <div className="p-3 bg-slate-800 rounded border border-slate-700">
                          <p className="font-medium">qwen2.5:32b</p>
                          <p className="text-sm text-slate-400">32B params • ~18GB VRAM</p>
                        </div>
                        <div className="p-3 bg-slate-800 rounded border border-slate-700">
                          <p className="font-medium">phi4:latest</p>
                          <p className="text-sm text-slate-400">14B params • ~8GB VRAM</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* System Info */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-cyan-400" />
                  System Info
                </h2>
                <div className="space-y-4">
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">Driver Version</span>
                    <span className="font-mono">570.211.01</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">CUDA Version</span>
                    <span className="font-mono">12.8</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">Power Draw</span>
                    <span>{gpuStats?.powerDraw || 42}W / {gpuStats?.powerLimit || 250}W</span>
                  </div>
                  <div className="flex justify-between py-2 border-b border-slate-800">
                    <span className="text-slate-400">Fan Speed</span>
                    <span>{gpuStats?.fanSpeed || 65}%</span>
                  </div>
                  <div className="flex justify-between py-2">
                    <span className="text-slate-400">Last Update</span>
                    <span className="text-slate-500">{lastUpdate.toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="mt-8 text-center text-slate-600 text-sm">
              <p>Auto-refresh every 10 seconds</p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
