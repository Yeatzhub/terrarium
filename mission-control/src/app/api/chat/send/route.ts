export async function POST(req: Request) {
  try {
    const { message, sessionKey = 'main' } = await req.json()
    
    if (!message) {
      return Response.json({ error: 'Message required' }, { status: 400 })
    }
    
    const GATEWAY_URL = process.env.GATEWAY_URL || 'http://127.0.0.1:18789'
    const GATEWAY_TOKEN = process.env.GATEWAY_TOKEN || '9a95fd94723eab4b6c332ada4ac919ba2b1082c8f69683cb'
    
    // Forward to Gateway via HTTP API
    const response = await fetch(`${GATEWAY_URL}/v1/sessions/send`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${GATEWAY_TOKEN}`
      },
      body: JSON.stringify({
        sessionKey,
        message
      })
    })
    
    if (!response.ok) {
      const error = await response.text()
      console.error('Gateway error:', error)
      return Response.json({ error: 'Failed to send message' }, { status: 500 })
    }
    
    return Response.json({ success: true })
    
  } catch (err) {
    console.error('Chat send error:', err)
    return Response.json({ error: 'Internal error' }, { status: 500 })
  }
}