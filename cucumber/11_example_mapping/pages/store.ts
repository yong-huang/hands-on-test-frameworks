import { expect, type Locator, type Page } from '@playwright/test';

export class StorePage {
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

    rows(): Locator {
        return this.root.getByTestId('order-item');
    }

    delButtons(): Locator {
        return this.root.getByTestId('order-del');
    }

    async delete(title: string) {
        await this.row(title).getByTestId('order-del').click();
    }

    async expectSeeded() {
        await expect(this.rows().first()).toBeVisible();
    }
}
