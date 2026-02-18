'use client'

import Link from 'next/link'
import { Cpu, HardDrive, Zap, Gauge, ArrowLeft, Server, Cloud } from 'lucide-react'

interface ModelInfo {
  id: string
  name: string
  provider: 'local' | 'cloud'
  vram: string
  speed: string
  bestFor: string
  status: 'available' | 'loading' | 'unavailable'
  costPer1k?: string
}

const models: ModelInfo[] = [
  {
    id: 'qwen2.5:32b',
    name: 'Qwen 2.5 32B',
    provider: 'local',
    vram: '18GB',
    speed: '30 tok/s',
    bestFor: 'Coding, complex reasoning',
    status: 'available'
  },
  {
    id: 'phi4:latest',
    name: 'Phi-4',
    provider: 'local',
    vram: '8GB',
    speed: '60 tok/s',
    bestFor: 'Quick tasks, heartbeats',
    status: 'available'
  },
  {
    id: 'kimi-k2.5:cloud',
    name: 'Kimi K2.5',
    provider: 'cloud',
    vram: 'Cloud',
    speed: 'Fast',
    bestFor: 'Complex tasks, synthesis',
    status: 'available',
    costPer1k: 'Subscription'
  },
  {
    id: 'mistral-large-2',
    name: 'Mistral Large 2',
    provider: 'cloud',
    vram: 'Cloud',
    speed: 'Variable',
    bestFor: 'Analysis, reasoning',
    status: 'available',
    costPer1k: '$0.008'
  },
  {
    id: 'mistral-nemo-12b',
    name: 'Mistral Nemo 12B',
    provider: 'cloud',
    vram: 'Cloud',
    speed: 'Fast',
    bestFor: 'Cheap overflow tasks',
    status: 'available',
    costPer1k: '$0.003'
  }
]

export default function LlmModelsPage() {
  const localModels = models.filter(m => m.provider === 'local')
  const cloudModels = models.filter(m => m.provider === 'cloud')

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
              Available Models
            </h1>
            <p className="text-slate-400">Local GPU + Cloud Options</p>
          </div>
        </div>

        {/* Local Models */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <Server className="w-5 h-5 text-cyan-400" />
            <h2 className="text-xl font-semibold">P40 Local (Free)</h2>
            <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-400 rounded text-xs">{localModels.filter(m => m.status === 'available').length} available</span>
          </div>

          <div className="grid gap-4">
            {localModels.map((model) => (
              <div key={model.id} className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-cyan-500/20 rounded-lg flex items-center justify-center">
                      <Cpu className="w-5 h-5 text-cyan-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg">{model.name}</h3>
                      <p className="text-slate-400">{model.bestFor}</p>
                    </div>
                  </div>
                  <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-xs font-medium">
                    {model.status}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div className="flex items-center gap-2 text-slate-400">
                    <HardDrive className="w-4 h-4" />
                    <span>{model.vram}</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-400">
                    <Gauge className="w-4 h-4" />
                    <span>{model.speed}</span>
                  </div>
                  <div className="flex items-center gap-2 text-emerald-400">
                    <span>$0.00</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Cloud Models */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <Cloud className="w-5 h-5 text-purple-400" />
            <h2 className="text-xl font-semibold">Cloud (Pay-per-use)</h2>
            <span className="px-2 py-0.5 bg-purple-500/20 text-purple-400 rounded text-xs">{cloudModels.filter(m => m.status === 'available').length} available</span>
          </div>

          <div className="grid gap-4">
            {cloudModels.map((model) => (
              <div key={model.id} className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-500/20 rounded-lg flex items-center justify-center">
                      <Cloud className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-lg">{model.name}</h3>
                      <p className="text-slate-400">{model.bestFor}</p>
                    </div>
                  </div>
                  <span className="px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded text-xs font-medium">
                    {model.status}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-4 mt-4">
                  <div className="flex items-center gap-2 text-slate-400">
                    <HardDrive className="w-4 h-4" />
                    <span>{model.vram}</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-400">
                    <Gauge className="w-4 h-4" />
                    <span>{model.speed}</span>
                  </div>
                  <div className="flex items-center gap-2 text-amber-400">
                    <Zap className="w-4 h-4" />
                    <span>{model.costPer1k}/1k tokens</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
