'use client'

import { useState, useEffect, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { 
  Activity, 
  Brain, 
  Cpu, 
  ChevronRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  Zap,
  Terminal,
  RefreshCw,
  Play,
  Pause,
  X,
  Check,
  AlertTriangle,
  Layers,
  Sparkles,
  Database,
  Code,
  TrendingUp,
  Palette,
  Link as LinkIcon
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
  sessionKey?: string
  runtime?: string
  tokensUsed?: number
}

interface PendingApproval {
  id: string
  agentId: string
  agentName: string
  task: string
  description: string
  requestedAt: string
  priority: 'high' | 'medium' | 'low'
}

export default function AgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([])
  const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>([])
  const [activeAgent, setActiveAgent] = useState<Agent | null>(null)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedApproval, setSelectedApproval] = useState<PendingApproval | null>(null)
  const [isProcessingApproval, setIsProcessingApproval] = useState(false)
  const router = useRouter()

  // Fetch agent data
  const fetchAgents = useCallback(async () => {
    try {
      const response = await fetch('/api/agents')
      if (!response.ok) throw new Error('Failed to fetch')
      const data = await response.json()
      setAgents(data.agents || [])
      setPendingApprovals(data.pendingApprovals || [])
      setLastUpdate(new Date())
      setError(null)
    } catch (err) {
      setError('Failed to load agent data')
      console.error('Fetch error:', err)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // Initial fetch and polling
  useEffect(() => {
    fetchAgents()
    const interval = setInterval(fetchAgents, 30000) // Poll every 30s
    return () => clearInterval(interval)
  }, [fetchAgents])

  // Handle approval action
  const handleApproval = async (approvalId: string, action: 'approve' | 'reject') => {
    setIsProcessingApproval(true)
    try {
      const response = await fetch('/api/agents', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, approvalId })
      })
      
      if (response.ok) {
        setPendingApprovals(prev => prev.filter(a => a.id !== approvalId))
        setSelectedApproval(null)
      }
    } catch (err) {
      console.error('Approval error:', err)
    } finally {
      setIsProcessingApproval(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'busy': return 'bg-amber-500'
      case 'learning': return 'bg-blue-500'
      case 'idle': return 'bg-emerald-500'
      case 'offline': return 'bg-slate-500'
      default: return 'bg-slate-500'
    }
  }

  const getStatusBg = (status: string) => {
    switch (status) {
      case 'busy': return 'bg-amber-500/10 border-amber-500/30'
      case 'learning': return 'bg-blue-500/10 border-blue-500/30'
      case 'idle': return 'bg-emerald-500/10 border-emerald-500/30'
      case 'offline': return 'bg-slate-500/10 border-slate-500/30'
      default: return 'bg-slate-500/10 border-slate-500/30'
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

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-400 bg-red-500/10 border-red-500/30'
      case 'medium': return 'text-amber-400 bg-amber-500/10 border-amber-500/30'
      case 'low': return 'text-blue-400 bg-blue-500/10 border-blue-500/30'
      default: return 'text-slate-400 bg-slate-500/10 border-slate-500/30'
    }
  }

  const getSkillIcon = (skill: string) => {
    const lower = skill.toLowerCase()
    if (lower.includes('python') || lower.includes('code') || lower.includes('rust')) return <Code className="w-3 h-3" />
    if (lower.includes('trading') || lower.includes('backtest') || lower.includes('risk')) return <TrendingUp className="w-3 h-3" />
    if (lower.includes('react') || lower.includes('ui') || lower.includes('design')) return <Palette className="w-3 h-3" />
    if (lower.includes('database') || lower.includes('data')) return <Database className="w-3 h-3" />
    if (lower.includes('async') || lower.includes('websocket') || lower.includes('api')) return <Zap className="w-3 h-3" />
    return <Layers className="w-3 h-3" />
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center">
        <div className="flex items-center gap-3">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span className="text-slate-400">Loading agents...</span>
        </div>
      </div>
    )
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
          <p className="text-slate-400">Real-time monitoring and task management for your AI team</p>
        </div>

        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-red-400">{error}</span>
            <button 
              onClick={fetchAgents}
              className="ml-auto px-3 py-1 bg-red-500/20 hover:bg-red-500/30 rounded text-sm"
            >
              Retry
            </button>
          </div>
        )}

        {/* Pending Approvals Section */}
        {pendingApprovals.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              <h2 className="text-xl font-semibold">Pending Approvals ({pendingApprovals.length})</h2>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              {pendingApprovals.map((approval) => (
                <div 
                  key={approval.id}
                  className="bg-slate-900 rounded-xl border border-amber-500/30 p-4"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(approval.priority)}`}>
                        {approval.priority.toUpperCase()}
                      </div>
                      <span className="text-slate-400 text-sm">{approval.agentName}</span>
                    </div>
                    <span className="text-slate-500 text-sm">
                      {new Date(approval.requestedAt).toLocaleTimeString()}
                    </span>
                  </div>
                  <h3 className="font-semibold mb-1">{approval.task}</h3>
                  <p className="text-slate-400 text-sm mb-4">{approval.description}</p>
                  <div className="flex gap-3">
                    <button
                      onClick={() => handleApproval(approval.id, 'approve')}
                      disabled={isProcessingApproval}
                      className="flex-1 flex items-center justify-center gap-2 py-2 bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-700 rounded-lg text-sm font-medium transition-colors"
                    >
                      <Check className="w-4 h-4" />
                      Approve
                    </button>
                    <button
                      onClick={() => handleApproval(approval.id, 'reject')}
                      disabled={isProcessingApproval}
                      className="flex-1 flex items-center justify-center gap-2 py-2 bg-slate-700 hover:bg-slate-600 disabled:bg-slate-800 rounded-lg text-sm font-medium transition-colors"
                    >
                      <X className="w-4 h-4" />
                      Reject
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

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
                  : `border-slate-800 hover:border-slate-700 ${getStatusBg(agent.status)}`
              }`}
              onClick={() => setActiveAgent(activeAgent?.id === agent.id ? null : agent)}
            >
              {/* Card Header */}
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className="text-4xl bg-slate-800 w-16 h-16 rounded-xl flex items-center justify-center border border-slate-700">
                      {agent.emoji}
                    </div>
                    <div>
                      <h3 className="text-xl font-bold">{agent.name}</h3>
                      <p className="text-slate-400 text-sm">{agent.role}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(agent.status)} animate-pulse`} />
                    <span className="text-sm capitalize text-slate-400">{agent.status}</span>
                  </div>
                </div>

                {/* Live Task Info */}
                {agent.currentTask && (
                  <div className="mb-4 p-3 bg-slate-800/80 rounded-lg border border-slate-700">
                    <div className="flex items-center gap-2 text-amber-400 mb-1">
                      {agent.status === 'learning' ? <Brain className="w-4 h-4" /> : <Activity className="w-4 h-4" />}
                      <span className="text-sm font-medium">
                        {agent.status === 'learning' ? 'Learning' : 'Current Task'}
                      </span>
                      {agent.runtime && (
                        <span className="text-xs text-slate-500 ml-auto">{agent.runtime}</span>
                      )}
                    </div>
                    <p className="text-slate-300">{agent.currentTask}</p>
                    {agent.tokensUsed && (
                      <p className="text-xs text-slate-500 mt-1">
                        {agent.tokensUsed.toLocaleString()} tokens used
                      </p>
                    )}
                  </div>
                )}

                {agent.status === 'learning' && agent.learningProgress && agent.learningProgress > 0 && (
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
                        style={{ width: `${Math.min(agent.learningProgress, 100)}%` }}
                      />
                    </div>
                  </div>
                )}

                {/* Model & Last Activity */}
                <div className="flex items-center justify-between text-sm mb-4">
                  <div className="flex items-center gap-2 text-slate-400">
                    <Cpu className="w-4 h-4" />
                    <span className="font-mono text-xs">{agent.model}</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-500">
                    <Clock className="w-4 h-4" />
                    <span>{agent.lastActivity}</span>
                  </div>
                </div>

                {/* Quick Skills Preview */}
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {agent.skills.slice(0, 4).map((skill) => (
                    <span 
                      key={skill}
                      className="px-2 py-0.5 bg-slate-800 text-slate-300 rounded text-xs flex items-center gap-1"
                    >
                      {getSkillIcon(skill)}
                      {skill}
                    </span>
                  ))}
                  {agent.skills.length > 4 && (
                    <span className="px-2 py-0.5 bg-slate-800 text-slate-500 rounded text-xs">
                      +{agent.skills.length - 4} more
                    </span>
                  )}
                </div>

                <p className="text-slate-400 text-sm">{agent.description}</p>

                {/* Expanded View */}
                {activeAgent?.id === agent.id && (
                  <div className="border-t border-slate-800 pt-4 mt-4">
                    {/* All Skills */}
                    <div className="mb-4">
                      <div className="flex items-center gap-2 text-emerald-400 mb-2">
                        <Terminal className="w-4 h-4" />
                        <span className="font-medium">All Skills ({agent.skills.length})</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {agent.skills.map((skill) => (
                          <span 
                            key={skill}
                            className="px-3 py-1.5 bg-emerald-500/20 text-emerald-400 rounded-full text-sm flex items-center gap-1.5"
                          >
                            {getSkillIcon(skill)}
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Recommended Skills */}
                    <div className="mb-4">
                      <div className="flex items-center gap-2 text-purple-400 mb-2">
                        <Sparkles className="w-4 h-4" />
                        <span className="font-medium">Recommended Skills</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {agent.recommendedSkills.map((skill) => (
                          <span 
                            key={skill}
                            className="px-3 py-1.5 bg-purple-500/20 text-purple-400 rounded-full text-sm flex items-center gap-1.5 border border-purple-500/30"
                          >
                            <Sparkles className="w-3 h-3" />
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3 pt-4 border-t border-slate-800">
                      <button className="flex-1 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
                        <Play className="w-4 h-4" />
                        Assign Task
                      </button>
                      <button className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors">
                        View History
                      </button>
                      <button 
                        onClick={(e) => {
                          e.stopPropagation()
                          fetchAgents()
                        }}
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
                      >
                        <RefreshCw className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}

                {/* Click to expand hint */}
                {activeAgent?.id !== agent.id && (
                  <div className="flex items-center justify-center text-slate-600 text-sm mt-4">
                    <span>Click to expand</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-8 flex items-center justify-between text-slate-600 text-sm">
          <span>Last updated: {lastUpdate.toLocaleTimeString()}</span>
          <button 
            onClick={fetchAgents}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      </div>
    </div>
  )
}
