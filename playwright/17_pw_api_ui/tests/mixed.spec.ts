// mixed.spec.ts — API+UI 分层：API 管造数与清场，UI 只验展示与交互
//   ① API 造 100 条 ≤5s（与 UI 造数对比）  ② 10 条"预置+分页验证"混合用例
//   ③ teardown 清零
import { test, expect } from '@playwright/test';

const API = 'http://127.0.0.1:9017';
const TOKEN = Buffer.from('admin:admin').toString('base64');
const AUTH = { 'content-type': 'application/json', authorization: `Bearer ${TOKEN}` };

async function apiCreate(title: string) {
    const res = await fetch(`${API}/api/orders`, {
        method: 'POST', headers: AUTH, body: JSON.stringify({ title }),
    });
    expect(res.status).toBe(201);
}

async function apiReset() {
    const res = await fetch(`${API}/api/reset`, { method: 'POST', headers: AUTH });
    expect(res.status).toBe(200);
}

async function apiCount(): Promise<number> {
    const res = await fetch(`${API}/api/orders`, { headers: AUTH });
    return ((await res.json()) as { orders: unknown[] }).orders.length;
}

async function uiLogin(page: import('@playwright/test').Page) {
    await page.addInitScript((tk) => {
        localStorage.setItem('pw-store-auth',
            JSON.stringify({ token: tk, role: 'admin', username: 'admin' }));
    }, TOKEN);
}

test.describe(() => {
    let batch = 0;
    test.beforeEach(async () => {
        batch += 1;
        await apiReset();                     // 每条混合用例从种子态出发
    });
    test.afterAll(async () => {
        await apiReset();                     // teardown：数据清零回种子
        const n = await apiCount();
        expect(n).toBe(3);
    });

    test('API 造 100 条 ≤5s（UI 造同量级约需数分钟，对比见 README）', async ({ page }) => {
        const started = Date.now();
        for (let i = 0; i < 100; i++) await apiCreate(`BATCH-${batch}-${String(i).padStart(3, '0')}`);
        const elapsed = Date.now() - started;
        console.log(`    [timing] API 造 100 条: ${elapsed} ms`);
        expect(elapsed).toBeLessThan(5_000);

        // UI 侧只做"验证"：第 1 页 20 条 + 分页指示 6 页
        await uiLogin(page);
        await page.goto('/');
        await expect(page.getByTestId('page-indicator')).toContainText('1 / 6');
        await expect(page.getByTestId('order-item')).toHaveCount(20);
    });

    for (let i = 1; i <= 10; i++) {
        test(`混合 ${String(i).padStart(2, '0')}: API 预置 ${40 + i} 条，UI 第 3 页验证目标行`, async ({ page }) => {
            const n = 40 + i;   // 41-50 条 → 恰好 3 页（20+20+余数）
            for (let k = 0; k < n; k++) {
                await apiCreate(`MIX-${String(i).padStart(2, '0')}-${String(k).padStart(3, '0')}`);
            }
            // 目标行是本批最后一条 → 固定落在第 3 页末尾
            const target = `MIX-${String(i).padStart(2, '0')}-${String(n - 1).padStart(3, '0')}`;

            await uiLogin(page);
            await page.goto('/');
            await expect(page.getByTestId('page-indicator')).toContainText('1 / 3');
            await page.getByTestId('page-next').click();   // 第 1 页 → 第 2 页
            await page.getByTestId('page-next').click();   // 第 2 页 → 第 3 页
            await expect(page.getByTestId('page-indicator')).toContainText('3 / 3');

            const lastPageCount = 3 + n - 40;               // 第 3 页 = 40 条之后（含 3 条种子在首页，末页为余数）
            await expect(page.getByTestId('order-item')).toHaveCount(lastPageCount);
            await expect(page.getByTestId('order-item').filter({ hasText: target }))
                .toHaveCount(1);
        });
    }

    test('UI 造数对照：10 条走表单的耗时（README 记录对比）', async ({ page }) => {
        await apiReset();
        await uiLogin(page);
        await page.goto('/');
        const started = Date.now();
        for (let k = 0; k < 10; k++) {
            await page.getByTestId('order-title').fill(`UI-MADE-${k}`);
            await page.getByTestId('order-add').click();
            await expect(page.getByTestId('order-item')
                .filter({ hasText: `UI-MADE-${k}` })).toHaveCount(1, { timeout: 8_000 });
        }
        const elapsed = Date.now() - started;
        console.log(`    [timing] UI 造 10 条: ${elapsed} ms（约 ${(elapsed / 10).toFixed(0)} ms/条）`);
        expect(elapsed).toBeGreaterThan(0);
    });
});
