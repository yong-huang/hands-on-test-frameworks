// shared_steps.ts — 坏版本（命令式）的步骤绑定：每个 UI 微动作一个步骤
import { Given, When, Then } from '@cucumber/cucumber';
import { CheckoutPage } from '../../pages/checkout_page.ts';
import { GherkinWorld } from '../support/world.ts';

Given('打开页面并登录admin账号', async function (this: GherkinWorld) {
    const checkout = new CheckoutPage(this.page);
    await checkout.goto();
});

When('在订单输入框输入 {string}', async function (this: GherkinWorld, title: string) {
    await this.page.getByTestId('order-title').fill(title);
});

When('再次在订单输入框输入 {string}', async function (this: GherkinWorld, title: string) {
    await this.page.getByTestId('order-title').fill(title);
});

When('点击订单添加按钮', async function (this: GherkinWorld) {
    await this.page.getByTestId('order-add').click();
    await this.page.waitForTimeout(1000);   // 命令式版本典型的裸等待
});

When('再次点击订单添加按钮', async function (this: GherkinWorld) {
    await this.page.getByTestId('order-add').click();
    await this.page.waitForTimeout(1000);
});

When('等待1秒', async function (this: GherkinWorld) {
    await this.page.waitForTimeout(1000);
});

Then('检查页面上出现 {string} 并且出现2次', async function (
    this: GherkinWorld, title: string,
) {
    const rows = await this.page.getByTestId('order-item').allTextContents();
    if (rows.filter((r) => r.includes(title)).length < 2) {
        throw new Error(`期望 2 笔 ${title}，实际 ${rows.filter((r) => r.includes(title)).length} 笔`);
    }
});
