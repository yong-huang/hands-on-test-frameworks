import { When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { CIWorld, BASE_URL } from '../support/world.ts';

When('探活 SUT 健康接口', async function (this: CIWorld) {
    expect(await this.healthy()).toBe(true);
});

Then('健康接口返回 {int}', async function (this: CIWorld, status: number) {
    const res = await fetch(`${BASE_URL}/api/health`);
    expect(res.status).toBe(status);
});

When('创建一笔 CI 冒烟订单', async function (this: CIWorld) {
    const status = await this.apiCreate(`CI-SMOKE-${Date.now().toString(36)}`);
    expect(status).toBe(201);
});

Then('订单总数增加 1', async function (this: CIWorld) {
    expect(await this.orderCount()).toBeGreaterThan(3);
});

When('重置到种子态', async function (this: CIWorld) {
    await fetch(`${BASE_URL}/api/reset`, {
        method: 'POST',
        headers: { authorization: `Bearer ${Buffer.from('admin:admin').toString('base64')}` },
    });
});

Then('订单总数是 {int}', async function (this: CIWorld, count: number) {
    expect(await this.orderCount()).toBe(count);
});
