#!/usr/bin/env bash
# =============================================================================
# dsl_engine.sh — architect 06 主演示脚本：起 SUT → DSL 10 条全绿 →
# 变异一条断言看行号定位 → DSL vs pytest 行数对比 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
SUT_DIR="$REPO/labs/11_sut_app"
SUT_PORT=8899
BASE_URL="http://127.0.0.1:${SUT_PORT}"
PIDFILE=".sut.pid"
LOG=".sut.log"

step() { echo; echo "=====> [$1] $2"; }

start_server() {
    if [ -f "$PIDFILE" ] && kill -0 "$(cat "$PIDFILE")" 2>/dev/null; then
        echo "SUT 已在运行 (pid $(cat "$PIDFILE"))"; return 0
    fi
    local here="$PWD"
    cd "$SUT_DIR/app"
    SUT_DB="$PWD/orders.db" nohup "$PY" -m uvicorn main:app \
        --host 127.0.0.1 --port "$SUT_PORT" </dev/null > "$here/$LOG" 2>&1 &
    echo $! > "$here/$PIDFILE"
    disown 2>/dev/null || true
    cd "$here"
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && { echo "SUT 就绪"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; return 1
}

do_apply() {
    step "apply" "① 依赖自检（pyyaml/httpx）+ 种子数据 + 起 SUT"
    "$PY" -c "import yaml, httpx" 2>/dev/null || "$PY" -m pip install -q pyyaml httpx
    ( cd "$SUT_DIR" && rm -f app/orders.db && "$PY" app/seed.py --db app/orders.db )
    start_server
}

do_observe() {
    step "observe" "① DSL 引擎跑 10 条用例（目标：10/10 全绿）"
    set +e
    "$PY" dsl.py
    rc=$?
    set -e
    [ "$rc" -eq 0 ] || { echo "DSL 未全绿，终止"; exit 1; }

    step "observe" "② 变异演示：把「创建订单」的期望 201 改成 200，看报错定位"
    mkdir -p reports
    sed 's/- { eq: \["\$.status_code", 201\] }/- { eq: ["$.status_code", 200] }/' \
        configs/cases.yaml > reports/cases_mutated.yaml
    set +e
    "$PY" dsl.py --cases reports/cases_mutated.yaml 2>&1 | grep -E "❌|定位|failed" | head -3
    set -e

    step "observe" "③ DSL vs pytest：同场景代码量对比"
    printf "DSL 用例层（configs/cases.yaml）: %s 行\n" "$(wc -l < configs/cases.yaml | tr -d ' ')"
    printf "pytest 等价用例（labs/12 test_api.py）: %s 行\n" "$(wc -l < "$REPO/labs/12_api_tests/tests/test_api.py" | tr -d ' ')"
    echo ">>> 验收：10 条 YAML 全绿；断言失败报错定位到 YAML 行号；行数对比给出权衡依据"
}

do_clean() {
    step "clean" "停 SUT、删报告与变异副本"
    if [ -f "$PIDFILE" ]; then kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; fi
    lsof -ti ":${SUT_PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf reports .pytest_cache __pycache__ "$LOG"
    ( cd "$SUT_DIR" && rm -f app/orders.db app/orders.db-journal ) || true
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
