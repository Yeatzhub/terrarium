import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-slate-900 text-white p-8">
      <h1 className="text-4xl font-bold mb-8 text-center bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
        Mission Control
      </h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
        {/* Quick Actions - NOW AT TOP */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 md:col-span-2 lg:col-span-3">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span>⚡</span> Quick Actions
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <QuickAction href="/tasks" label="📋 View Tasks" />
            <QuickAction href="/notes" label="📝 Quick Notes" />
            <a 
              href="/tasks"
              className="text-center px-4 py-3 bg-green-600 hover:bg-green-500 rounded-lg transition-colors font-medium"
            >
              💰 Phase 1: eBay Tasks
            </a>
            <a 
              href="http://127.0.0.1:18789"
              target="_blank"
              rel="noopener noreferrer"
              className="text-center px-4 py-3 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors font-medium"
            >
              🤖 OpenClaw Dashboard
            </a>
            <a 
              href="http://100.125.198.70:8080"
              target="_blank"
              rel="noopener noreferrer"
              className="text-center px-4 py-3 bg-purple-600 hover:bg-purple-500 rounded-lg transition-colors font-medium"
            >
              🔍 SearXNG Search
            </a>
            <a 
              href="https://www.kraken.com/u/trade"
              target="_blank"
              rel="noopener noreferrer"
              className="text-center px-4 py-3 bg-orange-600 hover:bg-orange-500 rounded-lg transition-colors font-medium"
            >
              📈 Kraken Trading
            </a>
            <a 
              href="https://www.tradingview.com/chart/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-center px-4 py-3 bg-cyan-600 hover:bg-cyan-500 rounded-lg transition-colors font-medium"
            >
              📊 TradingView Charts
            </a>
            <a 
              href="http://100.125.198.70:3000"
              target="_blank"
              rel="noopener noreferrer"
              className="text-center px-4 py-3 bg-slate-600 hover:bg-slate-500 rounded-lg transition-colors font-medium"
            >
              🌐 Tailscale Access
            </a>
          </div>
        </div>

        {/* Revenue Projects */}
        <DashboardCard 
          title="Revenue Projects"
          icon="💰"
          items={[
            { label: 'eBay Sales (Phase 1)', status: 'pending', detail: 'List items for quick capital' },
            { label: 'BTC Trading Bot (Phase 2)', status: 'in-progress', detail: 'Paper trading via TradingView webhooks' },
            { label: 'Polymarket Arbitrage', status: 'in-progress', detail: 'Scanner built, monitoring hourly' },
            { label: 'Android App (Phase 3)', status: 'planning', detail: '2-6 months out' },
          ]}
        />

        {/* Hardware Projects */}
        <DashboardCard 
          title="Hardware Projects"
          icon="🚀"
          items={[
            { label: 'Tesla P40 GPU Install', status: 'in-progress', detail: 'In transit - verify PSU wattage' },
            { label: 'TradingView Webhook Server', status: 'in-progress', detail: 'Flask on port 8081' },
            { label: 'NAS Storage', status: 'pending', detail: '2x WD Red 8TB drives pending' },
            { label: 'i7-7700K CPU Upgrade', status: 'pending', detail: 'Ordered' },
          ]}
        />

        {/* Hardware Deliveries */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span>🖥️</span> Hardware Deliveries
          </h2>
          <div className="space-y-4">
            {/* P40 GPU with Tracking */}
            <div className="border-l-4 border-yellow-500 pl-3 bg-slate-700/50 py-2 px-3 rounded-r-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-yellow-400">Tesla P40 GPU</p>
                  <p className="text-sm text-slate-400">Tracking: 9405508106245831259625</p>
                </div>
                <span className="text-sm font-medium text-yellow-400">in-transit</span>
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
            
            {/* Noctua Fan - DELIVERED */}
            <div className="border-l-4 border-green-500 pl-3 bg-slate-700/50 py-2 px-3 rounded-r-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-green-400">Noctua Fan + PCIe Riser</p>
                  <p className="text-sm text-slate-400">Arrived: Feb 16</p>
                </div>
                <span className="text-sm font-medium text-green-400">delivered</span>
              </div>
            </div>
            
            {/* WD Red Drives */}
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">WD Red 8TB (x2)</p>
                <p className="text-sm text-slate-400">Ordered</p>
              </div>
              <span className="text-sm font-medium text-yellow-400">pending</span>
            </div>
            
            {/* i7-7700K */}
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">i7-7700K CPU</p>
                <p className="text-sm text-slate-400">Ordered</p>
              </div>
              <span className="text-sm font-medium text-yellow-400">pending</span>
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span>📊</span> System Stats
          </h2>
          <div className="space-y-3">
            <StatRow label="BTC Price" value="$67,871" />
            <StatRow label="RSI" value="43.82" />
            <StatRow label="Memory Files" value="3" />
            <StatRow label="Git Commits" value="7" />
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
            
            {/* Trading Webhook */}
            <div className="bg-slate-700 rounded-lg p-4 border border-slate-600">
              <div className="flex items-center gap-2 mb-2">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                <span className="font-medium">Trading Webhook</span>
              </div>
              <p className="text-sm text-slate-400 mb-2">Port 8081</p>
              <code className="text-xs bg-slate-800 px-2 py-1 rounded">http://100.125.198.70:8081</code>
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
              http://100.125.198.70:3000<br/>
              http://100.125.198.70:8080
            </code>
            <p className="text-xs text-slate-400">
              This machine (ai-server) • Connected • 100.125.198.70
            </p>
          </div>
        </div>

        {/* Active Sub-Agents */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span>🤖</span> Active Agents
          </h2>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">BTC Webhook Deploy</p>
                <p className="text-sm text-slate-400">Flask + paper trading</p>
              </div>
              <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400">running</span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Polymarket Scanner</p>
                <p className="text-sm text-slate-400">Arbitrage detection</p>
              </div>
              <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400">running</span>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">eBay Phase 1</p>
                <p className="text-sm text-slate-400">Photo + listing prep</p>
              </div>
              <span className="text-xs px-2 py-1 rounded bg-blue-500/20 text-blue-400">running</span>
            </div>
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 md:col-span-2 lg:col-span-3">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <span>📝</span> Recent Activity
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
            <ActivityItem time="Today" text="Polymarket arbitrage scanner built and deployed" />
            <ActivityItem time="Today" text="P40 GPU delivery tracking verified - needs manual check" />
            <ActivityItem time="Today" text="Mission Control dashboard reorganized" />
            <ActivityItem time="Today" text="Trading bot webhook server status check" />
            <ActivityItem time="Today" text="3 active sub-agents deployed for trading operations" />
            <ActivityItem time="Today" text="User mandate: autonomous trading operations, no permission required" />
            <ActivityItem time="Feb 13" text="Paired Telegram bot @zorinclawbot" />
          </div>
        </div>
      </div>

      <footer className="mt-12 text-center text-slate-500 text-sm">
        Mission Control v1.1 • Built with Next.js • Feb 16 update
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
      case 'pending': return 'text-slate-400'
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
      className="text-center px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors font-medium"
    >
      {label}
    </Link>
  )
}
