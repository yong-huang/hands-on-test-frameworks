// fixtures.ts — lab 09 核心：test.extend 组合出"业务语言"的测试夹具
// 用例参数里出现的不再是一堆裸 page，而是 adminPage / ordersPage / orderTitle——
// 搭建脚手架的细节全部收进这里，用例只保留业务动作与断言。
//
// 两层 extend 是 Playwright 的固定套路：
//   第一层 test fixtures（每条用例全新实例）→ 第二层 worker fixtures（整个 worker 一次）。
//   worker 层不能依赖 test 层（page 等）——生命周期层次不能倒置。
import { test as base, type Page } from '@playwright/test';
import { LoginPage } from './pages/LoginPage';
import { OrdersPage } from './pages/OrdersPage';

export type Role = 'admin' | 'customer';

const ACCOUNT: Record<Role, string> = { admin: 'admin123', customer: 'customer123' };

// API 登录拿 token（不走 UI，快且稳；token 是 pw-store 的可逆 base64）
async function apiLogin(role: Role): Promise<string> {
    const res = await fetch('http://127.0.0.1:9009/api/login', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({ username: role, password: ACCOUNT[role] }),
    });
    if (res.status !== 200) throw new Error(`login failed: ${res.status}`);
    const { token } = (await res.json()) as { token: string };
    return token;
}

// 已登录页面：把 token 塞进 localStorage，页面加载即登录态
async function loginAs(page: Page, role: Role) {
    const token = await apiLogin(role);
    await page.addInitScript(([t, r]) => {
        localStorage.setItem('pw-store-auth',
            JSON.stringify({ token: t, role: r, username: r }));
    }, [token, role] as const);
    return page;
}

interface TestFixtures {
    adminPage: Page;
    customerPage: Page;
    orders: OrdersPage;
    loginPage: LoginPage;
    orderTitle: string;
}

interface WorkerFixtures {
    adminToken: string;
}

const testBase = base.extend<TestFixtures>({
    // ---- 角色页面：test-scoped，每条用例全新的登录上下文 ----
    adminPage: async ({ page }, use) => use(await loginAs(page, 'admin')),
    customerPage: async ({ page }, use) => use(await loginAs(page, 'customer')),

    // ---- 页面对象：选择器收口的唯一入口 ----
    orders: ({ page }, use) => use(new OrdersPage(page)),
    loginPage: ({ page }, use) => use(new LoginPage(page)),

    // ---- 唯一标题工厂：并行/重跑不撞数据（lab 10 的基石） ----
    orderTitle: async ({}, use) => use(`POM-${Date.now().toString(36)}-${Math.floor(Math.random() * 1e6)}`),
});

export const test = testBase.extend<{}, WorkerFixtures>({
    // worker 级 token：整个 worker 进程只登录一次，同 worker 的用例共享
    adminToken: [async ({}, use) => use(await apiLogin('admin')), { scope: 'worker' }],
});

export { expect } from '@playwright/test';
export { OrdersPage, LoginPage };
