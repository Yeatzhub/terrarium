import { Play, Pause, AlertCircle, TrendingUp } from 'lucide-react'

interface Bot {
  name: string
  type: 'jupiter' | 'polymarket'
  status: 'running' | 'stopped' | 'error'
  lastTrade?: string
  pnl24h?: string
}

const bots: Bot[] = [
  { name: 'Jupiter Momentum', type: 'jupiter', status: 'running', lastTrade: '2 min ago', pnl24h: '+$12.40' },
  { name: 'Polymarket Scanner', type: 'polymarket', status: 'running', lastTrade: '5 min ago', pnl24h: '+$3.20' }
]

const statusConfig = {
  running: { icon: Play, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  stopped: { icon: Pause, color: 'text-slate-400', bg: 'bg-slate-500/10' },
  error: { icon: AlertCircle, color: 'text-rose-400', bg: 'bg-rose-500/10' }
}

const typeLabels = {
  jupiter: 'Jupiter',
  polymarket: 'Polymarket'
}

export default function BotStatus() {
  return (
    <div className="space-y-3">
      {bots.map((bot) => {
        const config = statusConfig[bot.status]
        const Icon = config.icon
        const isPositivePnl = bot.pnl24h?.startsWith('+')

        return (
          <div
            key={bot.name}
            className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-xl bg-slate-800 p-4 shadow-lg"
          >
            <div className="flex items-center gap-4">
              <div className={`rounded-lg p-2 ${config.bg}`}>
                <Icon className={`h-5 w-5 ${config.color}`} />
              </div>
              <div>
                <h3 className="font-semibold text-white">{bot.name}</h3>
                <p className="text-xs text-slate-400">{typeLabels[bot.type]}</p>
              </div>
            </div>

            <div className="flex items-center gap-6 sm:gap-8">
              {bot.lastTrade && (
                <div className="text-right">
                  <p className="text-xs text-slate-500">Last Trade</p>
                  <p className="text-sm text-slate-300">{bot.lastTrade}</p>
                </div>
              )}
              {bot.pnl24h && (
                <div className="text-right">
                  <p className="text-xs text-slate-500">24h P&L</p>
                  <p className={`text-sm font-medium flex items-center gap-1 ${isPositivePnl ? 'text-emerald-400' : 'text-rose-400'}`}>
                    <TrendingUp className="h-3 w-3" />
                    {bot.pnl24h}
                  </p>
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
