// components.spec.tsx — 组件测试五件事：挂载、props、事件、插槽、重渲染
// mount 把组件直接挂进真浏览器。定位统一走 page.getByTestId：
// mount 返回的 comp 定位器带组件边界（internal:control=component），
// 在嵌套组件/裸元素场景下会找不到元素（实测坑，见 README Q&A）。
import { test, expect } from '@playwright/experimental-ct-react';
import { OrderCard, OrderForm, StatusBadge, CardShell } from '../src/components';
import type { Order } from '../../02_pw_sut/app/src/api';

const sample: Order = { id: 'o-1', title: '机械键盘', status: 'paid', owner: 'admin' };

test('StatusBadge：三种状态渲染三样文案', async ({ page, mount }) => {
    // ct 一个测试只有一个 React root：多次 mount 会报
    // "already has a React root"——要测多份就挂一个组合容器
    await mount(
        <div>
            {(['created', 'paid', 'shipped'] as const).map((s) => (
                <StatusBadge key={s} status={s} />
            ))}
        </div>,
    );
    const badges = page.getByTestId('status-badge');
    await expect(badges).toHaveCount(3);
    await expect(badges.nth(0)).toHaveText('已创建');
    await expect(badges.nth(1)).toHaveText('已支付');
    await expect(badges.nth(2)).toHaveText('已发货');
});

test('OrderCard：props 渲染标题与状态徽标', async ({ page, mount }) => {
    await mount(<OrderCard order={sample} />);
    await expect(page.getByTestId('order-card')).toContainText('机械键盘');
    await expect(page.getByTestId('status-badge')).toHaveText('已支付');
});

test('OrderCard：点删除按钮，onDelete 带着订单 id 回调', async ({ page, mount }) => {
    let deletedId = '';
    await mount(<OrderCard order={sample} onDelete={(id) => { deletedId = id; }} />);

    await page.getByTestId('card-delete').click();
    expect(deletedId).toBe('o-1');
});

test('OrderCard：不传 onDelete 就没有删除按钮（条件渲染）', async ({ page, mount }) => {
    await mount(<OrderCard order={sample} />);
    await expect(page.getByTestId('card-delete')).toHaveCount(0);
});

test('OrderForm：输入标题提交，onCreate 收到值且输入框复位', async ({ page, mount }) => {
    let created = '';
    await mount(<OrderForm onCreate={(t) => { created = t; }} />);

    await page.getByTestId('form-input').fill('显示器支架');
    await page.getByTestId('form-submit').click();

    expect(created).toBe('显示器支架');
    await expect(page.getByTestId('form-input')).toHaveValue('');
});

test('OrderForm：空白标题不触发回调（防御逻辑）', async ({ page, mount }) => {
    let calls = 0;
    await mount(<OrderForm onCreate={() => { calls += 1; }} />);

    await page.getByTestId('form-input').fill('   ');
    await page.getByTestId('form-submit').click();

    expect(calls).toBe(0);
});

test('CardShell：children 插槽内容正常挂载', async ({ page, mount }) => {
    await mount(
        <CardShell header="订单列表">
            <OrderCard order={sample} />
        </CardShell>,
    );
    await expect(page.getByTestId('card-shell')).toContainText('订单列表');
    await expect(page.getByTestId('order-card')).toBeVisible();
});

test('props 变化触发重渲染：徽标随 status 更新', async ({ page, mount }) => {
    // comp 引用在 update() 时仍需使用——这是它不可替代的两个能力之一
    const comp = await mount(<StatusBadge status="created" />);
    await expect(page.getByTestId('status-badge')).toHaveText('已创建');

    await comp.update(<StatusBadge status="shipped" />);
    await expect(page.getByTestId('status-badge')).toHaveText('已发货');
});
