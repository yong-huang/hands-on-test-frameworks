#!/usr/bin/env bash
# =============================================================================
# flaky.sh — lab 13 主演示脚本：flaky 治理验收
#   ① 单轮：2 条注入 flaky 经 retries 全绿且带 flaky 案底
#   ② 连续 5 轮：0 unexpected（套件级稳定性）
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9013
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
    step "observe" "① 单轮跑批：4 条用例全绿，其中 2 条带 flaky 案底"
    OUT=$(npx playwright test --project=chromium --reporter=list 2>&1)
    echo "$OUT" | grep -E '✓|passed|flaky' | head -8
    FLAKY=$(echo "$OUT" | grep -o '[0-9]* flaky' | grep -o '[0-9]*' | head -1 || true)
    FLAKY=${FLAKY:-0}
    [ "$FLAKY" -ge 2 ] && echo ">>> flaky 案底 ${FLAKY} 条 ✓（重试通过被如实记录）" \
        || { echo "flaky 案底不足 2 条（got $FLAKY）" >&2; exit 1; }

    step "observe" "② 连续 5 轮稳定性：每轮 0 unexpected"
    UNEXPECTED=0
    for i in 1 2 3 4 5; do
        OUT=$(npx playwright test --project=chromium --reporter=line 2>&1 || true)
        BAD=$(echo "$OUT" | grep -o '[0-9]* unexpected' | grep -o '[0-9]*' | head -1 || true)
        BAD=${BAD:-0}
        PASSED=$(echo "$OUT" | grep -oE '[0-9]+ (passed|flaky)' | tr '\n' ' ')
        echo ">>> 第 ${i}/5 轮：${PASSED:-无输出}，unexpected=${BAD}"
        UNEXPECTED=$((UNEXPECTED + BAD))
    done
    [ "$UNEXPECTED" -eq 0 ] && echo ">>> 5 轮 0 unexpected ✓" \
        || { echo "存在 unexpected，稳定性不达标" >&2; exit 1; }

    step "observe" "③ 手动体验"
    echo ">>> npx playwright show-report   （flaky 标记在 HTML 报告里有独立徽标）"
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
