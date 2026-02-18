interface Agent {
  name: string
  emoji: string
  status: 'idle' | 'busy' | 'offline'
  currentTask?: string
}

const agents: Agent[] = [
  { name: 'Ghost', emoji: '👻', status: 'idle' },
  { name: 'Oracle', emoji: '🔮', status: 'idle' },
  { name: 'Pixel', emoji: '🎨', status: 'busy', currentTask: 'Dashboard redesign' },
  { name: 'Synthesis', emoji: '🔗', status: 'idle' }
]

const statusColors = {
  idle: 'bg-emerald-500',
  busy: 'bg-amber-500',
  offline: 'bg-slate-500'
}

const statusText = {
  idle: 'Idle',
  busy: 'Busy',
  offline: 'Offline'
}

export default function AgentStatus() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {agents.map((agent) => (
        <div
          key={agent.name}
          className="relative rounded-xl bg-slate-800 p-4 shadow-lg transition-all hover:bg-slate-750"
        >
          <div className="flex items-center gap-3">
            <span className="text-2xl">{agent.emoji}</span>
            <div className="flex-1 min-w-0">
              <h3 className="font-semibold text-white truncate">{agent.name}</h3>
              <div className="flex items-center gap-2 mt-1">
                <span className={`h-2 w-2 rounded-full ${statusColors[agent.status]}`} />
                <span className="text-xs text-slate-400">{statusText[agent.status]}</span>
              </div>
            </div>
          </div>
          {agent.currentTask && (
            <p className="mt-3 text-xs text-slate-400 truncate border-t border-slate-700 pt-2">
              {agent.currentTask}
            </p>
          )}
        </div>
      ))}
    </div>
  )
}
