// simulation.spec.ts — 仿真三件套：timezone / offline / 触屏
import { test, expect } from '@playwright/test';

test.use({ timezoneId: 'America/New_York' });
test('timezone：纽约时区仿真的 Date 偏移生效', async ({ page }) => {
    await page.goto('/');
    // 纽约全年偏移 -300（EST）或 -240（EDT），绝不可能是本地时区的值
    const offset = await page.evaluate(() => new Date().getTimezoneOffset());
    expect([300, 240]).toContain(offset);
});

test('offline：断网仿真下请求失败、恢复后可用', async ({ page, context }) => {
    await page.goto('/');
    await context.setOffline(true);

    // 断网时再发请求必然失败（fetch 抛错被 evaluate 捕获为字符串）
    const err = await page.evaluate(async () => {
        try {
            await fetch('/api/health');
            return 'ok';
        } catch (e) {
            return `failed: ${(e as Error).message.slice(0, 40)}`;
        }
    });
    expect(err).toContain('failed');

    await context.setOffline(false);
    const ok = await page.evaluate(async () => {
        try {
            await fetch('/api/health');
            return 'ok';
        } catch {
            return 'failed';
        }
    });
    expect(ok).toBe('ok');
});

test('触屏：iPhone/Pixel project 具备触摸能力', async ({ page }, testInfo) => {
    await page.goto('/');
    const hasTouch = testInfo.project.use.hasTouch === true;
    const supports = await page.evaluate(() => 'ontouchstart' in window);
    expect(supports, `project ${testInfo.project.name} 的 hasTouch 仿真应生效`)
        .toBe(hasTouch);
});
