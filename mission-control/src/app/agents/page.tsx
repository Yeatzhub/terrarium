'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  Activity, 
  Brain, 
  Code2, 
  Palette, 
  Cpu, 
  ChevronRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  Zap,
  Terminal,
  RefreshCw
} from 'lucide-react'

interface Agent {
  id: string
  name: string
  emoji: string
  role: string
  description: string
  status: 'idle' | 'busy' | 'learning' | 'offline'
  currentTask?: string
  lastActivity: string
  model: string
  skills: string[]
  recommendedSkills: string[]
  learningProgress?: number
}

const agents: Agent[] = [
  {
    id: 'ghost',
    name: 'Ghost',
    emoji: '👻',
    role: 'Code Specialist',
    description: 'Builds trading bots, infrastructure, and async systems',
    status: 'busy',
    currentTask: 'Building Jupiter DEX bot v1',
    lastActivity: 'Just now',
    model: 'default',
    skills: ['Python', 'Async/await', 'WebSocket', 'Trading APIs', 'Database'],
    recommendedSkills: ['Rust', 'Solana smart contracts', 'MEV protection'],
    learningProgress: 85
  },
  {
    id: 'oracle',
    name: 'Oracle',
    emoji: '🔮',
    role: 'Trading Strategist',
    description: 'Designs strategies, backtests, and risk management',
    status: 'learning',
    currentTask: 'Documenting market regimes',
    lastActivity: '5 min ago',
    model: 'ollama/kimi-k2.5:cloud',
    skills: ['Technical Analysis', 'Backtesting', 'Risk Management', 'Indicators'],
    recommendedSkills: ['On-chain analysis', 'Order flow', 'Machine learning for trading'],
    learningProgress: 60
  },
  {
    id: 'pixel',
    name: 'Pixel',
    emoji: '🎨',
    role: 'UI/UX Engineer',
    description: 'Designs interfaces and component systems',
    status: 'idle',
    currentTask: 'Maintaining Mission Control',
    lastActivity: '1 hour ago',
    model: 'default',
    skills: ['React', 'Tailwind CSS', 'Next.js', 'Component Design'],
    recommendedSkills: ['Data visualization', 'Three.js', 'Motion design'],
    learningProgress: 40
  },
  {
    id: 'synthesis',
    name: 'Synthesis',
    emoji: '🔗',
    role: 'Team Lead',
    description: 'Coordinates tasks and integrates solutions',
    status: 'idle',
    lastActivity: '2 hours ago',
    model: 'default',
    skills: ['Architecture', 'Coordination', 'Documentation', 'Project Management'],
    recommendedSkills: ['Multi-agent coordination', 'Workflow optimization'],
    learningProgress: 75
  }
]

