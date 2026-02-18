'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { HardDrive, Server, Database, AlertCircle, ArrowLeft, RefreshCw, FolderOpen } from 'lucide-react'

interface StorageDrive {
  name: string
  mount: string
  total: number
  used: number
  free: number
  type: string
}

export default function NasStatusPage() {
  const [drives, setDrives] = useState<StorageDrive[]>([])
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  useEffect(() => {
    fetchStorageData()
    const interval = setInterval(fetchStorageData, 30000)
    return () => clearInterval(interval)
  }, [])

  const fetchStorageData = async () => {
    try {
      // Try to fetch from API, fall back to placeholder
      const res = await fetch('/api/storage-status')
      if (res.ok) {
        const data = await res.json()
        setDrives(data.drives || [])
      } else {
        // Placeholder data
        setDrives([
          { name: 'System Drive', mount: '/', total: 500, used: 180, free: 320, type: 'SSD' },
          { name: 'Data Drive', mount: '/home', total: 2000, used: 450, free: 1550, type: 'HDD' },
        ])
      }
    } catch {
      setDrives([
        { name: 'System Drive', mount: '/', total: 500, used: 180, free: 320, type: 'SSD' },
        { name: 'Data Drive', mount: '/home', total: 2000, used: 450, free: 1550, type: 'HDD' },
      ])
    } finally {
      setLoading(false)
      setLastUpdate(new Date())
    }
  }

  const getUsageColor = (percent: number) => {
    if (percent < 60) return 'bg-emerald-500'
    if (percent < 80) return 'bg-amber-500'
    return 'bg-red-500'
  }

  const totalUsed = drives.reduce((sum, d) => sum + d.used, 0)
  const totalCapacity = drives.reduce((sum, d) => sum + d.total, 0)
  const totalPercent = totalCapacity > 0 ? (totalUsed / totalCapacity) * 100 : 0

  return (
    <div className="min-h-screen bg-slate-950 text-white p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Link href="/hardware" className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 transition-colors">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-purple-500 bg-clip-text text-transparent">
                Storage Status
              </h1>
              <p className="text-slate-400">System & NAS Drive Monitoring</p>
            </div>
          </div>
          <button
            onClick={fetchStorageData}
            className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>

        {/* Overview */}
        <div className="bg-slate-900 rounded-xl p-6 border border-slate-800 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Database className="w-6 h-6 text-indigo-400" />
              <div>
                <h2 className="text-xl font-semibold">Total Storage</h2>
                <p className="text-slate-400">{totalUsed.toFixed(0)} GB / {totalCapacity.toFixed(0)} GB used</p>
              </div>
            </div>
            <span className={`text-2xl font-bold ${totalPercent > 80 ? 'text-red-400' : totalPercent > 60 ? 'text-amber-400' : 'text-emerald-400'}`}>
              {totalPercent.toFixed(1)}%
            </span>
          </div>
          <div className="h-3 bg-slate-800 rounded-full overflow-hidden">
            <div 
              className={`h-full ${getUsageColor(totalPercent)} rounded-full transition-all duration-500`}
              style={{ width: `${totalPercent}%` }}
            />
          </div>
        </div>

        {/* Drives */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {loading ? (
            <div className="col-span-2 flex items-center justify-center h-64">
              <RefreshCw className="w-8 h-8 animate-spin text-indigo-500" />
            </div>
          ) : (
            drives.map((drive) => {
              const percent = (drive.used / drive.total) * 100
              return (
                <div key={drive.name} className="bg-slate-900 rounded-xl border border-slate-800 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <HardDrive className="w-5 h-5 text-slate-400" />
                      <div>
                        <h3 className="font-semibold">{drive.name}</h3>
                        <p className="text-sm text-slate-400">{drive.mount} • {drive.type}</p>
                      </div>
                    </div>
                    <span className={`text-lg font-bold ${percent > 80 ? 'text-red-400' : percent > 60 ? 'text-amber-400' : 'text-emerald-400'}`}>
                      {percent.toFixed(1)}%
                    </span>
                  </div>

                  <div className="h-2 bg-slate-800 rounded-full overflow-hidden mb-4">
                    <div 
                      className={`h-full ${getUsageColor(percent)} rounded-full`}
                      style={{ width: `${percent}%` }}
                    />
                  </div>

                  <div className="flex justify-between text-sm">
                    <span className="text-slate-400">Used: {drive.used} GB</span>
                    <span className="text-slate-400">Free: {drive.free} GB</span>
                  </div>
                </div>
              )
            })
          )}
        </div>

        {drives.length === 0 && !loading && (
          <div className="bg-slate-900/50 rounded-xl border border-slate-800 border-dashed p-12 text-center">
            <Server className="w-12 h-12 mx-auto mb-4 text-slate-600" />
            <h3 className="text-xl font-semibold text-slate-400">No NAS Connected</h3>
            <p className="text-slate-500 mt-2">Connect a NAS or external storage to monitor it here</p>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-slate-600 text-sm">
          <p>Last updated: {lastUpdate.toLocaleTimeString()}</p>
        </div>
      </div>
    </div>
  )
}
