// serial_group.spec.ts — describe.serial：有依赖链的用例强制串行
// 反模式示范区：真实项目里优先改造掉依赖，确实存在的多步流程才用 serial
import { test, expect } from '@playwright/test';

const API = 'http://127.0.0.1:9010';
const TOKEN_AT = 'serial-group-token';

let token: string;

test.beforeAll(async () => {
    const res = await fetch(`${API}/api/login`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' }),
    });
    token = ((await res.json()) as { token: string }).token;
    process.env[TOKEN_AT] = token;
});

// serial：三条用例按声明顺序执行——每条依赖上一条的产物
test.describe.serial('订单生命周期（必须按序）', () => {
    let orderId = '';
    const title = `SERIAL-${Date.now().toString(36)}`;

    test('① 创建', async ({ request }) => {
        const res = await request.post('/api/orders', {
            data: { title },
            headers: { authorization: `Bearer ${token}` },
        });
        expect(res.status()).toBe(201);
        orderId = ((await res.json()) as { order: { id: string } }).order.id;
    });

    test('② 验证存在', async ({ request }) => {
        // 若不按序执行，此处在 ① 之前跑会拿不到 orderId
        expect(orderId, '依赖 ① 的产物').toBeTruthy();
        const res = await request.get('/api/orders', {
            headers: { authorization: `Bearer ${token}` },
        });
        const list = (await res.json()) as { orders: { id: string }[] };
        expect(list.orders.some((o) => o.id === orderId)).toBe(true);
    });

    test('③ 删除', async ({ request }) => {
        expect(orderId, '依赖 ① 的产物').toBeTruthy();
        const res = await request.delete(`/api/orders/${orderId}`, {
            headers: { authorization: `Bearer ${token}` },
        });
        expect(res.status()).toBe(200);
    });
});
