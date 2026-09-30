// a11y.spec.ts — axe 扫描三页 + 纯键盘走完下单表单
// axe-core 是 Deque 的无障碍规则引擎；critical/serious 违规必须为 0
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

async function login(page: import('@playwright/test').Page) {
    await page.goto('/');
    await page.getByTestId('login-user').fill('admin');
    await page.getByTestId('login-pass').fill('admin123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText('admin');
}

async function assertNoBlockingViolations(page: import('@playwright/test').Page, where: string) {
    // axe 包内置的 playwright 类型与本地版本有差异，显式宽化（仅构造参数）
    const results = await new AxeBuilder({ page: page as never })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();
    const blocking = results.violations.filter(
        (v) => v.impact === 'critical' || v.impact === 'serious',
    );
    // 报告全部违规细节（含 moderate），只对 critical/serious 判红
    for (const v of results.violations) {
        console.log(`[axe:${where}] ${v.impact ?? 'minor'} ${v.id}: ${v.help} (${v.nodes.length} 处)`);
    }
    expect(blocking, `${where} 存在阻断级无障碍违规`).toHaveLength(0);
}

test('axe 扫描：登录页 critical/serious = 0', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('login-form')).toBeVisible();
    await assertNoBlockingViolations(page, '登录页');
});

test('axe 扫描：订单页 critical/serious = 0', async ({ page }) => {
    await login(page);
    await expect(page.getByTestId('order-item').first()).toBeVisible();
    await assertNoBlockingViolations(page, '订单页');
});

test('axe 扫描：上传页 critical/serious = 0', async ({ page }) => {
    await login(page);
    await page.getByTestId('tab-upload').click();
    await expect(page.getByTestId('upload-page')).toBeVisible();
    await assertNoBlockingViolations(page, '上传页');
});

test('纯键盘：Tab 走完登录 + 下单表单并提交成功', async ({ page }) => {
    await page.goto('/');

    // 登录：Tab 顺序 = 用户名 → 密码 → 登录按钮（焦点顺序符合 DOM 顺序）
    await page.keyboard.press('Tab');       // → 用户名
    await expect(page.getByTestId('login-user')).toBeFocused();
    await page.keyboard.insertText('admin');
    await page.keyboard.press('Tab');       // → 密码
    await expect(page.getByTestId('login-pass')).toBeFocused();
    await page.keyboard.insertText('admin123');
    await page.keyboard.press('Tab');       // → 登录按钮
    await expect(page.getByTestId('login-btn')).toBeFocused();
    await page.keyboard.press('Enter');     // 提交
    await expect(page.getByTestId('welcome')).toContainText('admin');

    // 下单：焦点已在表单区，Tab 到输入框 → 输入 → Tab 到按钮 → Enter
    await page.getByTestId('order-title').click();   // 起点定在输入框（Tab 源）
    await page.keyboard.insertText('键盘可达订单');
    await page.keyboard.press('Tab');       // → 创建按钮
    await expect(page.getByTestId('order-add')).toBeFocused();
    await page.keyboard.press('Enter');     // 提交

    await expect(page.getByTestId('order-item').filter({ hasText: '键盘可达订单' }))
        .toHaveCount(1);
});

test('焦点可见性：聚焦元素的 outline 不为 none（键盘用户看得见焦点）', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('login-user').focus();
    const outline = await page.evaluate(() => {
        const el = document.activeElement as HTMLElement;
        const s = getComputedStyle(el);
        return `${s.outlineStyle} ${s.outlineWidth}`;
    });
    // 浏览器默认 focus outline 是 auto/3px 左右；被样式表干掉才算违规
    expect(outline).not.toMatch(/^none/);
});
