#!/usr/bin/env bash
# =============================================================================
# reports.sh — lab 09 主演示脚本：报告体系
#   apply 起靶场 → observe 跑批（含 1 条人为失败）→ 验证 json/junit/HTML 报告
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PORT=9110
BASE_URL="http://127.0.0.1:${PORT}"
SUT="../../playwright/02_pw_sut/server.mjs"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "环境体检（类型检查 + html-reporter 依赖 + SUT 就绪）"
    [ -d ../node_modules/multiple-cucumber-html-reporter ] || {
        echo "html-reporter 缺失：先执行 bash ../load_resources.sh" >&2; exit 1; }
    npx tsc -p tsconfig.json
    lsof -ti ":${PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    PORT=${PORT} nohup node "$SUT" </dev/null > .sut.log 2>&1 &
    echo $! > "$PIDFILE"; disown
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && { echo ">>> 探活通过"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; exit 1
}

do_observe() {
    step "observe" "① 跑批：2 绿 + 1 红（人为失败标本，预期容忍）"
    set +e
    npx cucumber-js --profile default \
        --format summary \
        --format json:reports/cucumber.json \
        --format junit:reports/junit.xml
    set -e

    step "observe" "② 产物核验：json/junit 存在且 junit 合法"
    [ -f reports/cucumber.json ] && echo ">>> cucumber.json ✓ ($(wc -c < reports/cucumber.json) bytes)"
    [ -f reports/junit.xml ] && { xmllint --noout reports/junit.xml && echo ">>> junit.xml 合法 ✓"; }

    step "observe" "③ HTML 活文档报告生成"
    node scripts/generate_report.mjs
    [ -d reports/html ] && echo ">>> reports/html/index.html ✓  （open 查看活文档）"
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
