// pages/doc_page.ts — 活文档演示页面对象
import { expect, type Locator, type Page } from '@playwright/test';

export class DocPage {
    private readonly page: Page;
    private readonly root: Locator;

    constructor(page: Page) {
        this.page = page;
        this.root = page.getByTestId('orders-page');
    }

    async goto() {
        await this.page.goto('');
        await this.root.waitFor({ state: 'visible' });
    }

    row(title: string): Locator {
        return this.root.getByTestId('order-item').filter({ hasText: title });
    }

    async create(title: string) {
        if (!await this.root.isVisible()) await this.goto();
        await this.page.getByTestId('order-title').fill(title);
        const resp = this.page.waitForResponse(
            (r) => r.url().includes('/api/orders') && r.request().method() === 'POST',
        );
        await this.page.getByTestId('order-add').click();
        await resp;
    }
}
