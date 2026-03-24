#!/usr/bin/env node
/**
 * TradingView Webhook Server for Thor
 * Runs on port 18790 and routes signals to Thor's SIGNAL.md
 */

import http from 'http';
import fs from 'fs/promises';
import path from 'path';

const PORT = process.env.TRADINGVIEW_WEBHOOK_PORT || 18790;
const THOR_SIGNAL_PATH = '/storage/workspace/agents/thor/SIGNAL.md';

const AGENTS = {
  thor: {
    symbol: 'XRPUSDT',
    signalPath: '/storage/workspace/agents/thor/SIGNAL.md',
    enabled: true
  }
};

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);
  
  // Health check
  if (url.pathname === '/health' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', agents: Object.keys(AGENTS) }));
    return;
  }
  
  // Agents list
  if (url.pathname === '/agents' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ agents: AGENTS }));
    return;
  }
  
  // TradingView webhook
  if (url.pathname === '/webhook/tradingview' && req.method === 'POST') {
    let body = '';
    
    req.on('data', chunk => { body += chunk; });
    req.on('end', async () => {
      try {
        const alert = JSON.parse(body);
        
        console.log(`[TradingView] Alert:`, {
          symbol: alert.symbol,
          action: alert.action,
          price: alert.price,
          time: new Date().toISOString()
        });
        
        // Find agent for symbol
        const agentName = findAgentForSymbol(alert.symbol || '');
        
        if (!agentName) {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ 
            status: 'ignored', 
            reason: 'no_agent_configured',
            symbol: alert.symbol 
          }));
          return;
        }
        
        const agent = AGENTS[agentName];
        
        if (!agent.enabled) {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ 
            status: 'ignored', 
            reason: 'agent_disabled',
            agent: agentName 
          }));
          return;
        }
        
        // Write signal file
        const signalContent = formatSignalContent(alert, agentName);
        await fs.writeFile(agent.signalPath, signalContent);
        
        console.log(`[TradingView] Signal routed to ${agentName}`);
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          status: 'accepted',
          agent: agentName,
          signal: {
            symbol: alert.symbol,
            action: alert.action,
            price: alert.price
          }
        }));
        
      } catch (err) {
        console.error('[TradingView] Error:', err.message);
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ status: 'error', error: err.message }));
      }
    });
    return;
  }
  
  // 404 for unknown routes
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
});

function findAgentForSymbol(symbol) {
  const normalized = symbol.toUpperCase().replace(/[^A-Z]/g, '');
  for (const [name, config] of Object.entries(AGENTS)) {
    const agentSymbol = config.symbol.toUpperCase().replace(/[^A-Z]/g, '');
    if (normalized === agentSymbol || normalized.includes(agentSymbol)) {
      return name;
    }
  }
  return null;
}

function formatSignalContent(alert, agentName) {
  const timestamp = new Date().toISOString();
  return `# Signal - TradingView Alert

**Received:** ${timestamp}

## Alert Data

| Field | Value |
|-------|-------|
| Symbol | ${alert.symbol || 'N/A'} |
| Action | ${alert.action || 'N/A'} |
| Price | ${alert.price || 'N/A'} |
| Strategy | ${alert.strategy || 'N/A'} |
| Timeframe | ${alert.timeframe || 'N/A'} |

## Raw Payload

\`\`\`json
${JSON.stringify(alert, null, 2)}
\`\`\`

---

*Awaiting ${agentName} execution*
`;
}

server.listen(PORT, () => {
  console.log(`[TradingView Webhook] Listening on port ${PORT}`);
  console.log(`[TradingView Webhook] Thor signal path: ${THOR_SIGNAL_PATH}`);
  console.log(`[TradingView Webhook] Agents: ${Object.keys(AGENTS).join(', ')}`);
});

// Handle shutdown
process.on('SIGTERM', () => {
  console.log('[TradingView Webhook] Shutting down...');
  server.close();
  process.exit(0);
});