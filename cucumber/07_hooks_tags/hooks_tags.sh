#!/usr/bin/env bash
# =============================================================================
# hooks_tags.sh — lab 07 主演示脚本：Hooks 与标签
#   apply 起靶场 → observe 四类钩子时序 + 标签过滤 → clean 清场
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9107
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
    step "observe" "① 四类钩子时序（BeforeAll → Before×N → After×N → AfterAll）"
    npx cucumber-js

    step "observe" "② 标签过滤三条命令"
    echo ">>> @smoke 子集:        npx cucumber-js --tags \"@smoke\"        （1 场景）"
    echo ">>> 排除 @wip:          npx cucumber-js --tags \"not @wip\"      （2 场景）"
    echo ">>> 全量（无过滤）:      npx cucumber-js                        （3 场景）"

    step "observe" "③ 失败自动截图（After 按 scenario.result 判定）"
    echo ">>> 故意跑红的场景可在 After 里 attach 截图——见 README Q&A 示例代码"
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
