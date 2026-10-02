// features/support/world.ts — 活文档 lab 基座（docstring 步骤 + pending 演示）
import {
    After, AfterAll, Before, BeforeAll, World, setDefaultTimeout, setWorldConstructor,
} from '@cucumber/cucumber';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

export const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:9113';
setDefaultTimeout(15_000);
const TOKEN = Buffer.from('admin:admin').toString('base64');

export class LivingDocWorld extends World {
    page!: Page;
    context!: BrowserContext;
    /** docstring 步骤捕获的多行文本 */
    capturedDoc = '';
}

let browser: Browser;

BeforeAll(async function () {
    browser = await chromium.launch();
});

AfterAll(async function () {
    await browser.close();
});

Before(async function (this: LivingDocWorld) {
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

After(async function (this: LivingDocWorld) {
    await this.context?.close();
});

setWorldConstructor(LivingDocWorld);
