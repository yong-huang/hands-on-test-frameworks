// features/support/world.ts — 从环境变量读 SUT 地址与账号（profile 注入）
import {
    After, AfterAll, Before, BeforeAll, World, setDefaultTimeout, setWorldConstructor,
} from '@cucumber/cucumber';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

// 环境变量三件套：profile 决定它们的值，World 只管消费
export const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:9108';
export const ADMIN_USER = process.env.ADMIN_USER ?? 'admin';
export const ADMIN_PASS = process.env.ADMIN_PASS ?? 'admin123';
setDefaultTimeout(15_000);

export class ProfileWorld extends World {
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

Before(async function (this: ProfileWorld) {
    this.context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL });
    this.page = await this.context.newPage();
});

After(async function (this: ProfileWorld) {
    await this.context?.close();
});

setWorldConstructor(ProfileWorld);
