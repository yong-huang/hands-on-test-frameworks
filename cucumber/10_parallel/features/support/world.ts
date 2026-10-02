// features/support/world.ts — 并行版 World：唯一前缀协议的数据工厂
import {
    After, AfterAll, Before, BeforeAll, World, setDefaultTimeout, setWorldConstructor,
} from '@cucumber/cucumber';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

export const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:9111';
setDefaultTimeout(15_000);

const TOKEN = Buffer.from('admin:admin').toString('base64');

export class ParallelWorld extends World {
    page!: Page;
    context!: BrowserContext;
    /** 本场景的唯一前缀：worker 序号 + 随机数，跨并行/重跑唯一 */
    prefix = `W${process.env.CUCUMBER_WORKER_INDEX ?? 0}-${Date.now().toString(36)}-${Math.floor(Math.random() * 1e6)}`;

    /** API 直打创建订单（毫秒级，不经 UI） */
    async apiCreate(title: string): Promise<number> {
        const res = await fetch(`${BASE_URL}/api/orders`, {
            method: 'POST',
            headers: { 'content-type': 'application/json', authorization: `Bearer ${TOKEN}` },
            body: JSON.stringify({ title }),
        });
        return res.status;
    }
}

let browser: Browser;

BeforeAll(async function () {
    browser = await chromium.launch();
});

AfterAll(async function () {
    await browser.close();
});

Before(async function (this: ParallelWorld) {
    await fetch(`${BASE_URL}/api/reset`, {
        method: 'POST',
        headers: { authorization: `Bearer ${TOKEN}` },
    });
    this.context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL });
    this.page = await this.context.newPage();
    // 登录态注入（admin）
    await this.page.addInitScript((tk) => {
        localStorage.setItem('pw-store-auth',
            JSON.stringify({ token: tk, role: 'admin', username: 'admin' }));
    }, TOKEN);
});

After(async function (this: ParallelWorld) {
    await this.context?.close();
});

setWorldConstructor(ParallelWorld);
