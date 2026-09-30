// playwright.config.ts — lab 08：调试武器库
// trace: 'on' 全量开轨迹（调试实验室可以奢侈，日常用 retain-on-failure 即可）
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 15_000,
    retries: 0,
    workers: 1,
    expect: { timeout: 3_000 },
    reporter: [['list']],

    use: {
        baseURL: 'http://127.0.0.1:9008',
        screenshot: 'on',            // 每步截图——调试实验要看完整时间线
        trace: 'on',
    },

    webServer: {
        command: 'PORT=9008 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9008/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
