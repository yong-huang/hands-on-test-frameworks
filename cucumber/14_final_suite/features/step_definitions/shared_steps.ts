// shared_steps.ts — 终极套件步骤层：登录/订单/上传，定位器全部收口 pages/
import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { FinalWorld } from '../support/world.ts';
import { StorePage } from '../../pages/store.ts';

const API = process.env.BASE_URL ?? 'http://127.0.0.1:9116';

Given('管理员已登录', async function (this: FinalWorld) {
    await this.page.goto('');
    await expect(this.page.getByTestId('welcome')).toContainText('管理员');
});

Given('打开 pw-store 首页', async function (this: FinalWorld) {
    await this.page.goto('');
});

When('点击退出登录', async function (this: FinalWorld) {
    await this.page.getByTestId('logout').click();
    await expect(this.page.getByTestId('login-form')).toBeVisible();
});

Then('登录表单可见', async function (this: FinalWorld) {
    await expect(this.page.getByTestId('login-form')).toBeVisible();
});

When('以用户名 {string} 密码 {string} 登录', async function (
    this: FinalWorld, user: string, password: string,
) {
    // 不做 goto：登出后的表单就在当前页，reload 会被 addInitScript 重新注入 token
    await this.page.getByTestId('login-user').fill(user);
    await this.page.getByTestId('login-pass').fill(password);
    await this.page.getByTestId('login-btn').click();
});

Then('显示错误提示 {string}', async function (this: FinalWorld, text: string) {
    await expect(this.page.getByTestId('login-error')).toContainText(text);
});

Then('欢迎语包含 {string}', async function (this: FinalWorld, text: string) {
    await expect(this.page.getByTestId('welcome')).toContainText(text);
});

When('以 {string} 打开订单区', async function (this: FinalWorld, role: string) {
    const page = await this.setRole(role as 'admin' | 'customer');
    await page.goto('');
});

Then('删除按钮 {string}', async function (this: FinalWorld, visibility: string) {
    const store = new StorePage(this.page);
    await store.expectSeeded();
    if (visibility === '可见') {
        await expect(store.delButtons().first()).toBeVisible();
    } else {
        await expect(store.delButtons()).toHaveCount(0);
    }
});

When('创建订单 {string}', async function (this: FinalWorld, title: string) {
    const store = new StorePage(this.page);
    await store.create(title);
});

Given('已存在订单 {string}', async function (this: FinalWorld, title: string) {
    const store = new StorePage(this.page);
    await store.create(title);
});

When('删除订单 {string}', async function (this: FinalWorld, title: string) {
    const store = new StorePage(this.page);
    await store.goto();   // 显式导航：防御页面状态漂移
    await store.delete(title);
});

Then('订单列表中存在 {string}', async function (this: FinalWorld, title: string) {
    const store = new StorePage(this.page);
    if (!await store.rows().first().isVisible()) await store.goto();
    await expect(store.row(title)).toHaveCount(1);
});

Then('订单列表中不存在 {string}', async function (this: FinalWorld, title: string) {
    const store = new StorePage(this.page);
    await store.goto();
    await expect(store.row(title)).toHaveCount(0);
});

When('上传文件 {string} 内容为 {string}', async function (
    this: FinalWorld, name: string, content: string,
) {
    const store = new StorePage(this.page);
    await store.upload({
        name,
        mimeType: 'text/plain',
        buffer: Buffer.from(content, 'utf-8'),
    });
});

Then('上传列表中存在 {string}', async function (this: FinalWorld, name: string) {
    const store = new StorePage(this.page);
    await store.openUploadTab();
    const items = await store.uploadList().allTextContents();
    await expect(store.uploadList().filter({ hasText: name })).toHaveCount(1);
});
