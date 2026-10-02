// cucumber.mjs — 只管步骤加载；报告 formatter 由 reports.sh 以 CLI 传参
// （CLI 支持 name:path 简写；配置文件里的 format 数组在 cucumber 13 校验更严，实测踩坑）
export default async function () {
    return {
        default: {
            import: ['tsx', 'features/**/*.ts'],
        },
    };
}
