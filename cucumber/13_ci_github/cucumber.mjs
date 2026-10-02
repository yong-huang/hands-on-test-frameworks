// cucumber.mjs — CI 套件配置（formatters 由 CI 脚本以 CLI 传参注入）
export default async function () {
    return {
        default: {
            import: ['tsx', 'features/**/*.ts'],
        },
    };
}
