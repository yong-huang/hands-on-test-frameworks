// artifacts.spec.ts — lab 12：两条绿用例 + 一条人为失败
// 失败用例是产物体系的"验收标本"：trace / 截图 / 视频 三产物应同时挂在它名下
import { test, expect } from '@playwright/test';

async function login(page: import('@playwright/test').Page) {
    await page.goto('/');
    await page.getByTestId('login-user').fill('admin');
    await page.getByTestId('login-pass').fill('admin123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText('admin');
}

test('订单区正常（绿用例，产物齐但用不上）', async ({ page }) => {
    await login(page);
    await expect(page.getByTestId('order-item').first()).toBeVisible();
});

test('慢加载表格终态（绿用例）', async ({ page }) => {
    await login(page);
    await page.getByTestId('tab-slow').click();
    await page.getByTestId('slow-load').click();
    await expect(page.getByTestId('slow-row')).toHaveCount(3);
});

test('人为失败标本：断言一个不存在的元素', async ({ page }) => {
    await login(page);
    // 故意的失败：页面上永远不会有 data-testid="ghost-element"
    await expect(page.getByTestId('ghost-element')).toBeVisible();
});
