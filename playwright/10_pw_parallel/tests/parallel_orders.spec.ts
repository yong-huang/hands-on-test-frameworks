// parallel_orders.spec.ts — 20 条订单用例全并行：唯一前缀数据证明零串号
// 隔离策略：每条用例用自己的唯一标题创建订单，只断言自己那行——
// 并行下别人的数据变来变去与我无关（数据前缀隔离法）
import { test, expect } from '@playwright/test';

const API = 'http://127.0.0.1:9010';

async function apiLogin() {
    const res = await fetch(`${API}/api/login`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ username: 'admin', password: 'admin123' }),
    });
    return ((await res.json()) as { token: string }).token;
}

// 纯 API 创建订单：并行用例尽量少走 UI，速度与稳定性都更好
async function apiCreate(token: string, title: string) {
    const res = await fetch(`${API}/api/orders`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', authorization: `Bearer ${token}` },
        body: JSON.stringify({ title }),
    });
    expect(res.status).toBe(201);
    return (await res.json()) as { order: { id: string; status: string } };
}

// worker 级 token：4 个 worker 各登录一次，20 条用例共享
let tokenCache: string | undefined;
test.beforeAll(async () => {
    tokenCache = await apiLogin();
});

for (let i = 0; i < 20; i++) {
    test(`并行订单 ${String(i).padStart(2, '0')}：创建并只认自己的行`, async ({ page }) => {
        const title = `W${test.info().workerIndex}-N${String(i).padStart(2, '0')}-${Date.now().toString(36)}`;
        const { order } = await apiCreate(tokenCache!, title);

        // 浏览器侧登录态：API 造的 token 注入 localStorage，页面加载即登录
        await page.addInitScript((tk) => {
            localStorage.setItem('pw-store-auth',
                JSON.stringify({ token: tk, role: 'admin', username: 'admin' }));
        }, tokenCache);

        // toPass 包裹"导航 + 找行"整体重试：列表带分页（lab 17），
        // 我的行可能在第 2 页——当前页找不到就翻页，整段失败重来
        const mine = page.getByTestId('order-item').filter({ hasText: title });
        await expect(async () => {
            await page.goto('/');
            if ((await mine.count()) === 0) {
                const next = page.getByTestId('page-next');
                if (await next.isEnabled()) await next.click();
            }
            await expect(mine).toHaveCount(1);
        }).toPass({ timeout: 15_000 });
        await expect(mine).toHaveAttribute('data-order-id', order.id);
    });
}
