// shard_pool.spec.ts — 40 条轻量 API 用例：分片池的标准负载
// 设计取舍（实测记录在 README）：刻意 API-only、单条 ~20ms——
// 分片的价值在"套件总时长 >> 单分片启动开销"的真实 CI 场景；
// 本地轻套件的分片对照数据（770ms vs 740ms）如实展示开销占比。
import { test, expect } from '@playwright/test';

const API = 'http://127.0.0.1:9018';
const AUTH: Record<string, string> = {
    'content-type': 'application/json',
    authorization: `Bearer ${Buffer.from('admin:admin').toString('base64')}`,
};

for (let i = 0; i < 40; i++) {
    test(`分片池 ${String(i).padStart(2, '0')}: 创建 + 回读一致`, async ({ request }) => {
        const title = `SHARD-${String(i).padStart(2, '0')}-${Date.now().toString(36)}`;
        const created = await request.post('/api/orders', { data: { title }, headers: AUTH });
        expect(created.status()).toBe(201);

        const list = await (await request.get('/api/orders', { headers: AUTH })).json();
        expect((list as { orders: { title: string }[] }).orders
            .some((o) => o.title === title)).toBe(true);
    });
}
