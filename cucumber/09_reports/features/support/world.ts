// features/support/world.ts — 失败场景自动 attach 截图（报告体系的数据源）
import {
    After, AfterAll, Before, BeforeAll, World, setDefaultTimeout, setWorldConstructor,
} from '@cucumber/cucumber';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

export const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:9110';
setDefaultTimeout(15_000);

export class ReportWorld extends World {
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

Before(async function (this: ReportWorld) {
    this.context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL });
    this.page = await this.context.newPage();
});

// 失败场景才 attach 截图——成功场景不产噪声
// scenario.attach 不在钩子参数类型上——cucumber 13 用 this.attach（World 方法）
After(async function (this: ReportWorld, scenario) {
    if (scenario.result?.status === 'FAILED' && this.page) {
        const shot = await this.page.screenshot();
        await this.attach(shot, { mediaType: 'image/png', fileName: 'failure.png' });
        await this.attach(
            `场景: ${scenario.pickle.name}\n时间: ${new Date().toISOString()}`,
            { mediaType: 'text/plain', fileName: 'context.txt' },
        );
    }
    await this.context?.close();
});

setWorldConstructor(ReportWorld);
