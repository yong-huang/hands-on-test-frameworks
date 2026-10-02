// cucumber.mjs — parallel: 4 开启文件级并行（每 feature 一个 worker 线程序列）
// 唯一前缀数据协议 + /api/reset 夹持保证跨 worker 隔离
export default async function () {
    return {
        default: {
            import: ['tsx', 'features/**/*.ts'],
            parallel: 1,
            format: ['summary'],
        },
    };
}
