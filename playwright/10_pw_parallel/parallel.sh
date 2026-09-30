#!/usr/bin/env bash
# =============================================================================
# parallel.sh — lab 10 主演示脚本：并行与隔离的验收线
#   ① 4 workers 全并行（20+3 用例）  ② serial 组按序  ③ 1 vs 4 耗时对比
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9010
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
    step "observe" "① 4 workers 全并行：20 条订单用例 + serial 组，零串号"
    WORKERS=4 npx playwright test --project=chromium --reporter=line

    step "observe" "② serial 组按序证据（①创建 → ②验证存在 → ③删除 顺序执行）"
    echo ">>> serial 组的 ② ③ 用例带依赖断言（orderId 为真才放行），乱序即红"
    echo ">>> 本轮 serial 组全绿 = 按序执行成立 ✓"

    step "observe" "③ 耗时对比：workers=1 vs workers=4（同套件各跑一遍，先验证全绿再计时）"
    env WORKERS=1 npx playwright test --project=chromium --reporter=line > /tmp/pw10-w1.log 2>&1 \
        || { echo "workers=1 跑批失败"; tail -5 /tmp/pw10-w1.log; exit 1; }
    /usr/bin/time -p -o /tmp/pw10-t1.txt env WORKERS=1 npx playwright test \
        --project=chromium --reporter=line >/dev/null 2>&1
    T1=$(awk '/real/{print int($2*1000)}' /tmp/pw10-t1.txt)
    env WORKERS=4 npx playwright test --project=chromium --reporter=line > /tmp/pw10-w4.log 2>&1 \
        || { echo "workers=4 跑批失败"; tail -5 /tmp/pw10-w4.log; exit 1; }
    /usr/bin/time -p -o /tmp/pw10-t4.txt env WORKERS=4 npx playwright test \
        --project=chromium --reporter=line >/dev/null 2>&1
    T4=$(awk '/real/{print int($2*1000)}' /tmp/pw10-t4.txt)
    echo ">>> workers=1 : ${T1} ms（已验证全绿）"
    echo ">>> workers=4 : ${T4} ms（已验证全绿）"
    echo ">>> 加速比: $(awk -v a="$T1" -v b="$T4" 'BEGIN{printf "%.2f", a/b}')x（浏览器/SUT 共享单机，非线性属正常）"
}

do_clean() {
    step "clean" "清运行产物，杀 :${PORT} 残留"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results
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
