// good_steps.ts — 好版本（声明式）的步骤绑定：一句一业务动作
// 注意 feature 行 "连续创建 2 笔" 与 "连续创建 {int} 笔" 的参数捕获
import { Given, Then, When } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { CheckoutPage } from '../../pages/checkout_page.ts';
import { GherkinWorld } from '../support/world.ts';

Given('管理员已登录 pw-store', async function (this: GherkinWorld) {
    const checkout = new CheckoutPage(this.page);
    await checkout.goto();
});

When('连续创建 {int} 笔 {string} 订单', async function (
    this: GherkinWorld, count: number, title: string,
) {
    const checkout = new CheckoutPage(this.page);
    for (let i = 0; i < count; i++) {
        await checkout.createOrder(title);   // 等待内聚在页面对象里
    }
});

Then('订单列表应包含 {int} 笔 {string}', async function (
    this: GherkinWorld, count: number, title: string,
) {
    await expect(checkout_row(this.page, title)).toHaveCount(count);
});

import type { Page } from '@playwright/test';
function checkout_row(page: Page, title: string) {
    return page.getByTestId('order-item').filter({ hasText: title });
}
