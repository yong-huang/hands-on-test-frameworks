#!/usr/bin/env bash
# =============================================================================
# pact_stub.sh — mocking 09 主演示脚本：
# 起真 provider(:9700, labs/11 SUT) + pact stub(:9701, 伺服 labs/15 契约)
# → 5 条消费方测试打 stub 全绿（含契约外 500）→ 同套测试打真 provider
# → 逐交互结构对比 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
UP=9700; STUB=9701
SUT_DIR="../../labs/11_sut_app"
PACT_DIR="../../labs/15_pact/pacts"

step() { echo; echo "=====> [$1] $2"; }

wait_up() {  # 任何 HTTP 应答都算活
    for i in $(seq 1 120); do
        curl -s -m 2 "$1" -o /dev/null 2>/dev/null && return 0
        sleep 0.5
    done
    echo "未就绪: $1" >&2; return 1
}

start_bg() {  # nohup 脱管启动（内层 trap- 恢复信号处置，防 SIG_IGN 继承）
    local name="$1"; shift
    nohup env PIDFILE="$PWD/reports/$name.pid" \
        bash -c 'trap "" TERM INT; ( trap - TERM INT; exec "$@" ) </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' run "$@" \
        </dev/null >>reports/servers.log 2>&1 &
}

kill_port() {
    local pids
    pids=$(lsof -ti ":$1" 2>/dev/null) || true
    [ -n "$pids" ] && kill $pids 2>/dev/null || true
    sleep 0.5
    pids=$(lsof -ti ":$1" 2>/dev/null) || true
    [ -n "$pids" ] && kill -9 $pids 2>/dev/null || true
    sleep 0.2
}

do_apply() {
    step "apply" "① 清场 + 起真 provider(:${UP}，labs/11 SUT)与 pact stub(:${STUB}，伺服 labs/15 契约)"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$UP"; kill_port "$STUB"
    mkdir -p reports
    rm -f "../../labs/11_sut_app/app/test_orders.db"
    nohup env PIDFILE="$PWD/reports/sut.pid" APP_DIR="$PWD/$SUT_DIR/app" SUT_DB="$PWD/$SUT_DIR/app/test_orders.db" PORT="$UP" PY="$PY" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; ( trap - TERM INT; exec "$PY" -m uvicorn main:app --host 127.0.0.1 --port "$PORT" ) </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null >>reports/servers.log 2>&1 &
    start_bg stubserver "$PY" pact_stub_server.py --port "$STUB" --pacts "$PACT_DIR"
    wait_up "http://127.0.0.1:$UP/api/orders"
    wait_up "http://127.0.0.1:$STUB/api/orders"
    echo "真 provider(:$UP) 与 pact stub(:$STUB) 均就绪"
}

do_observe() {
    step "observe" "② 5 条消费方测试打 pact stub（含契约外 500）"
    PACT_BASE_URL="http://127.0.0.1:$STUB" "$PY" -m pytest tests_consumer.py -q 2>&1 | tee reports/run_stub.txt
    grep -q "5 passed" reports/run_stub.txt && echo "stub 全绿 ✅（契约外交互被 500 interaction_not_found 拒绝）"

    step "observe" "③ 同一套测试打真 provider（stub_only 用例跳过）"
    PACT_BASE_URL="http://127.0.0.1:$UP" "$PY" -m pytest tests_consumer.py -q \
        -m "not stub_only" 2>&1 | tee reports/run_real.txt
    grep -q "4 passed" reports/run_real.txt && echo "真 provider 全绿 ✅"

    step "observe" "④ 逐交互对比：双方应答都符合契约声明形状（多余键放行，叶子值不比）"
    "$PY" compare_providers.py "http://127.0.0.1:$UP" "http://127.0.0.1:$STUB" "$PACT_DIR" | tee reports/compare.txt
    grep -q "❌" reports/compare.txt && { echo "存在不一致交互"; exit 1; } || true

    echo
    echo ">>> 验收：stub 全绿 ✅ 契约外 500 ✅ 真 provider 全绿 ✅ 结构一致 ✅"
}

do_clean() {
    step "clean" "杀真 provider 与 stub、删产物——环境回到实验前状态"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$UP"; kill_port "$STUB"
    rm -rf reports tests_consumer/__pycache__ __pycache__ .pytest_cache
    local residue=0
    for p in "$UP" "$STUB"; do
        lsof -ti ":$p" >/dev/null 2>&1 && { echo "❌ 端口 $p 仍被占用"; residue=1; }
    done
    [ "$residue" -eq 0 ] && echo "已清理（端口 $UP/$STUB 确认空闲）"
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
