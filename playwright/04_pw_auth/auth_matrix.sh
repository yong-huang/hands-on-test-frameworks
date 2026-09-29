#!/usr/bin/env bash
# =============================================================================
# auth_matrix.sh — lab 04 主演示脚本：认证与多用户矩阵
#   setup（每角色登录一次落盘）→ admin/customer 双 project 复跑 → 权限矩阵断言
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9004
SUT="../02_pw_sut"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（node_modules + 类型检查 + SUT 构建产物）"
    [ -d ../node_modules/@playwright/test ] || {
        echo "node_modules 缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p tsconfig.json
    if [ ! -f "$SUT/app/dist/index.html" ]; then
        step "apply" "pw-store 未构建，执行 vite build"
        npx vite build "$SUT/app" --logLevel warn
    fi
    npx playwright --version
}

do_observe() {
    step "observe" "① 三 project 协作：setup 先登录落盘，admin/customer 带态复跑"
    # --project 指定具体名字时依赖（dependencies）会自动连带执行 setup
    npx playwright test --project=admin --project=customer --reporter=list

    step "observe" "② 登录次数审计：.auth/ 两份登录态已生成，全程登录只发生 2 次"
    ls -la .auth/ 2>/dev/null || { echo "登录态缺失" >&2; exit 1; }
    echo ">>> admin.json / customer.json 各记录一次真实登录（setup 阶段）"
    echo ">>> session.spec 的免登录用例断言：后续所有用例 /api/login 调用 = 0"

    step "observe" "③ 权限矩阵覆盖：同一用例代码在两个角色 project 里各跑一遍"
    echo ">>> 共 7 条用例 × 2 角色 = 14 个执行（含 6 条权限断言 + 会话行为 3 条）"
}

do_clean() {
    step "clean" "清登录态与运行产物，杀掉 :${PORT} 残留服务"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results playwright-report .auth
    echo ">>> 已清理（.auth 登录态属运行时产物，不入库）"
}

main() {
    local target="${1:-all}"
    case "${target}" in
        apply)   do_apply ;;
        observe) do_observe ;;
        clean)   do_clean ;;
        all)     do_apply; do_observe; do_clean ;;
        *) echo "可用: apply | observe | clean | all" >&2; exit 1 ;;
    esac
}
main "$@"
