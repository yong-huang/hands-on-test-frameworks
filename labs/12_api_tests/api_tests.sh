#!/usr/bin/env bash
# =============================================================================
# api_tests.sh — lab 12 主演示脚本：起独立 SUT 实例 → 30 条 API 用例 → 清理
# 用独立端口 8901 与独立测试库：不污染 lab 11 的演示数据（测试必须封闭）。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
SUT_PORT=8901
BASE_URL="http://127.0.0.1:${SUT_PORT}"
SUT_DIR="../11_sut_app"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {
    rm -f "$SUT_DIR/app/test_orders.db"
    (cd "$SUT_DIR/app" && SUT_DB="$PWD/test_orders.db" nohup "$PY" -m uvicorn main:app \
        --host 127.0.0.1 --port "$SUT_PORT" </dev/null > ../.sut_test.log 2>&1 &
    echo $! > "../../labs/12_api_tests/${PIDFILE}"; disown)
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
    step "apply" "起 lab 11 的 SUT（独立端口 8901 + 独立空库——测试封闭性）"
    start_sut
}

do_observe() {
    step "observe" "① 收集：确认 30 条用例在册"
    SUT_BASE_URL="$BASE_URL" "$PY" -m pytest -c configs/pytest.ini --rootdir=. --collect-only -q | tail -2

    step "observe" "② 全量运行：schema 校验 + 负向用例 + 数据自造自清"
    SUT_BASE_URL="$BASE_URL" "$PY" -m pytest -c configs/pytest.ini --rootdir=. -q

    step "observe" "③ 乱序验证：用 -k 圈一半再圈另一半（独立性=任意子集都能过）"
    SUT_BASE_URL="$BASE_URL" "$PY" -m pytest -c configs/pytest.ini --rootdir=. -q -k "test_create or test_delete or test_patch"
    SUT_BASE_URL="$BASE_URL" "$PY" -m pytest -c configs/pytest.ini --rootdir=. -q -k "not (test_create or test_delete or test_patch)"

    step "observe" "④ 并行模式跑一遍：自造自清的用例天然 xdist 安全（serial 窗口用例除外）"
    SUT_BASE_URL="$BASE_URL" "$PY" -m pytest -c configs/pytest.ini --rootdir=. -q -n 4 -m "not serial"
}

do_clean() {
    step "clean" "停 SUT、删测试库与缓存"
    stop_sut
    rm -f "$SUT_DIR/app/test_orders.db" "$SUT_DIR/app/test_orders.db-journal"
    rm -rf .pytest_cache tests/__pycache__ __pycache__
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
