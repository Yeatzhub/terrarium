'use client';

import Link from 'next/link';
import { ArrowLeft, Brain, Activity, Database, Coins } from 'lucide-react';

const LLM_PAGES = [
  {
    id: 'status',
    name: 'System Status',
    icon: Activity,
    description: 'LLM service health, response times, and availability',
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/20',
  },
  {
    id: 'models',
    name: 'Models',
    icon: Brain,
    description: 'Available models, pricing, and capabilities',
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/20',
  },
  {
    id: 'tokens',
    name: 'Token Usage',
    icon: Coins,
    description: 'Daily token consumption and cost tracking',
    color: 'text-amber-400',
    bgColor: 'bg-amber-500/20',
  },
];

export default function LLMPage() {
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
              <Brain className="w-6 h-6 text-purple-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold">LLM Status</h1>
              <p className="text-slate-400">Model management and usage analytics</p>
            </div>
          </div>
        </div>

        {/* LLM Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {LLM_PAGES.map((page) => {
            const Icon = page.icon;
            return (
              <Link
                key={page.id}
                href={`/llm/${page.id}`}
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
