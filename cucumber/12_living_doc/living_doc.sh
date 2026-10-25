#!/usr/bin/env bash
# =============================================================================
# living_doc.sh — lab 12 主演示脚本：活文档与 pending
#   apply 起靶场 → observe 2 绿 + 2 pending（黄）→ 报告生成 → 功能清单抽取
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9113
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
    step "observe" "① 跑批：2 绿（退货规则）+ 2 pending（未实现规则，显式容忍）"
    set +e
    npx cucumber-js --profile default \
        --format summary \
        --format json:reports/cucumber.json \
        --format junit:reports/junit.xml
    set -e

    step "observe" "② 活文档 HTML 生成"
    node ../09_reports/scripts/generate_report.mjs 2>/dev/null || \
        node scripts/generate_report.mjs 2>/dev/null || true
    node scripts/extract_features.mjs
    echo ">>> 活文档: reports/html/index.html（业务可读）"
    echo ">>> 功能清单: reports/features.md（抽取的场景列表）"
}

do_clean() {
    step "clean" "停靶场、清报告产物"
    [ -f "$PIDFILE" ] && { kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; }
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf reports .sut.log
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
