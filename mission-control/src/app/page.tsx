'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Wifi, 
  WifiOff,
  Server,
  Cpu,
  Bot,
  Activity,
  RefreshCw,
  Loader2,
  Users,
  TrendingUp,
  CheckCircle2,
  Clock,
  Plus,
  Brain,
  DollarSign,
  Zap,
  Terminal
} from 'lucide-react';

interface Task {
  id: string;
  agent: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  description: string;
  createdAt: string;
}

const AGENTS = [
  { id: 'synthesis', name: 'Synthesis', emoji: '🧠', color: 'bg-purple-500', role: 'Team Lead' },
  { id: 'pixel', name: 'Pixel', emoji: '🎨', color: 'bg-pink-500', role: 'UI/UX' },
  { id: 'ghost', name: 'Ghost', emoji: '👻', color: 'bg-slate-500', role: 'Backend' },
  { id: 'oracle', name: 'Oracle', emoji: '🔮', color: 'bg-amber-500', role: 'Trading' },
  { id: 'nexus', name: 'Nexus', emoji: '📱', color: 'bg-blue-500', role: 'Mobile' },
];

const LEARNING_DATA = [
  { agent: 'ghost', emoji: '👻', time: '10:25', topic: 'Kelly + Monte Carlo' },
  { agent: 'synthesis', emoji: '🧠', time: '10:20', topic: 'Quality Standards' },
  { agent: 'ghost', emoji: '👻', time: '09:23', topic: 'Trade Journal Analytics' },
  { agent: 'oracle', emoji: '🔮', time: '07:53', topic: 'Trade Management' },
  { agent: 'pixel', emoji: '🎨', time: '07:25', topic: 'Button Design System' },
];

