// cucumber.mjs — cucumber 13 ESM 配置的正确形态：
// 默认导出一个【函数】，返回 profiles 表（.mjs 被加载成模块命名空间，
// 静态 profiles 对象会被包进 namespace 导致 --profile 找不到——实测踩坑）
export default async function () {
    return {
        default: {
            import: ['tsx', 'features/**/*.ts'],
        },
        dev: {
            import: ['tsx', 'features/**/*.ts'],
            env: { BASE_URL: 'http://127.0.0.1:9108' },
        },
        staging: {
            import: ['tsx', 'features/**/*.ts'],
            env: { BASE_URL: 'http://127.0.0.1:9109' },
        },
    };
}
