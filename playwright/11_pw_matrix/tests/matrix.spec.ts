// matrix.spec.ts — lab 11：矩阵与仿真的靶点用例
//   响应式（六 project 全跑）· 深色背景 · locale · timezone · offline · 触屏
import { test, expect } from '@playwright/test';

async function login(page: import('@playwright/test').Page) {
    await page.goto('/');
    await page.getByTestId('login-user').fill('admin');
    await page.getByTestId('login-pass').fill('admin123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText('admin');
}

// ---- ① 响应式：六个 project 各跑一遍，断言"放得下且可操作" ----
test('响应式：登录表单在当前视口完整可见', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('login-form')).toBeVisible();

    // 视口宽度内表单完全展开：横向不溢出（移动端最常见的布局事故）
    const overflow = await page.evaluate(() =>
        document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(2);

    // 登录流程走通：小屏（375px）到桌面（1280px）语义一致
    await page.getByTestId('login-user').fill('admin');
    await page.getByTestId('login-pass').fill('admin123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText('admin');
});

// ---- ② 深色模式：背景非纯白（colorScheme: dark 的 project 才有意义） ----
test('深色模式：页面背景随主题切换', async ({ page }, testInfo) => {
    await page.goto('/');
    await expect(page.getByTestId('login-form')).toBeVisible();

    const isDark = testInfo.project.use.colorScheme === 'dark';
    const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);

    if (isDark) {
        // 深色主题的 body 背景 #0d1117，亮度远低于浅色的 #f6f8fa
        const [r] = (bg.match(/\d+/g) ?? ['255']).map(Number);
        expect(r, `深色 project 期望暗背景，实际 ${bg}`).toBeLessThan(64);
    } else {
        expect(bg).toContain('246');   // 浅色 #f6f8fa 的 R 分量
    }
});

// ---- ③ locale 仿真：en-US 环境下应用显示英文文案 ----
test.use({ locale: 'en-US' });
test('locale：en-US 浏览器语言驱动应用初始文案为英文', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('login-user').fill('admin');
    await page.getByTestId('login-pass').fill('admin123');
    await page.getByTestId('login-btn').click();

    // App 初始语言跟随 navigator.language —— 仿真生效的直接证据
    await expect(page.getByTestId('tab-orders')).toHaveText('Orders');
});
