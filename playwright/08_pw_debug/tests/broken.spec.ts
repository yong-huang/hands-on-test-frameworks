// broken.spec.ts — lab 08 教学素材：三条"故意写坏"的用例，每条一种典型根因
// 这个套件默认就是红的——本实验不修它，而是练习用 trace viewer / UI Mode 找根因。
// 根因答案写在 DEBUGGING.md（先自己查，再看答案）。
import { test, expect, type Page } from '@playwright/test';

async function login(page: Page) {
    await page.goto('/');
    await page.getByTestId('login-user').fill('admin');
    await page.getByTestId('login-pass').fill('admin123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText('admin');
}

// 病例一：定位器写错（testid 拼错一个字母）——典型症状：element(s) not found
test('病例一：定位器拼写错误', async ({ page }) => {
    await login(page);
    // 正确是 order-title，这里写成 order-titel
    await page.getByTestId('order-titel').fill('调试实验室订单');
    await page.getByTestId('order-add').click();
    await expect(page.getByTestId('order-item').filter({ hasText: '调试实验室订单' }))
        .toHaveCount(1);
});

// 病例二：非等待 API 拿瞬时值——典型症状：数字对不上，"看起来应该对"
// count() 是立即查询：不发重试，拿到的是"此刻"的行数
test('病例二：立即查询代替 web-first 断言', async ({ page }) => {
    await login(page);
    await page.getByTestId('tab-slow').click();
    await page.getByTestId('slow-load').click();

    // 点击后立刻数行数：接口 1.2s 后才返回，此刻是 0
    const rows = await page.getByTestId('slow-row').count();
    expect(rows).toBe(3);
});

// 病例三：断言基于过时的世界观——典型症状：恒红，重试也没用
test('病例三：断言了与业务演进矛盾的状态', async ({ page }) => {
    await login(page);
    await page.getByTestId('order-title').fill('状态会演进的订单');
    await page.getByTestId('order-add').click();

    const row = page.getByTestId('order-item').filter({ hasText: '状态会演进的订单' });
    // 服务端 2 秒后把 created 推到 paid；先等 paid 到来……
    await expect(row).toHaveAttribute('data-status', 'paid', { timeout: 8_000 });
    // ……再回头断言"还是 created"——世界已经往前走了，这条永远红
    await expect(row).toHaveAttribute('data-status', 'created');
});
