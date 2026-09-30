// playwright.config.ts — lab 02 冒烟测试配置：验证靶场六大功能区本身可用
// 后续 17 个实验各自有 config，但都通过 webServer 复用本实验的 pw-store（端口 9002）
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 30_000,
    retries: 0,
    workers: 1,                        // SUT 状态在内存里，先串行保证可复现
    expect: { timeout: 5_000 },
    reporter: [['list'], ['html', { open: 'never' }]],

    use: {
        baseURL: 'http://127.0.0.1:9002',
        locale: 'zh-CN',
        screenshot: 'only-on-failure',
        trace: 'retain-on-failure',
    },

    webServer: {
        // 冒烟前需已构建（npx vite build，见 sut_app.sh apply）；这里只负责起停
        command: 'node server.mjs',
        url: 'http://127.0.0.1:9002/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
