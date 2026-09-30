// flaky.spec.ts — lab 13：两类注入 flaky + 三种治理武器
//   注入①  预热型：第一次必红、重试必绿（对应"环境预热"类偶发）
//   注入②  路由型：首次尝试注入 500（对应"后端偶发抖动"），重试放行
//   武器    retries 档案 · expect.poll/toPass 最终一致 · test.info().retry 分支
import { test, expect } from '@playwright/test';

const API = 'http://127.0.0.1:9013';

async function login(page: import('@playwright/test').Page) {
    await page.goto('/');
    await page.getByTestId('login-user').fill('admin');
    await page.getByTestId('login-pass').fill('admin123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText('admin');
}

// ---- 注入①：预热型 flaky（标注 test.flaky：重试通过也在报告里留案底） ----
test('注入① 预热型：首次必红，重试绿（已标 flaky）', async ({ page }, testInfo) => {
    // 本版本的 flaky 状态由"重试后通过"自动判定并进报告；
    // 这里再手动挂一条注解，把已知偶发的原因写进案底
    testInfo.annotations.push({ type: 'flaky', description: '预热型偶发：冷启动首跑必红' });
    await login(page);

    if (testInfo.retry === 0) {
        await expect(page.getByTestId('ghost-cold-start')).toBeVisible();
    }
    await expect(page.getByTestId('order-item').first()).toBeVisible();
});

// ---- 注入②：路由型 flaky（首次尝试注入 500，重试放行真实请求） ----
test('注入② 偶发 500：重试后恢复（治理对照）', async ({ page }, testInfo) => {
    const inject = testInfo.retry === 0;
    await page.route('**/api/orders', async (route) => {
        if (inject) {
            await route.fulfill({
                status: 500,
                contentType: 'application/json',
                body: '{"error":"偶发抖动"}',
            });
        } else {
            await route.fallback();
        }
    });

    await login(page);
    // 首次尝试：500 注入让列表加载失败 → 断言红 → 重试时抖动已过 → 绿
    if (inject) {
        await expect(page.getByTestId('orders-error')).toContainText('偶发抖动');
    }
    // 无条件断言核心路径：这让"注入的失败"成为真实的 flaky（首跑红重试绿）
    await expect(page.getByTestId('order-item').first()).toBeVisible({ timeout: 8_000 });
});

// ---- 武器①：expect().toPass——异步最终一致的标准姿势（5s 内收敛） ----
test('toPass：API 造单后最终一致（5s 窗口内收敛）', async ({ page }) => {
    await login(page);

    const title = `POLL-${Date.now().toString(36)}`;
    const token = Buffer.from('admin:admin').toString('base64');
    await fetch(`${API}/api/orders`, {
        method: 'POST',
        headers: { 'content-type': 'application/json', authorization: `Bearer ${token}` },
        body: JSON.stringify({ title }),
    });

    const start = Date.now();
    await expect(async () => {
        const res = await fetch(`${API}/api/orders`, {
            headers: { authorization: `Bearer ${token}` },
        });
        const list = (await res.json()) as { orders: { title: string }[] };
        expect(list.orders.some((o) => o.title === title)).toBe(true);
    }).toPass({ timeout: 5_000 });
    expect(Date.now() - start).toBeLessThan(5_000);

    // UI 侧同步验证：WS 推送刷新后的列表也含有它
    await expect(page.getByTestId('order-item').filter({ hasText: title }))
        .toHaveCount(1, { timeout: 5_000 });
});

// ---- 武器②：retry 分支——首次走全量，重试只验关键路径（省时间省暴露面） ----
test('retry 分支：首次全量回归，重试只验关键路径', async ({ page }, testInfo) => {
    await login(page);

    if (testInfo.retry === 0) {
        await page.getByTestId('tab-slow').click();
        await page.getByTestId('slow-load').click();
        await expect(page.getByTestId('slow-row')).toHaveCount(3);
    }
    await page.getByTestId('tab-orders').click();
    await expect(page.getByTestId('order-item').first()).toBeVisible();
});
