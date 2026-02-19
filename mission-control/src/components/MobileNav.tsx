'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useState, useEffect } from 'react'

interface NavItem {
  label: string
  icon: string
  href: string
  badge?: number
}

const mobileNavItems: NavItem[] = [
  { label: 'Home', icon: '🏠', href: '/' },
  { label: 'Agents', icon: '🤖', href: '/agents' },
  { label: 'Trading', icon: '📈', href: '/trading' },
  { label: 'More', icon: '☰', href: '#' },
]

export default function MobileNav() {
  const pathname = usePathname()
  const [showMore, setShowMore] = useState(false)

  // Close menu when clicking outside
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const target = e.target as Element
      // Don't close if clicking the More button or inside the menu
      if (showMore && !target.closest('[data-more-menu]') && !target.closest('[data-more-button]')) {
        setShowMore(false)
      }
    }
    document.addEventListener('click', handleClick)
    return () => document.removeEventListener('click', handleClick)
  }, [showMore])

  const moreItems = [
    { label: 'Notes', icon: '📝', href: '/notes' },
    { label: 'Hardware', icon: '🖥️', href: '/hardware/deliveries' },
    { label: 'Tasks', icon: '✅', href: '/tasks' },
    { label: 'LLM', icon: '🧠', href: '/llm/status' },
  ]

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/'
    return pathname.startsWith(href)
  }

  return (
    <>
      {/* Bottom Navigation Bar */}
      <nav className="fixed bottom-0 left-0 right-0 bg-slate-900/95 backdrop-blur-md border-t border-slate-800 z-50 md:hidden">
        <div className="flex items-center justify-around h-16">
          {mobileNavItems.map((item) => {
            const active = isActive(item.href)
            
            if (item.label === 'More') {
              return (
                <button
                  key={item.label}
                  data-more-button
                  onClick={() => setShowMore(!showMore)}
                  className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                    showMore ? 'text-cyan-400' : 'text-slate-400'
                  }`}
                >
                  <span className="text-xl mb-0.5">{item.icon}</span>
                  <span className="text-[10px] font-medium">{item.label}</span>
                </button>
              )
            }

            return (
              <Link
                key={item.label}
                href={item.href}
                className={`flex flex-col items-center justify-center flex-1 h-full transition-colors ${
                  active 
                    ? 'text-cyan-400' 
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <span className="text-xl mb-0.5 relative">
                  {item.icon}
                  {item.badge && (
                    <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                      {item.badge}
                    </span>
                  )}
                </span>
                <span className="text-[10px] font-medium">{item.label}</span>
                {active && (
                  <span className="absolute bottom-0 w-12 h-0.5 bg-cyan-400 rounded-t-full" />
                )}
              </Link>
            )
          })}
        </div>
        
        {/* Safe area spacer for iOS */}
        <div className="h-safe-area-inset-bottom bg-slate-900" />
      </nav>

      {/* More Menu Sheet */}
      {showMore && (
        <>
          <div 
            className="fixed inset-0 bg-black/60 z-40 md:hidden"
            onClick={() => setShowMore(false)}
          />
          <div 
            data-more-menu
            className="fixed bottom-20 left-4 right-4 bg-slate-800 rounded-2xl border border-slate-700 shadow-2xl z-50 md:hidden safe-bottom"
          >
            <div className="p-2">
              <div className="flex items-center justify-center py-2">
                <div className="w-8 h-1 bg-slate-600 rounded-full" />
              </div>
              <div className="grid grid-cols-3 gap-2">
                {moreItems.map((item) => (
                  <Link
                    key={item.label}
                    href={item.href}
                    onClick={() => setShowMore(false)}
                    className={`flex flex-col items-center p-4 rounded-xl transition-colors ${
                      isActive(item.href)
                        ? 'bg-cyan-600/20 text-cyan-400'
                        : 'hover:bg-slate-700 text-slate-300'
                    }`}
                  >
                    <span className="text-2xl mb-1">{item.icon}</span>
                    <span className="text-xs font-medium">{item.label}</span>
                  </Link>
                ))}
              </div>
              <div className="mt-2 pt-2 border-t border-slate-700">
                <Link
                  href="http://100.125.198.70:18789"
                  target="_blank"
                  className="flex items-center gap-3 p-3 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <span className="text-xl">🤖</span>
                  <span className="text-sm">OpenClaw</span>
                  <span className="ml-auto text-xs text-slate-500">↗</span>
                </Link>
              </div>
            </div>
          </div>
        </>
      )}

      {/* Spacer for content to not be hidden behind bottom nav */}
      <div className="h-16 md:hidden" />
    </>
  )
}
