'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { Send, Wifi, WifiOff, ArrowLeft, MessageCircle } from 'lucide-react'

export default function SimpleChat() {
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [error, setError] = useState('')
  const [messages, setMessages] = useState<{id: number, role: string, content: string}[]>([])
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [])

  function connect() {
    if (wsRef.current?.readyState === WebSocket.OPEN) return
    
    setConnecting(true)
    setError('')
    
    try {
      const GATEWAY_TOKEN = "9a95fd94723eab4b6c332ada4ac919ba2b1082c8f69683cb"
      const ws = new WebSocket('ws://127.0.0.1:18789')
      wsRef.current = ws
      
      ws.onopen = () => {
        console.log('WS: Connected')
        
        // Use webchat client (can receive, not send)
        ws.send(JSON.stringify({
          type: 'req',
          id: 'connect-' + Date.now(),
          method: 'connect',
          params: {
            minProtocol: 3,
            maxProtocol: 3,
            client: {
              id: 'webchat',
              version: '1.0.0',
              platform: 'browser',
              mode: 'webchat'
            },
            locale: 'en-US',
            userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'webchat',
            auth: {
              token: GATEWAY_TOKEN
            }
          }
        }))
      }
      
      ws.onmessage = (e: MessageEvent) => {
        console.log('WS: Message received:', e.data)
        try {
          const msg = JSON.parse(e.data)
          
          if (msg.type === 'res' && msg.id?.startsWith('connect-')) {
            if (msg.ok) {
              console.log('WS: Handshake successful!')
              setConnected(true)
              setConnecting(false)
              setError('')
            } else {
              console.error('WS: Handshake failed:', msg.error)
              setError('Handshake failed: ' + (msg.error?.message || 'Unknown error'))
              setConnecting(false)
            }
          }
          
          // Receive messages from Gateway
          if (msg.type === 'event') {
            console.log('WS: Event received:', msg.event, msg.payload)
            
            // Handle agent response messages (this is how responses flow)
            if (msg.event === 'agent' && msg.payload) {
              const stream = msg.payload.stream
              const data = msg.payload.data
              
              // Assistant response chunks
              if (stream === 'assistant' && data?.text) {
                // Append to last message if it's from assistant, otherwise create new
                setMessages(prev => {
                  const lastMsg = prev[prev.length - 1]
                  const isDelta = data.delta && lastMsg?.role === 'assistant'
                  
                  if (isDelta && lastMsg) {
                    // Append delta to existing message
                    const updated = [...prev]
                    updated[updated.length - 1] = {
                      ...lastMsg,
                      content: lastMsg.content + data.delta
                    }
                    return updated
                  } else {
                    // New assistant message
                    return [...prev, {
                      id: Date.now(),
                      role: 'assistant',
                      content: data.text
                    }]
                  }
                })
              }
              
              // System/tool messages
              if (stream === 'system' && data?.text) {
                setMessages(prev => [...prev, {
                  id: Date.now(),
                  role: 'system',
                  content: data.text
                }])
              }
            }
          }
          
        } catch (err) {
          console.error('WS: Failed to parse message:', err)
        }
      }
      
      ws.onerror = (e) => {
        console.error('WS Error:', e)
        setError('WebSocket error')
        setConnecting(false)
      }
      
      ws.onclose = () => {
        console.log('WS: Closed')
        setConnected(false)
        setConnecting(false)
      }
      
    } catch (err: any) {
      setError(err?.message || 'Connection failed')
      setConnecting(false)
    }
  }

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-white">
      <header className="flex items-center justify-between p-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Link href="/" className="p-2 hover:bg-slate-800 rounded">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="font-bold">OpenClaw Chat</h1>
        </div>
        <div className="flex items-center gap-2">
          {connected ? (
            <span className="flex items-center gap-1 text-green-400">
              <Wifi className="w-4 h-4" /> Connected
            </span>
          ) : connecting ? (
            <span className="text-yellow-400">Connecting...</span>
          ) : (
            <span className="flex items-center gap-1 text-red-400">
              <WifiOff className="w-4 h-4" /> Disconnected
            </span>
          )}
          <button 
            onClick={connect}
            className="px-3 py-1 bg-blue-600 rounded text-sm"
          >
            Reconnect
          </button>
        </div>
      </header>
      
      {error && (
        <div className="p-4 bg-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}
      
      {/* Info banner */}
      <div className="p-3 bg-blue-500/10 border-b border-blue-500/20 text-sm text-blue-400 flex items-center gap-2">
        <MessageCircle className="w-4 h-4" />
        <span>
          Read-only mode - Send messages via Telegram, view responses here
        </span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-slate-500 mt-8">
            {connected ? (
              <>
                <p>Connected to OpenClaw!</p>
                <p className="text-sm mt-2">Send messages via Telegram to see responses here</p>
              </>
            ) : (
              'Connecting to OpenClaw...'
            )}
          </div>
        )}
        {messages.map(m => (
          <div key={m.id} className={`p-3 rounded ${
            m.role === 'user' ? 'bg-blue-600 ml-12' : 'bg-slate-800 mr-12'
          }`}>
            {m.content}
          </div>
        ))}
      </div>
      
      <div className="p-4 border-t border-slate-800 text-center text-slate-500 text-sm">
        Send messages via Telegram - responses appear here automatically
      </div>
    </div>
  )
}
