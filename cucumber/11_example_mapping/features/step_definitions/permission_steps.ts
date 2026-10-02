import { Given, When, Then, setDefaultTimeout } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { MappingWorld } from '../support/world.ts';
import { StorePage } from '../../pages/store.ts';

setDefaultTimeout(15_000);

When('以 {} 打开订单区', async function (this: MappingWorld, role: string) {
    const page = await this.setRole(role as 'admin' | 'customer');
    await page.goto('');
    await expect(page.getByTestId('welcome')).toContainText(
        role === 'admin' ? '管理员' : '顾客',
    );
    await expect(page.getByTestId('order-item').first()).toBeVisible();   // 列表加载完成
});

Then('删除按钮 {}', async function (this: MappingWorld, visibility: string) {
    const store = new StorePage(this.page);
    const url = this.page.url();
    const rows = await store.rows().count();
    console.log(`[DEBUG admin] url=${url} rows=${rows} welcome=${await this.page.getByTestId('welcome').textContent().catch(() => 'n/a')}`);
    await store.expectSeeded();   // 等列表加载完成，再判按钮可见性
    if (visibility === '可见') {
        await expect(store.delButtons().first()).toBeVisible();
    } else {
        await expect(store.delButtons()).toHaveCount(0);
    }
});

Then('直接调删除接口的状态码是 {}', async function (
    this: MappingWorld, expectedStatus: number,
) {
    // 先取列表第一行的真实 id（绕过 UI 拿数据）
    const list = await fetch('http://127.0.0.1:9112/api/orders', {
        headers: { authorization: `Bearer ${Buffer.from('admin:admin').toString('base64')}` },
    }).then((r) => r.json());
    const firstId = list.orders[0].id;

    // {} 匿名参数传入的是字符串——与数字比较前先转换（实测踩坑：200 vs "200"）
    // 关键：fetch 的 token 必须是【当前场景角色】的 token——硬编码 admin 会让
    // customer 分支拿到 200，权限矩阵就假绿了（实测踩坑）
    const roleToken = Buffer.from(`${this.role}:${this.role}`).toString('base64');
    const res = await fetch(`http://127.0.0.1:9112/api/orders/${firstId}`, {
        method: 'DELETE',
        headers: { authorization: `Bearer ${roleToken}` },
    }).catch(() => ({ status: 0 }));
    expect(res.status).toBe(Number(expectedStatus));
});
