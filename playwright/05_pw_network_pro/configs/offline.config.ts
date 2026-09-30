// configs/offline.config.ts — 离线回放专用配置
// 与主配置的唯一本质区别：没有 webServer。后端死活与本套件无关——
// 所有 HTTP 交互都由 HAR 文件应答，这是"前端脱离后端独立测试"的形态
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    // -c 指向子目录配置时，路径相对配置文件解析——必须显式指回实验根下的 tests/
    testDir: fileURLToPath(new URL('../tests', import.meta.url)),
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    testMatch: '**/offline.spec.ts',
    timeout: 30_000,
    retries: 0,
    workers: 1,
    expect: { timeout: 5_000 },
    reporter: [['list']],

    use: {
        baseURL: 'http://127.0.0.1:9005',
        screenshot: 'only-on-failure',
        trace: 'retain-on-failure',
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
