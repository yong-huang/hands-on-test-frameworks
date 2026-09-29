// playwright.config.ts — 测试项目的"声明式总控台"（本系列所有 lab 的地基文件）
//
// pytest-playwright 里这些事散落在命令行参数与 pytest.ini：
//   --browser chromium / --base-url / --tracing / --html=report.html
// TS 原生栈把它们收进一个类型安全的配置文件，`npx playwright test` 读它即可。
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
    // 用例文件位置（正则）。子目录 configs/ 里是本 lab 专用的变体配置
    testDir: './tests',

    // 全局超时：单条用例 30s 兜底（自动等待的单次超时由 expect 单独控制）
    timeout: 30_000,

    // 失败重试：本地 0（红就是红，便于观察），CI 建议 2 —— lab 43 专门讲
    retries: 0,

    // 并行：本 lab 用例共享演示页状态，先串行；lab 40 专门讲并行与隔离
    fullyParallel: false,
    workers: 1,

    // 断言默认超时：web-first 断言（expect(...)）持续重试到成立或超时
    expect: { timeout: 5_000 },

    // ---- 报告 ----
    // list：终端逐条；html：可视化报告（show-report 打开）。二者可叠加
    reporter: [['list'], ['html', { open: 'never' }]],

    // ---- 每条用例的浏览器上下文默认值 ----
    use: {
        // baseURL：用例里 page.goto('/只写路径')。改端口/域名只动这里，用例零改动
        baseURL: 'http://127.0.0.1:9001',

        // 失败自动截图（trace 的完整开关体系在 lab 38 / 42 讲）
        screenshot: 'only-on-failure',

        // 每条用例的操作轨迹，失败时可在报告里回放
        trace: 'retain-on-failure',
    },

    // ---- webServer：声明"测试前要起的被测服务" ----
    // pytest 时代要手写 curl 探活循环；这里框架托管：起服务→探活→跑用例→收尾。
    // reuseExistingServer: 手动已起就复用（脚本演示时便于 observe 单步重跑）
    webServer: {
        command: 'node server.mjs',
        url: 'http://127.0.0.1:9001/api/health',
        reuseExistingServer: true,
        timeout: 15_000,
    },

    // ---- projects：同一套用例 × 多个浏览器/设备 ----
    // 每个项目是一份"上下文模板"。三核跑批 = --project 逐个或全部执行
    projects: [
        { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
        { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
        { name: 'webkit', use: { ...devices['Desktop Safari'] } },
    ],
});
