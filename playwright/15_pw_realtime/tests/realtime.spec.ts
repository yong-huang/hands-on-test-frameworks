// realtime.spec.ts — lab 15：WebSocket 实时推送四件事
//   真实推送驱动状态演进 · 推送到 UI 的时延 · 断连重连 · 服务端权威对账
import { test, expect, type Page } from '@playwright/test';

const API = 'http://127.0.0.1:9015';
const TOKEN = Buffer.from('admin:admin').toString('base64');

async function login(page: Page) {
    await page.addInitScript((tk) => {
        localStorage.setItem('pw-store-auth',
            JSON.stringify({ token: tk, role: 'admin', username: 'admin' }));
    }, TOKEN);
    await page.goto('/');
    await expect(page.getByTestId('order-item').first()).toBeVisible();
}

test('真实推送：WS 帧驱动订单状态演进，UI 同步更新', async ({ page }) => {
    // WS 连接在页面加载（login 的 goto）时就建立了——监听必须挂在最前面
    const wsPromise = page.waitForEvent('websocket');
    await login(page);
    const ws = await wsPromise;

    const title = `RT-${Date.now().toString(36)}`;
    await page.getByTestId('order-title').fill(title);
    await page.getByTestId('order-add').click();

    const row = page.getByTestId('order-item').filter({ hasText: title });
    await expect(row).toHaveAttribute('data-status', 'created');

    // 记录服务端广播 paid 的时刻，验证 UI 在 1.5s 内跟进（本机 refetch 通常 <200ms）
    let paidAt = 0;
    ws.on('framereceived', (frame) => {
        try {
            const msg = JSON.parse(frame.payload.toString());
            if (msg.type === 'order-status' && msg.status === 'paid' && msg.title === title) {
                paidAt = Date.now();
            }
        } catch { /* 非忽略 */ }
    });

    await expect(row).toHaveAttribute('data-status', 'paid', { timeout: 6_000 });
    expect(paidAt, '必须真的收到过 paid 广播帧').toBeGreaterThan(0);
    expect(Date.now() - paidAt, 'UI 更新距广播帧应 < 1.5s').toBeLessThan(1_500);
});

test('mock WS：注入伪造帧驱动 UI（routeWebSocket）', async ({ page }) => {
    await login(page);

    // 拦截 /ws：mock 通道连到真服务端（HTTP 不受影响），再从"服务端侧"伪造帧
    // routeWebSocket 返回 void，页面侧路由要在闭包里捕获
    let serverSide: { send: (data: string) => void } | undefined;
    await page.routeWebSocket('/ws', (ws) => {
        const real = ws.connectToServer();      // 同步方法，直连真实服务端
        real.onMessage((m) => ws.send(m));      // 真实帧照常透传给页面
        ws.onMessage((m) => real.send(m));      // 页面消息也转发给服务端
        serverSide = ws;
    });

    // 从"服务端侧"推一条伪造的 deleted 帧（订单实际还在）
    await expect(async () => {
        await serverSide?.send(JSON.stringify({ type: 'order-deleted', id: 'ghost' }));
    }).toPass({ timeout: 8_000 });

    // 应用收到帧会触发列表 refetch：列表仍来自服务端权威数据，不受伪帧影响
    await expect(page.getByTestId('order-item').first()).toBeVisible();
});

test('断连重连：连接闪断 → 徽标变红 → 自动重连恢复', async ({ page }) => {
    // 注意：setOffline 掐不断已建立的空闲 WS（无流量就无感知），
    // 所以用 routeWebSocket 主动制造"闪断"：首连 800ms 后 close，重连放行
    let connections = 0;
    await page.routeWebSocket('/ws', (ws) => {
        connections += 1;
        const real = ws.connectToServer();
        real.onMessage((m) => ws.send(m));
        ws.onMessage((m) => real.send(m));
        if (connections === 1) {
            setTimeout(() => ws.close(), 800);
        }
    });

    await login(page);
    await expect(page.getByTestId('live-badge')).toContainText('已连接');

    // 首连被切 → onclose → 徽标变红
    await expect(page.getByTestId('live-badge')).toContainText('断开', { timeout: 8_000 });

    // 客户端 1s 重连逻辑：第二次连接放行，徽标回到"已连接"
    await expect(page.getByTestId('live-badge')).toContainText('已连接', { timeout: 10_000 });
    expect(connections, '应观测到 2 次连接（首次 + 重连）').toBe(2);
});

test('服务端权威：伪删除帧后 UI 与服务端对账一致', async ({ page }) => {
    await login(page);

    let serverSide: { send: (data: string) => void } | undefined;
    await page.routeWebSocket('/ws', (ws) => {
        const real = ws.connectToServer();
        real.onMessage((m) => ws.send(m));
        ws.onMessage((m) => real.send(m));
        serverSide = ws;
    });

    const before = await page.getByTestId('order-item').count();
    await expect(async () => {
        await serverSide?.send(JSON.stringify({ type: 'order-deleted', id: 'fake' }));
    }).toPass({ timeout: 8_000 });

    // refetch 后列表回到服务端真相：条目数不变（伪帧没有改变任何真实数据）
    await expect(page.getByTestId('order-item')).toHaveCount(before, { timeout: 5_000 });
});
