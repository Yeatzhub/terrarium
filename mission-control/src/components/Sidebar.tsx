'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'

interface NavItem {
  id: string
  label: string
  icon: string
  href: string
  subItems?: { label: string; href: string }[]
}

const navItems: NavItem[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: '🏠',
    href: '/',
  },
  {
    id: 'chat',
    label: 'Chat',
    icon: '🤖',
    href: '/chat',
  },
  {
    id: 'trading',
    label: 'Trading',
    icon: '📈',
    href: '/trading',
    subItems: [
      { label: 'Kraken', href: '/trading?tab=kraken' },
      { label: 'Toobit', href: '/trading?tab=toobit' },
      { label: 'Jupiter', href: '/trading?tab=jupiter' },
      { label: 'Polymarket', href: '/trading?tab=polymarket' },
    ],
  },
  {
    id: 'hardware',
    label: 'Hardware',
    icon: '🖥️',
    href: '/hardware/deliveries',
    subItems: [
      { label: 'GPU Status', href: '/hardware/gpu' },
      { label: 'NAS Storage', href: '/hardware/nas' },
      { label: 'Deliveries', href: '/hardware/deliveries' },
    ],
  },
  {
    id: 'agents',
    label: 'Agents',
    icon: '🤖',
    href: '/agents',
    subItems: [
      { label: 'Active Agents', href: '/agents' },
      { label: 'Sub-agents', href: '/agents' },
      { label: 'Logs', href: '/agents' },
    ],
  },
  {
    id: 'llm',
    label: 'LLM',
    icon: '🧠',
    href: '/llm/status',
    subItems: [
      { label: 'Models', href: '/llm/models' },
      { label: 'Token Usage', href: '/llm/tokens' },
      { label: 'Status', href: '/llm/status' },
    ],
  },
  {
    id: 'notes',
    label: 'Notes',
    icon: '📝',
    href: '/notes',
  },
  {
    id: 'tasks',
    label: 'Tasks',
    icon: '⚙️',
    href: '/tasks',
  },
]

export default function Sidebar() {
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const [expandedItems, setExpandedItems] = useState<string[]>(['trading', 'hardware'])

  // Auto-collapse on mobile
  useEffect(() => {
    if (typeof window === 'undefined') return
    
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setIsCollapsed(true)
      } else {
        setIsCollapsed(false)
      }
    }
    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const toggleItem = (id: string) => {
    setExpandedItems(prev => 
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    )
  }

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/'
    return pathname.startsWith(href.split('?')[0])
  }

  const isSubActive = (href: string) => {
    if (pathname === href.split('?')[0]) return true
    if (typeof window !== 'undefined') {
      return pathname + window.location.search === href
    }
    return false
  }

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setIsMobileOpen(!isMobileOpen)}
        className="fixed top-4 left-4 z-50 md:hidden p-2 bg-slate-800 rounded-lg border border-slate-700 hover:bg-slate-700 transition-colors"
        aria-label="Toggle menu"
      >
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {isMobileOpen ? (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          ) : (
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          )}
        </svg>
      </button>

      {/* Overlay for mobile */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`
          fixed top-0 left-0 h-screen bg-slate-900 border-r border-slate-800 z-40
          transition-all duration-300 ease-in-out
          ${isCollapsed ? 'w-16' : 'w-64'}
          ${isMobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
        `}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800">
          {!isCollapsed && (
            <Link href="/" className="flex items-center gap-2 text-xl font-bold">
              <span>🚀</span>
              <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                MC
              </span>
            </Link>
          )}
          {isCollapsed && <span className="text-xl">🚀</span>}
          
          {/* Collapse button (desktop only) */}
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="hidden md:block p-1 hover:bg-slate-800 rounded transition-colors"
            aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <svg 
              className={`w-5 h-5 text-slate-400 transition-transform ${isCollapsed ? 'rotate-180' : ''}`}
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-2 space-y-1 overflow-y-auto h-[calc(100vh-80px)]">
          {navItems.map((item) => {
            const active = isActive(item.href)
            const expanded = expandedItems.includes(item.id)
            const hasSubItems = item.subItems && item.subItems.length > 0

            return (
              <div key={item.id}>
                {/* Main nav item */}
                <div className="relative">
                  {hasSubItems ? (
                    <div className="flex items-center">
                      <Link
                        href={item.href}
                        onClick={() => setIsMobileOpen(false)}
                        className={`
                          flex-1 flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
                          ${active 
                            ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' 
                            : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                          }
                          ${isCollapsed ? 'justify-center' : ''}
                        `}
                      >
                        <span className="text-xl flex-shrink-0">{item.icon}</span>
                        {!isCollapsed && (
                          <>
                            <span className="flex-1 text-left font-medium">{item.label}</span>
                          </>
                        )}
                      </Link>
                      {!isCollapsed && (
                        <button
                          onClick={() => toggleItem(item.id)}
                          className="p-2 hover:bg-slate-800 rounded-lg transition-colors"
                        >
                          <svg 
                            className={`w-4 h-4 text-slate-500 transition-transform ${expanded ? 'rotate-180' : ''}`}
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                          </svg>
                        </button>
                      )}
                    </div>
                  ) : (
                    <Link
                      href={item.href}
                      onClick={() => setIsMobileOpen(false)}
                      className={`
                        flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
                        ${active 
                          ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' 
                          : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                        }
                        ${isCollapsed ? 'justify-center' : ''}
                      `}
                    >
                      <span className="text-xl flex-shrink-0">{item.icon}</span>
                      {!isCollapsed && <span className="font-medium">{item.label}</span>}
                    </Link>
                  )}

                  {/* Active indicator dot */}
                  {active && isCollapsed && (
                    <span className="absolute right-1 top-1/2 -translate-y-1/2 w-1.5 h-1.5 bg-blue-400 rounded-full" />
                  )}
                </div>

                {/* Sub-items */}
                {!isCollapsed && hasSubItems && expanded && item.subItems && (
                  <div className="ml-4 mt-1 space-y-0.5 border-l-2 border-slate-800 pl-3">
                    {item.subItems.map((sub) => (
                      <Link
                        key={sub.label}
                        href={sub.href}
                        onClick={() => setIsMobileOpen(false)}
                        className={`
                          block px-3 py-2 rounded-lg text-sm transition-colors
                          ${isSubActive(sub.href)
                            ? 'text-blue-400 bg-blue-500/10' 
                            : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                          }
                        `}
                      >
                        {sub.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            )
          })}
        </nav>

        {/* Collapsed tooltip - show on hover */}
        {isCollapsed && (
          <div className="absolute bottom-4 left-4 right-4">
            <div className="w-8 h-8 bg-slate-800 rounded-full flex items-center justify-center mx-auto border border-slate-700">
              <span className="text-xs text-slate-400">v1.2</span>
            </div>
          </div>
        )}
      </aside>

      {/* Main content spacer */}
      <div className={`hidden md:block transition-all duration-300 ${isCollapsed ? 'w-16' : 'w-64'} flex-shrink-0`} />
    </>
  )
}
