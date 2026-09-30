// pages/LoginPage.ts — 登录页页面对象（未走 storageState 的场景用）
import { expect, type Page } from '@playwright/test';

export class LoginPage {
    constructor(private readonly page: Page) {}

    async goto() {
        await this.page.goto('/');
    }

    async login(user: string, password: string) {
        await this.page.getByTestId('login-user').fill(user);
        await this.page.getByTestId('login-pass').fill(password);
        await this.page.getByTestId('login-btn').click();
        await expect(this.page.getByTestId('welcome')).toContainText(user);
    }
}
