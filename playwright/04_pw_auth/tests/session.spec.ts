// session.spec.ts — 会话行为：零登录直达 + 过期/伪造 token 的降级表现
// 本文件在 admin 与 customer 两个 project 里各跑一遍（配置层 storageState 注入）
import { test, expect, type Page } from '@playwright/test';

test('storageState 免登录：打开首页即已登录，全程零次登录请求', async ({ page }) => {
    let loginCalls = 0;
    page.on('request', (req) => {
        if (req.url().includes('/api/login')) loginCalls += 1;
    });

    await page.goto('/');
    await expect(page.getByTestId('welcome')).toBeVisible();   // 直达登录态，未见登录表单

    // 到订单页再逛一圈，登录请求始终是 0——这就是 setup 预登录的意义
    await page.getByTestId('tab-slow').click();
    await page.getByTestId('tab-orders').click();
    await expect(page.getByTestId('order-item').first()).toBeVisible();
    expect(loginCalls).toBe(0);
});

// 伪造 token 用例单独一档：清空 config 注入的角色头——
// 否则 extraHTTPHeaders 会在网络层用有效 token 覆盖页面发出的伪造头，
// 服务端看到的就不再是"过期会话"（这也演示了 extraHTTPHeaders 的优先级语义）
test.describe('forged session', () => {
    test.use({ extraHTTPHeaders: {} });

    test('会话过期模拟：localStorage 里塞伪造 token，订单接口 401 降级', async ({ page }) => {
        // 先加载（storageState 生效），再覆盖为"形状正确但服务端不认"的登录态，
        // reload 后应用读到伪造值——模拟 token 过期/被吊销后的本地残留
        await page.goto('/');
        await page.evaluate(() => {
            localStorage.setItem('pw-store-auth', JSON.stringify({
                token: btoa('admin:intruder'),
                role: 'admin',
                username: 'intruder',
            }));
        });
        await page.reload();

        await expect(page.getByTestId('welcome')).toContainText('intruder');  // 前端只看本地态

        // 订单接口按服务端权威判定拒绝 → 页面出现 role=alert 错误提示
        await expect(page.getByTestId('orders-error')).toContainText('未登录');
    });
});

test('登出即清场：logout 后回到登录表单，刷新仍是未登录', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('welcome')).toBeVisible();

    await page.getByTestId('logout').click();
    await expect(page.getByTestId('login-form')).toBeVisible();

    await page.reload();
    await expect(page.getByTestId('login-form')).toBeVisible();   // localStorage 已清，刷新不复活
});
