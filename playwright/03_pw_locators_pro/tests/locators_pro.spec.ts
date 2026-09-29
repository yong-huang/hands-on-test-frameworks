// locators_pro.spec.ts — lab 03：定位引擎深水区十条用例
//   嵌套文档（iframe / Shadow DOM）· 严格模式 · filter 链式收窄 · or() 双保险
// 定位器（locator，"如何找到页面元素"的查询描述）是 E2E 稳定性的第一道闸门。
import { test, expect, type Page } from '@playwright/test';

async function login(page: Page, user = 'admin') {
    await page.goto('/');
    await page.getByTestId('login-user').fill(user);
    await page.getByTestId('login-pass').fill(user === 'admin' ? 'admin123' : 'customer123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText(user);
}

// ---- ① iframe：frameLocator 穿进内嵌文档操作 ----
// iframe（页面内嵌另一个文档的框架）有独立 DOM 树，主文档选择器看不见它，
// 必须经 frameLocator() 换轨到帧内上下文。
test('iframe：帧内标题可见，帧内按钮可连点', async ({ page }) => {
    await login(page);
    await page.getByTestId('tab-embed').click();

    const frame = page.getByTestId('embed-iframe').contentFrame();
    await expect(frame.getByRole('heading', { name: 'iframe 内部面板' })).toBeVisible();

    // 帧内内容模拟第三方页面：只有 id 没有 data-testid——
    // 真实世界的 iframe（广告/客服组件）正是如此，此时 id 是可接受的选择
    const btn = frame.locator('#embed-btn');
    await btn.click();
    await btn.click();
    await expect(frame.locator('#embed-btn')).toContainText('2');
});

// ---- ② Shadow DOM：Playwright 自动穿透 open shadow root ----
// Shadow DOM（挂在元素内部的独立 DOM 子树）对常规 CSS 隐藏，
// 但 Playwright 的定位器默认穿透 open 模式的 shadow 边界，写法零差异。
test('Shadow DOM：穿透点击 shadow 内按钮，驱动主文档计数', async ({ page }) => {
    await login(page);
    await page.getByTestId('tab-embed').click();

    const shadowBtn = page.getByTestId('shadow-host').getByTestId('shadow-btn');
    await shadowBtn.click();
    await shadowBtn.click();
    await shadowBtn.click();

    // 主文档的计数随 shadow 内操作增长（composed 事件穿边界冒泡）
    await expect(page.getByTestId('badge-count')).toHaveText('3');
});

// ---- ③ strict mode：歧义定位器被拒绝，报错列出全部候选 ----
// strict mode（严格模式，定位器命中多个元素时拒绝执行而非静默取第一个）
test('strict mode：locator("button") 命中多个即拒绝执行', async ({ page }) => {
    await login(page);

    const ambiguous = page.locator('button');   // 导航 + 订单区里有一堆按钮
    let message = '';
    try {
        await ambiguous.click();
    } catch (e) {
        message = (e as Error).message;
    }
    expect(message).toMatch(/strict mode violation/);
    expect(message).toMatch(/resolved to \d+ elements/);
});

// ---- ④ 收窄三板斧之一：filter({ hasText }) ----
test('filter：在订单列表里精确定位"机械键盘"那一行', async ({ page }) => {
    await login(page);

    const row = page.getByTestId('order-item').filter({ hasText: '机械键盘' });
    await expect(row).toHaveCount(1);
    await expect(row).toHaveAttribute('data-status', 'shipped');
});

// ---- ⑤ 收窄三板斧之二：区域链式限定 ----
test('链式收窄：先圈定区域，再在区域内找按钮', async ({ page }) => {
    await login(page);

    const createBtn = page.getByTestId('orders-page')
        .getByRole('button', { name: '创建订单' });
    await expect(createBtn).toBeVisible();

    // 布局按钮（导航 tab）不会被误命中——区域限定天然隔离
    await expect(page.getByTestId('orders-page').getByRole('tab')).toHaveCount(0);
});

// ---- ⑥ first/last：有序集合的确定性端点 ----
test('nth 端点：种子列表首尾可断言', async ({ page }) => {
    await login(page);

    const items = page.getByTestId('order-item');
    await expect(items.first()).toContainText('机械键盘');
    await expect(items.last()).toContainText('USB-C 扩展坞');
});

// ---- ⑦ or()：两个可能出现的元素，谁先算谁 ----
// 慢接口场景：点击后先看到 loading，数据到了才看到表格——断言"其中之一可见"
test('or()：loading 与表格的过渡期不断言错', async ({ page }) => {
    await login(page);
    await page.getByTestId('tab-slow').click();
    await page.getByTestId('slow-load').click();

    const outcome = page.getByTestId('slow-loading').or(page.getByTestId('slow-table'));
    await expect(outcome).toBeVisible();               // 过渡期：loading 在
    await expect(page.getByTestId('slow-row')).toHaveCount(3);   // 终态：表格在
});

// ---- ⑧ role + name：无障碍树是最高优先级的定位来源 ----
test('getByRole：按可访问名精确命中导航 tab', async ({ page }) => {
    await login(page);

    const uploadTab = page.getByRole('tab', { name: '上传' });
    await expect(uploadTab).toHaveAttribute('aria-selected', 'false');
    await uploadTab.click();
    await expect(uploadTab).toHaveAttribute('aria-selected', 'true');
});

// ---- ⑨ label 定位：表单元素跟着 <label> 走 ----
test('getByLabel：登录表单按标签文本定位输入框', async ({ page }) => {
    await page.goto('/');

    await page.getByLabel('用户名').fill('customer');
    await page.getByLabel('密码').fill('customer123');
    await page.getByRole('button', { name: '登录' }).click();

    await expect(page.getByTestId('welcome')).toContainText('customer');
});

// ---- ⑩ 帧内 filter：frameLocator 与 filter 组合 ----
test('嵌套组合：帧内元素再走文本过滤', async ({ page }) => {
    await login(page);
    await page.getByTestId('tab-embed').click();

    const frame = page.getByTestId('embed-iframe').contentFrame();
    const para = frame.locator('p').filter({ hasText: '帧穿透定位练习' });
    await expect(para).toBeVisible();
});
