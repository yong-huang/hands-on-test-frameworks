import { When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { ParallelWorld } from '../support/world.ts';

let lastTitle = '';

When('管理员创建自己的订单', async function (this: ParallelWorld) {
    lastTitle = `${this.prefix}-订单`;
    const status = await this.apiCreate(lastTitle);
    expect(status).toBe(201);
    await this.page.goto('');
});

Then('订单列表中恰好存在自己的那 1 笔', async function (this: ParallelWorld) {
    const mine = this.page.getByTestId('order-item').filter({ hasText: lastTitle });
    await expect(mine).toHaveCount(1);
});
