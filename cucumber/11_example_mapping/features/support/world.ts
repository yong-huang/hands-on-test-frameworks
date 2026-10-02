// features/support/world.ts — 与 lab 03 相同的基座（admin 登录态 + reset 隔离）
import {
    After, AfterAll, Before, BeforeAll, World, setDefaultTimeout, setWorldConstructor,
} from '@cucumber/cucumber';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

export const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:9112';
setDefaultTimeout(15_000);
const TOKEN = Buffer.from('admin:admin').toString('base64');

export type Role = 'admin' | 'customer';
const tokenFor = (role: Role) => Buffer.from(`${role}:${role}`).toString('base64');

export class MappingWorld extends World {
    page!: Page;
    context!: BrowserContext;
    /** 当前场景角色（setRole 时更新） */
    role: Role = 'admin';

    /** 以指定角色重建会话（token 与展示字段同源写入） */
    async setRole(role: Role): Promise<Page> {
        this.role = role;   // 同步更新 World 上的角色——Then 步骤的 token 依赖它
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

Before(async function (this: MappingWorld) {
    await fetch(`${BASE_URL}/api/reset`, {
        method: 'POST',
        headers: { authorization: `Bearer ${TOKEN}` },
    });
    this.context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL });
    await this.context.addInitScript((tk) => {
        localStorage.setItem('pw-store-auth',
            JSON.stringify({ token: tk, role: 'admin', username: 'admin' }));
    }, TOKEN);
    this.page = await this.context.newPage();
});

After(async function (this: MappingWorld) {
    await this.context?.close();
});

setWorldConstructor(MappingWorld);
