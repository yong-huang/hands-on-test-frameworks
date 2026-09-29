// server.mjs — lab 31 演示服务器：静态页 + 两个带延迟的 JSON 接口
// 用 Node 内置 http，不引框架：本 lab 的主角是测试栈，不是服务器
import { createServer } from 'node:http';
import { readFileSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = dirname(fileURLToPath(import.meta.url));
const PORT = Number(process.env.PORT || 9001);

const ITEMS = ['机械键盘', '显示器支架', 'USB-C 扩展坞'];

const server = createServer((req, res) => {
    const url = new URL(req.url, `http://${req.headers.host}`);

    // 接口一：列表查询，服务端延迟 800ms —— 制造"异步渲染窗口"给自动等待演示
    if (url.pathname === '/api/items') {
        setTimeout(() => {
            res.writeHead(200, { 'content-type': 'application/json' });
            res.end(JSON.stringify({ items: ITEMS }));
        }, 800);
        return;
    }

    // 接口二：表单提交，延迟 300ms 后返回确认号
    if (url.pathname === '/api/subscribe' && req.method === 'POST') {
        let body = '';
        req.on('data', (c) => (body += c));
        req.on('end', () => {
            const email = decodeURIComponent(body.replace('email=', '')) || 'anonymous';
            setTimeout(() => {
                res.writeHead(200, { 'content-type': 'application/json' });
                res.end(JSON.stringify({ ok: true, ticket: `SUB-${email.length}` }));
            }, 300);
        });
        return;
    }

    if (url.pathname === '/api/health') {
        res.writeHead(200, { 'content-type': 'application/json' });
        res.end(JSON.stringify({ status: 'ok' }));
        return;
    }

    // 静态文件：只服务根路径的演示页
    if (url.pathname === '/' || url.pathname === '/index.html') {
        res.writeHead(200, { 'content-type': 'text/html; charset=utf-8' });
        res.end(readFileSync(join(ROOT, 'static', 'index.html')));
        return;
    }

    res.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
    res.end('not found');
});

server.listen(PORT, '127.0.0.1', () => {
    console.log(`[lab31] demo server on http://127.0.0.1:${PORT}`);
});
