'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { Send, Bot, User, Trash2, Wifi, WifiOff, ArrowLeft, Settings } from 'lucide-react'
import { useGateway } from '@/hooks/useGateway'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  isStreaming?: boolean
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  // Auto-detect gateway URL based on current host
  const getDefaultGatewayUrl = () => {
    if (typeof window === 'undefined') return 'ws://127.0.0.1:18789'
    const host = window.location.hostname
    // If accessing via Tailscale, use the same host for gateway
    if (host.includes('100.') || (host !== 'localhost' && host !== '127.0.0.1')) {
      return `ws://${host}:18789`
    }
    return 'ws://127.0.0.1:18789'
  }
  const [gatewayUrl, setGatewayUrl] = useState(getDefaultGatewayUrl())
  const [authToken, setAuthToken] = useState('')
  const [showSettings, setShowSettings] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const streamingRef = useRef(false)

  const { isConnected, isConnecting, lastMessage, error, send } = useGateway({
    url: gatewayUrl,
    token: authToken || undefined,
    autoReconnect: true,
    reconnectInterval: 3000
  })

  // Handle incoming messages
  useEffect(() => {
    if (!lastMessage) return

    if (lastMessage.type === 'event' && lastMessage.event === 'agent') {
      // Handle agent streaming events
      const payload = lastMessage.payload
      
      if (payload.status === 'start') {
        streamingRef.current = true
        const newMessage: Message = {
          id: `agent_${Date.now()}`,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          isStreaming: true
        }
        setMessages(prev => [...prev, newMessage])
      } else if (payload.status === 'chunk' && payload.text) {
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last?.isStreaming) {
            return [
              ...prev.slice(0, -1),
              { ...last, content: last.content + payload.text }
            ]
          }
          return prev
        })
      } else if (payload.status === 'complete') {
        streamingRef.current = false
        setMessages(prev => {
          const last = prev[prev.length - 1]
          if (last?.isStreaming) {
            return [
              ...prev.slice(0, -1),
              { ...last, isStreaming: false }
            ]
          }
          return prev
        })
      }
    }
  }, [lastMessage])

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input
  useEffect(() => {
    if (isConnected) {
      inputRef.current?.focus()
    }
  }, [isConnected])

  const handleSend = useCallback(async () => {
    if (!input.trim() || !isConnected || streamingRef.current) return

    const userMessage: Message = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')

    try {
      // Send to main session
      await send('sessions_send', {
        sessionKey: 'main',
        message: userMessage.content
      })
    } catch (err) {
      console.error('Failed to send:', err)
      setMessages(prev => [...prev, {
        id: `error_${Date.now()}`,
        role: 'assistant',
        content: '❌ Failed to send. Please check connection.',
        timestamp: new Date()
      }])
    }
  }, [input, isConnected, send])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const clearChat = () => {
    if (confirm('Clear all messages?')) {
      setMessages([])
    }
  }

  return (
    <div className="flex flex-col h-screen bg-slate-900">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/95 backdrop-blur-md">
        <div className="flex items-center gap-3">
          <Link 
            href="/" 
            className="md:hidden p-2 -ml-2 text-slate-400 hover:text-white"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          
          <div>
            <h1 className="font-semibold text-white">OpenClaw</h1>
            <div className="flex items-center gap-1.5">
              {isConnected ? (
                <>
                  <Wifi className="w-3 h-3 text-green-500" />
                  <span className="text-xs text-green-500">Connected</span>
                </>
              ) : (
                <>
                  <WifiOff className="w-3 h-3 text-red-500" />
                  <span className="text-xs text-red-500">
                    {isConnecting ? 'Connecting...' : 'Disconnected'}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <Settings className="w-5 h-5" />
          </button>
          <button
            onClick={clearChat}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </header>

      {/* Settings Panel */}
      {showSettings && (
        <div className="px-4 py-3 border-b border-slate-800 bg-slate-800/50 space-y-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-400 w-16">Gateway:</span>
            <input
              type="text"
              value={gatewayUrl}
              onChange={(e) => setGatewayUrl(e.target.value)}
              className="flex-1 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-white"
              placeholder="ws://127.0.0.1:18789"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-400 w-16">Token:</span>
            <input
              type="password"
              value={authToken}
              onChange={(e) => setAuthToken(e.target.value)}
              className="flex-1 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-sm text-white"
              placeholder="Optional auth token"
            />
          </div>
          <p className="text-xs text-slate-500">
            Gateway URL auto-detected. Token required for external connections.
          </p>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="px-4 py-2 bg-red-500/20 border-b border-red-500/30">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {/* Connection Warning */}
      {!isConnected && !isConnecting && (
        <div className="px-4 py-8 text-center">
          <WifiOff className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <p className="text-slate-400 mb-4">Not connected to OpenClaw Gateway</p>
          <p className="text-sm text-slate-500 mb-4">
            Make sure OpenClaw is running locally:
            <br />
            <code className="bg-slate-800 px-2 py-1 rounded text-sm">openclaw gateway start</code>
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white font-medium"
          >
            Reconnect
          </button>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && isConnected && (
          <div className="text-center py-8 text-slate-500">
            <Bot className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>Start a conversation with OpenClaw</p>
            <p className="text-sm mt-2">
              Try: "Show me GPU status" or "Start a trading strategy"
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                message.role === 'user'
                  ? 'bg-blue-600'
                  : 'bg-gradient-to-br from-purple-500 to-pink-500'
              }`}
            >
              {message.role === 'user' ? (
                <User className="w-4 h-4 text-white" />
              ) : (
                <Bot className="w-4 h-4 text-white" />
              )}
            </div>

            <div
              className={`max-w-[85%] md:max-w-[75%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white rounded-br-md'
                  : 'bg-slate-800 text-slate-100 rounded-bl-md border border-slate-700'
              }`}
            >
              <div className="text-sm whitespace-pre-wrap break-words">{message.content}</div>
              
              {message.isStreaming && (
                <span className="inline-block w-2 h-2 bg-slate-400 rounded-full ml-1 animate-pulse" />
              )}

              <div
                className={`text-[10px] mt-1 ${
                  message.role === 'user' ? 'text-blue-200' : 'text-slate-500'
                }`}
              >
                {message.timestamp.toLocaleTimeString('en-US', {
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
            </div>
          </div>
        ))}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-slate-800 p-4 bg-slate-900/95 backdrop-blur-md">
        <div className="flex items-end gap-2 max-w-4xl mx-auto">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isConnected ? "Message OpenClaw..." : "Waiting for connection..."}
            disabled={!isConnected || streamingRef.current}
            rows={1}
            className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-4 py-3 pr-20 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 resize-none min-h-[48px] max-h-32 disabled:opacity-50 disabled:cursor-not-allowed"
          />
          
          <button
            onClick={handleSend}
            disabled={!input.trim() || !isConnected || streamingRef.current}
            className="p-3 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-xl transition-colors"
          >
            <Send className="w-5 h-5 text-white" />
          </button>
        </div>
        <div className="text-center mt-2 text-[10px] text-slate-500">
          Connected to OpenClaw Gateway • Press Enter to send
        </div>
      </div>
    </div>
  )
}
