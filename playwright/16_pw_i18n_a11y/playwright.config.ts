// playwright.config.ts — lab 16：i18n 与无障碍
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 20_000,
    retries: 0,
    workers: 1,
    expect: { timeout: 5_000 },
    reporter: [['list']],

    use: {
        baseURL: 'http://127.0.0.1:9016',
        locale: 'zh-CN',               // 默认中文（单条用例用 test.use 覆盖为 en）
        trace: 'off',
    },

    webServer: {
        command: 'PORT=9016 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9016/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
