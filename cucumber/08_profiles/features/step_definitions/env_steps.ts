import { Given, Then, When } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { ADMIN_PASS, ADMIN_USER, ProfileWorld } from '../support/world.ts';

Given('打开配置指向的 pw-store 首页', async function (this: ProfileWorld) {
    await this.page.goto('');
});

When('以配置的管理员凭据登录', async function (this: ProfileWorld) {
    await this.page.getByTestId('login-user').fill(ADMIN_USER);
    await this.page.getByTestId('login-pass').fill(ADMIN_PASS);
    await this.page.getByTestId('login-btn').click();
    await expect(this.page.getByTestId('welcome')).toContainText(ADMIN_USER);
});

Then('欢迎语包含配置的用户名', async function (this: ProfileWorld) {
    await expect(this.page.getByTestId('welcome')).toContainText(ADMIN_USER);
});

Then('页面标题包含 pw-store', async function (this: ProfileWorld) {
    await expect(this.page).toHaveTitle(/pw-store/);
});
