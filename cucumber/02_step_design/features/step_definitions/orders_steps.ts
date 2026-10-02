// orders_steps.ts — 步骤层：业务句子到页面对象的绑定
// 每个步骤只做一个业务动作；参数捕获用 Cucumber 表达式；定位器零出现
import { Given, Then, When } from '@cucumber/cucumber';
import { expect } from '@playwright/test';
import { StepDesignWorld } from '../support/world.ts';
import { LoginPage } from '../../pages/login_page.ts';
import { OrdersPage } from '../../pages/orders_page.ts';

Given('管理员 {string} 已登录', async function (this: StepDesignWorld, user: string) {
    const login = new LoginPage(this.page);
    await login.goto();
    await login.login(user, user === 'admin' ? 'admin123' : 'customer123');
});

When('创建标题为 {string} 的订单', async function (this: StepDesignWorld, title: string) {
    const orders = new OrdersPage(this.page);
    await orders.create(title);
});

When('再创建标题为 {string} 的订单', async function (this: StepDesignWorld, title: string) {
    const orders = new OrdersPage(this.page);
    await orders.create(title);
});

Given('已存在标题为 {string} 的订单', async function (this: StepDesignWorld, title: string) {
    const orders = new OrdersPage(this.page);
    await orders.create(title);
});

When('删除标题为 {string} 的订单', async function (this: StepDesignWorld, title: string) {
    const orders = new OrdersPage(this.page);
    await orders.delete(title);
});

Then('订单列表中存在 {string}', async function (this: StepDesignWorld, title: string) {
    const orders = new OrdersPage(this.page);
    await expect(orders.row(title)).toHaveCount(1);
});

Then('订单列表中不存在 {string}', async function (this: StepDesignWorld, title: string) {
    const orders = new OrdersPage(this.page);
    await expect(orders.row(title)).toHaveCount(0);
});

Then('标题为 {string} 的订单恰有 {int} 笔', async function (
    this: StepDesignWorld, title: string, count: number,
) {
    const orders = new OrdersPage(this.page);
    await expect(orders.row(title)).toHaveCount(count);
});
