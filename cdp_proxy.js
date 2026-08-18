// CDP Proxy — 反向代理到带调试端口的 Chrome DevTools Protocol
// 端口：默认 3456（可用命令行参数 node cdp_proxy.js <port> 覆盖，便于隔离测试）
// API 契约（严格匹配 fangdi_cdp_proxy_scraper.js）：
//   GET  /                 -> 状态页
//   POST /new?url=...      -> 在 Chrome 新建 tab，返回 { targetId }
//   POST /eval?target=ID   -> 请求体为 JS 表达式，返回 { value }
//   GET  /close?target=ID  -> 关闭该 tab
//
// 依赖：ws 包（已装于托管 node 工作区）；Node 内置 http
// Chrome 侧端点：
//   PUT  http://127.0.0.1:9222/json/new?url=<encoded>  -> { id, webSocketDebuggerUrl }
//   GET  http://127.0.0.1:9222/json/close/<id>          -> 关闭 tab

const http = require('http');
const WebSocket = require('C:\\Users\\huaxi\\.workbuddy\\binaries\\node\\workspace\\node_modules\\ws');

const CHROME = 'http://127.0.0.1:9222';
const PORT = process.argv[2]
  ? parseInt(process.argv[2], 10)
  : (process.env.CDP_PROXY_PORT ? parseInt(process.env.CDP_PROXY_PORT, 10) : 3456);
const EVAL_TIMEOUT = 30000;

// targetId -> webSocketDebuggerUrl
const targets = new Map();

function chromeHttpRequest(method, path, body) {
  return new Promise((resolve, reject) => {
    const url = new URL(CHROME + path);
    const req = http.request(url, {
      method,
      headers: body ? { 'Content-Type': 'application/json' } : {}
    }, (res) => {
      let data = '';
      res.on('data', (c) => { data += c; });
      res.on('end', () => {
        try { resolve(data ? JSON.parse(data) : {}); }
        catch (e) { resolve(data); }
      });
    });
    req.on('error', reject);
    if (body) req.write(typeof body === 'string' ? body : JSON.stringify(body));
    req.end();
  });
}

function evalInTarget(targetId, expression) {
  return new Promise((resolve, reject) => {
    const wsUrl = targets.get(targetId);
    if (!wsUrl) return reject(new Error('unknown targetId: ' + targetId));
    const ws = new WebSocket(wsUrl);
    const msgId = 1;
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      try { ws.close(); } catch (e) {}
      reject(new Error('eval timeout'));
    }, EVAL_TIMEOUT);

    ws.on('open', () => {
      ws.send(JSON.stringify({
        id: msgId,
        method: 'Runtime.evaluate',
        params: { expression, returnByValue: true, awaitPromise: true }
      }));
    });

    ws.on('message', (data) => {
      let msg;
      try { msg = JSON.parse(data.toString()); } catch (e) { return; }
      if (msg.id !== msgId) return; // 忽略其它事件
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      try { ws.close(); } catch (e) {}
      if (msg.error) return reject(new Error(msg.error.message || 'cdp error'));
      const r = msg.result && msg.result.result;
      if (r && (r.subtype === 'error' || (msg.result && msg.result.exceptionDetails))) {
        const desc = (r.description) || (msg.result.exceptionDetails && msg.result.exceptionDetails.text) || 'eval error';
        return reject(new Error(desc));
      }
      resolve(r ? r.value : undefined);
    });

    ws.on('error', (e) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      reject(e);
    });
  });
}

// 新建 tab 后用 CDP Page.navigate 导航（Chrome 150 的 /json/new?url= 已不再导航）
function navigateTab(wsUrl, url) {
  return new Promise((resolve) => {
    let done = false;
    const ws = new WebSocket(wsUrl);
    const finish = () => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      try { ws.close(); } catch (e) {}
      resolve();
    };
    const timer = setTimeout(finish, 15000);
    ws.on('open', () => {
      ws.send(JSON.stringify({ id: 1, method: 'Page.enable' }));
      ws.send(JSON.stringify({ id: 2, method: 'Page.navigate', params: { url } }));
    });
    ws.on('message', (data) => {
      let msg; try { msg = JSON.parse(data.toString()); } catch (e) { return; }
      if (msg.method === 'Page.loadEventFired' || msg.method === 'Page.frameNavigated') finish();
    });
    ws.on('error', finish);
  });
}

const server = http.createServer(async (req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  const u = new URL(req.url, 'http://localhost');
  const send = (code, obj) => {
    res.writeHead(code, { 'Content-Type': 'application/json' });
    res.end(typeof obj === 'string' ? obj : JSON.stringify(obj));
  };

  try {
    if (req.method === 'GET' && u.pathname === '/') {
      res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
      res.end('<h1>CDP Proxy Server</h1><p>状态：运行中</p><p>API：</p><ul>' +
        '<li>GET /new?url=... - 创建新tab</li>' +
        '<li>POST /eval?target=ID - 执行JS（body 为表达式）</li>' +
        '<li>GET /close?target=ID - 关闭tab</li></ul>');
      return;
    }

    if (req.method === 'POST' && u.pathname === '/new') {
      const target = u.searchParams.get('url');
      if (!target) return send(400, { error: 'missing url' });
      const info = await chromeHttpRequest('PUT', '/json/new');
      const id = info && info.id;
      if (!id) return send(500, { error: 'no id from chrome', raw: info });
      targets.set(id, info.webSocketDebuggerUrl);
      await navigateTab(info.webSocketDebuggerUrl, target);
      return send(200, { targetId: id });
    }

    if (req.method === 'POST' && u.pathname === '/eval') {
      const targetId = u.searchParams.get('target');
      let body = '';
      await new Promise((r) => { req.on('data', (c) => { body += c; }); req.on('end', r); });
      const value = await evalInTarget(targetId, body);
      return send(200, { value });
    }

    if (req.method === 'GET' && u.pathname === '/close') {
      const targetId = u.searchParams.get('target');
      await chromeHttpRequest('GET', '/json/close/' + targetId);
      targets.delete(targetId);
      return send(200, { ok: true });
    }

    send(404, { error: 'not found: ' + req.method + ' ' + u.pathname });
  } catch (e) {
    send(500, { error: e.message });
  }
});

server.listen(PORT, () => {
  console.log('[初始化] CDP Proxy 监听 ' + PORT + '（Chrome=' + CHROME + '）');
});
