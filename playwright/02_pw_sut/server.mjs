// server.mjs — pw-store 靶场服务器（labs 32-49 全系列共用的被测系统）
// 单端口 9002 承载四类流量：
//   ① 静态资源（Vite 构建产物 app/dist）  ② JSON API（登录/订单/文件/慢接口）
//   ③ 文件上传下载（raw body，免 multipart 依赖）  ④ WebSocket /ws（订单状态实时广播）
// 状态存内存，进程重启即回到种子数据——对测试来说"重启即重置"是特性不是缺陷。
import { createServer } from 'node:http';
import { createHash, randomUUID } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync, statSync } from 'node:fs';
import { join, dirname, extname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { WebSocketServer } from 'ws';

const ROOT = dirname(fileURLToPath(import.meta.url));
const DIST = join(ROOT, 'app', 'dist');
const UPLOADS = join(ROOT, '.uploads');
const PORT = Number(process.env.PORT || 9002);

mkdirSync(UPLOADS, { recursive: true });

// ---------------------------------------------------------------------------
// 内存数据层
// ---------------------------------------------------------------------------
const USERS = {
    admin:    { password: 'admin123',    role: 'admin' },
    customer: { password: 'customer123', role: 'customer' },
};

let orders = new Map();
const files = new Map();   // name -> { size, sha256 }

function seed() {
    orders = new Map();
    const seedRows = [
        { title: '机械键盘', status: 'shipped' },
        { title: '显示器支架', status: 'paid' },
        { title: 'USB-C 扩展坞', status: 'created' },
    ];
    for (const row of seedRows) {
        const id = randomUUID().slice(0, 8);
        orders.set(id, { id, title: row.title, status: row.status, owner: 'seed', createdAt: Date.now() });
    }
}
seed();

// ---------------------------------------------------------------------------
// 工具
// ---------------------------------------------------------------------------
const MIME = {
    '.html': 'text/html; charset=utf-8', '.js': 'text/javascript', '.css': 'text/css',
    '.svg': 'image/svg+xml', '.png': 'image/png', '.json': 'application/json',
    '.woff2': 'font/woff2', '.ico': 'image/x-icon',
};

function json(res, code, body) {
    res.writeHead(code, { 'content-type': 'application/json' });
    res.end(JSON.stringify(body));
}

function readBody(req) {
    return new Promise((resolve) => {
        const chunks = [];
        req.on('data', (c) => chunks.push(c));
        req.on('end', () => resolve(Buffer.concat(chunks)));
    });
}

// token 形如 base64("role:username")——教学靶场，明文可逆是刻意设计，方便测试断言角色
function auth(req) {
    const header = req.headers.authorization || '';
    if (!header.startsWith('Bearer ')) return null;
    try {
        const [role, name] = Buffer.from(header.slice(7), 'base64').toString().split(':');
        if (!USERS[name] || USERS[name].role !== role) return null;
        return { role, name };
    } catch { return null; }
}

// ---------------------------------------------------------------------------
// WebSocket：订单状态广播（lab 45 的主靶点）
// ---------------------------------------------------------------------------
const sockets = new Set();
const wss = new WebSocketServer({ noServer: true });

function broadcast(payload) {
    const frame = JSON.stringify(payload);
    for (const ws of sockets) {
        if (ws.readyState === 1 /* OPEN */) ws.send(frame);
    }
}

// 订单状态自动演进：created →(2s)→ paid →(2s)→ shipped，每步都广播
// 定时器是真实的异步行为源，给"实时推送"用例提供确定性素材
function scheduleStatus(id) {
    setTimeout(() => {
        const order = orders.get(id);
        if (!order || order.status !== 'created') return;
        order.status = 'paid';
        broadcast({ type: 'order-status', id, status: 'paid', title: order.title });
        setTimeout(() => {
            const o2 = orders.get(id);
            if (!o2 || o2.status !== 'paid') return;
            o2.status = 'shipped';
            broadcast({ type: 'order-status', id, status: 'shipped', title: o2.title });
        }, 2000);
    }, 2000);
}

// ---------------------------------------------------------------------------
// HTTP 服务
// ---------------------------------------------------------------------------
const server = createServer(async (req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    const p = url.pathname;

    // ---- 健康探活（webServer 用）----
    if (p === '/api/health') {
        return json(res, 200, { status: 'ok', zones: ['orders', 'upload', 'slow', 'embed'] });
    }

    // ---- 登录 ----
    if (p === '/api/login' && req.method === 'POST') {
        const { username, password } = JSON.parse((await readBody(req)).toString() || '{}');
        const user = USERS[username];
        if (!user || user.password !== password) return json(res, 401, { error: '用户名或密码错误' });
        const token = Buffer.from(`${user.role}:${username}`).toString('base64');
        return json(res, 200, { token, role: user.role, username });
    }

    // ---- 订单 CRUD（需登录）----
    if (p === '/api/orders' && req.method === 'GET') {
        const user = auth(req);
        if (!user) return json(res, 401, { error: '未登录' });
        return json(res, 200, { orders: [...orders.values()] });
    }

    if (p === '/api/orders' && req.method === 'POST') {
        const user = auth(req);
        if (!user) return json(res, 401, { error: '未登录' });
        const { title } = JSON.parse((await readBody(req)).toString() || '{}');
        if (!title) return json(res, 400, { error: '标题必填' });
        const id = randomUUID().slice(0, 8);
        orders.set(id, { id, title, status: 'created', owner: user.name, createdAt: Date.now() });
        scheduleStatus(id);
        broadcast({ type: 'order-created', id, title });
        return json(res, 201, { order: orders.get(id) });
    }

    // ---- 订单删除：仅 admin（lab 34 权限矩阵的靶点）----
    const delMatch = p.match(/^\/api\/orders\/([\w-]+)$/);
    if (delMatch && req.method === 'DELETE') {
        const user = auth(req);
        if (!user) return json(res, 401, { error: '未登录' });
        if (user.role !== 'admin') return json(res, 403, { error: '仅管理员可删除' });
        if (!orders.has(delMatch[1])) return json(res, 404, { error: '订单不存在' });
        orders.delete(delMatch[1]);
        broadcast({ type: 'order-deleted', id: delMatch[1] });
        return json(res, 200, { ok: true });
    }

    // ---- 重置到种子数据（仅 admin；给测试隔离用）----
    if (p === '/api/reset' && req.method === 'POST') {
        const user = auth(req);
        if (!user || user.role !== 'admin') return json(res, 403, { error: '仅管理员可重置' });
        seed();
        return json(res, 200, { ok: true });
    }

    // ---- 上传：raw body + ?name=（lab 44 的主靶点）----
    if (p === '/api/upload' && req.method === 'PUT') {
        const user = auth(req);
        if (!user) return json(res, 401, { error: '未登录' });
        const name = url.searchParams.get('name');
        if (!name) return json(res, 400, { error: '缺少 name 参数' });
        const body = await readBody(req);
        const safe = name.replace(/[^\w.-]/g, '_');   // 基础路径安全处理
        writeFileSync(join(UPLOADS, safe), body);
        const sha256 = createHash('sha256').update(body).digest('hex');
        files.set(safe, { size: body.length, sha256 });
        return json(res, 201, { name: safe, size: body.length, sha256 });
    }

    // ---- 文件列表 / 下载 ----
    if (p === '/api/files' && req.method === 'GET') {
        const user = auth(req);
        if (!user) return json(res, 401, { error: '未登录' });
        return json(res, 200, {
            files: [...files.entries()].map(([name, meta]) => ({ name, ...meta })),
        });
    }
    const dlMatch = p.match(/^\/api\/files\/([\w.-]+)$/);
    if (dlMatch && req.method === 'GET') {
        const user = auth(req);
        if (!user) return json(res, 401, { error: '未登录' });
        const name = dlMatch[1];
        if (!files.has(name)) return json(res, 404, { error: '文件不存在' });
        const body = readFileSync(join(UPLOADS, name));
        res.writeHead(200, {
            'content-type': 'application/octet-stream',
            'content-disposition': `attachment; filename="${name}"`,
        });
        return res.end(body);
    }

    // ---- 慢接口：1.2s 延迟（lab 17 风格的"等待训练"靶点，本系列给 SlowPanel 用）----
    if (p === '/api/slow-data' && req.method === 'GET') {
        const user = auth(req);
        if (!user) return json(res, 401, { error: '未登录' });
        setTimeout(() => {
            json(res, 200, { rows: [
                { sku: 'A-1001', name: '机械键盘', stock: 12 },
                { sku: 'A-1002', name: '显示器支架', stock: 7 },
                { sku: 'A-1003', name: 'USB-C 扩展坞', stock: 0 },
            ] });
        }, 1200);
        return;
    }

    // ---- 静态资源（Vite 构建产物）----
    let filePath = join(DIST, p === '/' ? 'index.html' : p.slice(1));
    if (!filePath.startsWith(DIST)) return json(res, 403, { error: 'forbidden' });
    try { statSync(filePath); } catch {
        filePath = join(DIST, 'index.html');   // SPA fallback
    }
    try {
        const body = readFileSync(filePath);
        res.writeHead(200, { 'content-type': MIME[extname(filePath)] || 'application/octet-stream' });
        return res.end(body);
    } catch {
        return json(res, 503, { error: '前端未构建：先执行 npx vite build（见 sut_app.sh apply）' });
    }
});

// ---- WebSocket 升级 ----
server.on('upgrade', (req, socket, head) => {
    const url = new URL(req.url, `http://${req.headers.host}`);
    if (url.pathname !== '/ws') return socket.destroy();
    wss.handleUpgrade(req, socket, head, (ws) => {
        sockets.add(ws);
        ws.send(JSON.stringify({ type: 'welcome', zones: sockets.size }));
        ws.on('close', () => sockets.delete(ws));
        ws.on('error', () => sockets.delete(ws));
    });
});

server.listen(PORT, '127.0.0.1', () => {
    console.log(`[pw-store] http://127.0.0.1:${PORT}  (api + ws + static)`);
});
