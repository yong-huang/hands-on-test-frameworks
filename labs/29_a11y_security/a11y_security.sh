#!/usr/bin/env bash
# =============================================================================
# a11y_security.sh — lab 29 主演示脚本：axe 无障碍门禁 + ZAP 安全基线扫描
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
SUT_PORT=8929
BASE_URL="http://127.0.0.1:${SUT_PORT}"
SUT_DIR="../11_sut_app"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {
    rm -f "$SUT_DIR/app/test_orders.db"
    (cd "$SUT_DIR/app" && SUT_DB="$PWD/test_orders.db" nohup "$PY" -m uvicorn main:app \
        --host 127.0.0.1 --port "$SUT_PORT" </dev/null > ../.sut_a11y.log 2>&1 &
    echo $! > "../../labs/29_a11y_security/${PIDFILE}"; disown)
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && return 0
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; return 1
}

stop_sut() {
    [ -f "$PIDFILE" ] && { kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; }
    lsof -ti ":${SUT_PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
}

do_apply() {
    step "apply" "起 SUT（${SUT_PORT}）"
    start_sut
}

do_observe() {
    step "observe" "① axe 无障碍门禁：critical/serious 必须为 0（修复历史见 docs/axe_before_after.md）"
    SUT_URL="$BASE_URL" $PY -m pytest -c configs/pytest.ini --rootdir=. -q
    echo ">>> 上面若红：SUT 出现了新的 High 级违例，先修页面再合入"

    step "observe" "② ZAP 基线扫描（docker，被动扫 + 爬虫；WARN 不阻断，清单落 docs/）"
    docker run --rm -v "$PWD/docs:/zap/wrk" -t zaproxy/zap-stable \
        zap-baseline.py -t "http://host.docker.internal:${SUT_PORT}/" \
        -r zap_report.html -I 2>&1 | grep -E "FAIL-NEW|WARN-NEW|PASS:" | tail -3
    echo ">>> 报告: docs/zap_report.html（浏览器打开可看全部告警明细）"

    step "observe" "③ 一键重跑语义：本脚本即为可回归的 a11y+安全门禁（CI 见 lab 30）"
}

do_clean() {
    step "clean" "停 SUT、清库（扫描报告保留在 docs/）"
    stop_sut
    rm -f "$SUT_DIR/app/test_orders.db" "$SUT_DIR/app/test_orders.db-journal"
    rm -rf .pytest_cache tests/__pycache__
    echo "已清理"
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
