// pages/login_page.ts — 登录页面对象
// 注意：node 22 的 TS strip 模式不支持构造器参数属性（constructor(private x)），
// 字段一律显式声明并赋值
import { expect, type Page } from '@playwright/test';

export class LoginPage {
    private readonly page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    async goto() {
        await this.page.goto('');
        await expect(this.page.getByTestId('login-form')).toBeVisible();
    }

    async login(user: string, password: string) {
        await this.page.getByTestId('login-user').fill(user);
        await this.page.getByTestId('login-pass').fill(password);
        await this.page.getByTestId('login-btn').click();
        await expect(this.page.getByTestId('welcome')).toContainText(user);
    }
}
