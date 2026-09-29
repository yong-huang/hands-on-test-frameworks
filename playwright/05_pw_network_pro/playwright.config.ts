// playwright.config.ts — lab 05 主配置：录制与注入套件（需要真实后端）
// 离线回放套件（offline.spec.ts）走 configs/offline.config.ts——
// 那份配置不配 webServer，专门证明"HAR 回放不依赖活着的后端"
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    testDir: './tests',
    testIgnore: '**/offline.spec.ts',     // 离线套件由独立配置接管
    timeout: 30_000,
    retries: 0,
    workers: 1,
    expect: { timeout: 5_000 },
    reporter: [['list'], ['html', { open: 'never' }]],

    use: {
        baseURL: 'http://127.0.0.1:9005',
        screenshot: 'only-on-failure',
        trace: 'retain-on-failure',
    },

    webServer: {
        command: 'PORT=9005 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9005/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
