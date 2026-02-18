import { LucideIcon } from 'lucide-react'

interface StatCardProps {
  title: string
  value: string
  change?: string
  changeUp?: boolean
  icon: LucideIcon
}

export default function StatCard({ title, value, change, changeUp, icon: Icon }: StatCardProps) {
  return (
    <div className="relative overflow-hidden rounded-xl bg-gradient-to-br from-slate-800 to-slate-900 p-6 shadow-lg">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-slate-400">{title}</p>
          <p className="mt-2 text-3xl font-bold text-white">{value}</p>
          {change && (
            <p className={`mt-1 text-sm font-medium ${changeUp ? 'text-emerald-400' : 'text-rose-400'}`}>
              {changeUp ? '↑' : '↓'} {change}
            </p>
          )}
        </div>
        <div className="rounded-lg bg-slate-700/50 p-3">
          <Icon className="h-6 w-6 text-slate-300" />
        </div>
      </div>
    </div>
  )
}
