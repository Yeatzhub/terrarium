'use client'

import Link from 'next/link'

const deliveries = [
  {
    name: 'Tesla P40 GPU',
    status: 'in-transit',
    tracking: '9405508106245831259625',
    eta: 'Soon',
    details: '24GB VRAM, needs 250W PSU verification',
    icon: '🎮',
  },
  {
    name: 'Noctua Fan + PCIe Riser',
    status: 'delivered',
    arrived: 'Feb 16',
    icon: '🔧',
  },
  {
    name: 'WD Red 8TB',
    status: 'pending',
    quantity: 2,
    icon: '💾',
  },
  {
    name: 'i7-7700K CPU',
    status: 'pending',
    icon: '⚙️',
  },
]

export default function HardwareDeliveries() {
  const getStatusColor = (status: string) => {
    switch(status) {
      case 'delivered': return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'in-transit': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      default: return 'bg-slate-700/50 text-slate-400 border-slate-600'
    }
  }

  return (
    <div className="p-4 md:p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <Link href="/" className="text-sm text-slate-400 hover:text-slate-300 mb-2 block">
            ← Back to Dashboard
          </Link>
          <h1 className="text-3xl font-bold flex items-center gap-3">
            <span>🚚</span> Hardware Deliveries
          </h1>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {[
          { label: 'Delivered', value: '1', color: 'text-green-400' },
          { label: 'In Transit', value: '1', color: 'text-yellow-400' },
          { label: 'Pending', value: '2', color: 'text-slate-400' },
        ].map((stat) => (
          <div key={stat.label} className="bg-slate-800 rounded-xl p-4 border border-slate-700 text-center">
            <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
            <p className="text-sm text-slate-400">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Deliveries List */}
      <div className="space-y-4">
        {deliveries.map((item) => (
          <div 
            key={item.name}
            className={`bg-slate-800 rounded-xl p-6 border ${getStatusColor(item.status)}`}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-start gap-4">
                <span className="text-4xl">{item.icon}</span>
                <div>
                  <h3 className="text-lg font-semibold">{item.name}</h3>
                  {'quantity' in item && (
                    <p className="text-sm text-slate-400">Quantity: {item.quantity}</p>
                  )}
                  {'details' in item && (
                    <p className="text-sm text-slate-500 mt-2">{item.details}</p>
                  )}
                </div>
              </div>
              <div className="text-right">
                <span className={`
                  px-3 py-1 rounded-full text-sm font-medium
                  ${item.status === 'delivered' ? 'bg-green-500/20 text-green-400' :
                    item.status === 'in-transit' ? 'bg-yellow-500/20 text-yellow-400' :
                    'bg-slate-700 text-slate-400'}
                `}>
                  {item.status.replace('-', ' ')}
                </span>
                {'arrived' in item && (
                  <p className="text-sm text-slate-400 mt-2">Arrived: {item.arrived}</p>
                )}
                {'eta' in item && (
                  <p className="text-sm text-slate-400 mt-2">ETA: {item.eta}</p>
                )}
              </div>
            </div>

            {'tracking' in item && (
              <div className="mt-4 pt-4 border-t border-slate-700/50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">Tracking Number</p>
                    <p className="font-mono text-sm">{item.tracking}</p>
                  </div>
                  <a
                    href={`https://tools.usps.com/go/TrackConfirmAction?tLabels=${item.tracking}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg transition-colors text-sm font-medium"
                  >
                    Track Package →
                  </a>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
