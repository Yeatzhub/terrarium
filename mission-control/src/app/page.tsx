import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-900 text-white p-8">
      <h1 className="text-4xl font-bold mb-8 text-center bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
        Mission Control
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
        {/* Hardware Status */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span>🖥️</span> Hardware Deliveries
          </h2>
          <div className="space-y-4">
            {/* P40 GPU with Tracking */}
            <div className="border-l-4 border-green-500 pl-3 bg-slate-700/50 py-2 px-3 rounded-r-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-green-400">Tesla P40 GPU</p>
                  <p className="text-sm text-slate-400">Tracking: 9405508106245831259625</p>
                </div>
                <span className="text-sm font-medium text-green-400">shipped</span>
              </div>
              <a 
                href="https://tools.usps.com/go/TrackConfirmAction?tLabels=9405508106245831259625"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-block mt-2 text-sm text-blue-400 hover:text-blue-300 transition-colors"
              >
                Track on USPS →
              </a>
            </div>
            
            {/* Other Items */}
            <div className="border-l-4 border-green-500 pl-3 bg-slate-700/50 py-2 px-3 rounded-r-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-green-400">Noctua Fan + PCIe Riser</p>
                  <p className="text-sm text-slate-400">Arrived: Feb 16</p>
                </div>
                <span className="text-sm font-medium text-green-400">delivered</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">WD Red 8TB (x2)</p>
                <p className="text-sm text-slate-400">ETA: Soon</p>
              </div>
              <span className="text-sm font-medium text-yellow-400">ordered</span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">i7-7700K CPU</p>
                <p className="text-sm text-slate-400">ETA: Soon</p>
              </div>
              <span className="text-sm font-medium text-yellow-400">ordered</span>
            </div>
          </div>
        </div>

        {/* Revenue Projects */}
        <DashboardCard 
          title="Revenue Projects"
          icon="💰"
          items={[
            { label: 'eBay Sales (Phase 1)', status: 'in-progress', detail: 'Quick cash - list items' },
            { label: 'BTC Trading Bot', status: 'in-progress', detail: 'Phase 2 - Scaffold ready' },
            { label: 'Android App', status: 'planning', detail: 'Phase 3 - 2-6 months' },
          ]}
        />

        {/* Hardware Projects */}
        <DashboardCard 
          title="Hardware Projects"
          icon="🚀"
          items={[
            { label: 'OpenClaw Setup', status: 'complete', detail: 'Optimized' },
            { label: 'Tesla P40 GPU Install', status: 'in-progress', detail: 'Fan & riser delivered' },
            { label: 'NAS Storage', status: 'pending', detail: 'Awaiting drives' },
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
            <StatRow label="Git Commits" value="5" />
          </div>
        </div>

        {/* Running Services */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 md:col-span-2">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span>🟢</span> Running Services
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Mission Control */}
            <div className="bg-slate-700 rounded-lg p-4 border border-slate-600">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                <span className="font-medium">Mission Control</span>
              </div>
              <p className="text-sm text-slate-400 mb-2">Port 3000</p>
              <code className="text-xs bg-slate-800 px-2 py-1 rounded">http://localhost:3000</code>
            </div>
            
            {/* SearXNG */}
            <div className="bg-slate-700 rounded-lg p-4 border border-slate-600">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                <span className="font-medium">SearXNG</span>
              </div>
              <p className="text-sm text-slate-400 mb-2">Port 8080</p>
              <code className="text-xs bg-slate-800 px-2 py-1 rounded">http://localhost:8080</code>
            </div>
            
            {/* OpenClaw */}
            <div className="bg-slate-700 rounded-lg p-4 border border-slate-600">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                <span className="font-medium">OpenClaw</span>
              </div>
              <p className="text-sm text-slate-400 mb-2">Port 18789</p>
              <code className="text-xs bg-slate-800 px-2 py-1 rounded">http://127.0.0.1:18789</code>
            </div>
          </div>
          
          {/* Tailscale Info */}
          <div className="mt-4 p-4 bg-blue-900/30 border border-blue-700 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <span>🔒</span>
              <span className="font-semibold text-blue-300">Tailscale Access</span>
            </div>
            <p className="text-sm text-slate-300 mb-2">
              Access securely from anywhere on your tailnet:
            </p>
            <code className="text-sm bg-slate-800 px-3 py-2 rounded block mb-2">
              http://100.125.198.70:3000 (Mission Control)<br/>
              http://100.125.198.70:8080 (SearXNG)
            </code>
            <p className="text-xs text-slate-400">
              This machine (ai-server) • Connected • 100.125.198.70
            </p>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 md:col-span-2">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span>📝</span> Recent Activity
          </h2>
          <div className="space-y-2 text-sm">
            <ActivityItem time="Today" text="BTC trading bot scaffold complete" />
            <ActivityItem time="Today" text="Fan and PCIe adapter delivered" />
            <ActivityItem time="Today" text="Phase 1 revenue plan: eBay sales" />
            <ActivityItem time="Today" text="Phases 2-3: BTC bot & Android app" />
            <ActivityItem time="Today" text="P40 GPU shipped! Tracking: 9405508106245831259625" />
            <ActivityItem time="Today" text="Created Mission Control dashboard" />
            <ActivityItem time="Today" text="Optimized context files (50% reduction)" />
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
              href="/tasks" 
              className="block w-full text-left px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg transition-colors"
            >
              💰 Phase 1: eBay Tasks →
            </a>
            <a 
              href="http://127.0.0.1:18789" 
              target="_blank" 
              rel="noopener noreferrer"
              className="block w-full text-left px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors"
            >
              OpenClaw Dashboard →
            </a>
            <a 
              href="http://100.125.198.70:8080"
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full text-left px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg transition-colors"
            >
              SearXNG (Tailscale) →
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