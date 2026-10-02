// features/support/world.ts — 自定义 World：Cucumber 版的"每场景新上下文"
// 与 @playwright/test 的 fixtures 对应：Before ≈ test-scoped fixture，
// BeforeAll/AfterAll ≈ worker-scoped。cucumber 13 没有内置浏览器管理，这里自建。
import { After, AfterAll, Before, BeforeAll, World, setWorldConstructor } from '@cucumber/cucumber';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

export const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:9101';

// 自定义 World：步骤函数里的 this 就是它。字段公开给所有步骤文件使用。
export class LoginWorld extends World {
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

Before(async function (this: LoginWorld) {
    // locale 钉死中文：Playwright 默认 en-US，而 pw-store 的界面语言跟随浏览器（labs/11 的能力）
    this.context = await browser.newContext({ locale: 'zh-CN' });
    this.page = await this.context.newPage();
});

After(async function (this: LoginWorld) {
    await this.context?.close();   // 场景间隔离：每个场景全新 context，localStorage 互不可见
});

setWorldConstructor(LoginWorld);
