// playwright.config.ts — lab 13：flaky 治理
// retries: 2 是治理的前提——重试给"偶发"留活口，报告给"偶发"留案底（flaky 标记）
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 20_000,
    retries: 2,                    // 本 lab 的主角：失败自动重试两次
    workers: 1,
    fullyParallel: false,
    expect: { timeout: 5_000 },
    reporter: [
        ['list'],
        ['html', { open: 'never' }],   // HTML 报告会给重试通过的用例打 flaky 标记
    ],

    use: {
        baseURL: 'http://127.0.0.1:9013',
        trace: 'retain-on-failure',    // 重试也救不回来的才有 trace，避免噪声
    },

    webServer: {
        command: 'PORT=9013 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9013/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
