// pages/store.ts — 终极套件页面对象（覆盖登录/订单/上传三区）
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

    /** 确保已在订单页：所有定位/操作方法的公共前置（防御性导航） */
    private async ensure() {
        if (!await this.root.isVisible()) await this.goto();
    }

    async create(title: string) {
        if (!await this.root.isVisible()) await this.goto();
        console.log(`[create debug] origin=${this.page.url()} title=${title}`);
        await this.page.getByTestId('order-title').fill(title);
        const resp = this.page.waitForResponse(
            (r) => r.url().includes('/api/orders') && r.request().method() === 'POST',
        );
        await this.page.getByTestId('order-add').click();
        await resp;
    }

    async rowReady(title: string): Promise<Locator> {
        await this.ensure();
        return this.row(title);
    }

    row(title: string): Locator {
        return this.root.getByTestId('order-item').filter({ hasText: title });
    }

    rows(): Locator {
        return this.root.getByTestId('order-item');
    }

    async rowsReady(): Promise<Locator> {
        await this.ensure();
        return this.rows();
    }

    delButtons(): Locator {
        return this.root.getByTestId('order-del');
    }

    async delete(title: string) {
        await this.ensure();
        // WS 广播触发的 refetch 有延迟——先等行渲染再点删除
        await expect(this.row(title)).toHaveCount(1, { timeout: 10_000 }).catch(async (e) => {
            const rows = await this.rows().allTextContents();
            console.log(`[DEBUG delete] 行列表: ${JSON.stringify(rows)} url=${this.page.url()}`);
            throw e;
        });
        const resp = this.page.waitForResponse(
            (r) => r.url().includes('/api/orders/') && r.request().method() === 'DELETE',
        );
        await this.row(title).getByTestId('order-del').click();
        await resp;
    }

    async expectSeeded() {
        await expect(this.rows().first()).toBeVisible();
    }

    uploadList(): Locator {
        return this.page.getByTestId('file-item');
    }

    async openUploadTab() {
        await this.page.getByTestId('tab-upload').click();
    }

    async upload(file: { name: string; mimeType: string; buffer: Buffer }) {
        await this.page.getByTestId('tab-upload').click();
        const resp = this.page.waitForResponse(
            (r) => r.url().includes('/api/upload') && r.request().method() === 'PUT',
        );
        await this.page.getByTestId('upload-input').setInputFiles([file]);
        await resp;   // PUT 落库后再切页，避免竞态
        await this.page.getByTestId('tab-orders').click();
    }
}
