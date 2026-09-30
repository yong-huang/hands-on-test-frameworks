// playwright.config.ts — lab 03：定位引擎深水区
// 被测对象是 lab 02 的 pw-store，但起在独立端口 9003——
// 每个实验一个端口是本系列的隔离约定（90NN），互不串扰
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
        baseURL: 'http://127.0.0.1:9003',
        locale: 'zh-CN',
        screenshot: 'only-on-failure',
        trace: 'retain-on-failure',
    },

    webServer: {
        // 复用 lab 02 的服务器代码与构建产物（app/dist 由 02 的 apply 产出）
        command: 'PORT=9003 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9003/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
