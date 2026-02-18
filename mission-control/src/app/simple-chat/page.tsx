'use client'

import { useState, useEffect, useRef } from 'react'
import Link from 'next/link'
import { Send, Wifi, WifiOff, ArrowLeft } from 'lucide-react'

export default function SimpleChat() {
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [error, setError] = useState('')
  const [messages, setMessages] = useState<{id: number, role: string, content: string}[]>([])
  const [input, setInput] = useState('')
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    connect()
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
        
        ws.send(JSON.stringify({
          type: 'req',
          id: 'connect-' + Date.now(),
          method: 'connect',
          params: {
            minProtocol: 3,
            maxProtocol: 3,
            client: {
              id: 'openclaw-control-ui',
              version: '2.0.0',
              platform: 'browser',
              mode: 'ui'
            },
            locale: 'en-US',
            userAgent: navigator.userAgent,
            auth: {
              token: GATEWAY_TOKEN
            },
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
              setMessages(prev => [...prev, { 
                id: Date.now(), 
                role: 'assistant', 
                content: 'Connected to OpenClaw! Session: ' + (msg.payload?.sessionId || 'N/A')
              }])
            } else {
              console.error('WS: Handshake failed:', msg.error)
              setError('Handshake failed: ' + (msg.error?.message || 'Unknown error'))
              setConnecting(false)
            }
          }
          
          // Listen for ALL events and log them
          if (msg.type === 'event') {
            console.log('WS: Event received:', msg.event, msg.payload)
            
            if (msg.event === 'session.message' || msg.event === 'message') {
              const content = msg.payload?.message?.content || msg.payload?.content || msg.payload?.text
              const role = msg.payload?.message?.role || msg.payload?.role
              if (content && role === 'assistant') {
                setMessages(prev => [...prev, {
                  id: Date.now(),
                  role: 'assistant',
                  content: content
                }])
              }
            }
            
            if (msg.event === 'chat.message' || msg.event === 'agent.message') {
              const content = msg.payload?.content || msg.payload?.text || msg.payload?.message
              if (content) {
                setMessages(prev => [...prev, {
                  id: Date.now(),
                  role: 'assistant',
                  content: content
                }])
              }
            }
          }
          
          if (msg.type === 'event' && msg.event === 'connect.challenge') {
            console.log('WS: Received challenge, waiting for response...')
          }
          
        } catch (err) {
          console.error('WS: Failed to parse message:', err)
        }
      }
      
      ws.onerror = (e) => {
        console.error('WS Error:', e)
        setError('WebSocket error. Check console.')
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

  function sendMessage() {
    if (!input.trim() || !wsRef.current || !connected) return
    
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: input }])
    
    const GATEWAY_TOKEN = "9a95fd94723eab4b6c332ada4ac919ba2b1082c8f69683cb"
    wsRef.current.send(JSON.stringify({
      type: 'req',
      id: 'msg-' + Date.now(),
      method: 'sessions_send',
      params: {
        sessionKey: 'main',
        message: input,
      }
    }))
    
    setInput('')
  }

  return (
    <div className="flex flex-col h-screen bg-slate-900 text-white">
      <header className="flex items-center justify-between p-4 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <Link href="/" className="p-2 hover:bg-slate-800 rounded">
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <h1 className="font-bold">Simple Chat</h1>
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
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-slate-500 mt-8">
            {connected ? 'Type a message to chat with OpenClaw' : 'Connecting to OpenClaw...'}
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
      
      <div className="p-4 border-t border-slate-800">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && sendMessage()}
            placeholder="Type message..."
            className="flex-1 bg-slate-800 border border-slate-700 rounded px-4 py-2"
          />
          <button 
            onClick={sendMessage}
            disabled={!connected}
            className="px-4 py-2 bg-blue-600 rounded disabled:bg-slate-700"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
