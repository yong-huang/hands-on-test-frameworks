// features/support/world.ts — ⛓️ 本 lab 主角：类型安全 World + API 预登录 + 场景隔离
// 三个机制：setWorldConstructor（类型字段）、Before（每场景装备）、/api/reset（隔离）
import {
    After, AfterAll, Before, BeforeAll, World, setDefaultTimeout, setWorldConstructor,
} from '@cucumber/cucumber';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

export const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:9103';
setDefaultTimeout(15_000);

export type Role = 'admin' | 'customer';
const PASSWORD: Record<Role, string> = { admin: 'admin123', customer: 'customer123' };
// pw-store 的 token 是可逆 base64（靶场刻意设计），构造登录态零成本
const tokenFor = (role: Role, name: string) => Buffer.from(`${role}:${name}`).toString('base64');

export class SessionWorld extends World {
    page!: Page;
    context!: BrowserContext;
    /** 当前场景的角色（默认 admin） */
    role: Role = 'admin';
    /** 已执行的场景序号：验证隔离性的探针数据 */
    createdTitles: string[] = [];

    /** 以指定角色装备全新登录态页面（token 直写 localStorage，零 UI 登录成本） */
    async asRole(role: Role): Promise<Page> {
        this.role = role;
        await this.context.close();
        this.context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL });
        // localStorage 里的 role/username 必须与 token 一致——UI 展示读前者，API 鉴权读后者
        await this.context.addInitScript(([t, r]) => {
            localStorage.setItem('pw-store-auth',
                JSON.stringify({ token: t, role: r, username: 'admin' }));
        }, [tokenFor(role, 'admin'), role] as const);
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

Before(async function (this: SessionWorld) {
    // 场景隔离：SUT 内存态先回种子（admin /api/reset），再开全新上下文
    const res = await fetch(`${BASE_URL}/api/reset`, {
        method: 'POST',
        headers: { authorization: `Bearer ${tokenFor('admin', 'admin')}` },
    });
    if (res.status !== 200) throw new Error(`reset failed: ${res.status}`);

    this.context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL });
    this.page = await this.context.newPage();
    this.createdTitles = [];
});

After(async function (this: SessionWorld) {
    await this.context?.close();
});

setWorldConstructor(SessionWorld);