export default function AgentsPage() {
  const [activeAgent, setActiveAgent] = useState<Agent | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const router = useRouter()

  useEffect(() => {
    const interval = setInterval(() => {
      setLastUpdate(new Date())
    }, 60000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'busy': return 'bg-amber-500'
      case 'learning': return 'bg-blue-500'
      case 'idle': return 'bg-emerald-500'
      case 'offline': return 'bg-slate-500'
      default: return 'bg-slate-500'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'busy': return <Activity className="w-4 h-4" />
      case 'learning': return <Brain className="w-4 h-4" />
      case 'idle': return <CheckCircle2 className="w-4 h-4" />
      case 'offline': return <AlertCircle className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <button 
              onClick={() => router.push('/')}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            </button>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              Agent Control Center
            </h1>
          </div>
          <p className="text-slate-400">Manage and monitor your specialist AI team</p>
        </div>

        {/* Status Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Active', value: agents.filter(a => a.status !== 'offline').length, icon: Zap, color: 'text-emerald-400' },
            { label: 'Busy', value: agents.filter(a => a.status === 'busy').length, icon: Activity, color: 'text-amber-400' },
            { label: 'Learning', value: agents.filter(a => a.status === 'learning').length, icon: Brain, color: 'text-blue-400' },
            { label: 'Idle', value: agents.filter(a => a.status === 'idle').length, icon: CheckCircle2, color: 'text-slate-400' },
          ].map((stat) => (
            <div key={stat.label} className="bg-slate-900 rounded-xl p-4 border border-slate-800">
              <div className="flex items-center gap-3">
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
                <div>
                  <p className="text-2xl font-bold">{stat.value}</p>
                  <p className="text-sm text-slate-500">{stat.label}</p>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Agents Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {agents.map((agent) => (
            <div 
              key={agent.id}
              className={`bg-slate-900 rounded-xl border transition-all cursor-pointer ${
                activeAgent?.id === agent.id 
                  ? 'border-blue-500 ring-1 ring-blue-500' 
                  : 'border-slate-800 hover:border-slate-700'
              }`}
              onClick={() => setActiveAgent(activeAgent?.id === agent.id ? null : agent)}
            >
              {/* Card Header */}
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className="text-4xl bg-slate-800 w-16 h-16 rounded-xl flex items-center justify-center">
                      {agent.emoji}
                    </div>
                    <div>
                      <h3 className="text-xl font-bold">{agent.name}</h3>
                      <p className="text-slate-400 text-sm">{agent.role}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)}`} />
                    <span className="text-sm capitalize text-slate-400">{agent.status}</span>
                  </div>
                </div>

                {/* Status Info */}
                {agent.currentTask && (
                  <div className="mb-4 p-3 bg-slate-800 rounded-lg">
                    <div className="flex items-center gap-2 text-amber-400 mb-1">
                      <Activity className="w-4 h-4" />
                      <span className="text-sm font-medium">Current Task</span>
                    </div>
                    <p className="text-slate-300">{agent.currentTask}</p>
                  </div>
                )}

                {agent.status === 'learning' && (
                  <div className="mb-4 p-3 bg-slate-800 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2 text-blue-400">
                        <Brain className="w-4 h-4" />
                        <span className="text-sm font-medium">Learning Progress</span>
                      </div>
                      <span className="text-sm text-slate-400">{agent.learningProgress}%</span>
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-blue-500 rounded-full transition-all"
                        style={{ width: `${agent.learningProgress}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Model & Last Activity */}
                <div className="flex items-center justify-between text-sm text-slate-500 mb-4">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4" />
                    <span>{agent.model}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    <span>{agent.lastActivity}</span>
                  </div>
                </div>

                <p className="text-slate-400 mb-4">{agent.description}</p>

                {/* Expanded View */}
                {activeAgent?.id === agent.id && (
                  <div className="border-t border-slate-800 pt-4 mt-4">
                    {/* Skills */}
                    <div className="mb-4">
                      <div className="flex items-center gap-2 text-emerald-400 mb-2">
                        <Terminal className="w-4 h-4" />
                        <span className="font-medium">Skills</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {agent.skills.map((skill) => (
                          <span 
                            key={skill}
                            className="px-3 py-1 bg-emerald-500/20 text-emerald-400 rounded-full text-sm"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Recommended Skills */}
                    <div className="mb-4">
                      <div className="flex items-center gap-2 text-purple-400 mb-2">
                        <Zap className="w-4 h-4" />
                        <span className="font-medium">Recommended Skills</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {agent.recommendedSkills.map((skill) => (
                          <span 
                            key={skill}
                            className="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-full text-sm"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 pt-4 border-t border-slate-800">
                      <button className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors">
                        Assign Task
                      </button>
                      <button className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors">
                        View History
                      </button>
                      <button className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors">
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Click to expand hint */}
                {activeAgent?.id !== agent.id && (
                  <div className="flex items-center justify-center text-slate-600 text-sm">
                    <span>Click to expand</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-8 text-center text-slate-600 text-sm">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}
