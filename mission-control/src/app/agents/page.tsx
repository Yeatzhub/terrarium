'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { ArrowLeft, User, Bot, Brain, Code, Activity, Clock, CheckCircle, AlertCircle, Zap } from 'lucide-react'

interface Agent {
  id: string
  name: string
  emoji: string
  role: string
  status: 'active' | 'idle' | 'busy' | 'offline'
  description: string
  skills: string[]
  lastActivity?: string
  currentTask?: string
  color: string
}

const AGENTS: Agent[] = [
  {
    id: 'synthesis',
    name: 'Synthesis',
    emoji: '🔗',
    role: 'Team Lead / Coordinator',
    status: 'idle',
    description: 'Coordinates between you and the specialist agents. Breaks down tasks and delegates to Ghost or Oracle.',
    skills: ['Task Decomposition', 'Integration', 'Communication', 'Project Management'],
    color: 'from-blue-500 to-cyan-500'
  },
  {
    id: 'ghost',
    name: 'Ghost',
    emoji: '👻',
    role: 'Code Execution Engine',
    status: 'idle',
    description: 'Implements trading bots, scripts, and infrastructure. Writes clean, tested code with no technical debt.',
    skills: ['Python', 'TypeScript', 'Rust', 'SQL', 'Trading Bot Architecture', 'APIs'],
    color: 'from-emerald-500 to-teal-500'
  },
  {
    id: 'oracle',
    name: 'Oracle',
    emoji: '🔮',
    role: 'Trading Strategist',
    status: 'idle',
    description: 'Designs and validates trading strategies. Uses data-driven analysis to find edges in the markets.',
    skills: ['Technical Analysis', 'Backtesting', 'Risk Management', 'Quantitative Research'],
    color: 'from-purple-500 to-pink-500'
  }
]

// Task history stored in localStorage
interface Task {
  id: string
  agent: string
  task: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  startTime: string
  endTime?: string
  result?: string
}

const TASKS_STORAGE_KEY = 'openclaw_agent_tasks'

