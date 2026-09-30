// playwright.config.ts — lab 10：并行与隔离
// workers 由环境变量驱动（脚本对比 1 vs 4 两种档位），fullyParallel 全开
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 20_000,
    retries: 0,
    // 并行档位：WORKERS=4 npx playwright test 即 4 进程并发
    workers: Number(process.env.WORKERS || 4),
    fullyParallel: true,           // 同文件内用例也并行（默认只有跨文件）
    expect: { timeout: 5_000 },
    reporter: [['line']],

    use: {
        baseURL: 'http://127.0.0.1:9010',
        locale: 'zh-CN',
        trace: 'off',              // 并行跑批不开轨迹：磁盘 IO 会吃掉并行收益
    },

    webServer: {
        command: 'PORT=9010 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9010/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
