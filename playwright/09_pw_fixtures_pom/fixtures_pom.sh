#!/usr/bin/env bash
# =============================================================================
# fixtures_pom.sh — lab 09 主演示脚本：fixture 体系 + 类型安全 POM 的验收线
#   ① 全量用例绿  ② 新用例 ≤10 行（wc -l）  ③ tsc 零错误  ④ 选择器收口检查
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9009
SUT="../02_pw_sut"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（node_modules + 类型检查 + SUT 构建产物）"
    [ -d ../node_modules/@playwright/test ] || {
        echo "node_modules 缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p tsconfig.json
    if [ ! -f "$SUT/app/dist/index.html" ]; then
        npx vite build "$SUT/app" --logLevel warn
    fi
    npx playwright --version
}

do_observe() {
    step "observe" "① 全量用例（fixture 驱动，6 条全绿）"
    npx playwright test --project=chromium --reporter=list

    step "observe" "② 验收线 A：新增一条用例 ≤10 行"
    LINES=$(grep -vc '^\s*//\|^\s*$' tests/new_order.pom.spec.ts)
    echo ">>> tests/new_order.pom.spec.ts 有效行数（去注释/空行）: ${LINES}"
    [ "$LINES" -le 10 ] && echo ">>> ≤10 行 ✓" || { echo "超出 10 行 ✗" >&2; exit 1; }

    step "observe" "③ 验收线 B：tsc --noEmit 零错误（fixture 类型推导全链路）"
    npx tsc -p tsconfig.json --noEmit && echo ">>> tsc 零错误 ✓"

    step "observe" "④ 验收线 C：选择器收口——tests/ 目录零选择器"
    if grep -rn "getByTestId\|locator(" tests/*.spec.ts >/dev/null 2>&1; then
        echo "tests/ 里发现选择器，违反收口原则：" >&2
        grep -rn "getByTestId\|locator(" tests/*.spec.ts | head -5 >&2
        exit 1
    fi
    echo ">>> tests/ 零选择器 ✓（全部收口在 pages/）"
    echo ">>> pages/ 选择器计数: $(grep -rc "getByTestId\|locator(" pages/*.ts | paste -sd' ' -)"
}

do_clean() {
    step "clean" "清运行产物，杀 :${PORT} 残留"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results playwright-report
    echo ">>> 已清理"
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
