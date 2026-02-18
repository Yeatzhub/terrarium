# OpenClaw Gateway Integration Plan

## Architecture

```
Mission Control (Next.js)
    ↓ WebSocket (operator role)
OpenClaw Gateway (127.0.0.1:18789)
    ↓ WebSocket  
OpenClaw Agent (processes requests)
```

## Implementation Steps

### Phase 1: WebSocket Connection ✅
- [ ] Create WebSocket hook for Gateway connection
- [ ] Handle handshake (connect → hello-ok)
- [ ] Auto-reconnect on disconnect
- [ ] Token-based auth

### Phase 2: Message Flow ✅
- [ ] Send: `req` frames with `id`, `method`, `params`
- [ ] Receive: `res` frames and `event` frames
- [ ] Map Gateway events to chat UI

### Phase 3: Session Management ✅
- [ ] List active sessions
- [ ] Send message to session
- [ ] Receive streaming responses
- [ ] Handle agent events (start, progress, complete)

### Phase 4: Mobile Optimization ✅
- [ ] Work offline/reconnect gracefully
- [ ] Background sync
- [ ] Push notifications for new messages

## Gateway Methods Needed

- `connect` - Handshake with auth
- `sessions.list` - Get active sessions
- `sessions.send` - Send message to session
- `sessions.history` - Get session history
- `agent` - Run agent (for new conversations)

## WebSocket Frame Format

```json
// Send
{
  "type": "req",
  "id": "uuid",
  "method": "sessions.send",
  "params": {
    "sessionKey": "main",
    "message": "Hello"
  }
}

// Receive response
{
  "type": "res",
  "id": "uuid",
  "ok": true,
  "payload": { ... }
}

// Receive event (streaming)
{
  "type": "event",
  "event": "agent",
  "payload": { ... }
}
```
