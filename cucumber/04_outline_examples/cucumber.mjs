// cucumber.mjs — Cucumber 13 的配置入口（对应 @playwright/test 的 playwright.config.ts）
// import 数组的执行语义：先加载裸模块名（tsx 是转译钩子，让 .ts 步骤文件可被直接 import），
// 再按 glob 加载步骤定义与 support 文件。这是 cucumber 官方文档的 TS 接入方式。
export default {
    import: ['tsx', 'features/**/*.ts'],
    // 注意：cucumber 13 的文件配置没有步骤超时键——步骤超时用 support 代码里的
    // setDefaultTimeout() 设置（见 features/support/world.ts）
};
