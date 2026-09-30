// playwright.config.ts — lab 17：API+UI 混合测试
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 30_000,               // 100 条 API 造数 + UI 验证需要宽裕窗口
    retries: 0,
    workers: 1,                    // 共享 SUT 内存态 + /api/reset，串行保可复现
    expect: { timeout: 5_000 },
    reporter: [['list']],

    use: {
        baseURL: 'http://127.0.0.1:9017',
        locale: 'zh-CN',
        trace: 'off',
    },

    webServer: {
        command: 'PORT=9017 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9017/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
