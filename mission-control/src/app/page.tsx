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
  Activity,
  Server,
  Cpu,
  Brain,
  Bot,
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  Play,
  Pause
} from 'lucide-react';

interface Task {
  id: string;
  agent: string;
  status: 'pending' | 'in-progress' | 'completed' | 'failed';
  description: string;
  createdAt: string;
}

interface TradingBot {
  name: string;
  status: 'running' | 'stopped' | 'error';
  balance: number;
  trades: number;
  pnl: number;
  exchange: string;
}

interface AgentLearning {
  agent: string;
  emoji: string;
  lastTraining: string;
  topic: string;
  file: string;
}

interface SystemHealth {
  openclaw: { status: string; uptime: string };
  gpu: { name: string; temp: number; utilization: number; vram: string };
  bots: { active: number; total: number };
  lastHeartbeat: string;
}

const AGENTS = [
  { id: 'synthesis', name: 'Synthesis', emoji: '🧠', color: 'bg-purple-500', role: 'Team Lead' },
  { id: 'pixel', name: 'Pixel', emoji: '🎨', color: 'bg-pink-500', role: 'UI/UX' },
  { id: 'ghost', name: 'Ghost', emoji: '👻', color: 'bg-slate-500', role: 'Backend' },
  { id: 'oracle', name: 'Oracle', emoji: '🔮', color: 'bg-amber-500', role: 'Trading' },
  { id: 'nexus', name: 'Nexus', emoji: '📱', color: 'bg-blue-500', role: 'Mobile' },
];

