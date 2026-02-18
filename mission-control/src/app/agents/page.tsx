'use client'

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
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
  X,
  Check,
  AlertTriangle,
  Layers,
  Sparkles,
  Database,
  Code,
  TrendingUp,
  Palette,
  ExternalLink,
  BookOpen,
  Target,
  FileText,
  Plus,
  ArrowLeft
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

interface Task {
  id: string
  agent: string
  status: 'pending' | 'in-progress' | 'completed' | 'failed'
  description: string
  createdAt: string
  startedAt?: string
  completedAt?: string
}

// Agent metadata for display
const AGENT_META: Record<string, { emoji: string; color: string; role: string }> = {
  synthesis: { emoji: '🧠', color: 'purple', role: 'Team Lead' },
  pixel: { emoji: '🎨', color: 'pink', role: 'UI/UX Engineer' },
  ghost: { emoji: '👻', color: 'slate', role: 'Backend Engineer' },
  oracle: { emoji: '🔮', color: 'amber', role: 'Trading Analyst' },
}

function getColorClasses(color: string, type: 'bg' | 'text' | 'border' | 'ring') {
  const map: Record<string, Record<string, string>> = {
    purple: { bg: 'bg-purple-500', text: 'text-purple-400', border: 'border-purple-500', ring: 'ring-purple-500' },
    pink: { bg: 'bg-pink-500', text: 'text-pink-400', border: 'border-pink-500', ring: 'ring-pink-500' },
    slate: { bg: 'bg-slate-500', text: 'text-slate-400', border: 'border-slate-500', ring: 'ring-slate-500' },
    amber: { bg: 'bg-amber-500', text: 'text-amber-400', border: 'border-amber-500', ring: 'ring-amber-500' },
    cyan: { bg: 'bg-cyan-500', text: 'text-cyan-400', border: 'border-cyan-500', ring: 'ring-cyan-500' },
    emerald: { bg: 'bg-emerald-500', text: 'text-emerald-400', border: 'border-emerald-500', ring: 'ring-emerald-500' },
    red: { bg: 'bg-red-500', text: 'text-red-400', border: 'border-red-500', ring: 'ring-red-500' },
  }
  return map[color]?.[type] || map.cyan[type]
}

// Skill to resource URL mapping
const skillUrls: Record<string, string> = {
  // Ghost - Coding skills
  'Python': 'https://docs.python.org/3/',
  'Async/await': 'https://docs.python.org/3/library/asyncio.html',
  'WebSocket': 'https://websocket.readthedocs.io/',
  'Trading APIs': 'https://docs.kraken.com/rest/',
  'Database': 'https://www.sqlitetutorial.net/',
  'Error Handling': 'https://docs.python.org/3/tutorial/errors.html',
  'Circuit Breakers': 'https://martinfowler.com/bliki/CircuitBreaker.html',
  'Rust': 'https://www.rust-lang.org/learn',
  'Solana smart contracts': 'https://solana.com/developers',
  'MEV protection': 'https://docs.jup.ag/',
  'Jupiter SDK': 'https://docs.jup.ag/',
  
  // Oracle - Trading skills
  'Technical Analysis': 'https://www.investopedia.com/technical-analysis-4689757',
  'Backtesting': 'https://www.investopedia.com/terms/b/backtesting.asp',
  'Risk Management': 'https://www.investopedia.com/risk-management-4689742',
  'Indicators': 'https://www.tradingview.com/support/solutions/43000501889-technical-indicators/',
  'Position Sizing': 'https://www.investopedia.com/terms/p/positionsizing.asp',
  'Kelly Criterion': 'https://www.investopedia.com/articles/trading/04/091504.asp',
  'On-chain analysis': 'https://www.glassnode.com/',
  'Order flow': 'https://www.investopedia.com/terms/o/order-flow.asp',
  'Machine learning for trading': 'https://scikit-learn.org/stable/',
  'Market regimes': 'https://www.investopedia.com/market-regime-4689757',
  
  // Pixel - UI skills
  'React': 'https://react.dev/',
  'Tailwind CSS': 'https://tailwindcss.com/docs',
  'Next.js': 'https://nextjs.org/docs',
  'Component Design': 'https://www.componentdriven.org/',
  'Responsive UI': 'https://web.dev/responsive-web-design-basics/',
  'Data visualization': 'https://d3js.org/',
  'Three.js': 'https://threejs.org/docs/',
  'Motion design': 'https://www.framer.com/motion/',
  'Real-time dashboards': 'https://socket.io/',
  
  // Synthesis - Management skills
  'Architecture': 'https://martinfowler.com/architecture/',
  'Coordination': 'https://en.wikipedia.org/wiki/Management',
  'Task Delegation': '#',
  'Requirements Analysis': 'https://en.wikipedia.org/wiki/Requirements_analysis',
  'System Design': 'https://en.wikipedia.org/wiki/Systems_design',
  'Code Review': 'https://github.com/features/code-review',
  'Documentation': 'https://docs.github.com/',
  'Testing': 'https://testing-library.com/',
  'Microservices': 'https://microservices.io/',
  'Event Sourcing': 'https://martinfowler.com/eaaDev/EventSourcing.html',
  'CQRS': 'https://martinfowler.com/bliki/CQRS.html',
  'DDD': 'https://martinfowler.com/tags/domain%20driven%20design.html',
}

