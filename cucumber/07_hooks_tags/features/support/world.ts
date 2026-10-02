// features/support/world.ts — hooks 时序演示World：四类钩子各打一行标记
import {
    After, AfterAll, Before, BeforeAll, World, setDefaultTimeout, setWorldConstructor,
} from '@cucumber/cucumber';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

export const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:9107';
setDefaultTimeout(15_000);

export class HooksWorld extends World {
    page!: Page;
    context!: BrowserContext;
    /** 钩子时序标记（After 里断言用） */
    timeline: string[] = [];
}

let browser: Browser;

BeforeAll(async function () {
    console.log('[hooks] BeforeAll —— 整个套件一次');
    browser = await chromium.launch();
});

AfterAll(async function () {
    console.log('[hooks] AfterAll —— 整个套件一次');
    await browser.close();
});

Before(async function (this: HooksWorld, scenario) {
    console.log(`[hooks] Before —— 场景「${scenario.pickle.name}」开始`);
    this.context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL });
    this.page = await this.context.newPage();
    this.timeline = ['Before'];
});

After(async function (this: HooksWorld, scenario) {
    console.log(`[hooks] After —— 场景「${scenario.pickle.name}」结束（${scenario.result?.status}）`);
    await this.context?.close();
});

setWorldConstructor(HooksWorld);
