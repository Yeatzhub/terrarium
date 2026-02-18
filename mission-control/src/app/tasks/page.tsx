'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { ArrowLeft, Plus, Clock, CheckCircle, XCircle, Play, Loader2 } from 'lucide-react'

interface Task {
  id: string
  agent: string
  status: 'pending' | 'in-progress' | 'completed' | 'failed'
  description: string
  createdAt: string
  startedAt?: string
  completedAt?: string
}

const AGENTS = [
  { id: 'synthesis', name: 'Synthesis 🧠', role: 'Team Lead - Task Coordinator', color: 'bg-purple-500', accent: 'border-purple-500/50' },
  { id: 'pixel', name: 'Pixel 🎨', role: 'UI/UX Engineer', color: 'bg-pink-500', accent: 'border-pink-500/50' },
  { id: 'ghost', name: 'Ghost 👻', role: 'Backend Engineer', color: 'bg-slate-500', accent: 'border-slate-500/50' },
  { id: 'oracle', name: 'Oracle 🔮', role: 'Trading Analyst', color: 'bg-amber-500', accent: 'border-amber-500/50' },
]

const STATUS_COLORS = {
  pending: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  'in-progress': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
  completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  failed: 'bg-red-500/10 text-red-400 border-red-500/30',
}

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [newTask, setNewTask] = useState('')
  const [selectedAgent, setSelectedAgent] = useState('synthesis')
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    fetchTasks()
    const interval = setInterval(fetchTasks, 5000)
    return () => clearInterval(interval)
  }, [])

  const fetchTasks = async () => {
    try {
      const res = await fetch('/api/tasks')
      const data = await res.json()
      if (data.tasks) {
        setTasks(data.tasks)
      }
    } finally {
      setLoading(false)
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
        setShowForm(false)
        fetchTasks()
      }
    } catch (error) {
      console.error('Failed to create task:', error)
    }
  }

  const getAgentInfo = (agentId: string) => AGENTS.find((a) => a.id === agentId) || AGENTS[0]

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link href="/" className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 via-cyan-400 to-purple-500 bg-clip-text text-transparent">
                Assign Task to Synthesis
              </h1>
              <p className="text-slate-400">
                Tell Synthesis what you need — he'll delegate to the right specialist
              </p>
            </div>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Task
          </button>
        </div>

        {/* New Task Form */}
        {showForm && (
          <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 mb-6">
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
                    {AGENTS.map((agent) => (
                      <button
                        key={agent.id}
                        type="button"
                        onClick={() => setSelectedAgent(agent.id)}
                        className={`p-3 rounded-lg border transition-all text-left relative ${
                          selectedAgent === agent.id
                            ? `border-cyan-500 bg-cyan-500/10 ring-1 ring-cyan-500/50`
                            : 'border-slate-700 hover:border-slate-600'
                        } ${agent.id === 'synthesis' ? 'ring-1 ring-purple-500/30' : ''}`}
                      >
                        {agent.id === 'synthesis' && (
                          <span className="absolute -top-2 left-2 px-1.5 py-0.5 bg-purple-500 text-white text-[10px] rounded font-medium">
                            RECOMMENDED
                          </span>
                        )}
                        <div className="flex items-center gap-2 mb-1">
                          <div className={`w-3 h-3 rounded-full ${agent.color}`} />
                          <span className="font-medium">{agent.name}</span>
                        </div>
                        <p className="text-xs text-slate-400">{agent.role}</p>
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
                    className="w-full bg-slate-800 rounded-lg p-3 text-white placeholder-slate-500 h-32 resize-none focus:outline-none focus:ring-2 focus:ring-cyan-500"
                  />
                </div>

                <div className="flex justify-end gap-3">
                  <button
                    type="button"
                    onClick={() => setShowForm(false)}
                    className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!newTask.trim()}
                    className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 rounded-lg transition-colors"
                  >
                    Assign Task
                  </button>
                </div>
              </div>
            </form>
          </div>
        )}

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {['pending', 'in-progress', 'completed', 'failed'].map((status) => {
            const count = tasks.filter((t) => t.status === status).length
            return (
              <div key={status} className="bg-slate-900 rounded-xl p-4 border border-slate-800">
                <p className="text-sm text-slate-400 capitalize">{status.replace('-', ' ')}</p>
                <p className="text-2xl font-bold">{count}</p>
              </div>
            )
          })}
        </div>

        {/* Task List */}
        <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Tasks</h2>
            {loading && <Loader2 className="w-4 h-4 animate-spin text-slate-400" />}
          </div>

          {tasks.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              <p>No tasks yet. Click "New Task" to assign work to an agent.</p>
            </div>
          ) : (
            <div className="divide-y divide-slate-800">
              {tasks.map((task) => {
                const agent = getAgentInfo(task.agent)
                return (
                  <div
                    key={task.id}
                    className="px-6 py-4 hover:bg-slate-800/50 transition-colors"
                  >
                    <div className="flex items-start gap-4">
                      <div className={`w-10 h-10 rounded-lg ${agent.color} flex items-center justify-center shrink-0`}>
                        <span className="text-lg">{agent.name.split(' ')[1]}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-1">
                          <span className="font-medium">{agent.name}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-xs border ${STATUS_COLORS[task.status]}`}
                          >
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
                              <CheckCircle className="w-3 h-3" />
                              Done
                            </span>
                          )}
                          {task.status === 'failed' && (
                            <span className="flex items-center gap-1 text-red-400">
                              <XCircle className="w-3 h-3" />
                              Failed
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
            <h3 className="text-sm font-semibold text-purple-400">HOW SYNTHESIS WORKS</h3>
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
