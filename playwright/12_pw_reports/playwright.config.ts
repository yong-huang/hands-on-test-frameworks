// playwright.config.ts — lab 12：报告与产物体系
// 三路 reporter 并行产出：HTML（人看）+ JUnit（机器吃，CI 平台用）+ list（终端）
// 产物三件套全开：video / screenshot / trace——人为失败用例会把三者集齐
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 20_000,
    retries: 0,
    workers: 1,
    expect: { timeout: 5_000 },
    reporter: [
        ['list'],
        ['html', { open: 'never', outputFolder: 'playwright-report' }],
        ['junit', { outputFile: 'report.xml' }],
    ],

    use: {
        baseURL: 'http://127.0.0.1:9012',
        video: 'on',                    // 本 lab 全程录像（日常用 retain-on-failure）
        screenshot: 'on',               // 每步截图
        trace: 'on',                    // 全量轨迹
        viewport: { width: 1024, height: 640 },   // 视频文件别太大
    },

    webServer: {
        command: 'PORT=9012 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9012/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
