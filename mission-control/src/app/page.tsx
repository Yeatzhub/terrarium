'use client';

import { useState, useEffect } from 'react';
import StatCard from '../components/StatCard';
import StatusBadge from '../components/StatusBadge';
import AgentStatus from '../components/AgentStatus';
import BotStatus from '../components/BotStatus';
import Sidebar from '../components/Sidebar';
import { Menu, X, Wifi, WifiOff } from 'lucide-react';

interface ActivityItem {
  id: string;
  timestamp: Date;
  type: 'trade' | 'alert' | 'system' | 'error';
  message: string;
  details?: string;
}

const mockActivities: ActivityItem[] = [
  { id: '1', timestamp: new Date(Date.now() - 5 * 60000), type: 'trade', message: 'Long position opened', details: 'BTC-PERP @ $52,350' },
  { id: '2', timestamp: new Date(Date.now() - 12 * 60000), type: 'alert', message: 'Stop loss triggered', details: 'ETH-PERP @ $3,125' },
  { id: '3', timestamp: new Date(Date.now() - 28 * 60000), type: 'system', message: 'Agent reconnected', details: 'Trading agent active' },
  { id: '4', timestamp: new Date(Date.now() - 45 * 60000), type: 'trade', message: 'Position closed', details: 'SOL-PERP +$234 P&L' },
  { id: '5', timestamp: new Date(Date.now() - 62 * 60000), type: 'alert', message: 'Take profit hit', details: 'AVAX-PERP @ $28.50' },
  { id: '6', timestamp: new Date(Date.now() - 78 * 60000), type: 'system', message: 'Portfolio rebalanced', details: 'Risk adjustment applied' },
  { id: '7', timestamp: new Date(Date.now() - 95 * 60000), type: 'trade', message: 'Short position opened', details: 'ETH-PERP @ $3,200' },
  { id: '8', timestamp: new Date(Date.now() - 110 * 60000), type: 'error', message: 'API rate limit hit', details: 'Retrying in 60s' },
  { id: '9', timestamp: new Date(Date.now() - 135 * 60000), type: 'trade', message: 'Long position opened', details: 'LINK-PERP @ $15.75' },
  { id: '10', timestamp: new Date(Date.now() - 150 * 60000), type: 'system', message: 'Daily report generated', details: 'P&L: +$1,234' },
];

export default function MissionControl() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isConnected, setIsConnected] = useState(true);

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true,
    });
  };

  const formatRelativeTime = (date: Date) => {
    const diffMs = Date.now() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    return `${Math.floor(diffMins / 60)}h ago`;
  };

  const getActivityIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'trade': return '💰';
      case 'alert': return '🔔';
      case 'system': return '⚙️';
      case 'error': return '❌';
      default: return '📋';
    }
  };

  const getActivityColor = (type: ActivityItem['type']) => {
    switch (type) {
      case 'trade': return 'text-emerald-400';
      case 'alert': return 'text-amber-400';
      case 'system': return 'text-blue-400';
      case 'error': return 'text-red-400';
      default: return 'text-slate-400';
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-14 bg-slate-900 border-b border-slate-800 flex items-center justify-between px-4 z-50">
        <button
          onClick={() => setIsMobileMenuOpen(true)}
          className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
        >
          <Menu className="w-5 h-5" />
        </button>
        <span className="font-semibold">Mission Control</span>
        <div className="w-9" />
      </div>

      {/* Mobile Menu Overlay */}
      {isMobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 bg-black/50 z-50" onClick={() => setIsMobileMenuOpen(false)}>
          <div className="absolute top-0 left-0 bottom-0 w-64 bg-slate-900 border-r border-slate-800" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <span className="font-bold text-lg">Menu</span>
              <button onClick={() => setIsMobileMenuOpen(false)} className="p-2 hover:bg-slate-800 rounded-lg">
                <X className="w-5 h-5" />
              </button>
            </div>
            <nav className="p-4 space-y-1">
              {['Dashboard', 'Agents', 'Bots', 'Trades', 'Settings'].map((item) => (
                <a
                  key={item}
                  href="#"
                  className="block px-3 py-2 rounded-lg hover:bg-slate-800 transition-colors"
                >
                  {item}
                </a>
              ))}
            </nav>
          </div>
        </div>
      )}

      {/* Sidebar (Desktop) */}
      <Sidebar />

      {/* Main Content */}
      <div className="lg:ml-64 lg:pt-0 pt-14">
        {/* Header */}
        <header className="h-16 bg-slate-900/80 backdrop-blur border-b border-slate-800 flex items-center justify-between px-6 sticky top-0 z-40">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              Mission Control
            </h1>
          </div>
          <div className="flex items-center gap-4">
            {/* Connection Status */}
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
            {/* Time */}
            <div className="text-sm text-slate-400 font-mono">
              {formatTime(currentTime)}
            </div>
          </div>
        </header>

        {/* Content */}
        <main className="p-6 space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard
              title="Portfolio Value"
              value="$124,567.89"
              change="+$3,456.78 (+2.85%)"
              changeUp={true}
              icon={Wifi}
            />
            <StatCard
              title="24h P&L"
              value="+$1,234.56"
              change="+$456.78 (+0.58%)"
              changeUp={true}
              icon={Wifi}
            />
            <StatCard
              title="Open Positions"
              value="12"
              change="+2 today"
              changeUp={true}
              icon={Wifi}
            />
            <StatCard
              title="Win Rate"
              value="67.8%"
              change="+1.2% vs last week"
              changeUp={true}
              icon={Wifi}
            />
          </div>

          {/* Status Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <BotStatus />
            <AgentStatus />
          </div>

          {/* Activity Feed */}
          <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
              <h2 className="text-lg font-semibold">Activity Feed</h2>
              <span className="text-xs text-slate-500">Last 10 events</span>
            </div>
            <div className="divide-y divide-slate-800/50">
              {mockActivities.map((activity) => (
                <div
                  key={activity.id}
                  className="px-6 py-3 flex items-start gap-3 hover:bg-slate-800/30 transition-colors group"
                >
                  <span className="text-lg mt-0.5">{getActivityIcon(activity.type)}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className={`text-sm font-medium ${getActivityColor(activity.type)}`}>
                        {activity.message}
                      </p>
                      <span className="text-xs text-slate-500">{formatRelativeTime(activity.timestamp)}</span>
                    </div>
                    {activity.details && (
                      <p className="text-xs text-slate-400 mt-0.5">{activity.details}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
