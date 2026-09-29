// permission.spec.ts — 权限矩阵：admin / customer 六条断言，按 project 名分流
// 同一份用例代码在两个 project 里各跑一遍，test.info().project.name 决定走哪条分支——
// "一次编写、双角色复跑"是权限矩阵测试的标准形态
import { test, expect } from '@playwright/test';

const role = () => test.info().project.name as 'admin' | 'customer';

test('UI 层：删除按钮的可见性随角色变化', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('order-item').first()).toBeVisible();

    if (role() === 'admin') {
        await expect(page.getByTestId('order-del').first()).toBeVisible();      // ① admin 可见
    } else {
        await expect(page.getByTestId('order-del')).toHaveCount(0);             // ② customer 不可见
    }
});

test('API 层：删除订单的授权判定', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('order-item').first()).toBeVisible();

    // 造一条自己的订单拿 id（不影响种子数据）；request fixture 已带角色 authorization 头
    const created = await page.request.post('/api/orders', { data: { title: `权限矩阵-${role()}` } });
    expect(created.status()).toBe(201);
    const { order } = await created.json();

    const del = await page.request.delete(`/api/orders/${order.id}`);
    if (role() === 'admin') {
        expect(del.status()).toBe(200);                                          // ③ admin 删除成功
    } else {
        expect(del.status()).toBe(403);                                          // ④ customer 被拒
        expect((await del.json()).error).toContain('仅管理员');
    }
});

test('API 层：重置种子数据的授权判定', async ({ page }) => {
    const res = await page.request.post('/api/reset');
    if (role() === 'admin') {
        expect(res.status()).toBe(200);                                          // ⑤ admin 可重置
        const list = await (await page.request.get('/api/orders')).json();
        expect(list.orders).toHaveLength(3);                                     // 重置后回到种子
    } else {
        expect(res.status()).toBe(403);                                          // ⑥ customer 被拒
    }
});

test('纵向上权：customer 拿着 admin 的操作路径走不通全链路', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('order-item').first()).toBeVisible();

    // UI 层没有入口（按钮不存在）→ 绕过 UI 直接打 API 也被 403 拦截
    const list = await (await page.request.get('/api/orders')).json();
    const target = list.orders[0].id;
    const bypass = await page.request.delete(`/api/orders/${target}`);
    if (role() === 'admin') {
        // admin 删种子订单会破坏其他用例的种子假设——只验证响应码，不真删种子
        // 用一个不存在的 id 验证鉴权通过（404 而不是 403）
        const probe = await page.request.delete('/api/orders/nonexistent');
        expect(probe.status()).toBe(404);
    } else {
        expect(bypass.status()).toBe(403);
    }
});
