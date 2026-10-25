#!/usr/bin/env bash
# =============================================================================
# downstream_chain.sh — mocking 15 主演示脚本：
# 真模式（3 下游 :9801-9803）BFF 全绿 → 杀光真下游 → 虚拟化模式（01 替身
# :9810）同套测试全绿 → 注入支付 500 → 降级分支正确 → 环境对比数据 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
MOCK=9810

step() { echo; echo "=====> [$1] $2"; }

start_bg() {  # nohup 脱管启动（内层 trap- 恢复信号处置，防 SIG_IGN 继承）
    local name="$1"; shift
    nohup env PIDFILE="$PWD/reports/$name.pid" \
        bash -c 'trap "" TERM INT; ( trap - TERM INT; exec "$@" ) </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' run "$@" \
        </dev/null >>reports/servers.log 2>&1 &
}

wait_up() {
    for i in $(seq 1 120); do
        curl -s -m 2 "http://127.0.0.1:$1/" -o /dev/null 2>/dev/null && return 0
        sleep 0.5
    done
    echo "未就绪: $1" >&2; return 1
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

alive() {  # 端口存活计数（环境对比数据用）
    local n=0 p
    for p in 9801 9802 9803; do
        lsof -ti ":$p" >/dev/null 2>&1 && n=$((n+1))
    done
    echo "$n"
}

do_apply() {
    step "apply" "① 清场（含上次中断残留）"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    for p in 9801 9802 9803 9804 9810; do kill_port "$p"; done
    mkdir -p reports
    echo "已清场"
}

do_observe() {
    step "observe" "② 真模式：3 个真下游全部在场，BFF 集成测试全绿"
    start_bg realpay "$PY" real_downstreams.py pay 9801
    start_bg realrisk "$PY" real_downstreams.py risk 9802
    start_bg realsms "$PY" real_downstreams.py sms 9803
    for p in 9801 9802 9803; do wait_up "$p"; done
    DOWNSTREAM_MODE=real start_bg bff_real "$PY" bff.py
    wait_up 9804
    echo "真下游存活数：$(alive)/3"
    "$PY" bff_tests.py http://127.0.0.1:9804 all-green | tee -a reports/run_real.txt
    grep -q "❌" reports/run_real.txt && { echo "真模式失败"; exit 1; } || true

    step "observe" "③ 断网：杀光全部 3 个真下游，切换虚拟化模式（01 声明式替身 :9810）"
    for f in reports/real*.pid reports/bff_real.pid; do
        [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true
    done
    sleep 0.5
    for p in 9801 9802 9803 9804; do kill_port "$p"; done
    echo "真下游存活数：$(alive)/3（全部阵亡）"
    start_bg mockdown "$PY" ../01_declarative_mock/mockserver.py --port "$MOCK" --stubs stubs_normal
    wait_up "$MOCK"
    DOWNSTREAM_MODE=mock start_bg bff_mock "$PY" bff.py
    wait_up 9804
    "$PY" bff_tests.py http://127.0.0.1:9804 all-green | tee reports/run_mock.txt
    grep -q "❌" reports/run_mock.txt && { echo "虚拟化模式失败"; exit 1; } || true

    step "observe" "④ 故障注入：替身里的支付改 500 → BFF 走 PENDING_RETRY 降级"
    kill "$(cat reports/mockdown.pid)" 2>/dev/null || true
    sleep 0.5
    start_bg mockfault "$PY" ../01_declarative_mock/mockserver.py \
        --port "$MOCK" --stubs stubs_fault
    wait_up "$MOCK"
    "$PY" bff_tests.py http://127.0.0.1:9804 pay-fail | tee reports/run_fault.txt
    grep -q "❌" reports/run_fault.txt && { echo "降级分支失败"; exit 1; } || true

    echo
    echo ">>> 环境对比：真依赖模式需 3 个下游存活，虚拟化模式 0 个（数据见上）"
    echo ">>> 验收：真模式全绿 ✅ 断网后虚拟化模式全绿 ✅ 支付故障降级 PENDING_RETRY ✅"
}

do_clean() {
    step "clean" "杀全部服务、删产物——环境回到实验前状态"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    for p in 9801 9802 9803 9804 9810; do kill_port "$p"; done
    rm -rf reports __pycache__
    local residue=0
    for p in 9801 9802 9803 9804 9810; do
        lsof -ti ":$p" >/dev/null 2>&1 && { echo "❌ 端口 $p 仍被占用"; residue=1; }
    done
    [ "$residue" -eq 0 ] && echo "已清理（端口 9801-9810 确认空闲）"
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
