// pages/orders_page.ts — 订单页面对象：定位器收口的唯一出口
// 步骤层（step_definitions/）只调用这里的方法；grep 门禁在 ci 脚本里强制执行
import { expect, type Locator, type Page } from '@playwright/test';

export class OrdersPage {
    readonly page: Page;
    private readonly root: Locator;

    constructor(page: Page) {
        this.page = page;
        this.root = page.getByTestId('orders-page');
    }

    async goto() {
        await this.page.goto('');
        await this.root.waitFor({ state: 'visible' });
    }

    async create(title: string) {
        if (!await this.root.isVisible()) await this.goto();
        await this.page.getByTestId('order-title').fill(title);
        // 动作边界处等待网络确认：click 返回 ≠ 数据已落库（页面对象负责"做到位"）
        const resp = this.page.waitForResponse(
            (r) => r.url().includes('/api/orders') && r.request().method() === 'POST',
        );
        await this.page.getByTestId('order-add').click();
        try {
            const r = await resp;
            console.log(`[create] POST ${r.status()} ${r.url()}`);
        } catch (e) {
            console.log(`[create] waitForResponse 失败: ${(e as Error).message.slice(0, 80)}`);
            throw e;
        }
    }

    row(title: string): Locator {
        return this.root.getByTestId('order-item').filter({ hasText: title });
    }

    async delete(title: string) {
        await this.row(title).getByTestId('order-del').click();
    }
}
