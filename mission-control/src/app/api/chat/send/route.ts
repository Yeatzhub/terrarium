import { NextResponse } from 'next/server'

export async function POST(req: Request) {
  try {
    const { message, sessionKey = 'main' } = await req.json()
    
    if (!message) {
      return NextResponse.json({ error: 'Message required' }, { status: 400 })
    }
    
    // Forward to Gateway via internal tool
    const result = await sendViaTool(message, sessionKey)
    
    if (!result.success) {
      return NextResponse.json({ error: result.error }, { status: 500 })
    }
    
    return NextResponse.json({ success: true })
    
  } catch (err) {
    console.error('Chat send error:', err)
    return NextResponse.json({ error: 'Internal error' }, { status: 500 })
  }
}

async function sendViaTool(message: string, sessionKey: string): Promise<{success: boolean, error?: string}> {
  // This will be handled by the Gateway's internal routing
  // We need to use the proper Gateway HTTP endpoint
  
  const GATEWAY_URL = process.env.GATEWAY_URL || 'http://127.0.0.1:18789'
  const GATEWAY_TOKEN = process.env.GATEWAY_TOKEN || '9a95fd94723eab4b6c332ada4ac919ba2b1082c8f69683cb'
  
  try {
    // Try the gateway's built-in HTTP endpoint for sending
    const response = await fetch(`${GATEWAY_URL}/api/sessions/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${GATEWAY_TOKEN}`
      },
      body: JSON.stringify({ sessionKey, message })
    })
    
    if (!response.ok) {
      const text = await response.text()
      return { success: false, error: `Gateway error: ${text}` }
    }
    
    return { success: true }
    
  } catch (err: any) {
    return { success: false, error: err.message }
  }
}