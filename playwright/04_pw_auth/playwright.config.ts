// playwright.config.ts — lab 04：认证与多用户矩阵
// 三个 project 协作：setup 先跑（每角色登录一次 → storageState 落盘），
// admin / customer 两个 project 依赖 setup，各自带着登录态跑同一批用例。
// 这是官方的 "setup project + storageState" 认证模式，全系列后续实验都沿用。
import { defineConfig, devices } from '@playwright/test';
import { fileURLToPath } from 'node:url';

// pw-store 的 token 是可逆的 base64("role:name")——config 里静态构造，
// 让 request fixture 也能直接带角色头（生产环境请改从密钥管理服务取）
const bearer = (role: string, name: string) =>
    `Bearer ${Buffer.from(`${role}:${name}`).toString('base64')}`;

export default defineConfig({
    testDir: './tests',
    outputDir: fileURLToPath(new URL('./test-results', import.meta.url)),
    timeout: 30_000,
    retries: 0,
    workers: 1,
    expect: { timeout: 5_000 },
    reporter: [['list'], ['html', { open: 'never' }]],

    use: {
        baseURL: 'http://127.0.0.1:9004',
        locale: 'zh-CN',
        screenshot: 'only-on-failure',
        trace: 'retain-on-failure',
    },

    webServer: {
        command: 'PORT=9004 node ../02_pw_sut/server.mjs',
        url: 'http://127.0.0.1:9004/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    projects: [
        // ① setup：只跑 auth.setup.ts，产出两份登录态
        {
            name: 'setup',
            testMatch: /auth\.setup\.ts/,
            use: { ...devices['Desktop Chrome'] },
        },
        // ② admin：依赖 setup，带 admin 登录态 + admin 角色 API 头
        {
            name: 'admin',
            dependencies: ['setup'],
            use: {
                ...devices['Desktop Chrome'],
                storageState: '.auth/admin.json',
                extraHTTPHeaders: { authorization: bearer('admin', 'admin') },
            },
        },
        // ③ customer：同构，角色换成 customer
        {
            name: 'customer',
            dependencies: ['setup'],
            use: {
                ...devices['Desktop Chrome'],
                storageState: '.auth/customer.json',
                extraHTTPHeaders: { authorization: bearer('customer', 'customer') },
            },
        },
    ],
});
