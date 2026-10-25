#!/usr/bin/env bash
# =============================================================================
# good_gherkin.sh — lab 06 主演示脚本：好坏 Gherkin 重构实战
#   apply 起靶场 → observe 语义等价（同跑同绿）+ 门禁（声明式零 UI 词）→ clean
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9106
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
    step "observe" "① 语义等价：坏/好两版同跑同绿（同一 SUT，同一业务结果）"
    echo "--- 坏版本（命令式）：---"
    npx cucumber-js features/checkout_bad.feature
    echo "--- 好版本（声明式）：---"
    npx cucumber-js features/checkout_good.feature

    step "observe" "② 门禁：声明式 feature 禁 UI 操作词"
    ./scripts/check_gherkin.sh

    step "observe" "③ 耗时对照（等待内聚 vs 裸等待的执行成本）"
    /usr/bin/time -p -o /tmp/pw06-bad.txt npx cucumber-js features/checkout_bad.feature >/dev/null 2>&1
    T_BAD=$(awk '/real/{print int($2*1000)}' /tmp/pw06-bad.txt)
    /usr/bin/time -p -o /tmp/pw06-good.txt npx cucumber-js features/checkout_good.feature >/dev/null 2>&1
    T_GOOD=$(awk '/real/{print int($2*1000)}' /tmp/pw06-good.txt)
    echo ">>> 坏版本（含 2s 裸等待）: ${T_BAD} ms"
    echo ">>> 好版本（web-first 等待）: ${T_GOOD} ms"
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
