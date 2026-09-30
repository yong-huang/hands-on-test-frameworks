// playwright.config.ts — lab 15：WebSocket 实时推送
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
        baseURL: 'http://127.0.0.1:9015',
        locale: 'zh-CN',
        trace: 'off',
    },

    webServer: {
        command: 'PORT=9015 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9015/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
