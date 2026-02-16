export default function TasksPage() {
  const tasks = [
    { id: 1, title: 'Setup cron for memory cleanup', priority: 'high', status: 'pending' },
    { id: 2, title: 'Install Tesla P40 GPU', priority: 'high', status: 'waiting' },
    { id: 3, title: 'Install Noctua fan on P40 shroud', priority: 'high', status: 'waiting' },
    { id: 4, title: 'Setup PCIe riser cable', priority: 'high', status: 'waiting' },
    { id: 5, title: 'Build/buy GPU test bench frame', priority: 'high', status: 'waiting' },
    { id: 6, title: 'Install i7-7700K CPU', priority: 'medium', status: 'waiting' },
    { id: 7, title: 'Setup NAS with WD Red drives', priority: 'medium', status: 'waiting' },
    { id: 8, title: 'Install Docker', priority: 'medium', status: 'pending' },
    { id: 9, title: 'Setup SearXNG', priority: 'low', status: 'pending' },
    { id: 10, title: 'Install BTC bot dependencies (ccxt, pandas, numpy)', priority: 'medium', status: 'pending' },
    { id: 11, title: 'Test phi4 vs cloud API', priority: 'medium', status: 'pending' },
    { id: 12, title: 'Sell i5-6600K', priority: 'low', status: 'in-progress' },
    { id: 13, title: 'Configure xrdp remote desktop', priority: 'low', status: 'complete' },
  ]

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
        
        <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
          <div className="grid grid-cols-12 gap-4 p-4 bg-slate-700 font-semibold text-sm">
            <div className="col-span-1">Status</div>
            <div className="col-span-6">Task</div>
            <div className="col-span-2">Priority</div>
            <div className="col-span-3">Actions</div>
          </div>
          
          {tasks.map((task) => (
            <div key={task.id} className="grid grid-cols-12 gap-4 p-4 border-t border-slate-700 hover:bg-slate-750 transition-colors items-center">
              <div className="col-span-1 text-xl">{getStatusIcon(task.status)}</div>
              <div className="col-span-6">
                <p className={task.status === 'complete' ? 'line-through text-slate-500' : ''}>
                  {task.title}
                </p>
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
          ))}
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