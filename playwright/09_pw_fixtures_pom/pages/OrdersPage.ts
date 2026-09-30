// pages/OrdersPage.ts — 订单区页面对象：全仓库只有这里允许出现订单区选择器
// 方法名讲业务（create / row / delete），返回 locator 供断言——不藏断言、不藏等待
import { expect, type Locator, type Page } from '@playwright/test';

export class OrdersPage {
    readonly page: Page;
    private readonly root: Locator;

    constructor(page: Page) {
        this.page = page;
        this.root = page.getByTestId('orders-page');
    }

    /** 打开首页并等订单区可见（导航细节内聚在页面对象里） */
    async goto() {
        await this.page.goto('/');
        await this.root.waitFor({ state: 'visible' });
    }

    /** 创建订单：自动先到位，用例可以一行调用 */
    async create(title: string) {
        if (!await this.root.isVisible()) await this.goto();
        await this.page.getByTestId('order-title').fill(title);
        await this.page.getByTestId('order-add').click();
    }

    /** 按标题定位一行订单（返回 locator，断言交给用例） */
    row(title: string): Locator {
        return this.root.getByTestId('order-item').filter({ hasText: title });
    }

    /** 删除按钮集合（customer 视色为 0 个——断言写不用例侧） */
    deleteButtons(): Locator {
        return this.root.getByTestId('order-del');
    }

    async delete(title: string) {
        await this.row(title).getByTestId('order-del').click();
    }

    async expectVisible() {
        await expect(this.root).toBeVisible();
    }

    /** 断言辅助：列表已有种子数据 */
    async expectSeeded() {
        await expect(this.root.getByTestId('order-item').first()).toBeVisible();
    }
}
