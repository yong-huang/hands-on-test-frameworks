#!/usr/bin/env bash
# =============================================================================
# perf_mock.sh — mocking 16 主演示脚本：
# 起替身下游(:9810, 50ms)+BFF(:9804) → k6 100 VUs → 切 500ms 再压 → 对比+零泄漏 → 清理
# 真下游（9801-9803）全程不在场——零泄漏由替身命中计数与端口死亡双证。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
PM=9810; BFF=9804

step() { echo; echo "=====> [$1] $2"; }

wait_up() {
    for i in $(seq 1 120); do
        curl -s -m 2 "http://127.0.0.1:$1/" -o /dev/null 2>/dev/null && return 0
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

start_stack() {  # $1 = 延迟档位
    start_bg mockdown "$PY" mock_downstream.py --port "$PM" --delay-ms "$1"
    start_bg bff "$PY" bff.py   # DOWNSTREAM_MODE 默认 mock → :9810
    wait_up "$PM"
    wait_up "$BFF"
}

do_apply() {
    step "apply" "① 依赖体检（k6）+ 清场 + 确认真下游端口全部死亡"
    command -v k6 >/dev/null || { echo "缺 k6（brew install k6）" >&2; exit 1; }
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    for p in 9801 9802 9803 9804 9810; do kill_port "$p"; done
    mkdir -p reports
    local dead=0
    for p in 9801 9802 9803; do
        lsof -ti ":$p" >/dev/null 2>&1 || dead=$((dead+1))
    done
    [ "$dead" -eq 3 ] || { echo "❌ 真下游端口未清干净"; exit 1; }
    echo "真下游 9801-9803 全部不在场（零泄漏的构造性前提）"
}

do_observe() {
    step "observe" "② 第一档：替身延迟 50ms，k6 100 VUs × 15s"
    start_stack 50
    k6 run --quiet --summary-export reports/summary_fast.json k6_checkout.js \
        2>&1 | tail -2 | tee reports/k6_fast.txt

    step "observe" "③ 第二档：替身延迟 500ms（换 stub 重启替身），再压 15s"
    kill "$(cat reports/mockdown.pid)" 2>/dev/null || true
    sleep 0.5
    start_bg mockdown "$PY" mock_downstream.py --port "$PM" --delay-ms 500
    wait_up "$PM"
    k6 run --quiet --summary-export reports/summary_slow.json k6_checkout.js \
        2>&1 | tail -2 | tee reports/k6_slow.txt

    step "observe" "④ 对比 + 零泄漏断言"
    HITS=$(curl -s "http://127.0.0.1:$PM/stats" | "$PY" -c "import json,sys; print(json.load(sys.stdin)['hits'])")
    "$PY" compare_perf.py reports/summary_fast.json reports/summary_slow.json "$HITS" \
        | tee reports/compare.txt
    grep -q "❌" reports/compare.txt && { echo "存在失败断言"; exit 1; } || true

    echo
    echo ">>> 验收：100 并发零错答 ✅ 延迟敏感性成立 ✅ 零泄漏 ✅"
}

do_clean() {
    step "clean" "杀服务、删产物——环境回到实验前状态"
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
