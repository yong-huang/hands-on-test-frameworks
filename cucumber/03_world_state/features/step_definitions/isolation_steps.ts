import { Given, Then, When } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { SessionWorld } from '../support/world.ts';
import { StorePage } from '../../pages/store.ts';

When('管理员创建订单 {string}', async function (this: SessionWorld, title: string) {
    const page = await this.asRole('admin');
    const store = new StorePage(page);
    await store.goto();
    await store.create(title);
    this.createdTitles.push(title);
});

Then('订单列表中存在 {string}', async function (this: SessionWorld, title: string) {
    const store = new StorePage(this.page);
    await store.goto();
    await expect(store.row(title)).toHaveCount(1);
});

Then('订单列表中不存在 {string}', async function (this: SessionWorld, title: string) {
    const store = new StorePage(this.page);
    await store.goto();
    await expect(store.row(title)).toHaveCount(0);
});

When('以 {string} 角色打开订单区', async function (this: SessionWorld, role: string) {
    await this.asRole(role as 'admin' | 'customer');
    const store = new StorePage(this.page);
    await store.goto();
});

Then('界面显示顾客身份', async function (this: SessionWorld) {
    await expect(this.page.getByTestId('welcome')).toContainText('顾客');
});

Then('界面显示管理员身份', async function (this: SessionWorld) {
    await expect(this.page.getByTestId('welcome')).toContainText('管理员');
});

Then('admin 可见删除按钮', async function (this: SessionWorld) {
    await expect(this.page.getByTestId('order-del').first()).toBeVisible();
});
