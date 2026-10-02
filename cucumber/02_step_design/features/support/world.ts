// features/support/world.ts — 与 lab 01 相同的 World 基座（系列约定逐步长成公共底座）
import {
    After, AfterAll, Before, BeforeAll, World, setDefaultTimeout, setWorldConstructor,
} from '@cucumber/cucumber';
import { chromium, type Browser, type BrowserContext, type Page } from '@playwright/test';

export const BASE_URL = process.env.BASE_URL ?? 'http://127.0.0.1:9102';

// 步骤级超时：需大于 expect 断言自身的 timeout，否则断言的重试窗口被截断
setDefaultTimeout(15_000);

export class StepDesignWorld extends World {
    page!: Page;
    context!: BrowserContext;
    /** 场景内共享的业务数据（本 lab 先用最朴素的字段，lab 03 系统化） */
    lastError = '';
}

let browser: Browser;

BeforeAll(async function () {
    browser = await chromium.launch();
});

AfterAll(async function () {
    await browser.close();
});

Before(async function (this: StepDesignWorld) {
    // 场景隔离纪律：SUT 是跨场景共享的内存态，先 /api/reset 回种子再开新上下文
    // （否则同名订单跨运行累积，"恰有 N 笔"这类断言必然漂移——本 lab 实测踩坑）
    await fetch(`${BASE_URL}/api/reset`, {
        method: 'POST',
        headers: { authorization: `Bearer ${btoa('admin:admin')}` },
    });
    this.context = await browser.newContext({ locale: 'zh-CN', baseURL: BASE_URL });
    this.page = await this.context.newPage();
});

After(async function (this: StepDesignWorld) {
    await this.context?.close();
});

setWorldConstructor(StepDesignWorld);
