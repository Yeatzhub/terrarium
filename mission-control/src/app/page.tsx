import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-900 text-white p-8">
      <h1 className="text-4xl font-bold mb-8 text-center bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
        Mission Control
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
        {/* Hardware Status */}
        <DashboardCard 
          title="Hardware Deliveries"
          icon="🖥️"
          items={[
            { label: 'Tesla P40 GPU', status: 'ordered', eta: 'This week' },
            { label: 'WD Red 8TB (x2)', status: 'ordered', eta: 'Soon' },
            { label: 'i7-7700K CPU', status: 'ordered', eta: 'Soon' },
            { label: 'Noctua Fan + Riser', status: 'ordered', eta: 'Soon' },
          ]}
        />

        {/* Projects */}
        <DashboardCard 
          title="Active Projects"
          icon="🚀"
          items={[
            { label: 'OpenClaw Setup', status: 'complete', detail: 'Optimized' },
            { label: 'NAS Storage', status: 'pending', detail: 'Awaiting drives' },
            { label: 'BTC Trading Bot', status: 'pending', detail: 'Needs deps' },
            { label: 'Mission Control', status: 'in-progress', detail: 'Building now' },
          ]}
        />

        {/* Quick Stats */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span>📊</span> System Stats
          </h2>
          <div className="space-y-3">
            <StatRow label="Context Lines" value="192" />
            <StatRow label="Token Savings" value="~50%" />
            <StatRow label="Memory Files" value="2" />
            <StatRow label="Git Commits" value="1" />
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 md:col-span-2">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span>📝</span> Recent Activity
          </h2>
          <div className="space-y-2 text-sm">
            <ActivityItem time="Today" text="Created Mission Control dashboard" />
            <ActivityItem time="Today" text="Optimized context files (50% reduction)" />
            <ActivityItem time="Today" text="Ordered P40 GPU + accessories" />
            <ActivityItem time="Today" text="Set up token efficiency automation" />
            <ActivityItem time="Feb 13" text="Paired Telegram bot @zorinclawbot" />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span>⚡</span> Quick Actions
          </h2>
          <div className="space-y-2">
            <QuickAction href="/tasks" label="View Tasks" />
            <QuickAction href="/notes" label="Quick Notes" />
            <a 
              href="http://127.0.0.1:18789" 
              target="_blank" 
              rel="noopener noreferrer"
              className="block w-full text-left px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
            >
              OpenClaw Dashboard →
            </a>
          </div>
        </div>
      </div>

      <footer className="mt-12 text-center text-slate-500 text-sm">
        Mission Control v1.0 • Built with Next.js
      </footer>
    </main>
  )
}

function DashboardCard({ title, icon, items }: { title: string, icon: string, items: Array<{label: string, status: string, eta?: string, detail?: string}> }) {
  const getStatusColor = (status: string) => {
    switch(status) {
      case 'complete': return 'text-green-400'
      case 'in-progress': return 'text-blue-400'
      case 'ordered': return 'text-yellow-400'
      default: return 'text-slate-400'
    }
  }

  return (
    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <span>{icon}</span> {title}
      </h2>
      <div className="space-y-3">
        {items.map((item, i) => (
          <div key={i} className="flex items-center justify-between">
            <div>
              <p className="font-medium">{item.label}</p>
              {item.detail && <p className="text-sm text-slate-400">{item.detail}</p>}
              {item.eta && <p className="text-sm text-slate-400">ETA: {item.eta}</p>}
            </div>
            <span className={`text-sm font-medium ${getStatusColor(item.status)}`}>
              {item.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

function StatRow({ label, value }: { label: string, value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-slate-400">{label}</span>
      <span className="font-mono font-medium">{value}</span>
    </div>
  )
}

function ActivityItem({ time, text }: { time: string, text: string }) {
  return (
    <div className="flex gap-4 items-start">
      <span className="text-slate-500 text-xs whitespace-nowrap w-16">{time}</span>
      <span className="text-slate-300">{text}</span>
    </div>
  )
}

function QuickAction({ href, label }: { href: string, label: string }) {
  return (
    <Link 
      href={href}
      className="block w-full text-left px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors"
    >
      {label} →
    </Link>
  )
}