import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  try {
    const { message } = await request.json()
    
    if (!message) {
      return NextResponse.json({ error: 'Message required' }, { status: 400 })
    }

    // Get OpenClaw session key from environment or config
    // For now, try to send via the local OpenClaw instance
    const openclawUrl = process.env.OPENCLAW_URL || 'http://127.0.0.1:18789'
    
    // Send message to OpenClaw
    // Note: This would need the actual OpenClaw API endpoint
    // For this demo, we'll return a mock response
    
    return NextResponse.json({ 
      response: `This is a demo. To integrate with real OpenClaw, you'd need:

1. OpenClaw API endpoint exposed
2. Session authentication
3. WebSocket for real-time chat

For now, you can click "OpenClaw" in the quick actions to open the native app.`,
      success: true
    })
  } catch (error) {
    console.error('Chat error:', error)
    return NextResponse.json({ 
      error: 'Failed to process message',
      response: 'Connection error to OpenClaw'
    }, { status: 500 })
  }
}
