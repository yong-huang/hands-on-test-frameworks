#!/usr/bin/env bash
# =============================================================================
# debug_tools.sh — lab 08 主演示脚本：调试武器库
#   跑一套"设计好的红" → 验证 trace 产物完整 → 给出四个工具的打开方式
# 注意：本套件的 3 failed 是预期结果（教学素材），脚本对此显式容忍
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9008
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
    step "observe" "① 跑三条病例用例——预期 3 failed（这就是素材）"
    npx playwright test --project=chromium --reporter=line || true

    step "observe" "② trace 产物完整性：unzip -l 验证含网络快照与逐步截图"
    TRACE=$(find test-results -name 'trace.zip' | head -1)
    [ -n "$TRACE" ] || { echo "未找到 trace.zip" >&2; exit 1; }
    echo ">>> 样本: $TRACE"
    unzip -l "$TRACE" | awk '{print $4}' | grep -E '\.trace$|\.png$|network' | head -6
    PNGS=$(unzip -l "$TRACE" | grep -cE '\.png|\.jpeg')
    if [ "$PNGS" -ge 3 ]; then echo ">>> 逐步截图 $PNGS 张 ✓（每步动作都有留影）"; fi
    if unzip -l "$TRACE" | grep -q 'network'; then echo ">>> 网络快照存在 ✓"; fi

    step "observe" "③ 四个调试工具的打开方式（GUI，请手动执行）"
    echo ">>> trace viewer : npx playwright show-trace $TRACE"
    echo ">>> UI Mode      : npx playwright test --ui"
    echo ">>> Inspector    : npx playwright test --debug"
    echo ">>> HTML 报告    : npx playwright test --reporter=html && npx playwright show-report"

    step "observe" "④ 排查手册在位（先自查病例，再看答案）"
    [ -f DEBUGGING.md ] && echo ">>> DEBUGGING.md 存在，含速查表 + 三病例根因"
}

do_clean() {
    step "clean" "清运行产物，杀 :${PORT} 残留"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results
    echo ">>> 已清理（broken.spec.ts 保持原样，下次再红一遍）"
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
