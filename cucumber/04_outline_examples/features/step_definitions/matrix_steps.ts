import { Given, Then, When, setDefaultTimeout } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { OutlineWorld } from '../support/world.ts';

setDefaultTimeout(15_000);

Given('打开 pw-store 首页', async function (this: OutlineWorld) {
    await this.page.goto('');
});

When('以用户名 {} 密码 {} 登录', async function (
    this: OutlineWorld, user: string, password: string,
) {
    await this.page.getByTestId('login-user').fill(user);
    await this.page.getByTestId('login-pass').fill(password);
    await this.page.getByTestId('login-btn').click();
});

// 注意：Outline 占位符是纯文本替换——表格值不带引号时 {string} 匹配不上
// （它只认带引号的文本），要用匿名参数 {} 匹配任意文本
Then('登录 {} 且欢迎语或错误提示包含 {}', async function (
    this: OutlineWorld, outcome: string, keyText: string,
) {
    if (outcome === '成功') {
        await expect(this.page.getByTestId('welcome')).toContainText(keyText);
    } else {
        await expect(this.page.getByTestId('login-error')).toContainText(keyText);
    }
});
