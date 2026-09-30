// playwright-ct.config.ts — 组件测试专用配置（与 E2E 配置是两套体系）
// ct runner 内嵌一个 vite dev server 把组件挂进真浏览器——不起 SUT、没有网络依赖
import { defineConfig } from '@playwright/experimental-ct-react';
import { devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 10_000,
    retries: 0,
    workers: 1,
    reporter: [['list']],

    use: {
        trace: 'off',
        // ct dev server 端口沿用系列 90NN 约定
        ctPort: 9007,
    },

    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    ],
});
