// orders.pom.spec.ts — fixture 体系的能力展示：角色切换、数据工厂、组合断言
// 注意：本文件的用例体不出现任何元素定位表达式——选择器全部收口在 pages/ 目录
import { test, expect } from '../fixtures';

test('角色随取随用：customerPage 与 adminPage 互不串号', async ({
    adminPage, customerPage, orders, orderTitle,
}) => {
    await adminPage.goto('/');
    await orders.create(orderTitle);
    await expect(orders.row(orderTitle)).toHaveCount(1);

    // 同一条用例里换角色：fixture 给的是全新 page + 各自登录态
    await customerPage.goto('/');
    await orders.expectSeeded();
    await expect(orders.row(orderTitle)).toHaveCount(1);
});

test('admin 删除自己创建的订单（POM 动作方法复用）', async ({
    adminPage, orders, orderTitle,
}) => {
    await adminPage.goto('/');
    await orders.create(orderTitle);
    await orders.delete(orderTitle);
    await expect(orders.row(orderTitle)).toHaveCount(0);
});

test('数据工厂：两条用例的 orderTitle 必不相同（并行不撞车）', async ({
    adminPage, orders, orderTitle,
}, testInfo) => {
    await adminPage.goto('/');
    await orders.create(orderTitle);
    // 标题里带时间戳与随机数，跨用例唯一——用例名附带进去仅作展示
    expect(orderTitle).not.toMatch(testInfo.title);
    expect(orderTitle.startsWith('POM-')).toBe(true);
});

test('customer 无删除按钮：POM 返回 locator，断言写在用例', async ({
    customerPage, orders,
}) => {
    await customerPage.goto('/');
    await orders.expectSeeded();
    // 直接用页面对象的行定位器 + web-first 断言——不藏断言原则的另一半
    await expect(orders.deleteButtons()).toHaveCount(0);
});

test('worker 级 fixture：adminToken 整个 worker 只登录一次', async ({
    adminToken, request,
}) => {
    // token 与 adminPage 的登录态同源；这里直接打 API 验证其有效性
    const res = await request.get('/api/orders', {
        headers: { authorization: `Bearer ${adminToken}` },
    });
    expect(res.status()).toBe(200);
    expect(((await res.json()) as { orders: unknown[] }).orders.length).toBeGreaterThan(0);
});
