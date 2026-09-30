// playwright.config.ts — lab 14：文件上传下载
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 30_000,               // 大文件用例需要宽裕的执行窗口
    retries: 0,
    workers: 1,
    expect: { timeout: 5_000 },
    reporter: [['list']],

    use: {
        baseURL: 'http://127.0.0.1:9014',
        locale: 'zh-CN',   // 固定中文界面（lab 11 的 locale 感知默认会是 en-US）
        trace: 'off',
    },

    webServer: {
        command: 'PORT=9014 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9014/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
