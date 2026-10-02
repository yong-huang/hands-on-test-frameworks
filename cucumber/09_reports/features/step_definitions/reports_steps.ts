import { Given, Then, When } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { BASE_URL, ReportWorld } from '../support/world.ts';

Given('打开 pw-store 首页', async function (this: ReportWorld) {
    await this.page.goto(BASE_URL);
});

When('以用户名 {string} 密码 {string} 登录', async function (
    this: ReportWorld, user: string, password: string,
) {
    await this.page.getByTestId('login-user').fill(user);
    await this.page.getByTestId('login-pass').fill(password);
    await this.page.getByTestId('login-btn').click();
});

Then('页面显示 {string}', async function (this: ReportWorld, text: string) {
    await expect(this.page.getByTestId('welcome')).toContainText(text);
});

Then('订单列表可见', async function (this: ReportWorld) {
    await expect(this.page.getByTestId('order-item').first()).toBeVisible();
});
