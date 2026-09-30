// new_order.pom.spec.ts — 验收样本：fixture + POM 之后的"新用例"长什么样
// 整条用例 8 行：业务动作 + 断言，零选择器、零登录脚手架。
// wc -l 本文件应 ≤ 10 行（不含注释）；这就是 lab 09 的验收线。
import { test, expect } from '../fixtures';

test('admin 创建订单并验证', async ({ adminPage, orders, orderTitle }) => {
    await orders.goto();
    await orders.create(orderTitle);
    await expect(orders.row(orderTitle)).toHaveCount(1);
});
