// features/support/world.ts — 与前序 lab 相同的基座（含每场景 reset 隔离）
import {
    After, AfterAll, Before, BeforeAll, World, setDefaultTimeout, setWorldConstructor,
} from '@cucumber/cucumber';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

export const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:9106';
setDefaultTimeout(15_000);

export class GherkinWorld extends World {
    page!: Page;
    context!: BrowserContext;
}

let browser: Browser;

BeforeAll(async function () {
    browser = await chromium.launch();
});

AfterAll(async function () {
    await browser.close();
});

Before(async function (this: GherkinWorld) {
    await fetch(`${BASE_URL}/api/reset`, {
        method: 'POST',
        headers: { authorization: `Bearer ${Buffer.from('admin:admin').toString('base64')}` },
    });
    this.context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL });
    this.page = await this.context.newPage();
});

After(async function (this: GherkinWorld) {
    await this.context?.close();
});

setWorldConstructor(GherkinWorld);