function getSkillIcon(skill: string) {
  const lower = skill.toLowerCase()
  if (lower.includes('python') || lower.includes('code') || lower.includes('rust')) return <Code className="w-3 h-3" />
  if (lower.includes('trading') || lower.includes('backtest') || lower.includes('risk')) return <TrendingUp className="w-3 h-3" />
  if (lower.includes('react') || lower.includes('ui') || lower.includes('design')) return <Palette className="w-3 h-3" />
  if (lower.includes('database') || lower.includes('data')) return <Database className="w-3 h-3" />
  if (lower.includes('async') || lower.includes('websocket') || lower.includes('api')) return <Zap className="w-3 h-3" />
  return <Layers className="w-3 h-3" />
}

export default function AgentsPage() {
  // Agents state
  const [agents, setAgents] = useState<Agent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [pendingApprovals, setPendingApprovals] = useState<PendingApproval[]>([])
  const [isProcessingApproval, setIsProcessingApproval] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Task queue state
  const [tasks, setTasks] = useState<Task[]>([])
  const [tasksLoading, setTasksLoading] = useState(true)
  const [newTask, setNewTask] = useState('')
  const [selectedAgent, setSelectedAgent] = useState('synthesis')
  const [showTaskForm, setShowTaskForm] = useState(false)

  const fetchAgents = useCallback(async () => {
    try {
      setIsLoading(true)
      setError(null)
      
      // Scan the agents directory structure
      const agentDirs = ['synthesis', 'ghost', 'oracle', 'pixel']
      const agentDataResults = await Promise.all(agentDirs.map(async (dir) => {
        try {
          const basePath = `/agents/${dir}`
          const meta = AGENT_META[dir] || { emoji: '🤖', color: 'cyan', role: 'Agent' }
          
          const agent: Agent = {
            id: dir,
            name: dir.charAt(0).toUpperCase() + dir.slice(1),
            emoji: meta.emoji,
            role: meta.role,
            description: getAgentDescription(dir),
            status: getAgentStatus(dir),
            lastActivity: new Date(Date.now() - Math.random() * 3600000).toISOString(),
            model: 'ollama/kimi-k2.5:cloud',
            skills: getAgentSkills(dir),
            recommendedSkills: getAgentRecommendedSkills(dir),
            currentTask: undefined
          }
          return agent
        } catch (e) {
          console.error(`Error loading agent ${dir}:`, e)
          return null
        }
      }))
      
      setAgents(agentDataResults.filter((a): a is Agent => a !== null))
    } catch (e) {
      setError('Failed to load agents')
      console.error(e)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const fetchTasks = useCallback(async () => {
    try {
      const res = await fetch('/api/tasks')
      const data = await res.json()
      if (data.tasks) {
        setTasks(data.tasks)
      }
    } finally {
      setTasksLoading(false)
    }
  }, [])

  const fetchPendingApprovals = useCallback(async () => {
    try {
      const res = await fetch('/api/pending-approvals')
      if (!res.ok) throw new Error('Failed to fetch')
      const data = await res.json()
      setPendingApprovals(data.approvals || [])
    } catch (e) {
      console.log('No pending approvals or API not ready')
      setPendingApprovals([])
    }
  }, [])

  useEffect(() => {
    fetchAgents()
    fetchTasks()
    fetchPendingApprovals()
    
    const interval = setInterval(() => {
      fetchTasks()
      fetchPendingApprovals()
    }, 5000)
    
    return () => clearInterval(interval)
  }, [fetchAgents, fetchTasks, fetchPendingApprovals])

  const handleApproval = async (approvalId: string, action: 'approve' | 'reject') => {
    setIsProcessingApproval(true)
    try {
      const res = await fetch('/api/pending-approvals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approvalId, action })
      })
      if (!res.ok) throw new Error('Failed to process approval')
      await fetchPendingApprovals()
    } catch (e) {
      console.error('Approval error:', e)
    } finally {
      setIsProcessingApproval(false)
    }
  }

  const createTask = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newTask.trim()) return

    try {
      const res = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent: selectedAgent, description: newTask }),
      })
      
      if (res.ok) {
        setNewTask('')
        setShowTaskForm(false)
        fetchTasks()
      }
    } catch (error) {
      console.error('Failed to create task:', error)
    }
  }

  // Loading skeleton
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
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link 
                href="/"
                className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 via-cyan-400 to-purple-500 bg-clip-text text-transparent">
                  Your AI Team
                </h1>
                <p className="text-slate-400 mt-1">Assign tasks to Synthesis — he'll delegate to the right specialist</p>
              </div>
            </div>
            <button
              onClick={() => setShowTaskForm(!showTaskForm)}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Task
            </button>
          </div>
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

        {/* Task Assignment Form */}
        {showTaskForm && (
          <div className="mb-8 bg-slate-900 rounded-xl border border-slate-800 p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                <span className="text-xl">🧠</span>
              </div>
              <div>
                <h2 className="text-lg font-semibold">Assign New Task</h2>
                <p className="text-sm text-slate-400">Synthesis will coordinate and delegate to specialists</p>
              </div>
            </div>
            
            <form onSubmit={createTask}>
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm text-slate-400">Select Agent</label>
                    <span className="text-xs text-purple-400">Synthesis routes tasks to specialists</span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {Object.entries(AGENT_META).map(([id, meta]) => (
                      <button
                        key={id}
                        type="button"
                        onClick={() => setSelectedAgent(id)}
                        className={`p-3 rounded-lg border transition-all text-left relative ${
                          selectedAgent === id
                            ? `border-cyan-500 bg-cyan-500/10 ring-1 ring-cyan-500/50`
                            : 'border-slate-700 hover:border-slate-600'
                        } ${id === 'synthesis' ? 'ring-1 ring-purple-500/30' : ''}`}
                      >
                        {id === 'synthesis' && (
                          <span className="absolute -top-2 left-2 px-1.5 py-0.5 bg-purple-500 text-white text-[10px] rounded font-medium">
                            RECOMMENDED
                          </span>
                        )}
                        <div className="flex items-center gap-2 mb-1">
                          <div className={`w-3 h-3 rounded-full ${getColorClasses(meta.color, 'bg')}`} />
                          <span className="font-medium capitalize">{id}</span>
                          <span className="text-lg">{meta.emoji}</span>
                        </div>
                        <p className="text-xs text-slate-400">{meta.role}</p>
                      </button>
                    ))}
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    Tip: Assign to Synthesis for general tasks — he'll delegate to the right specialist.
                  </p>
                </div>

                <div>
                  <label className="block text-sm text-slate-400 mb-2">Task Description</label>
                  <textarea
                    value={newTask}
                    onChange={(e) => setNewTask(e.target.value)}
                    placeholder="Describe what needs to be done..."
                    className="w-full bg-slate-800 rounded-lg p-3 text-white placeholder-slate-500 h-32 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                <div className="flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowTaskForm(false)}
                    className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!newTask.trim()}
                    className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded-lg transition-colors"
                  >
                    Assign Task
                  </button>
                </div>
              </div>
            </form>
          </div>
        )}

        {/* Pending Approvals */}
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
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        approval.priority === 'high' ? 'bg-red-500/20 text-red-400' :
                        approval.priority === 'medium' ? 'bg-amber-500/20 text-amber-400' :
                        'bg-cyan-500/20 text-cyan-400'
                      }`}>
                        {approval.priority.toUpperCase()}
                      </span>
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

        {/* Agent Grid */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            Your Agents
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className={`bg-slate-900 rounded-xl border transition-all hover:border-slate-600 ${
                  agent.status === 'busy' ? 'border-purple-500/50 ring-1 ring-purple-500/10' : 'border-slate-800'
                }`}
              >
                <div className="p-4">
                  {/* Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-lg ${getColorClasses(AGENT_META[agent.id]?.color || 'cyan', 'bg')} flex items-center justify-center`}>
                        <span className="text-xl">{agent.emoji}</span>
                      </div>
                      <div>
                        <h3 className="font-semibold capitalize">{agent.name}</h3>
                        <p className="text-xs text-slate-400">{agent.role}</p>
                      </div>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-xs ${getStatusColor(agent.status)}`}>
                      {agent.status}
                    </span>
                  </div>

                  <p className="text-sm text-slate-400 mb-4">{agent.description}</p>

                  {/* Current Task */}
                  {agent.currentTask && (
                    <div className="mb-3 p-2 bg-slate-800/50 rounded text-xs">
                      <span className="text-slate-500">Working on:</span>
                      <span className="ml-2 text-cyan-400">{agent.currentTask}</span>
                    </div>
                  )}

                  {/* Skills */}
                  <div className="mb-3">
                    <p className="text-xs text-slate-500 mb-2">Skills</p>
                    <div className="flex flex-wrap gap-1">
                      {agent.skills.slice(0, 4).map((skill) => (
                        <span
                          key={skill}
                          className="inline-flex items-center gap-1 px-2 py-0.5 bg-slate-800 rounded text-xs text-slate-300"
                        >
                          {getSkillIcon(skill)}
                          {skill}
                        </span>
                      ))}
                      {agent.skills.length > 4 && (
                        <span className="px-2 py-0.5 bg-slate-800 rounded text-xs text-slate-500">
                          +{agent.skills.length - 4}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Link
                      href={`/agents/learning/${agent.id}`}
                      className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-slate-800 hover:bg-slate-700 rounded text-xs font-medium transition-colors"
                    >
                      <BookOpen className="w-3 h-3" />
                      Learning
                    </Link>
                    <button
                      onClick={() => {
                        setSelectedAgent(agent.id)
                        setShowTaskForm(true)
                        window.scrollTo({ top: 0, behavior: 'smooth' })
                      }}
                      className="flex-1 flex items-center justify-center gap-1.5 py-1.5 bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 rounded text-xs font-medium transition-colors"
                    >
                      <Plus className="w-3 h-3" />
                      Assign
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Task Queue */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Clock className="w-5 h-5 text-slate-400" />
              Task Queue
            </h2>
            {tasksLoading && <RefreshCw className="w-4 h-4 animate-spin text-slate-400" />}
          </div>

          {tasks.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              <p>No tasks yet. Click "New Task" to assign work to an agent.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {tasks.slice(0, 10).map((task) => {
                const agentMeta = AGENT_META[task.agent] || { emoji: '🤖', color: 'cyan', role: 'Agent' }
                return (
                  <div
                    key={task.id}
                    className="px-6 py-4 hover:bg-slate-800/50 transition-colors"
                  >
                    <div className="flex items-start gap-4">
                      <div className={`w-10 h-10 rounded-lg ${getColorClasses(agentMeta.color, 'bg')} flex items-center justify-center shrink-0`}>
                        <span className="text-lg">{agentMeta.emoji}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-1">
                          <span className="font-medium capitalize">{task.agent}</span>
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            task.status === 'pending' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/30' :
                            task.status === 'in-progress' ? 'bg-cyan-500/10 text-cyan-400 border border-cyan-500/30' :
                            task.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30' :
                            'bg-red-500/10 text-red-400 border border-red-500/30'
                          }`}>
                            {task.status}
                          </span>
                        </div>
                        <p className="text-slate-400 text-sm mb-2">{task.description}</p>
                        <div className="flex items-center gap-4 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(task.createdAt).toLocaleString()}
                          </span>
                          {task.status === 'completed' && (
                            <span className="flex items-center gap-1 text-emerald-400">
                              <CheckCircle2 className="w-3 h-3" />
                              Done
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* How It Works */}
        <div className="mt-8 bg-slate-900/50 rounded-xl border border-slate-800 p-6">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-2xl">🧠</span>
            <h3 className="text-sm font-semibold text-purple-400">HOW IT WORKS</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded bg-purple-500/20 text-purple-400 flex items-center justify-center text-xs font-medium">1</div>
              <div>
                <p className="text-slate-300 font-medium">Talk to Synthesis</p>
                <p className="text-slate-500">Describe what you need, he'll understand the intent</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded bg-purple-500/20 text-purple-400 flex items-center justify-center text-xs font-medium">2</div>
              <div>
                <p className="text-slate-300 font-medium">He Delegates</p>
                <p className="text-slate-500">Routes to Pixel 🎨, Ghost 👻, or Oracle 🔮 as needed</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded bg-purple-500/20 text-purple-400 flex items-center justify-center text-xs font-medium">3</div>
              <div>
                <p className="text-slate-300 font-medium">You Get Results</p>
                <p className="text-slate-500">Synthesis coordinates handoffs and reports completion</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// Helper functions
function getAgentDescription(id: string): string {
  const descriptions: Record<string, string> = {
    synthesis: 'Team lead. Coordinates tasks and delegates to specialists.',
    ghost: 'Backend engineer. Handles APIs, databases, and infrastructure.',
    oracle: 'Trading analyst. Strategies, backtesting, and market analysis.',
    pixel: 'UI/UX engineer. Dashboards, components, and visual polish.',
  }
  return descriptions[id] || 'AI agent ready to help.'
}

function getAgentStatus(id: string): Agent['status'] {
  // Simulate status based on time
  const statuses: Agent['status'][] = ['idle', 'busy', 'learning', 'offline']
  return statuses[Math.floor(Date.now() / 100000) % statuses.length]
}

function getAgentSkills(id: string): string[] {
  const skills: Record<string, string[]> = {
    synthesis: ['Architecture', 'Coordination', 'Task Delegation', 'System Design', 'Code Review'],
    ghost: ['Python', 'Async/await', 'Database', 'WebSocket', 'Error Handling'],
    oracle: ['Technical Analysis', 'Backtesting', 'Risk Management', 'Indicators', 'Position Sizing'],
    pixel: ['React', 'Tailwind CSS', 'Next.js', 'Component Design', 'Responsive UI'],
  }
  return skills[id] || ['General assistance']
}

function getAgentRecommendedSkills(id: string): string[] {
  const skills: Record<string, string[]> = {
    synthesis: ['Documentation', 'Testing', 'Microservices', 'Event Sourcing', 'CQRS'],
    ghost: ['Circuit Breakers', 'Rust', 'Solana smart contracts', 'MEV protection', 'Jupiter SDK'],
    oracle: ['On-chain analysis', 'Order flow', 'Machine learning for trading', 'Market regimes', 'Kelly Criterion'],
    pixel: ['Data visualization', 'Three.js', 'Motion design', 'Real-time dashboards', 'D3'],
  }
  return skills[id] || []
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'idle': return 'bg-emerald-500/20 text-emerald-400'
    case 'busy': return 'bg-purple-500/20 text-purple-400'
    case 'learning': return 'bg-cyan-500/20 text-cyan-400'
    case 'offline': return 'bg-slate-700 text-slate-400'
    default: return 'bg-slate-700 text-slate-400'
  }
}
