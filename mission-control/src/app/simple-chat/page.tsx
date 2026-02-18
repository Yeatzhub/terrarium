'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import Link from 'next/link'
import { Wifi, WifiOff, ArrowLeft, MessageCircle } from 'lucide-react'

interface Message {
  id: number
  role: 'assistant' | 'system'
  content: string
}

export default function ChatMonitor() {
  const [connected, setConnected] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    connect()
    return () => wsRef.current?.close()
  }, [])

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    
    const GATEWAY_TOKEN = "9a95fd94723eab4b6c332ada4ac919ba2b1082c8f69683cb"
    const ws = new WebSocket('ws://127.0.0.1:18789')
    wsRef.current = ws
    
    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'req',
        id: 'connect-' + Date.now(),
        method: 'connect',
        params: {
          minProtocol: 3,
          maxProtocol: 3,
          client: { id: 'webchat', version: '1.0.0', platform: 'browser', mode: 'webchat' },
          locale: 'en-US',
          userAgent: navigator.userAgent,
          auth: { token: GATEWAY_TOKEN }
        }
      }))
    }
    
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      
      if (msg.type === 'res' && msg.id?.startsWith('connect-')) {
        setConnected(msg.ok)
      }
      
      if (msg.type === 'event' && msg.event === 'agent' && msg.payload?.stream === 'assistant') {
        const data = msg.payload.data
        if (data?.text) {
          setMessages(prev => {
            const last = prev[prev.length - 1]
            if (data.delta && last) {
              const updated = [...prev]
              updated[updated.length - 1] = { ...last, content: last.content + data.delta }
              return updated
            }
            return [...prev, { id: Date.now(), role: 'assistant', content: data.text }]
          })
        }
      }
    }
    
    ws.onclose = () => setConnected(false)
  }, [])

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-white">
      <header className="flex items-center justify-between p-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Link href="/" className="p-2 hover:bg-slate-800 rounded">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="font-bold">Mission Control Monitor</h1>
        </div>
        
        <div className="flex items-center gap-2">
          {connected ? (
            <span className="flex items-center gap-1 text-green-400">
              <Wifi className="w-4 h-4" /> Live
            </span>
          ) : (
            <span className="flex items-center gap-1 text-red-400">
              <WifiOff className="w-4 h-4" /> Offline
            </span>
          )}
        </div>
      </header>
      
      <div className="bg-cyan-500/10 border-b border-cyan-500/20 p-3 text-sm text-cyan-400 flex items-center gap-2">
        <MessageCircle className="w-4 h-4" />
        <span>Send messages via Telegram. Responses appear here in real-time.</span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(m => (
          <div key={m.id} className="bg-slate-800 p-4 rounded-lg">
            {m.content}
          </div>
        ))}
        {messages.length === 0 && (
          <p className="text-slate-500 text-center mt-8">Waiting for messages...</p>
        )}
      </div>
    </div>
  )
}
