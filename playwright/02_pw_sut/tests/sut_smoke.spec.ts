// sut_smoke.spec.ts — 靶场自检：登录 + 四大功能区 + 实时通道，逐区走一遍
// 这套用例是 pw-store 的"出厂检验"：后续实验都用它打靶，靶子先自证可打
import { test, expect } from '@playwright/test';

async function login(page: import('@playwright/test').Page, user = 'admin') {
    await page.goto('/');
    await page.getByTestId('login-user').fill(user);
    await page.getByTestId('login-pass').fill(user === 'admin' ? 'admin123' : 'customer123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText(user);
}

test('登录：admin 登录后进入订单区，欢迎语带角色徽标', async ({ page }) => {
    await login(page);
    await expect(page.getByTestId('welcome')).toContainText('管理员');
    await expect(page.getByTestId('orders-page')).toBeVisible();
});

test('登录失败：错误密码出 role=alert 提示', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('login-user').fill('admin');
    await page.getByTestId('login-pass').fill('wrong');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('login-error')).toBeVisible();
});

test('订单区：种子数据可见 + 创建新单 + 实时通道已连接', async ({ page }) => {
    await login(page);
    const items = page.getByTestId('order-item');
    await expect(items.first()).toBeVisible();   // 种子 3 条（服务器内存态，重启即重置）

    const title = `E2E 自检订单-${Date.now() % 100000}`;
    await page.getByTestId('order-title').fill(title);
    await page.getByTestId('order-add').click();
    await expect(items.filter({ hasText: title })).toHaveCount(1);
    await expect(page.getByTestId('live-badge')).toContainText('已连接');
});

test('订单状态实时演进：新单 created → paid（WS 广播驱动）', async ({ page }) => {
    await login(page);
    const title = `状态演进订单-${Date.now() % 100000}`;
    await page.getByTestId('order-title').fill(title);
    await page.getByTestId('order-add').click();

    const row = page.getByTestId('order-item').filter({ hasText: title });
    await expect(row).toHaveAttribute('data-status', 'created');
    await expect(row).toHaveAttribute('data-status', 'paid', { timeout: 5_000 });   // 服务端 2s 后广播
});

test('admin 删除按钮可见；customer 不可见（权限差异 UI 层）', async ({ page }) => {
    await login(page, 'admin');
    await expect(page.getByTestId('order-del').first()).toBeVisible();

    await page.getByTestId('logout').click();
    await login(page, 'customer');
    await expect(page.getByTestId('order-del')).toHaveCount(0);
});

test('上传区：传 2 个文件全部出现在列表', async ({ page }) => {
    await login(page);
    await page.getByTestId('tab-upload').click();

    // 按 name 过滤断言而非全量计数：服务器文件列表是累积的（observe ② 可能已传过探活文件）
    await page.getByTestId('upload-input').setInputFiles([
        { name: 'smoke-a.txt', mimeType: 'text/plain', buffer: Buffer.from('alpha') },
        { name: 'smoke-b.txt', mimeType: 'text/plain', buffer: Buffer.from('beta!') },
    ]);
    const items = page.getByTestId('file-item');
    await expect(items.filter({ hasText: 'smoke-a.txt' })).toHaveCount(1);
    await expect(items.filter({ hasText: 'smoke-b.txt' })).toHaveCount(1);
});

test('慢加载区：loading 出现后表格 3 行（自动等待覆盖 1.2s 接口）', async ({ page }) => {
    await login(page);
    await page.getByTestId('tab-slow').click();
    await page.getByTestId('slow-load').click();

    await expect(page.getByTestId('slow-loading')).toBeVisible();      // loading 态先出现
    await expect(page.getByTestId('slow-row')).toHaveCount(3);          // 断言自动等到数据
});

test('嵌入区：iframe 内标题可见 + shadow 按钮点击驱动主文档计数', async ({ page }) => {
    await login(page);
    await page.getByTestId('tab-embed').click();

    await expect(page.getByTestId('embed-iframe').contentFrame()
        .getByRole('heading', { name: 'iframe 内部面板' })).toBeVisible();

    const shadowBtn = page.getByTestId('shadow-host').getByTestId('shadow-btn');
    await shadowBtn.click();
    await shadowBtn.click();
    await expect(page.getByTestId('badge-count')).toHaveText('2');
});
