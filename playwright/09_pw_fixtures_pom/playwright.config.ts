// playwright.config.ts — lab 09：fixture + 类型安全 POM
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 30_000,
    retries: 0,
    workers: 1,
    expect: { timeout: 5_000 },
    reporter: [['list'], ['html', { open: 'never' }]],

    use: {
        baseURL: 'http://127.0.0.1:9009',
        locale: 'zh-CN',
        screenshot: 'only-on-failure',
        trace: 'retain-on-failure',
    },

    webServer: {
        command: 'PORT=9009 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9009/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
