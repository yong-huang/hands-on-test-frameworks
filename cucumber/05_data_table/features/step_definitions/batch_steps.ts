import { DataTable, Given, Then, When } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { DataTableWorld } from '../support/world.ts';
import { OrdersAdminPage } from '../../pages/orders_admin_page.ts';

Given('管理员已登录', async function (this: DataTableWorld) {
    await this.page.addInitScript((tk) => {
        localStorage.setItem('pw-store-auth',
            JSON.stringify({ token: tk, role: 'admin', username: 'admin' }));
    }, Buffer.from('admin:admin').toString('base64'));
});

When('按下表批量创建订单', async function (this: DataTableWorld, table: DataTable) {
    const store = new OrdersAdminPage(this.page);
    await store.goto();
    // rows()：每行是数组（本表单列表头，取第一列）
    for (const cells of table.rows()) {
        await store.create(cells[0]);
    }
});

Then('以上 {int} 笔订单全部出现在列表中', async function (
    this: DataTableWorld, count: number,
) {
    const store = new OrdersAdminPage(this.page);
    for (const title of ['表格订单-键盘', '表格订单-支架', '表格订单-扩展坞', '表格订单-鼠标垫', '表格订单-线缆']) {
        await expect(store.row(title)).toHaveCount(1);
    }
});

When('创建以下订单', async function (this: DataTableWorld, table: DataTable) {    const store = new OrdersAdminPage(this.page);
    await store.goto();
    // hashes()：表头作 key，每行映射成对象——字段自解释
    for (const row of table.hashes()) {
        await store.create(row['商品标题']);
    }
});

Then('以下订单应存在于列表且状态正确', async function (
    this: DataTableWorld, table: DataTable,
) {
    const store = new OrdersAdminPage(this.page);
    for (const row of table.hashes()) {
        await expect(store.row(row['商品标题'])).toHaveCount(1);
        await expect(store.row(row['商品标题'])).toContainText(row['状态']);
    }
});
