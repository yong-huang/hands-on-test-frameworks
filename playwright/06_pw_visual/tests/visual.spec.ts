// visual.spec.ts — lab 06：视觉回归四条基线
//   登录页整页 · 订单页（mask 动态区）· 表单元素级 · 慢加载表格终态
// 首次运行没有基线：用 --update-snapshots 生成，之后每次运行都是"现在 vs 应然"的比对。
import { test, expect } from '@playwright/test';

async function login(page: import('@playwright/test').Page) {
    await page.goto('/');
    await page.getByTestId('login-user').fill('admin');
    await page.getByTestId('login-pass').fill('admin123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText('admin');
}

test('登录页整页基线：结构稳定，无动态内容', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('login-btn')).toBeVisible();

    // 登录页没有时间戳/列表等动态区，整页截图可直接作为基线
    await expect(page).toHaveScreenshot('login-page.png', { fullPage: true });
});

test('订单页基线：mask 掉会随时间演变的动态区', async ({ page }) => {
    await login(page);

    // 订单状态由服务端定时器自动演进（created→paid→shipped），
    // 连接徽标文本依赖 WS 建连时机——两处都 mask，比对"布局"而不是"数据"
    await expect(page).toHaveScreenshot('orders-page.png', {
        mask: [
            page.getByTestId('order-list'),
            page.getByTestId('live-badge'),
        ],
        fullPage: true,
    });
});

test('订单表单元素级基线：只盯组件本身', async ({ page }) => {
    await login(page);

    // 元素级截图：组件内部像素比对，页面其他区域的改动不会误伤它
    await expect(page.getByTestId('order-form')).toHaveScreenshot('order-form.png');
});

test('慢加载表格终态基线：等数据到齐再截，不给 spinner 出镜', async ({ page }) => {
    await login(page);
    await page.getByTestId('tab-slow').click();
    await page.getByTestId('slow-load').click();

    // 先等终态（3 行渲染完成），截图断言自然落在稳定画面上
    await expect(page.getByTestId('slow-row')).toHaveCount(3);
    await expect(page.getByTestId('slow-table')).toHaveScreenshot('slow-table.png');
});