export default function AgentsPage() {
  const [activeAgents, setActiveAgents] = useState<Agent[]>(AGENTS)
  const [tasks, setTasks] = useState<Task[]>([])
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    // Load tasks from localStorage
    try {
      const stored = localStorage.getItem(TASKS_STORAGE_KEY)
      if (stored) {
        setTasks(JSON.parse(stored))
      }
    } catch {
      // Ignore storage errors
    }

    // Simulate polling for agent status
    const interval = setInterval(() => {
      // In real implementation, this would fetch from API
      // For now, we'll infer from tasks
      updateAgentStatusFromTasks()
    }, 5000)

    return () => clearInterval(interval)
  }, [])

  const updateAgentStatusFromTasks = () => {
    setActiveAgents(prev => prev.map(agent => {
      const agentTasks = tasks.filter(t => t.agent === agent.id && t.status === 'running')
      if (agentTasks.length > 0) {
        return { ...agent, status: 'busy', currentTask: agentTasks[0].task }
      }
      return { ...agent, status: 'idle', currentTask: undefined }
    }))
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'busy':
        return <Activity className="w-4 h-4 text-yellow-400 animate-pulse" />
      case 'idle':
        return <CheckCircle className="w-4 h-4 text-green-400" />
      case 'offline':
        return <AlertCircle className="w-4 h-4 text-slate-500" />
      default:
        return null
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'busy':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'idle':
        return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'offline':
        return 'bg-slate-700/50 text-slate-500 border-slate-600'
      default:
        return 'bg-slate-700/50'
    }
  }

  const recentTasks = tasks.slice(-10).reverse()

  if (!mounted) return null

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Mobile Header */}
      <header className="sticky top-0 z-40 bg-slate-900/95 backdrop-blur-md border-b border-slate-800 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link 
              href="/" 
              className="p-2 -ml-2 rounded-lg hover:bg-slate-800 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-slate-400" />
            </Link>
            <div>
              <h1 className="text-lg font-bold text-white">Agent Team</h1>
              <p className="text-xs text-slate-500">Specialist AI Agents</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-2xl">👥</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6 space-y-6">
        {/* Team Overview */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-3">
            Active Agents
          </h2>
          <div className="grid grid-cols-3 gap-3">
            {activeAgents.map(agent => (
              <div 
                key={agent.id}
                className={`bg-slate-800 rounded-lg p-3 border border-slate-700 ${
                  agent.status === 'busy' ? 'ring-1 ring-yellow-500/50' : ''
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-2xl">{agent.emoji}</span>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-white text-sm truncate">{agent.name}</h3>
                    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border ${getStatusColor(agent.status)}`}>
                      {getStatusIcon(agent.status)}
                      <span className="capitalize">{agent.status}</span>
                    </span>
                  </div>
                </div>
                {agent.currentTask && (
                  <p className="text-xs text-yellow-400 truncate">
                    {agent.currentTask}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Agent Details */}
        <div className="space-y-4">
          <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider">
            Agent Profiles
          </h2>
          
          {activeAgents.map(agent => (
            <div 
              key={agent.id}
              className="bg-slate-800 border border-slate-700 rounded-xl overflow-hidden"
            >
              {/* Header */}
              <div className={`bg-gradient-to-r ${agent.color} p-4`}>
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-white/20 backdrop-blur rounded-full flex items-center justify-center text-3xl">
                    {agent.emoji}
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-bold text-white">{agent.name}</h3>
                    <p className="text-sm text-white/80">{agent.role}</p>
                  </div>
                  <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border border-white/30 ${getStatusColor(agent.status)}`}>
                    {getStatusIcon(agent.status)}
                    <span className="capitalize">{agent.status}</span>
                  </span>
                </div>
              </div>

              {/* Body */}
              <div className="p-4 space-y-3">
                <p className="text-slate-300 text-sm">{agent.description}</p>
                
                <div>
                  <h4 className="text-xs font-medium text-slate-500 uppercase tracking-wider mb-2">
                    Skills
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {agent.skills.map((skill, idx) => (
                      <span 
                        key={idx}
                        className="px-2 py-1 bg-slate-700 text-slate-300 rounded text-xs"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Recent Activity */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider">
              Recent Activity
            </h2>
            {recentTasks.length === 0 && (
              <span className="text-xs text-slate-500">No recent tasks</span>
            )}
          </div>
          
          {recentTasks.length > 0 ? (
            <div className="space-y-2">
              {recentTasks.map(task => (
                <div 
                  key={task.id}
                  className="flex items-center gap-3 p-3 bg-slate-800 rounded-lg border border-slate-700"
                >
                  <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
                    {task.agent === 'synthesis' && <Brain className="w-4 h-4 text-blue-400" />}
                    {task.agent === 'ghost' && <Code className="w-4 h-4 text-emerald-400" />}
                    {task.agent === 'oracle' && <Zap className="w-4 h-4 text-purple-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-slate-200 truncate">{task.task}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        task.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                        task.status === 'running' ? 'bg-yellow-500/20 text-yellow-400' :
                        task.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                        'bg-slate-600 text-slate-400'
                      }`}>
                        {task.status}
                      </span>
                      <span className="text-[10px] text-slate-500">
                        {new Date(task.startTime).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-500">
              <Bot className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>Agents are ready and waiting for tasks</p>
              <p className="text-sm mt-2">
                Assign work via Synthesis in the Chat
              </p>
            </div>
          )}
        </div>

        {/* Task Assignment CTA */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-4 text-center">
          <h3 className="font-semibold text-white mb-2">Need something done?</h3>
          <p className="text-sm text-indigo-200 mb-3">
            Synthesis will route your request to the right specialist
          </p>
          <Link 
            href="/chat"
            className="inline-flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 rounded-lg text-white font-medium transition-colors"
          >
            <Bot className="w-4 h-4" />
            Open Chat
          </Link>
        </div>
      </main>
    </div>
  )
}
