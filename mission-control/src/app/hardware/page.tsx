'use client';

import Link from 'next/link';
import { ArrowLeft, Server, HardDrive, Cpu, Package } from 'lucide-react';

const HARDWARE_PAGES = [
  {
    id: 'nas',
    name: 'NAS Setup',
    icon: HardDrive,
    description: 'Network Attached Storage configuration and drive management',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/20',
  },
  {
    id: 'gpu',
    name: 'GPU Status',
    icon: Cpu,
    description: 'P40 GPU monitoring, temperature, and utilization',
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/20',
  },
  {
    id: 'deliveries',
    name: 'Deliveries',
    icon: Package,
    description: 'Hardware delivery tracking and shipment status',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/20',
  },
];

export default function HardwarePage() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <Link 
            href="/" 
            className="inline-flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to The Hub
          </Link>
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-slate-800 flex items-center justify-center">
              <Server className="w-6 h-6 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">Hardware</h1>
              <p className="text-slate-400">System hardware monitoring and setup</p>
            </div>
          </div>
        </div>

        {/* Hardware Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {HARDWARE_PAGES.map((page) => {
            const Icon = page.icon;
            return (
              <Link
                key={page.id}
                href={`/hardware/${page.id}`}
                className="block bg-slate-900 rounded-xl border border-slate-800 p-6 hover:border-slate-600 transition-colors"
              >
                <div className={`w-12 h-12 rounded-lg ${page.bgColor} flex items-center justify-center mb-4`}>
                  <Icon className={`w-6 h-6 ${page.color}`} />
                </div>
                <h3 className="text-lg font-semibold mb-2">{page.name}</h3>
                <p className="text-sm text-slate-400">{page.description}</p>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
