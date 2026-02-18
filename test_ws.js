const WebSocket = require('ws');

const tests = [
  { id: 'openclaw', mode: 'app' },
  { id: 'openclaw', mode: 'ui' },
  { id: 'openclaw', mode: 'web' },
  { id: 'app', mode: 'app' },
  { id: 'ui', mode: 'app' },
  { id: 'web', mode: 'app' },
  { id: 'browser', mode: 'app' },
  { id: 'client', mode: 'app' },
];

async function testOne(cfg) {
  return new Promise((resolve) => {
    const ws = new WebSocket('ws://127.0.0.1:18789');
    let resolved = false;
    
    ws.on('open', () => {
      ws.send(JSON.stringify({
        type: 'req',
        id: 'test',
        method: 'connect',
        params: {
          minProtocol: 3,
          maxProtocol: 3,
          client: { id: cfg.id, version: '1.0.0', platform: 'web', mode: cfg.mode },
          locale: 'en-US',
          userAgent: 'test'
        }
      }));
    });
    
    ws.on('message', (data) => {
      const msg = JSON.parse(data.toString());
      if (msg.type === 'res' && msg.id === 'test') {
        if (!resolved) {
          resolved = true;
          ws.close();
          if (msg.ok) {
            console.log('SUCCESS:', cfg);
          } else {
            console.log('FAIL:', cfg, '-', msg.error?.message);
          }
          resolve();
        }
      }
    });
    
    ws.on('error', () => { if (!resolved) { resolved = true; resolve(); }});
    ws.on('close', () => { if (!resolved) { resolved = true; resolve(); }});
    setTimeout(() => { if (!resolved) { resolved = true; ws.close(); resolve(); }}, 3000);
  });
}

async function run() {
  console.log('Testing specific combinations...\n');
  for (const test of tests) {
    await testOne(test);
    await new Promise(r => setTimeout(r, 500));
  }
}

run();
