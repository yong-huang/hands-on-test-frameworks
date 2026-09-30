// playwright.config.ts — lab 06：视觉回归流水线
// 关键差异在 expect.toHaveScreenshot 段：阈值、动画、光标三件套
// 基线图默认落在 tests/<spec>-snapshots/ 目录，随仓库入库（它们是"应然的像素"）
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 30_000,
    retries: 0,
    workers: 1,
    reporter: [['list'], ['html', { open: 'never' }]],

    use: {
        baseURL: 'http://127.0.0.1:9006',
        locale: 'zh-CN',
        screenshot: 'off',          // 视觉断言自己截图，失败留痕截图反而干扰基线目录
        trace: 'retain-on-failure',
    },

    expect: {
        toHaveScreenshot: {
            // 容差：0.02 = 允许 2% 像素差异（字体渲染微差留余地，1px 布局变异依然能抓住）
            maxDiffPixelRatio: 0.02,
            animations: 'disabled',  // 截图瞬间冻结动画，消除"截到第几帧"的随机性
            caret: 'hide',           // 输入框光标闪烁会让每次截图都不同
        },
    },

    webServer: {
        command: 'PORT=9006 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9006/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        // 单浏览器起跑：跨浏览器基线 = 基线数 ×3，等跨浏览器矩阵稳定后再扩（见 README）
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
