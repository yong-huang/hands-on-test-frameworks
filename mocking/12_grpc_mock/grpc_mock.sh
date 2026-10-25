#!/usr/bin/env bash
# =============================================================================
# grpc_mock.sh — mocking 12 主演示脚本：
# protoc 生成桩 → 起 gRPC 替身(:9850) → grpcurl 探 unary/校验 → Python 探流式顺序 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3
GP=9850

step() { echo; echo "=====> [$1] $2"; }

wait_grpc() {  # grpcurl 反射探活
    for i in $(seq 1 120); do
        grpcurl -plaintext -max-time 2 "127.0.0.1:$1" list >/dev/null 2>&1 && return 0
        sleep 0.5
    done
    echo "gRPC 端口 $1 未就绪" >&2; return 1
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
    step "apply" "① 依赖体检 + protoc 生成桩 + 起 gRPC 替身(:$GP)"
    "$PY" -c "import grpc, grpc_tools, grpc_reflection" 2>/dev/null || {
        echo "缺依赖：pip install grpcio grpcio-tools grpcio-reflection" >&2; exit 1; }
    command -v grpcurl >/dev/null || { echo "缺 grpcurl（brew install grpcurl）" >&2; exit 1; }
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$GP"
    mkdir -p reports proto
    "$PY" -m grpc_tools.protoc -I proto \
        --python_out=proto --grpc_python_out=proto proto/order.proto
    echo "--- 已生成：$(ls proto/order_pb2*.py | tr '\n' ' ') ---"
    start_bg grpcserver "$PY" grpc_mock_server.py --port "$GP"
    wait_grpc "$GP"
    echo "--- 服务清单（反射）---"
    grpcurl -plaintext "127.0.0.1:$GP" list order.v1.OrderQuery
}

do_observe() {
    step "observe" "② grpcurl 探 unary：proto 合法 JSON 应答"
    grpcurl -plaintext -d '{"order_id": "ORD-1"}' \
        "127.0.0.1:$GP" order.v1.OrderQuery/GetOrder | tee reports/grpcurl_unary.txt

    step "observe" "③ grpcurl 探字段校验：缺 order_id → INVALID_ARGUMENT 点名字段"
    set +e
    grpcurl -plaintext -d '{"order_id": ""}' \
        "127.0.0.1:$GP" order.v1.OrderQuery/GetOrder 2>&1 | tee reports/grpcurl_invalid.txt
    rc=$?
    set -e
    if [ "$rc" -ne 0 ] && grep -q "order_id" reports/grpcurl_invalid.txt \
        && grep -q "InvalidArgument" reports/grpcurl_invalid.txt; then
        echo ">>> 校验按预期拒绝（rc=${rc}）：消息点名字段 order_id"
    else
        echo "❌ 字段校验未生效（rc=${rc}）"; exit 1
    fi

    step "observe" "④ Python 探流式：5 条事件全收 + 顺序断言"
    "$PY" grpc_client.py "127.0.0.1:$GP" | tee reports/client.txt
    grep -q "❌" reports/client.txt && { echo "存在失败断言"; exit 1; } || true

    echo
    echo ">>> 验收：grpcurl unary 合法应答 ✅ 字段校验点名字段 ✅ 流式 5 条有序全收 ✅"
}

do_clean() {
    step "clean" "杀服务、删产物（生成桩可随时重生成）——环境回到实验前状态"
    for f in reports/*.pid; do [ -f "$f" ] && kill "$(cat "$f")" 2>/dev/null || true; done
    kill_port "$GP"
    rm -rf reports proto/order_pb2.py proto/order_pb2_grpc.py __pycache__ proto/__pycache__
    lsof -ti ":$GP" >/dev/null 2>&1 && { echo "❌ 端口 $GP 仍被占用"; exit 1; }
    echo "已清理（端口 $GP 确认空闲）"
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
