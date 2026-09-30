// i18n.spec.ts — 双语文案矩阵：两种 locale 下同一批 key 各断言一次
import { test, expect } from '@playwright/test';

async function login(page: import('@playwright/test').Page, user = 'admin') {
    await page.goto('/');
    await page.getByTestId('login-user').fill(user);
    await page.getByTestId('login-pass').fill(user === 'admin' ? 'admin123' : 'customer123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText(user);
}

test.describe('中文环境（zh-CN）', () => {
    test.use({ locale: 'zh-CN' });

    test('登录页与导航使用中文文案', async ({ page }) => {
        await page.goto('/');
        await expect(page.getByRole('heading', { name: '登录 pw-store' })).toBeVisible();
        await page.getByTestId('login-user').fill('admin');
        await page.getByTestId('login-pass').fill('admin123');
        await page.getByTestId('login-btn').click();

        await expect(page.getByRole('tab', { name: '订单' })).toBeVisible();
        await expect(page.getByRole('tab', { name: '上传' })).toBeVisible();
        await expect(page.getByRole('button', { name: '退出' })).toBeVisible();
    });

    test('订单区中文：创建按钮与状态徽标', async ({ page }) => {
        await login(page);
        await expect(page.getByRole('button', { name: '创建订单' })).toBeVisible();
        await expect(page.getByTestId('status-badge-text').or(page.locator('.status')).first())
            .toBeVisible();
        await expect(page.getByTestId('live-badge')).toContainText('已连接');
    });
});

test.describe('英文环境（en-US）', () => {
    test.use({ locale: 'en-US' });

    test('登录页与导航使用英文文案', async ({ page }) => {
        await page.goto('/');
        await expect(page.getByRole('heading', { name: 'Sign in to pw-store' })).toBeVisible();
        await page.getByTestId('login-user').fill('admin');
        await page.getByTestId('login-pass').fill('admin123');
        await page.getByTestId('login-btn').click();

        await expect(page.getByRole('tab', { name: 'Orders' })).toBeVisible();
        await expect(page.getByRole('tab', { name: 'Upload' })).toBeVisible();
        await expect(page.getByRole('button', { name: 'Sign out' })).toBeVisible();
    });

    test('订单区英文：创建按钮与实时徽标', async ({ page }) => {
        await login(page);
        await expect(page.getByRole('button', { name: 'Create order' })).toBeVisible();
        await expect(page.getByTestId('live-badge')).toContainText('connected');
    });

    test('手动切换语言：en 初始环境 toggle 后整页换中文', async ({ page }) => {
        await login(page);   // en-US 环境下初始为英文
        await expect(page.getByRole('tab', { name: 'Orders' })).toBeVisible();

        await page.getByTestId('lang-toggle').click();
        await expect(page.getByRole('tab', { name: '订单' })).toBeVisible();
        await expect(page.getByTestId('welcome')).toContainText('欢迎');
    });
});
