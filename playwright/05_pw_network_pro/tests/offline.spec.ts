// offline.spec.ts — HAR 回放：同样的用户路径，后端可以完全不在线
// routeFromHAR 不带 update：每个请求按 URL+方法在 HAR 里找应答。
// 回放语义注意：同一请求永远拿到同一条录制应答（详见 README Q&A），
// 所以断言落在"每一步的响应正确"，而不是"服务端状态演进"。
import { test, expect } from '@playwright/test';

test('离线回放：登录 → 下单，全程无活后端', async ({ page }) => {
    await page.routeFromHAR('har/pw-store.har');

    await page.goto('/');
    await page.getByTestId('login-user').fill('admin');
    await page.getByTestId('login-pass').fill('admin123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText('admin');

    // 下单请求被 HAR 应答 201——不依赖任何真实服务
    const respPromise = page.waitForResponse(
        (r) => r.url().includes('/api/orders') && r.request().method() === 'POST',
    );
    await page.getByTestId('order-title').fill('HAR 回放下单');
    await page.getByTestId('order-add').click();
    expect((await respPromise).status()).toBe(201);

    // 无错误降级、输入框复位：页面行为与在线时一致
    await expect(page.getByTestId('orders-error')).toHaveCount(0);
    await expect(page.getByTestId('order-title')).toHaveValue('');
});
