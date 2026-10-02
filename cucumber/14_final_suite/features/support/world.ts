// features/support/world.ts — 终极套件 World：双角色会话 + 活文档数据源
import {
    After, AfterAll, Before, BeforeAll, World, setDefaultTimeout, setWorldConstructor,
} from '@cucumber/cucumber';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

export const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:9116';
export type Role = 'admin' | 'customer';
const tokenFor = (role: Role) => Buffer.from(`${role}:${role}`).toString('base64');
const PASSWORD: Record<Role, string> = { admin: 'admin123', customer: 'customer123' };

setDefaultTimeout(15_000);

export class FinalWorld extends World {
    page!: Page;
    context!: BrowserContext;
    role: Role = 'admin';
    /** 场景内创建的订单标题（隔离断言用） */
    lastTitle = '';

    async setRole(role: Role): Promise<Page> {
        this.role = role;
        await this.context.close();
        this.context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL });
        await this.context.addInitScript(([t, r]) => {
            localStorage.setItem('pw-store-auth',
                JSON.stringify({ token: t, role: r, username: r }));
        }, [tokenFor(role), role] as const);
        this.page = await this.context.newPage();
        return this.page;
    }
}

let browser: Browser;

BeforeAll(async function () {
    browser = await chromium.launch();
});

AfterAll(async function () {
    await browser.close();
});

Before(async function (this: FinalWorld) {
    await fetch(`${BASE_URL}/api/reset`, {
        method: 'POST',
        headers: { authorization: `Bearer ${Buffer.from('admin:admin').toString('base64')}` },
    });
    this.context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL });
    await this.context.addInitScript(([t, r]) => {
        localStorage.setItem('pw-store-auth',
            JSON.stringify({ token: t, role: r, username: r }));
    }, [tokenFor('admin'), 'admin'] as const);
    this.page = await this.context.newPage();
});

After(async function (this: FinalWorld) {
    await this.context?.close();
});

setWorldConstructor(FinalWorld);
export { PASSWORD };
