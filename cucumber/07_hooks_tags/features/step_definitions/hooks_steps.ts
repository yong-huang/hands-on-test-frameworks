import { Given, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { BASE_URL, HooksWorld } from '../support/world.ts';

Given('打开 pw-store 首页', async function (this: HooksWorld) {
    await this.page.goto(BASE_URL);
});

Then('登录表单可见', async function (this: HooksWorld) {
    await expect(this.page.getByTestId('login-form')).toBeVisible();
});

Then('Before 已执行且记录在 timeline', async function (this: HooksWorld) {
    expect(this.timeline).toContain('Before');
});
