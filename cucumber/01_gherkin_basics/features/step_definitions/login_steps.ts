// login_steps.ts — 步骤层：把 Gherkin 句子绑定到浏览器动作
// lab 01 刻意把定位器直接写在这里（getByTestId）——收口到页面对象是 lab 02 的课题
import { Given, Then, When } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { BASE_URL, LoginWorld } from '../support/world.ts';

Given('打开 pw-store 首页', async function (this: LoginWorld) {
    await this.page.goto(BASE_URL);
});

When('以用户名 {string} 密码 {string} 登录', async function (
    this: LoginWorld, user: string, password: string,
) {
    await this.page.getByTestId('login-user').fill(user);
    await this.page.getByTestId('login-pass').fill(password);
    await this.page.getByTestId('login-btn').click();
});

Then('页面显示 {string}', async function (this: LoginWorld, text: string) {
    await expect(this.page.getByTestId('welcome')).toContainText(text);
});

Then('页面显示错误提示 {string}', async function (this: LoginWorld, text: string) {
    await expect(this.page.getByTestId('login-error')).toContainText(text);
});

Then('页面显示登录表单', async function (this: LoginWorld) {
    await expect(this.page.getByTestId('login-form')).toBeVisible();
});
