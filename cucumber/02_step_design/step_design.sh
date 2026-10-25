#!/usr/bin/env bash
# =============================================================================
# step_design.sh — lab 02 主演示脚本：步骤层设计与参数捕获
#   apply 起靶场 → observe 三场景 + 选择器泄漏门禁 → clean 清场
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9102
BASE_URL="http://127.0.0.1:${PORT}"
SUT="../../playwright/02_pw_sut/server.mjs"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（类型检查 + SUT 就绪）"
    npx tsc -p tsconfig.json
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    # 脱管包装壳：node 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0（根除 Terminated 噪声）
    nohup env PORT="${PORT}" SUT="$SUT" PIDFILE="$PWD/$PIDFILE" \
        bash -c 'trap "" TERM INT; node "$SUT" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > .sut.log 2>&1 &
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && { echo ">>> 探活通过"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; exit 1
}

do_observe() {
    step "observe" "① 订单管理三场景（同一 Given 复用、参数捕获、And 连接）"
    # SUT 在 apply 已起；这里确认存活（observe 可单独执行）
    curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 || { echo "SUT 未运行：先执行 ./step_design.sh apply" >&2; exit 1; }
    npx cucumber-js

    step "observe" "② 步骤层收口门禁：step_definitions/ 零定位器表达式"
    if grep -rnE "getByTestId|getByRole|locator\(" features/step_definitions/ >/dev/null 2>&1; then
        echo "步骤层发现定位器，违反收口原则：" >&2
        grep -rnE "getByTestId|getByRole|locator\(" features/step_definitions/ | head -5 >&2
        exit 1
    fi
    echo ">>> step_definitions/ 零定位器 ✓"
    echo ">>> pages/ 定位器计数: $(grep -cE "getByTestId|getByRole|locator\(" pages/*.ts | paste -sd' ' -)"

    step "observe" "③ 参数捕获演示：{string} 与 {int} 各一条"
    echo ">>> 当 创建标题为 {string} 的订单    ← 字符串参数"
    echo ">>> 那么 标题为 {string} 的订单恰有 {int} 笔 ← 字符串+整数参数"
    echo ">>> 修改 feature 里的数字（如 2 → 1）重跑，断言即红——参数真实生效"

    step "observe" "④ Cucumber 表达式解析器速查（未定义步骤的提示会推荐匹配表达式）"
    echo ">>> 临时加一句 未定义的句子 到 feature 重跑，cucumber 会给出建议表达式"
}

do_clean() {
    step "clean" "停靶场、清运行产物"
    [ -f "$PIDFILE" ] && { kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; }
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf .sut.log
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
