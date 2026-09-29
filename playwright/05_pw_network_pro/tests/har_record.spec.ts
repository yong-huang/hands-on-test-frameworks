// har_record.spec.ts — HAR 录制：走一遍真实核心路径，把全部 HTTP 交互录进 har/pw-store.har
// update: true 时请求穿透到真实后端并被记录，updateContent: 'embed' 把响应体嵌进 HAR。
// 录制内容 = 回放侧的全部家当：登录 POST、订单列表 GET、下单 POST。
import { test, expect } from '@playwright/test';

test('录制：登录 → 下单 的完整 HTTP 轨迹', async ({ page }) => {
    await page.routeFromHAR('har/pw-store.har', { update: true, updateContent: 'embed' });

    await page.goto('/');
    await page.getByTestId('login-user').fill('admin');
    await page.getByTestId('login-pass').fill('admin123');
    await page.getByTestId('login-btn').click();
    await expect(page.getByTestId('welcome')).toContainText('admin');

    await page.getByTestId('order-title').fill('HAR 回放下单');
    await page.getByTestId('order-add').click();
    await expect(page.getByTestId('order-item').filter({ hasText: 'HAR 回放下单' }))
        .toHaveCount(1);

    // 等网络静默，确保静态资源与接口应答全部录完
    await page.waitForLoadState('networkidle');
});
