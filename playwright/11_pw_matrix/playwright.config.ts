// playwright.config.ts — lab 11：设备与仿真矩阵
// 六个 project = 3 设备 × 明/暗主题。同一套响应式用例在六个组合下各跑一遍。
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

const DESKTOP = devices['Desktop Chrome'];
const IPHONE = devices['iPhone 13'];
const PIXEL = devices['Pixel 7'];

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 20_000,
    retries: 0,
    workers: 2,
    fullyParallel: true,
    expect: { timeout: 5_000 },
    reporter: [['list']],

    use: {
        baseURL: 'http://127.0.0.1:9011',
        trace: 'off',
        screenshot: 'only-on-failure',
    },

    webServer: {
        command: 'PORT=9011 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9011/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        { name: 'desktop-light', use: { ...DESKTOP, colorScheme: 'light' } },
        { name: 'desktop-dark', use: { ...DESKTOP, colorScheme: 'dark' } },
        { name: 'iphone-light', use: { ...IPHONE, colorScheme: 'light' } },
        { name: 'iphone-dark', use: { ...IPHONE, colorScheme: 'dark' } },
        { name: 'pixel-light', use: { ...PIXEL, colorScheme: 'light' } },
        { name: 'pixel-dark', use: { ...PIXEL, colorScheme: 'dark' } },
    ],
});
