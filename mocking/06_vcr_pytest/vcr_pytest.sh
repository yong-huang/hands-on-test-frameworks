#!/usr/bin/env bash
# =============================================================================
# vcr_pytest.sh — mocking 06 主演示脚本：
# 起真上游(:9600) → pytest 录制 cassette → 杀上游断网 → none 模式回放全绿
# → 无 cassette 的新用例必红（防偷跑）→ 展示 YAML cassette → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
UP=9600
UPSTREAM_SCRIPT="../../architect/08_mock_server/mockserver.py"

step() { echo; echo "=====> [$1] $2"; }

wait_up() {  # 任何 HTTP 应答都算活（上游对 GET /pay 回 404 也是活）
    for i in $(seq 1 120); do
        curl -s -m 2 "http://127.0.0.1:$1/pay" -o /dev/null 2>/dev/null && return 0
        sleep 0.5
    done
    echo "上游未就绪" >&2; return 1
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
    step "apply" "① 依赖体检 + 清场 + 起真上游(:${UP}，复用 architect/08 假支付网关)"
    "$PY" -c "import vcr, pytest_recording, httpx" 2>/dev/null || {
        echo "缺依赖：pip install vcrpy pytest-recording httpx" >&2; exit 1; }
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$UP"
    mkdir -p reports
    start_bg upstream "$PY" "$UPSTREAM_SCRIPT" upstream --port "$UP"
    wait_up "$UP"
    echo "上游就绪（vcrpy + pytest-recording + httpx 已就位）"
}

do_observe() {
    step "observe" "② 录制：pytest 打真上游，交互落成 YAML cassette"
    "$PY" -m pytest --record-mode=all tests/test_pay.py -q 2>&1 | tee reports/run_record.txt
    echo "--- 生成的 cassette ---"
    ls -la tests/cassettes/
    echo "--- cassette 内容（test_pay_and_status.yaml，节选）---"
    head -18 tests/cassettes/test_pay/test_pay_and_status.yaml

    step "observe" "③ 断网：杀掉上游进程，none 模式回放——测试代码零改动"
    kill "$(cat reports/upstream.pid)" 2>/dev/null || true
    sleep 0.5
    lsof -ti ":$UP" >/dev/null 2>&1 && { echo "上游未死干净"; exit 1; }
    "$PY" -m pytest --record-mode=none --block-network tests/test_pay.py -q 2>&1 | tee reports/run_replay.txt
    grep -q "2 passed" reports/run_replay.txt && echo "断网回放全绿 ✅（上游已死 + none 模式 = 零真实网络请求）"

    step "observe" "④ 防偷跑：新增无 cassette 的用例，none 模式必红"
    set +e
    "$PY" -m pytest --record-mode=none --block-network tests/ -q 2>&1 | tee reports/run_newcase.txt
    rc=$?
    set -e
    if [ "$rc" -ne 0 ] && grep -q "1 failed" reports/run_newcase.txt; then
        echo ">>> 新用例按预期红（rc=${rc}）：无录制的请求被挡下（--block-network 在 socket 层断网，绝不泄漏）"
    else
        echo "❌ 防偷跑未生效（rc=${rc}）"; exit 1
    fi

    echo
    echo ">>> 验收：录制 ✅ 断网回放全绿 ✅ 零真实网络 ✅ 新用例必红防偷跑 ✅ cassette 可读可 diff 可进 git ✅"
}

do_clean() {
    step "clean" "杀上游、删产物（cassette 可随时重录）——环境回到实验前状态"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$UP"
    rm -rf reports tests/cassettes tests/__pycache__ .pytest_cache __pycache__
    lsof -ti ":$UP" >/dev/null 2>&1 && { echo "❌ 端口 $UP 仍被占用"; exit 1; }
    echo "已清理（端口 $UP 确认空闲）"
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
