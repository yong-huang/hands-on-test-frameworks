#!/usr/bin/env bash
# =============================================================================
# pact_lab.sh — lab 15 主演示脚本：consumer 生成契约 → provider 校验 → 改字段→红→修复
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."
SUT_PORT=8902
BASE_URL="http://localhost:${SUT_PORT}"
SUT_DIR="../11_sut_app"
PIDFILE=".sut.pid"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {
    rm -f "$SUT_DIR/app/test_orders.db"
    # 脱管包装壳：内层 uvicorn 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0
    # （uvicorn 收到 TERM 后按信号语义退出，若被任何 bash 当作业收尸会打印 Terminated 噪声）
    nohup env APP_DIR="$PWD/$SUT_DIR/app" SUT_DB="$PWD/$SUT_DIR/app/test_orders.db" \
        PY="$PY" PORT="$SUT_PORT" PIDFILE="$PWD/$PIDFILE" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; "$PY" -m uvicorn main:app --host 127.0.0.1 --port "$PORT" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > ../.sut_pact.log 2>&1 &
    for i in $(seq 1 40); do
        curl -sf -m 2 "${BASE_URL}/api/health" >/dev/null 2>&1 && return 0
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; return 1
}

seed_sut() {  # 契约要求 items 至少 1 条（each_like min=1）——provider 状态准备
    curl -s -X POST "${BASE_URL}/api/orders" -H 'Content-Type: application/json' \
        -d '{"customer":"契约员","item":"种子商品","qty":1,"price":1.0}' >/dev/null
}

stop_sut() {
    [ -f "$PIDFILE" ] && { kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; }
    lsof -ti ":${SUT_PORT}" 2>/dev/null | xargs kill 2>/dev/null || true
}

do_apply() {
    step "apply" "起 SUT（provider 实体）+ consumer 生成契约文件 pacts/*.json"
    start_sut
    rm -rf pacts && mkdir -p pacts
    $PY -m pytest $INI -q
    ls -la pacts/
    echo ">>> 本地文件交换代替付费 Broker：pacts/ 可以提交进 git、随 MR 走"
}

do_observe() {
    step "observe" "① provider 校验：契约满足，退出码 0"
    seed_sut
    $PY provider/verify_provider.py --base-url "$BASE_URL"
    echo ">>> 退出码 = $?"

    step "observe" "② 演练'破坏'：consumer 改成期望 customerName 字段，重新生成契约"
    set +e
    PACT_BREAK=1 $PY -m pytest $INI -q 2>/dev/null | tail -1
    set -e

    step "observe" "③ provider 再校验：字段对不上，verify 变红（退出码非 0）——预期失败"
    set +e
    $PY provider/verify_provider.py --base-url "$BASE_URL" 2>&1 | tail -6
    echo ">>> 退出码 = $?（非 0：契约破坏被拦下，provider 不能随意改字段）"
    set -e

    step "observe" "④ 修复：consumer 恢复期望 customer，重新生成并校验——回到绿"
    rm -rf pacts && mkdir -p pacts
    $PY -m pytest $INI -q 2>/dev/null | tail -1
    $PY provider/verify_provider.py --base-url "$BASE_URL" 2>&1 | tail -1
}

do_clean() {
    step "clean" "停 SUT、删测试库（pacts/ 保留——契约是应提交的资产）"
    stop_sut
    rm -f "$SUT_DIR/app/test_orders.db" "$SUT_DIR/app/test_orders.db-journal"
    rm -rf .pytest_cache consumer/__pycache__ __pycache__
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
