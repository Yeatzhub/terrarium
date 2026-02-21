'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

interface GatewayMessage {
  type: 'req' | 'res' | 'event'
  id?: string
  method?: string
  params?: any
  ok?: boolean
  payload?: any
  error?: any
  event?: string
}

interface UseGatewayOptions {
  url: string
  token?: string
  autoReconnect?: boolean
  reconnectInterval?: number
}

export function useGateway(options: UseGatewayOptions) {
  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [lastMessage, setLastMessage] = useState<GatewayMessage | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reqIdCounter = useRef(0)
  const pendingReqs = useRef<Map<string, { resolve: Function; reject: Function }>>(new Map())

  const generateId = () => {
    reqIdCounter.current += 1
    return `req_${Date.now()}_${reqIdCounter.current}`
  }

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN || isConnecting) return
    
    setIsConnecting(true)
    setError(null)

    try {
      const ws = new WebSocket(options.url)
      wsRef.current = ws

      ws.onopen = () => {
        console.log('[Gateway] WebSocket opened, sending handshake...')
        console.log('[Gateway] URL:', options.url)
        
        // Send connect handshake - include auth token if provided
        const connectId = generateId()
        const connectReq = {
          type: 'req',
          id: connectId,
          method: 'connect',
          params: {
            minProtocol: 3,
            maxProtocol: 3,
            client: {
              id: 'the-hub',
              version: '2.0.0',
              platform: 'web',
              mode: 'app'
            },
            locale: 'en-US',
            userAgent: 'the-hub/2.0.0',
            token: options.token
          }
        }
        
        console.log('[Gateway] Sending handshake:', JSON.stringify(connectReq))
        
        pendingReqs.current.set(connectId, {
          resolve: (res: any) => {
            console.log('[Gateway] Handshake response:', res)
            if (res.ok) {
              console.log('[Gateway] Handshake successful')
              setIsConnected(true)
              setIsConnecting(false)
              setError(null)
            } else {
              console.error('[Gateway] Handshake failed:', res.error)
              setError(res.error?.message || 'Authentication failed')
              setIsConnecting(false)
              ws.close()
            }
          },
          reject: (err: any) => {
            console.error('[Gateway] Handshake rejected:', err)
            setError(err?.message || 'Handshake failed')
            setIsConnecting(false)
          }
        })
        
        // Timeout handshake after 10 seconds
        setTimeout(() => {
          if (pendingReqs.current.has(connectId)) {
            console.error('[Gateway] Handshake timeout')
            pendingReqs.current.delete(connectId)
            setError('Handshake timeout')
            setIsConnecting(false)
            ws.close()
          }
        }, 10000)
        
        ws.send(JSON.stringify(connectReq))
      }

      ws.onmessage = (event) => {
        try {
          const msg: GatewayMessage = JSON.parse(event.data)
          setLastMessage(msg)
          
          if (msg.type === 'res' && msg.id && pendingReqs.current.has(msg.id)) {
            const { resolve, reject } = pendingReqs.current.get(msg.id)!
            pendingReqs.current.delete(msg.id)
            
            if (msg.ok) {
              resolve(msg)
            } else {
              reject(msg.error)
            }
          }
        } catch (err) {
          console.error('[Gateway] Failed to parse message:', err)
        }
      }

      ws.onerror = (err) => {
        console.error('[Gateway] WebSocket error:', err)
        console.error('[Gateway] Error type:', (err as any).type || 'unknown')
        console.error('[Gateway] ReadyState at error:', ws.readyState)
        setError('Connection error - check console for details')
      }

      ws.onclose = (event) => {
        console.log('[Gateway] Disconnected:', event.code, event.reason)
        setIsConnected(false)
        setIsConnecting(false)
        
        // Clear pending requests
        pendingReqs.current.forEach(({ reject }) => {
          reject(new Error('Connection closed'))
        })
        pendingReqs.current.clear()
        
        // Auto-reconnect
        if (options.autoReconnect !== false) {
          const interval = options.reconnectInterval || 3000
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('[Gateway] Attempting reconnect...')
            connect()
          }, interval)
        }
      }
    } catch (err) {
      console.error('[Gateway] Failed to connect:', err)
      setError('Failed to connect')
      setIsConnecting(false)
    }
  }, [options.url, options.token, options.autoReconnect, options.reconnectInterval, isConnecting])

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
  }, [])

  const send = useCallback((method: string, params?: any): Promise<any> => {
    return new Promise((resolve, reject) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        reject(new Error('Not connected'))
        return
      }
      
      const id = generateId()
      const req = { type: 'req', id, method, params }
      
      pendingReqs.current.set(id, { resolve, reject })
      
      // Timeout after 30 seconds
      setTimeout(() => {
        if (pendingReqs.current.has(id)) {
          pendingReqs.current.delete(id)
          reject(new Error('Request timeout'))
        }
      }, 30000)
      
      wsRef.current.send(JSON.stringify(req))
    })
  }, [])

  // Connect on mount
  useEffect(() => {
    connect()
    return () => disconnect()
  }, [connect, disconnect])

  return {
    isConnected,
    isConnecting,
    lastMessage,
    error,
    connect,
    disconnect,
    send
  }
}
