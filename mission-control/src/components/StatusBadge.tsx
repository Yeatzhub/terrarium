interface StatusBadgeProps {
  status: 'online' | 'offline' | 'running' | 'error' | 'warning'
  text: string
}

export default function StatusBadge({ status, text }: StatusBadgeProps) {
  const statusColors = {
    online: 'bg-emerald-500',
    running: 'bg-emerald-500',
    error: 'bg-rose-500',
    warning: 'bg-amber-500',
    offline: 'bg-slate-500'
  }

  const bgColors = {
    online: 'bg-emerald-500/10 text-emerald-400',
    running: 'bg-emerald-500/10 text-emerald-400',
    error: 'bg-rose-500/10 text-rose-400',
    warning: 'bg-amber-500/10 text-amber-400',
    offline: 'bg-slate-500/10 text-slate-400'
  }

  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-sm font-medium ${bgColors[status]}`}>
      <span className={`h-2 w-2 rounded-full ${statusColors[status]}`} />
      {text}
    </span>
  )
}
