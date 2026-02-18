'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import Link from 'next/link'
import { Send, Wifi, WifiOff, ArrowLeft } from 'lucide-react'

interface Message {
  id: number
  role: 'user' | 'assistant' | 'system'
  content: string
}

export default function SimpleChat() {
  const [connected, setConnected] = useState(false)
  const [connecting, setConnecting] = useState(false)
  const [error, setError] = useState('')
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Connect to WebSocket for receiving messages
  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
    }
  }, [])

  const connect = useCallback(() => {
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
              id: 'webchat',
              version: '1.0.0',
              platform: 'browser',
              mode: 'webchat'
            },
            locale: 'en-US',
            userAgent: typeof navigator !== 'undefined' ? navigator.userAgent : 'webchat',
            auth: { token: GATEWAY_TOKEN }
          }
        }))
      }
      
      ws.onmessage = (e: MessageEvent) => {
        try {
          const msg = JSON.parse(e.data)
          
          if (msg.type === 'res' && msg.id?.startsWith('connect-')) {
            if (msg.ok) {
              console.log('WS: Handshake successful!')
              setConnected(true)
              setConnecting(false)
            } else {
              setError('Handshake failed: ' + (msg.error?.message || 'Unknown error'))
              setConnecting(false)
            }
          }
          
          // Receive assistant responses
          if (msg.type === 'event' && msg.event === 'agent' && msg.payload) {
            const { stream, data } = msg.payload
            
            if (stream === 'assistant' && data?.text) {
              setMessages(prev => {
                const lastMsg = prev[prev.length - 1]
                const isDelta = data.delta && lastMsg?.role === 'assistant'
                
                if (isDelta && lastMsg) {
                  const updated = [...prev]
                  updated[updated.length - 1] = {
                    ...lastMsg,
                    content: lastMsg.content + data.delta
                  }
                  return updated
                } else {
                  return [...prev, {
                    id: Date.now(),
                    role: 'assistant',
                    content: data.text
                  }]
                }
              })
            }
          }
          
        } catch (err) {
          console.error('WS message error:', err)
        }
      }
      
      ws.onerror = () => {
        setError('Connection error')
        setConnecting(false)
      }
      
      ws.onclose = () => {
        setConnected(false)
        setConnecting(false)
      }
      
    } catch (err: any) {
      setError(err?.message || 'Connection failed')
      setConnecting(false)
    }
  }, [])

  // Send message via API route
  const sendMessage = async (e?: React.FormEvent) => {
    e?.preventDefault()
    if (!input.trim() || sending) return
    
    const messageText = input.trim()
    setInput('')
    setSending(true)
    
    // Add user message immediately
    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'user',
      content: messageText
    }])
    
    try {
      const res = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: messageText })
      })
      
      if (!res.ok) {
        throw new Error('Failed to send')
      }
      
    } catch (err) {
      console.error('Send error:', err)
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: 'system',
        content: '⚠️ Failed to send message. Please try again.'
      }])
    } finally {
      setSending(false)
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
            className="px-3 py-1 bg-cyan-600 rounded text-sm hover:bg-cyan-700"
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
            <p>Connected to OpenClaw! 🎉</p>
            <p className="text-sm mt-2">Send a message to start chatting</p>
          </div>
        )}
        
        {messages.map(m => (
          <div
            key={m.id}
            className={`p-3 rounded-lg max-w-[80%] ${
              m.role === 'user' 
                ? 'bg-cyan-600 ml-auto' 
                : m.role === 'system'
                ? 'bg-yellow-600/50 mx-auto text-center text-sm'
                : 'bg-slate-800 mr-auto'
            }`}
          >
            {m.content}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>
      
      <form onSubmit={sendMessage} className="p-4 border-t border-slate-800 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={connected ? "Type a message..." : "Connecting..."}
          disabled={!connected || sending}
          className="flex-1 px-4 py-2 bg-slate-800 rounded-lg border border-slate-700 focus:border-cyan-500 focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!connected || !input.trim() || sending}
          className="px-4 py-2 bg-cyan-600 rounded-lg hover:bg-cyan-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
        >
          {sending ? 'Sending...' : <Send className="w-4 h-4" />}
        </button>
      </form>
    </div>
  )
}
