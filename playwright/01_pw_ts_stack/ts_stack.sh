#!/usr/bin/env bash
# =============================================================================
# ts_stack.sh — lab 31 主演示脚本：TS 原生测试栈四步走
#   类型检查 → 单浏览器 → 三浏览器跑批 → 报告产物
# 与 Python 系列的区别：被测服务不用脚本手工探活——playwright.config.ts 的
# webServer 字段由框架托管（起服务→探活→收尾），这就是 TS 栈的第一课。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"          # 任意 cwd 运行都正确

PORT=9001
PW="npx playwright"           # 二进制在 playwright/node_modules/.bin，npx 向上查找

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（node 依赖 + 浏览器构建 + 类型检查）"
    [ -d ../node_modules/@playwright/test ] || {
        echo "node_modules 缺失：先执行 bash ../load_resources.sh（playwright/ 目录）" >&2; exit 1; }
    $PW --version
    npx tsc -p tsconfig.json
    echo ">>> tsc 零错误：fixture 类型、定位器链在编译期就已校验"
}

do_observe() {
    step "observe" "① 单浏览器（chromium）：5 条用例，webServer 由框架自动托管"
    $PW test --project=chromium --reporter=list

    step "observe" "② 三浏览器跑批：同一套用例 × chromium/firefox/webkit"
    # HTML 报告随之生成（config 的 reporter 段），失败用例自动带截图+trace
    $PW test --reporter=list
    [ -d playwright-report ] && echo ">>> HTML 报告已随跑批生成"
    echo ">>> 打开报告:   npx playwright show-report   （在本目录执行）"
    echo ">>> 打开 UI Mode: npx playwright test --ui    （watch 模式 + 时间旅行）"
}

do_clean() {
    step "clean" "清理运行产物（报告/结果/trace），杀掉可能残留的演示服务"
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf test-results playwright-report
    echo ">>> 已清理。仓库回到实验前状态"
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
