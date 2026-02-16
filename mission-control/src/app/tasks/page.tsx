'use client'

import { useState } from 'react'

export default function TasksPage() {
  const [showCompleted, setShowCompleted] = useState(true)

  const tasks = [
    // Phase 1: Quick Cash (eBay)
    { id: 1, title: 'Phase 1: Take photos of items for eBay', priority: 'high', status: 'pending' },
    { id: 2, title: 'Phase 1: List 3-5 items on eBay', priority: 'high', status: 'pending' },
    { id: 3, title: 'Phase 1: Research market prices for items', priority: 'medium', status: 'pending' },
    
    // Phase 2: BTC Trading Bot
    { id: 4, title: 'Phase 2: Check Binance.US API access', priority: 'medium', status: 'pending' },
    { id: 5, title: 'Phase 2: Design bot architecture on paper', priority: 'medium', status: 'complete' },
    { id: 6, title: 'Phase 2: Scaffold Python trading bot project', priority: 'medium', status: 'complete' },
    { id: 49, title: 'Phase 2: Switch to Kraken exchange (Binance blocked)', priority: 'medium', status: 'complete' },
    { id: 7, title: 'Phase 2: Paper trade bot for 2 weeks', priority: 'medium', status: 'pending' },
    
    // Phase 3: Android App
    { id: 8, title: 'Phase 3: Validate app idea (problem to solve)', priority: 'low', status: 'pending' },
    { id: 9, title: 'Phase 3: Create app wireframes', priority: 'low', status: 'pending' },
    
    // Hardware Tasks
    { id: 10, title: 'Install Tesla P40 GPU', priority: 'high', status: 'waiting' },
    { id: 11, title: 'Install Noctua fan on P40 shroud', priority: 'high', status: 'waiting' },
    { id: 12, title: 'Setup PCIe riser cable', priority: 'high', status: 'waiting' },
    { id: 13, title: 'Build/buy GPU test bench frame', priority: 'high', status: 'waiting' },
    { id: 14, title: 'Install i7-7700K CPU', priority: 'medium', status: 'waiting' },
    { id: 15, title: 'Setup NAS with WD Red drives', priority: 'medium', status: 'waiting' },
    
    // Completed Tasks
    { id: 50, title: 'Setup cron for memory cleanup', priority: 'high', status: 'complete' },
    { id: 51, title: 'Fan and PCIe adapter delivered', priority: 'high', status: 'complete' },
    { id: 52, title: 'BTC bot scaffold with RSI strategy', priority: 'medium', status: 'complete' },
    { id: 52, title: 'Phase 1 revenue plan established', priority: 'high', status: 'complete' },
    { id: 53, title: 'Install Docker', priority: 'medium', status: 'complete' },
    { id: 54, title: 'Setup SearXNG', priority: 'low', status: 'complete' },
    { id: 55, title: 'Install BTC bot dependencies (ccxt, pandas, numpy)', priority: 'medium', status: 'complete' },
    { id: 56, title: 'Configure xrdp remote desktop', priority: 'low', status: 'complete' },
    { id: 57, title: 'Configure Tailscale', priority: 'medium', status: 'complete' },
    { id: 58, title: 'Sell i5-6600K (moved to Phase 1)', priority: 'low', status: 'complete' },
  ]

  const activeTasks = tasks.filter(t => t.status !== 'complete')
  const completedTasks = tasks.filter(t => t.status === 'complete')

  const getPriorityColor = (p: string) => {
    switch(p) {
      case 'high': return 'text-red-400 bg-red-400/20'
      case 'medium': return 'text-yellow-400 bg-yellow-400/20'
      default: return 'text-blue-400 bg-blue-400/20'
    }
  }

  const getStatusIcon = (s: string) => {
    switch(s) {
      case 'complete': return '✅'
      case 'in-progress': return '🔄'
      case 'waiting': return '⏳'
      default: return '⭕'
    }
  }

  return (
    <main className="min-h-screen bg-slate-900 text-white p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Task Manager</h1>
        
        {/* Stats Summary */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <p className="text-3xl font-bold text-blue-400">{activeTasks.length}</p>
            <p className="text-sm text-slate-400">Active Tasks</p>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <p className="text-3xl font-bold text-green-400">{completedTasks.length}</p>
            <p className="text-sm text-slate-400">Completed</p>
          </div>
          <div className="bg-slate-800 rounded-lg p-4 border border-slate-700 text-center">
            <p className="text-3xl font-bold text-yellow-400">
              {Math.round((completedTasks.length / tasks.length) * 100)}%
            </p>
            <p className="text-sm text-slate-400">Progress</p>
          </div>
        </div>

        {/* Active Tasks */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden mb-6">
          <div className="p-4 bg-slate-700 border-b border-slate-600">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <span>📋</span> Active Tasks ({activeTasks.length})
            </h2>
          </div>
          
          <div className="grid grid-cols-12 gap-4 p-4 bg-slate-700 font-semibold text-sm border-b border-slate-600">
            <div className="col-span-1">Status</div>
            <div className="col-span-6">Task</div>
            <div className="col-span-2">Priority</div>
            <div className="col-span-3">Actions</div>
          </div>
          
          {activeTasks.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              No active tasks! 🎉
            </div>
          ) : (
            activeTasks.map((task) => (
              <div key={task.id} className="grid grid-cols-12 gap-4 p-4 border-t border-slate-700 hover:bg-slate-750 transition-colors items-center">
                <div className="col-span-1 text-xl">{getStatusIcon(task.status)}</div>
                <div className="col-span-6">
                  <p className="font-medium">{task.title}</p>
                </div>
                <div className="col-span-2">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getPriorityColor(task.priority)}`}>
                    {task.priority}
                  </span>
                </div>
                <div className="col-span-3 flex gap-2">
                  <button className="px-3 py-1 bg-blue-600 hover:bg-blue-500 rounded text-sm transition-colors">
                    Edit
                  </button>
                  <button className="px-3 py-1 bg-green-600 hover:bg-green-500 rounded text-sm transition-colors">
                    Done
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Completed Tasks */}
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <button 
            onClick={() => setShowCompleted(!showCompleted)}
            className="w-full p-4 bg-slate-700 border-b border-slate-600 flex items-center justify-between hover:bg-slate-650 transition-colors"
          >
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <span>✅</span> Completed Tasks ({completedTasks.length})
            </h2>
            <span className="text-slate-400">
              {showCompleted ? '▼' : '▶'}
            </span>
          </button>
          
          {showCompleted && (
            <>
              <div className="grid grid-cols-12 gap-4 p-4 bg-slate-700/50 font-semibold text-sm border-b border-slate-600 text-slate-400">
                <div className="col-span-1">Status</div>
                <div className="col-span-9">Task</div>
                <div className="col-span-2">Priority</div>
              </div>
              
              {completedTasks.map((task) => (
                <div key={task.id} className="grid grid-cols-12 gap-4 p-4 border-t border-slate-700 bg-slate-800/50">
                  <div className="col-span-1 text-xl">{getStatusIcon(task.status)}</div>
                  <div className="col-span-9">
                    <p className="line-through text-slate-500">{task.title}</p>
                  </div>
                  <div className="col-span-2">
                    <span className={`px-2 py-1 rounded text-xs font-medium opacity-50 ${getPriorityColor(task.priority)}`}>
                      {task.priority}
                    </span>
                  </div>
                </div>
              ))}
            </>
          )}
        </div>

        <div className="mt-6 flex gap-4">
          <button className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors">
            + New Task
          </button>
          <a 
            href="/"
            className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
          >
            ← Back to Dashboard
          </a>
        </div>
      </div>
    </main>
  )
}