'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Wifi, 
  WifiOff, 
  Plus, 
  Users, 
  CheckCircle2, 
  Clock, 
  AlertCircle,
  ChevronRight,
  Terminal,
  Zap,
  TrendingUp,
  Activity
} from 'lucide-react';

interface Task {
  id: string;
  agent: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  description: string;
  createdAt: string;
}

interface Agent {
  id: string;
  name: string;
  emoji: string;
  status: 'idle' | 'busy' | 'learning' | 'offline';
  currentTask?: string;
}

const AGENTS = [
  { id: 'synthesis', name: 'Synthesis', emoji: '🧠', color: 'bg-purple-500', role: 'Team Lead' },
  { id: 'pixel', name: 'Pixel', emoji: '🎨', color: 'bg-pink-500', role: 'UI/UX' },
  { id: 'ghost', name: 'Ghost', emoji: '👻', color: 'bg-slate-500', role: 'Backend' },
  { id: 'oracle', name: 'Oracle', emoji: '🔮', color: 'bg-amber-500', role: 'Trading' },
];

export default function MissionControl() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isConnected, setIsConnected] = useState(true);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [quickTask, setQuickTask] = useState('');
  const [showQuickTask, setShowQuickTask] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchTasks = async () => {
    try {
      const res = await fetch('/api/tasks');
      const data = await res.json();
      if (data.tasks) {
        setTasks(data.tasks.slice(0, 5));
      }
    } catch (e) {
      console.error('Failed to fetch tasks:', e);
    }
  };

  const createQuickTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickTask.trim()) return;

    try {
      await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent: 'synthesis', description: quickTask }),
      });
      setQuickTask('');
      setShowQuickTask(false);
      fetchTasks();
    } catch (e) {
      console.error('Failed to create task:', e);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    });
  };

  const pendingCount = tasks.filter(t => t.status === 'pending').length;
  const activeCount = tasks.filter(t => t.status === 'in-progress').length;
  const completedCount = tasks.filter(t => t.status === 'completed').length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <header className="h-16 bg-slate-900/80 backdrop-blur border-b border-slate-800 flex items-center justify-between px-6 sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 via-cyan-400 to-purple-500 bg-clip-text text-transparent">
            Mission Control
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 rounded-full">
            {isConnected ? (
              <>
                <Wifi className="w-4 h-4 text-emerald-400" />
                <span className="text-sm text-emerald-400">Connected</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-red-400" />
                <span className="text-sm text-red-400">Disconnected</span>
              </>
            )}
          </div>
          <div className="text-sm text-slate-400 font-mono">
            {formatTime(currentTime)}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="p-6">
        <div className="max-w-7xl mx-auto">
          
          {/* Welcome Section */}
          <div className="mb-8">
            <h2 className="text-3xl font-bold mb-2">Welcome back</h2>
            <p className="text-slate-400">
              Your AI team is ready. Assign tasks to Synthesis and he'll delegate to the right specialist.
            </p>
          </div>

          {/* Quick Actions Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
            {/* Quick Task */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <Plus className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Quick Task</h3>
                    <p className="text-sm text-slate-400">Assign to Synthesis</p>
                  </div>
                </div>
                <button 
                  onClick={() => setShowQuickTask(!showQuickTask)}
                  className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 rounded text-sm transition-colors"
                >
                  New
                </button>
              </div>
              
              {showQuickTask && (
                <form onSubmit={createQuickTask} className="mt-4">
                  <textarea
                    value={quickTask}
                    onChange={(e) => setQuickTask(e.target.value)}
                    placeholder="What do you need?"
                    className="w-full bg-slate-800 rounded-lg p-3 text-sm text-white placeholder-slate-500 h-20 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 mb-2"
                  />
                  <div className="flex justify-end gap-2">
                    <button
                      type="button"
                      onClick={() => setShowQuickTask(false)}
                      className="px-3 py-1 text-sm text-slate-400 hover:text-white"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={!quickTask.trim()}
                      className="px-3 py-1 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 rounded text-sm"
                    >
                      Assign
                    </button>
                  </div>
                </form>
              )}
            </div>

            {/* Task Stats */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                  <Activity className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <h3 className="font-semibold">Task Queue</h3>
                  <p className="text-sm text-slate-400">Live status</p>
                </div>
              </div>
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-2xl font-bold text-amber-400">{pendingCount}</p>
                  <p className="text-xs text-slate-500">Pending</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-cyan-400">{activeCount}</p>
                  <p className="text-xs text-slate-500">Active</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-emerald-400">{completedCount}</p>
                  <p className="text-xs text-slate-500">Done</p>
                </div>
              </div>
            </div>

            {/* Agents Status */}
            <Link href="/agents" className="block">
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 hover:border-slate-700 transition-colors">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                    <Users className="w-5 h-5 text-emerald-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Your Team</h3>
                    <p className="text-sm text-slate-400">4 agents ready</p>
                  </div>
                </div>
                <div className="flex -space-x-2">
                  {AGENTS.map((agent) => (
                    <div 
                      key={agent.id}
                      className={`w-8 h-8 rounded-full ${agent.color} flex items-center justify-center text-sm ring-2 ring-slate-900`}
                      title={agent.name}
                    >
                      {agent.emoji}
                    </div>
                  ))}
                </div>
                <div className="mt-4 flex items-center text-sm text-slate-400">
                  <span>View Agents</span>
                  <ChevronRight className="w-4 h-4 ml-1" />
                </div>
              </div>
            </Link>
          </div>

          {/* Recent Tasks */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden mb-8">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-slate-400" />
                <h2 className="text-lg font-semibold">Recent Tasks</h2>
              </div>
              <Link href="/agents" className="text-sm text-cyan-400 hover:text-cyan-300">
                View All
              </Link>
            </div>
            
            {tasks.length === 0 ? (
              <div className="p-8 text-center text-slate-500">
                <p>No tasks yet. Use "Quick Task" to assign work.</p>
              </div>
            ) : (
              <div className="divide-y divide-slate-800">
                {tasks.map((task) => {
                  const agent = AGENTS.find(a => a.id === task.agent) || AGENTS[0];
                  return (
                    <div key={task.id} className="px-6 py-3 flex items-center gap-4">
                      <div className={`w-8 h-8 rounded-full ${agent.color} flex items-center justify-center text-sm`}>
                        {agent.emoji}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{task.description}</p>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-xs ${
                        task.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' :
                        task.status === 'in-progress' ? 'bg-cyan-500/10 text-cyan-400' :
                        task.status === 'failed' ? 'bg-red-500/10 text-red-400' :
                        'bg-amber-500/10 text-amber-400'
                      }`}>
                        {task.status}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Quick Links Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link href="/trading" className="block">
              <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-4 hover:border-slate-700 transition-colors">
                <TrendingUp className="w-5 h-5 text-cyan-400 mb-2" />
                <p className="font-medium">Trading</p>
                <p className="text-xs text-slate-500">Bots & positions</p>
              </div>
            </Link>
            <Link href="/hardware/gpu" className="block">
              <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-4 hover:border-slate-700 transition-colors">
                <Zap className="w-5 h-5 text-cyan-400 mb-2" />
                <p className="font-medium">GPU</p>
                <p className="text-xs text-slate-500">P40 status</p>
              </div>
            </Link>
            <Link href="/llm/status" className="block">
              <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-4 hover:border-slate-700 transition-colors">
                <Terminal className="w-5 h-5 text-cyan-400 mb-2" />
                <p className="font-medium">LLM</p>
                <p className="text-xs text-slate-500">Models & usage</p>
              </div>
            </Link>
            <Link href="/agents" className="block">
              <div className="bg-slate-900/50 rounded-xl border border-slate-800 p-4 hover:border-slate-700 transition-colors">
                <CheckCircle2 className="w-5 h-5 text-cyan-400 mb-2" />
                <p className="font-medium">Tasks</p>
                <p className="text-xs text-slate-500">Assign & track</p>
              </div>
            </Link>
          </div>

          {/* Automation Status */}
          <div className="mt-8 bg-slate-900/30 rounded-xl border border-slate-800 p-4">
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <p className="text-sm text-slate-400">
                <span className="text-slate-300 font-medium">Automation Active:</span> Agents auto-poll every 2-4 minutes
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
