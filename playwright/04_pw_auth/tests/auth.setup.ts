// auth.setup.ts — setup 项目：每个角色走一遍真实 UI 登录，登录态落盘
// 这两份 storageState 之后被 admin / customer 两个 project 复用：
// 全套件每角色的登录请求只出现这一次（脚本输出里可见 2 条 setup 用例）
import { test as setup, expect } from '@playwright/test';

const ACCOUNTS = [
    { user: 'admin', password: 'admin123' },
    { user: 'customer', password: 'customer123' },
] as const;

for (const { user, password } of ACCOUNTS) {
    setup(`login once as ${user}`, async ({ page }) => {
        await page.goto('/');
        await page.getByTestId('login-user').fill(user);
        await page.getByTestId('login-pass').fill(password);
        await page.getByTestId('login-btn').click();
        await expect(page.getByTestId('welcome')).toContainText(user);

        // 登录态（localStorage 里的 token + cookies）写入 project 配置指向的文件
        await page.context().storageState({ path: `.auth/${user}.json` });
    });
}