export default function Dashboard() {
  const [time, setTime] = useState(new Date());
  const [tasks, setTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [openclawOnline, setOpenclawOnline] = useState(false);
  const [toobitData, setToobitData] = useState({ status: 'active', balance: 10000, trades: 0 });
  const [pionexData, setPionexData] = useState({ status: 'running', balance: 84.27, trades: 14 });

  // Clock
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Fetch all data
  const loadData = async () => {
    setIsLoading(true);
    
    try {
      // Check OpenClaw
      fetch('http://100.125.198.70:18789/status', { 
        mode: 'no-cors',
        signal: AbortSignal.timeout(3000)
      }).then(() => setOpenclawOnline(true))
        .catch(() => setOpenclawOnline(false));

      // Fetch tasks
      const tasksRes = await fetch('/api/tasks');
      if (tasksRes.ok) {
        const data = await tasksRes.json();
        setTasks(data.tasks?.slice(0, 5) || []);
      }

      // Fetch Toobit
      const toobitRes = await fetch('/api/trading-data?exchange=toobit');
      if (toobitRes.ok) {
        const data = await toobitRes.json();
        setToobitData({
          status: data.status || 'active',
          balance: data.balance || 10000,
          trades: data.stats?.total_trades || 0
        });
      }

      // Fetch Pionex
      const pionexRes = await fetch('/api/pionex-xrp');
      if (pionexRes.ok) {
        const data = await pionexRes.json();
        setPionexData({
          status: data.status || 'running',
          balance: data.balance || 84.27,
          trades: data.totalTrades || 14
        });
      }
    } catch (err) {
      console.error('Error loading data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const pending = tasks.filter(t => t.status === 'pending').length;
  const active = tasks.filter(t => t.status === 'in-progress').length;
  const completed = tasks.filter(t => t.status === 'completed').length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Header */}
      <header className="h-16 bg-slate-900/80 backdrop-blur border-b border-slate-800 flex items-center justify-between px-6 sticky top-0 z-40">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 via-cyan-400 to-purple-500 bg-clip-text text-transparent">
            The Hub
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-800/50 rounded-full">
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 text-amber-400 animate-spin" />
                <span className="text-sm text-amber-400">Loading...</span>
              </>
            ) : openclawOnline ? (
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
          <button 
            onClick={loadData}
            disabled={isLoading}
            className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-5 h-5 text-slate-400 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
          <div className="text-sm text-slate-400 font-mono">
            {time.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: true })}
          </div>
        </div>
      </header>

      <main className="p-6">
        <div className="max-w-7xl mx-auto space-y-6">
          
          {/* Welcome */}
          <div>
            <h2 className="text-3xl font-bold mb-2">Overview</h2>
            <p className="text-slate-400">Real-time status of your AI team, trading bots, and system health.</p>
          </div>

          {/* Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* OpenClaw */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${openclawOnline ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
                  <Server className={`w-5 h-5 ${openclawOnline ? 'text-emerald-400' : 'text-red-400'}`} />
                </div>
                <div>
                  <h3 className="font-semibold">OpenClaw</h3>
                  <p className={`text-sm ${openclawOnline ? 'text-emerald-400' : 'text-red-400'}`}>
                    {openclawOnline ? 'Online' : 'Offline'}
                  </p>
                </div>
              </div>
              <p className="text-xs text-slate-500">100.125.198.70:18789</p>
            </div>

            {/* GPU */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                  <Cpu className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <h3 className="font-semibold">GPU (P40)</h3>
                  <p className="text-sm text-cyan-400">42°C</p>
                </div>
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">Utilization</span>
                  <span className="text-slate-300">15%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">VRAM</span>
                  <span className="text-slate-300">4.2/24 GB</span>
                </div>
              </div>
            </div>

            {/* Trading Bots */}
            <Link href="/trading" className="block">
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 hover:border-slate-700 transition-colors">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-amber-500/20 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-amber-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Trading Bots</h3>
                    <p className="text-sm text-amber-400">2/2 Active</p>
                  </div>
                </div>
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Toobit</span>
                    <span className="text-emerald-400">● {toobitData.trades} trades</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Pionex</span>
                    <span className="text-emerald-400">● {pionexData.trades} trades</span>
                  </div>
                </div>
              </div>
            </Link>

            {/* Tasks */}
            <Link href="/agents" className="block">
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 hover:border-slate-700 transition-colors">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <Activity className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Task Queue</h3>
                    <p className="text-sm text-purple-400">{pending} pending</p>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-lg font-bold text-amber-400">{pending}</p>
                    <p className="text-xs text-slate-500">Pending</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-cyan-400">{active}</p>
                    <p className="text-xs text-slate-500">Active</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-emerald-400">{completed}</p>
                    <p className="text-xs text-slate-500">Done</p>
                  </div>
                </div>
              </div>
            </Link>
          </div>

          {/* Main Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column */}
            <div className="lg:col-span-2 space-y-6">
              {/* Team */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-slate-400" />
                    <h2 className="text-lg font-semibold">Your AI Team</h2>
                  </div>
                  <Link href="/agents" className="text-sm text-cyan-400 hover:text-cyan-300">View All</Link>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  {AGENTS.map(agent => (
                    <div key={agent.id} className="bg-slate-800/50 rounded-lg p-4 text-center">
                      <div className={`w-12 h-12 rounded-full ${agent.color} flex items-center justify-center text-xl mx-auto mb-2`}>
                        {agent.emoji}
                      </div>
                      <p className="font-medium text-sm">{agent.name}</p>
                      <p className="text-xs text-slate-500">{agent.role}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recent Training */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-slate-400" />
                    <h2 className="text-lg font-semibold">Recent Agent Training</h2>
                  </div>
                  <span className="text-xs text-slate-500">Last 24h</span>
                </div>
                <div className="divide-y divide-slate-800">
                  {LEARNING_DATA.map((item, idx) => {
                    const agent = AGENTS.find(a => a.emoji === item.emoji) || AGENTS[0];
                    return (
                      <div key={idx} className="px-6 py-3 flex items-center gap-4 hover:bg-slate-800/50">
                        <div className={`w-8 h-8 rounded-full ${agent.color} flex items-center justify-center text-sm`}>
                          {item.emoji}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{item.topic}</p>
                          <p className="text-xs text-slate-500">{item.agent} • {item.time}</p>
                        </div>
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Recent Tasks */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-slate-400" />
                    <h2 className="text-lg font-semibold">Recent Tasks</h2>
                  </div>
                  <Link href="/agents" className="text-sm text-cyan-400 hover:text-cyan-300">View All</Link>
                </div>
                {tasks.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    {isLoading ? (
                      <div className="flex items-center justify-center gap-2">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        <p>Loading tasks...</p>
                      </div>
                    ) : (
                      <p>No tasks yet. Use Quick Task to assign work.</p>
                    )}
                  </div>
                ) : (
                  <div className="divide-y divide-slate-800">
                    {tasks.map(task => {
                      const agent = AGENTS.find(a => a.id === task.agent) || AGENTS[0];
                      return (
                        <div key={task.id} className="px-6 py-3 flex items-center gap-4 hover:bg-slate-800/50">
                          <div className={`w-8 h-8 rounded-full ${agent.color} flex items-center justify-center text-sm`}>
                            {agent.emoji}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{task.description.slice(0, 50)}...</p>
                            <p className="text-xs text-slate-500">{agent.name}</p>
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
            </div>

            {/* Right Column */}
            <div className="space-y-6">
              {/* Quick Task */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <Plus className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Quick Task</h3>
                    <p className="text-sm text-slate-400">Assign to Synthesis</p>
                  </div>
                </div>
                <button className="w-full py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm transition-colors">
                  + Create New Task
                </button>
              </div>

              {/* Trading */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-slate-400" />
                    <h3 className="font-semibold">Trading</h3>
                  </div>
                  <Link href="/trading" className="text-sm text-cyan-400">Details →</Link>
                </div>
                <div className="space-y-4">
                  <div className="bg-slate-800/50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm">Toobit BTC</span>
                      <span className="text-xs text-emerald-400">● Running</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-slate-500">Balance</span>
                        <p className="text-slate-300">${toobitData.balance.toFixed(2)}</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Trades</span>
                        <p className="text-slate-300">{toobitData.trades}</p>
                      </div>
                    </div>
                  </div>
                  <div className="bg-slate-800/50 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm">Pionex XRP</span>
                      <span className="text-xs text-emerald-400">● Running</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-slate-500">Balance</span>
                        <p className="text-slate-300">{pionexData.balance.toFixed(2)} XRP</p>
                      </div>
                      <div>
                        <span className="text-slate-500">Trades</span>
                        <p className="text-slate-300">{pionexData.trades}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Quick Links */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <h3 className="font-semibold mb-4">Quick Links</h3>
                <div className="space-y-2">
                  <Link href="/trading" className="flex items-center gap-3 p-2 hover:bg-slate-800 rounded-lg">
                    <DollarSign className="w-4 h-4 text-cyan-400" />
                    <span className="text-sm">Trading Dashboard</span>
                  </Link>
                  <Link href="/hardware/gpu" className="flex items-center gap-3 p-2 hover:bg-slate-800 rounded-lg">
                    <Zap className="w-4 h-4 text-cyan-400" />
                    <span className="text-sm">GPU Status</span>
                  </Link>
                  <Link href="/llm/status" className="flex items-center gap-3 p-2 hover:bg-slate-800 rounded-lg">
                    <Terminal className="w-4 h-4 text-cyan-400" />
                    <span className="text-sm">LLM Models</span>
                  </Link>
                  <Link href="/agents" className="flex items-center gap-3 p-2 hover:bg-slate-800 rounded-lg">
                    <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                    <span className="text-sm">Agent Tasks</span>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
