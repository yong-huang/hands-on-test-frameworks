#!/usr/bin/env bash
# =============================================================================
# drift_gate.sh — mocking 10 主演示脚本：
# 起真服务(:9900)+Prism(:9901, 对齐契约) → 基线巡检 0 漂移 → 注入字段删减
# → 巡检定位该字段且退出码 1 → 再注入类型漂移 → 恢复契约归零 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
RS=9900; PM=9901
PRISM="@stoplight/prism-cli@5.16.0"

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

start_prism() {  # $1 = 契约文件
    [ -f reports/prism.pid ] && kill "$(cat reports/prism.pid)" 2>/dev/null || true
    kill_port "$PM"
    start_bg prism npx -y "$PRISM" mock "$1" -h 127.0.0.1 -p "$PM"
    wait_up "$PM"
    sleep 0.5
    kill -0 "$(cat reports/prism.pid)" 2>/dev/null || { echo "Prism 启动即死" >&2; exit 1; }
}

expect_exit() {  # $1 期望退出码；其余为命令
    local want="$1"; shift
    set +e
    "$@"
    local rc=$?
    set -e
    [ "$rc" -eq "$want" ] || { echo "❌ 退出码 ${rc}，期望 $want"; exit 1; }
    echo ">>> 退出码 ${rc}（符合预期 ${want}）"
}

do_apply() {
    step "apply" "① 清场 + 起真服务(:$RS)与 Prism(:${PM}，对齐契约 orders_ok)"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$RS"; kill_port "$PM"
    mkdir -p reports
    start_bg realservice "$PY" real_service.py --port "$RS"
    start_prism contracts/orders_ok.yaml
    echo "真服务(:$RS) 与 Prism(:$PM) 就绪"
}

do_observe() {
    step "observe" "② 基线巡检：契约与真服务对齐，0 漂移，退出码 0"
    expect_exit 0 "$PY" drift_gate.py "http://127.0.0.1:$RS" "http://127.0.0.1:$PM" \
        contracts/orders_ok.yaml | tee -a reports/run.txt

    step "observe" "③ 注入字段删减（created_at 从契约移除）→ 巡检定位该字段 + 退出码 1"
    start_prism contracts/orders_missing.yaml
    expect_exit 1 "$PY" drift_gate.py "http://127.0.0.1:$RS" "http://127.0.0.1:$PM" \
        contracts/orders_missing.yaml 2>&1 | tee reports/run_missing.txt
    grep -q "mock_missing.*created_at" reports/run_missing.txt \
        && echo ">>> 巡检报告定位到被删字段 created_at ✅"

    step "observe" "④ 再注入类型漂移（amount number→string）→ type_changed 同样拦截"
    start_prism contracts/orders_type.yaml
    expect_exit 1 "$PY" drift_gate.py "http://127.0.0.1:$RS" "http://127.0.0.1:$PM" \
        contracts/orders_type.yaml 2>&1 | tee reports/run_type.txt
    grep -q "type_changed.*amount" reports/run_type.txt \
        && echo ">>> 巡检报告定位到类型漂移 amount ✅"

    step "observe" "⑤ 恢复对齐契约 → 门禁归零放行"
    start_prism contracts/orders_ok.yaml
    expect_exit 0 "$PY" drift_gate.py "http://127.0.0.1:$RS" "http://127.0.0.1:$PM" \
        contracts/orders_ok.yaml

    echo
    echo ">>> 验收：结构 diff 报告 ✅ 字段删减定位+退出码 1 ✅ 类型漂移拦截 ✅ 归零放行 ✅"
}

do_clean() {
    step "clean" "杀服务、删产物——环境回到实验前状态"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$RS"; kill_port "$PM"
    rm -rf reports __pycache__
    local residue=0
    for p in "$RS" "$PM"; do
        lsof -ti ":$p" >/dev/null 2>&1 && { echo "❌ 端口 $p 仍被占用"; residue=1; }
    done
    [ "$residue" -eq 0 ] && echo "已清理（端口 $RS/$PM 确认空闲）"
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
