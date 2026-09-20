#!/usr/bin/env bash
# =============================================================================
# contract_matrix.sh — architect 15 主演示脚本：
# 起 v1(真 SUT)与 v2(破坏变体) → 生成契约 → 版本矩阵验证 → can-i-deploy 判定 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
SUT_DIR="$REPO/labs/11_sut_app"
PIDFILE=".providers.pid"

step() { echo; echo "=====> [$1] $2"; }

start_v1() {  # 真 SUT :8899（种子数据 + 健康轮询，同 lab 01 模式）
    ( cd "$SUT_DIR" && rm -f app/orders.db && "$PY" app/seed.py --db app/orders.db )
    local here="$PWD"
    cd "$SUT_DIR/app"
    SUT_DB="$PWD/orders.db" nohup "$PY" -m uvicorn main:app --host 127.0.0.1 --port 8899 \
        </dev/null > "$here/.v1.log" 2>&1 &
    echo $! >> "$here/$PIDFILE"
    disown 2>/dev/null || true
    cd "$here"
}

start_v2() {  # 破坏变体 :8902（middleware 把 customer 改名 clientName）
    local here="$PWD"
    cd "$REPO/labs/11_sut_app/app"
    PYTHONPATH="$PWD" nohup "$PY" "$here/broken_provider.py" </dev/null > "$here/.v2.log" 2>&1 &
    echo $! >> "$here/$PIDFILE"
    disown 2>/dev/null || true
    cd "$here"
}

wait_up() {
    for i in $(seq 1 40); do
        curl -sf -m 2 "$1" >/dev/null 2>&1 && return 0
        sleep 0.25
    done
    echo "服务未就绪：$1" >&2; tail -5 "$2" >&2; return 1
}

do_apply() {
    step "apply" "① 起 v1 真 SUT(:8899) 与 v2 破坏变体(:8902)"
    rm -f "$PIDFILE"
    start_v1
    start_v2
    wait_up "http://127.0.0.1:8899/api/health" ".v1.log"
    wait_up "http://127.0.0.1:8902/api/health" ".v2.log"
    echo "两个 provider 已就绪（v2 会把响应里的 customer 改名 clientName）"
}

do_observe() {
    step "observe" "① 版本矩阵：每个 pact × 每个 provider 版本独立验证"
    set +e
    "$PY" matrix.py
    rc=$?
    set -e
    [ "$rc" -eq 0 ] || { echo "❌ 验收未过"; exit 1; }
    echo ">>> 验收：v1 全绿可发布；v2 破坏契约被 can-i-deploy 拦截"
}

do_clean() {
    step "clean" "停双 provider、还原 SUT 数据库、删产物"
    if [ -f "$PIDFILE" ]; then
        while read -r pid; do kill "$pid" 2>/dev/null || true; done < "$PIDFILE"
        rm -f "$PIDFILE"
    fi
    lsof -ti :8899 2>/dev/null | xargs kill 2>/dev/null || true
    lsof -ti :8902 2>/dev/null | xargs kill 2>/dev/null || true
    rm -f .v1.log .v2.log
    rm -rf reports __pycache__
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
