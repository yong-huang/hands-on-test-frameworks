// network_pro.spec.ts — 网络注入四件套（需要真实后端的场景）
//   ① 500 注入 → 错误 UI   ② 3s 慢接口 → loading 态   ③ 断连 → 降级提示   ④ waitForResponse
// route 回调是网络层的"安检口"：可以放行（continue）、改写（fulfill）、拦截（abort）。
import { test, expect } from '@playwright/test';

async function login(page: import('@playwright/test').Page) {
    await page.goto('/');
    await page.getByTestId('login-user').fill('admin');
    await page.getByTestId('login-pass').fill('admin123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText('admin');
}

test('500 注入：订单接口挂了，页面出现正确错误提示', async ({ page }) => {
    await login(page);

    // 拦截下一次 GET /api/orders，伪造 500 应答（不打真实后端）
    await page.route('**/api/orders', async (route) => {
        await route.fulfill({
            status: 500,
            contentType: 'application/json',
            body: JSON.stringify({ error: '服务开小差了' }),
        });
    });
    await page.reload();

    await expect(page.getByTestId('orders-error')).toContainText('服务开小差了');
});

test('3s 慢接口注入：loading 态真实可见，数据到达后表格渲染', async ({ page }) => {
    await login(page);
    await page.getByTestId('tab-slow').click();

    // 放行真实请求，但人为加 3 秒延迟——模拟"接口偶尔很慢"
    await page.route('**/api/slow-data', async (route) => {
        const response = await route.fetch();          // 先拿真实应答
        await new Promise((r) => setTimeout(r, 3000)); // 压住 3 秒
        await route.fulfill({ response });
    });

    await page.getByTestId('slow-load').click();
    await expect(page.getByTestId('slow-loading')).toBeVisible();   // 延迟窗口内 loading 在
    await expect(page.getByTestId('slow-row')).toHaveCount(3);      // 数据到达后表格在
});

test('断连注入：连接被拒，页面降级到错误提示而不是崩死', async ({ page }) => {
    await login(page);

    await page.route('**/api/orders', (route) => route.abort('connectionrefused'));
    await page.reload();

    await expect(page.getByTestId('orders-error')).toBeVisible();
});

test('waitForResponse：下单与响应断言同帧对齐', async ({ page }) => {
    await login(page);

    // 先挂好响应等待，再触发动作——竞态写法的标准姿势（先等后动）
    const respPromise = page.waitForResponse(
        (r) => r.url().includes('/api/orders') && r.request().method() === 'POST',
    );
    await page.getByTestId('order-title').fill('waitForResponse 下单');
    await page.getByTestId('order-add').click();

    const resp = await respPromise;
    expect(resp.status()).toBe(201);
    expect((await resp.json()).order.title).toBe('waitForResponse 下单');
});