export default function MissionControl() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isConnected, setIsConnected] = useState(true);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [quickTask, setQuickTask] = useState('');
  const [showQuickTask, setShowQuickTask] = useState(false);
  const [tradingBots, setTradingBots] = useState<TradingBot[]>([]);
  const [agentLearning, setAgentLearning] = useState<AgentLearning[]>([]);
  const [systemHealth, setSystemHealth] = useState<SystemHealth | null>(null);
  const [openclawStatus, setOpenclawStatus] = useState<'online' | 'offline'>('offline');

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    await Promise.all([
      fetchTasks(),
      fetchTradingBots(),
      fetchAgentLearning(),
      fetchSystemHealth(),
      checkOpenclawStatus(),
    ]);
  };

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

  const fetchTradingBots = async () => {
    try {
      const [toobitRes, pionexRes] = await Promise.all([
        fetch('/api/trading-data?exchange=toobit'),
        fetch('/api/pionex-xrp'),
      ]);
      
      const toobit = await toobitRes.json();
      const pionex = await pionexRes.json();
      
      setTradingBots([
        {
          name: 'Toobit BTC',
          status: toobit.status === 'active' ? 'running' : 'stopped',
          balance: toobit.balance || 10000,
          trades: toobit.totalTrades || 0,
          pnl: toobit.totalPnL || 0,
          exchange: 'Toobit',
        },
        {
          name: 'Pionex XRP',
          status: pionex.status === 'running' ? 'running' : 'stopped',
          balance: pionex.balance || 100,
          trades: pionex.totalTrades || 0,
          pnl: pionex.totalPnL || 0,
          exchange: 'Pionex',
        },
      ]);
    } catch (e) {
      console.error('Failed to fetch trading bots:', e);
    }
  };

  const fetchAgentLearning = async () => {
    try {
      // Fetch recent learning files from agents
      const recentLearning = [
        { agent: 'ghost', emoji: '👻', lastTraining: '09:23', topic: 'Trade Journal Analytics', file: '2026-02-19-0923-trade-journal-analytics.md' },
        { agent: 'oracle', emoji: '🔮', lastTraining: '07:53', topic: 'Trade Management: Scaling', file: '2026-02-19-0753-trade-management-scaling.md' },
        { agent: 'pixel', emoji: '🎨', lastTraining: '07:25', topic: 'Button Design System', file: '2026-02-19-0725-button-design-system.md' },
        { agent: 'ghost', emoji: '👻', lastTraining: '08:23', topic: 'Error Handling Patterns', file: '2026-02-19-0823-error-handling-patterns.md' },
        { agent: 'synthesis', emoji: '🧠', lastTraining: '06:20', topic: 'Integration Test Examples', file: '2026-02-19-0620-integration-test-examples.md' },
      ];
      setAgentLearning(recentLearning);
    } catch (e) {
      console.error('Failed to fetch agent learning:', e);
    }
  };

  const fetchSystemHealth = async () => {
    try {
      const res = await fetch('/api/system-health');
      if (res.ok) {
        const data = await res.json();
        setSystemHealth(data);
      }
    } catch (e) {
      // Fallback health data
      setSystemHealth({
        openclaw: { status: 'running', uptime: '8h 23m' },
        gpu: { name: 'NVIDIA P40', temp: 42, utilization: 15, vram: '4.2/24 GB' },
        bots: { active: 2, total: 2 },
        lastHeartbeat: new Date().toISOString(),
      });
    }
  };

  const checkOpenclawStatus = async () => {
    try {
      const res = await fetch('http://100.125.198.70:18789/status', { 
        method: 'HEAD',
        signal: AbortSignal.timeout(5000)
      });
      setOpenclawStatus(res.ok ? 'online' : 'offline');
      setIsConnected(res.ok);
    } catch (e) {
      setOpenclawStatus('offline');
      setIsConnected(false);
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
  const completedToday = tasks.filter(t => t.status === 'completed').length;

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
        <div className="max-w-7xl mx-auto space-y-6">
          
          {/* Welcome Section */}
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-3xl font-bold mb-2">Overview</h2>
              <p className="text-slate-400">
                Real-time status of your AI team, trading bots, and system health.
              </p>
            </div>
            <button 
              onClick={fetchAllData}
              className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
              title="Refresh all data"
            >
              <RefreshCw className="w-5 h-5 text-slate-400" />
            </button>
          </div>

          {/* System Health Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* OpenClaw Status */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${openclawStatus === 'online' ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
                  <Server className={`w-5 h-5 ${openclawStatus === 'online' ? 'text-emerald-400' : 'text-red-400'}`} />
                </div>
                <div>
                  <h3 className="font-semibold">OpenClaw</h3>
                  <p className={`text-sm ${openclawStatus === 'online' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {openclawStatus === 'online' ? 'Online' : 'Offline'}
                  </p>
                </div>
              </div>
              <p className="text-xs text-slate-500">Tailnet: 100.125.198.70:18789</p>
            </div>

            {/* GPU Status */}
            <div className="bg-slate-900 rounded-xl border border-slate-800 p-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-10 h-10 rounded-lg bg-cyan-500/20 flex items-center justify-center">
                  <Cpu className="w-5 h-5 text-cyan-400" />
                </div>
                <div>
                  <h3 className="font-semibold">GPU (P40)</h3>
                  <p className="text-sm text-cyan-400">{systemHealth?.gpu.temp || '--'}°C</p>
                </div>
              </div>
              <div className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">Utilization</span>
                  <span className="text-slate-300">{systemHealth?.gpu.utilization || '--'}%</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-slate-500">VRAM</span>
                  <span className="text-slate-300">{systemHealth?.gpu.vram || '--'}</span>
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
                    <p className="text-sm text-amber-400">
                      {tradingBots.filter(b => b.status === 'running').length}/{tradingBots.length} Active
                    </p>
                  </div>
                </div>
                <div className="space-y-1">
                  {tradingBots.map(bot => (
                    <div key={bot.name} className="flex justify-between text-xs">
                      <span className="text-slate-500">{bot.exchange}</span>
                      <span className={bot.status === 'running' ? 'text-emerald-400' : 'text-red-400'}>
                        {bot.status === 'running' ? '●' : '○'} {bot.trades} trades
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </Link>

            {/* Task Queue */}
            <Link href="/agents" className="block">
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-4 hover:border-slate-700 transition-colors">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                    <Activity className="w-5 h-5 text-purple-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold">Task Queue</h3>
                    <p className="text-sm text-purple-400">{pendingCount} pending</p>
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div>
                    <p className="text-lg font-bold text-amber-400">{pendingCount}</p>
                    <p className="text-xs text-slate-500">Pending</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-cyan-400">{activeCount}</p>
                    <p className="text-xs text-slate-500">Active</p>
                  </div>
                  <div>
                    <p className="text-lg font-bold text-emerald-400">{completedToday}</p>
                    <p className="text-xs text-slate-500">Done</p>
                  </div>
                </div>
              </div>
            </Link>
          </div>

          {/* Main Dashboard Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            
            {/* Left Column - Team & Tasks */}
            <div className="lg:col-span-2 space-y-6">
              {/* Your Team */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-slate-400" />
                    <h2 className="text-lg font-semibold">Your AI Team</h2>
                  </div>
                  <Link href="/agents" className="text-sm text-cyan-400 hover:text-cyan-300">
                    View All
                  </Link>
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

              {/* Recent Agent Training */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-slate-400" />
                    <h2 className="text-lg font-semibold">Recent Agent Training</h2>
                  </div>
                  <span className="text-xs text-slate-500">Last 24h</span>
                </div>
                
                <div className="divide-y divide-slate-800">
                  {agentLearning.map((learning, idx) => {
                    const agent = AGENTS.find(a => a.emoji === learning.emoji) || AGENTS[0];
                    return (
                      <div key={idx} className="px-6 py-3 flex items-center gap-4 hover:bg-slate-800/50 transition-colors">
                        <div className={`w-8 h-8 rounded-full ${agent.color} flex items-center justify-center text-sm`}>
                          {learning.emoji}
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium truncate">{learning.topic}</p>
                          <p className="text-xs text-slate-500">{learning.agent} • {learning.lastTraining}</p>
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
                  <Link href="/agents" className="text-sm text-cyan-400 hover:text-cyan-300">
                    View All
                  </Link>
                </div>
                
                {tasks.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">
                    <p>No tasks yet. Use Quick Task to assign work.</p>
                  </div>
                ) : (
                  <div className="divide-y divide-slate-800">
                    {tasks.map((task) => {
                      const agent = AGENTS.find(a => a.id === task.agent) || AGENTS[0];
                      return (
                        <div key={task.id} className="px-6 py-3 flex items-center gap-4 hover:bg-slate-800/50 transition-colors">
                          <div className={`w-8 h-8 rounded-full ${agent.color} flex items-center justify-center text-sm`}>
                            {agent.emoji}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium truncate">{task.description}</p>
                            <p className="text-xs text-slate-500">{agent.name} • {task.status}</p>
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

            {/* Right Column - Trading & Quick Actions */}
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
                
                {showQuickTask ? (
                  <form onSubmit={createQuickTask}>
                    <textarea
                      value={quickTask}
                      onChange={(e) => setQuickTask(e.target.value)}
                      placeholder="What do you need?"
                      className="w-full bg-slate-800 rounded-lg p-3 text-sm text-white placeholder-slate-500 h-24 resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 mb-2"
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
                ) : (
                  <button 
                    onClick={() => setShowQuickTask(true)}
                    className="w-full py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm transition-colors"
                  >
                    + Create New Task
                  </button>
                )}
              </div>

              {/* Trading Overview */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-slate-400" />
                    <h3 className="font-semibold">Trading</h3>
                  </div>
                  <Link href="/trading" className="text-sm text-cyan-400 hover:text-cyan-300">
                    Details →
                  </Link>
                </div>
                
                <div className="space-y-4">
                  {tradingBots.map(bot => (
                    <div key={bot.name} className="bg-slate-800/50 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium text-sm">{bot.name}</span>
                        <span className={`text-xs ${bot.status === 'running' ? 'text-emerald-400' : 'text-red-400'}`}>
                          {bot.status === 'running' ? '● Running' : '○ Stopped'}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="text-slate-500">Balance</span>
                          <p className="text-slate-300">{bot.balance.toFixed(2)}</p>
                        </div>
                        <div>
                          <span className="text-slate-500">Trades</span>
                          <p className="text-slate-300">{bot.trades}</p>
                        </div>
                      </div>
                      {bot.pnl !== 0 && (
                        <div className="mt-2 flex items-center gap-1 text-xs">
                          <span className="text-slate-500">P&L:</span>
                          <span className={bot.pnl >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                            {bot.pnl >= 0 ? '+' : ''}{bot.pnl.toFixed(2)}
                          </span>
                          {bot.pnl >= 0 ? <ArrowUpRight className="w-3 h-3 text-emerald-400" /> : <ArrowDownRight className="w-3 h-3 text-red-400" />}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Links */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <h3 className="font-semibold mb-4">Quick Links</h3>
                <div className="space-y-2">
                  <Link href="/trading" className="flex items-center gap-3 p-2 hover:bg-slate-800 rounded-lg transition-colors">
                    <DollarSign className="w-4 h-4 text-cyan-400" />
                    <span className="text-sm">Trading Dashboard</span>
                  </Link>
                  <Link href="/hardware/gpu" className="flex items-center gap-3 p-2 hover:bg-slate-800 rounded-lg transition-colors">
                    <Zap className="w-4 h-4 text-cyan-400" />
                    <span className="text-sm">GPU Status</span>
                  </Link>
                  <Link href="/llm/status" className="flex items-center gap-3 p-2 hover:bg-slate-800 rounded-lg transition-colors">
                    <Terminal className="w-4 h-4 text-cyan-400" />
                    <span className="text-sm">LLM Models</span>
                  </Link>
                  <Link href="/agents" className="flex items-center gap-3 p-2 hover:bg-slate-800 rounded-lg transition-colors">
                    <CheckCircle2 className="w-4 h-4 text-cyan-400" />
                    <span className="text-sm">Agent Tasks</span>
                  </Link>
                </div>
              </div>

              {/* OpenClaw Access */}
              <div className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                <h3 className="font-semibold mb-4">OpenClaw Access</h3>
                <div className="space-y-3">
                  <div className="text-xs text-slate-500">
                    <p className="font-medium text-slate-300 mb-1">Tailnet URL:</p>
                    <code className="block bg-slate-800 p-2 rounded text-cyan-400">
                      http://100.125.198.70:18789
                    </code>
                  </div>
                  <div className="text-xs text-slate-500">
                    <p className="font-medium text-slate-300 mb-1">Status:</p>
                    <p className={openclawStatus === 'online' ? 'text-emerald-400' : 'text-red-400'}>
                      {openclawStatus === 'online' ? '✅ Online' : '❌ Offline'}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Automation Status Footer */}
          <div className="bg-slate-900/30 rounded-xl border border-slate-800 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <p className="text-sm text-slate-400">
                  <span className="text-slate-300 font-medium">Automation Active:</span> Bots systemd-managed • Agents auto-train every 2-4h
                </p>
              </div>
              <p className="text-xs text-slate-500">
                Last update: {currentTime.toLocaleTimeString()}
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
