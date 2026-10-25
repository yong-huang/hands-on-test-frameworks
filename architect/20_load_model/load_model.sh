#!/usr/bin/env bash
# =============================================================================
# load_model.sh — architect 20 主演示脚本：
# 推导目标 TPS → 生成含推导注释的 k6 场景 → 多档速率实测 → 容量结论 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
SUT_DIR="$REPO/labs/11_sut_app"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① k6 自检 + 种子数据 + 起 SUT"
    k6 version | head -1
    ( cd "$SUT_DIR" && rm -f app/orders.db && "$PY" app/seed.py --db app/orders.db )
    local here="$PWD"
    # 脱管包装壳：uvicorn 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0（根除 Terminated 噪声）
    local app_dir; app_dir="$(cd "$SUT_DIR/app" && pwd)"
    nohup env APP_DIR="$app_dir" SUT_DB="$app_dir/orders.db" PY="$PY" PIDFILE="$here/.sut.pid" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; "$PY" -m uvicorn main:app --host 127.0.0.1 --port 8899 </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > "$here/.sut.log" 2>&1 &
    cd "$here"
    for i in $(seq 1 40); do
        curl -sf -m 2 "http://127.0.0.1:8899/api/health" >/dev/null 2>&1 && { echo "SUT 就绪"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; return 1
}

do_observe() {
    step "observe" "① 流量推导 + 生成 k6 场景（推导过程写进脚本注释）"
    step "observe" "② 多档速率实测（0.5×/1×/2× 目标 TPS 各 12s）+ 容量结论"
    set +e
    "$PY" load_model.py
    rc=$?
    set -e
    [ "$rc" -eq 0 ] || { echo "❌ 容量结论未能取得"; exit 1; }

    step "observe" "③ 生成的 k6 脚本头部（推导注释即方案）"
    head -10 generated/orders_load.js
    echo ">>> 验收：k6 脚本含推导注释 ✅；容量结论有实测依据（X TPS + 水位 Y）✅"
}

do_clean() {
    step "clean" "停 SUT、删产物与生成脚本"
    if [ -f .sut.pid ]; then kill "$(cat .sut.pid)" 2>/dev/null || true; rm -f .sut.pid; fi
    lsof -ti :8899 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf reports generated .sut.log __pycache__
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
