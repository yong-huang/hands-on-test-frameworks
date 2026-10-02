// pages/checkout_page.ts — 下单页面对象（两套 Gherkin 共用同一实现）
import { expect, type Page } from '@playwright/test';

export class CheckoutPage {
    private readonly page: Page;

    constructor(page: Page) {
        this.page = page;
    }

    async goto() {
        await this.page.goto('');
        await this.page.getByTestId('login-user').fill('admin');
        await this.page.getByTestId('login-pass').fill('admin123');
        await this.page.getByTestId('login-btn').click();
        await expect(this.page.getByTestId('welcome')).toContainText('admin');
    }

    async createOrder(title: string) {
        await this.page.getByTestId('order-title').fill(title);
        const resp = this.page.waitForResponse(
            (r) => r.url().includes('/api/orders') && r.request().method() === 'POST',
        );
        await this.page.getByTestId('order-add').click();
        await resp;
    }

    orderRow(title: string) {
        return this.page.getByTestId('order-item').filter({ hasText: title });
    }
}
