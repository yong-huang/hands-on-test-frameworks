// playwright.config.ts — lab 18：分片专用轻量套件
// 40 条 API 用例：无 UI、无构建依赖，专为 CI 容器与分片流水线设计
// 分片由 CLI --shard=x/4 控制（config 不写死，同一份配置本地/CI 通用）
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 15_000,
    retries: 0,
    fullyParallel: true,
    workers: Number(process.env.WORKERS || 4),   // 宿主机 4 worker；CI 容器按 CPU 自适应
    expect: { timeout: 5_000 },
    reporter: process.env.CI ? [['junit', { outputFile: `junit-${process.env.SHARD_ID || 'x'}.xml` }], ['list']]
                             : [['line']],

    use: {
        baseURL: 'http://127.0.0.1:9018',
        trace: 'off',
    },

    webServer: {
        command: 'PORT=9018 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9018/api/health',
        reuseExistingServer: true,     // 多分片并行起跑：先到的起服务，其余复用
        timeout: 15_000,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
