#!/usr/bin/env bash
# =============================================================================
# fault_injection.sh — architect 21 主演示脚本：
# 起 SUT + 故障代理 → 四阶段混沌实验（基线/延迟/503/恢复）→ 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
SUT_DIR="$REPO/labs/11_sut_app"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 种子数据 + 起 SUT(:8899) 与故障代理(:8904)"
    ( cd "$SUT_DIR" && rm -f app/orders.db && "$PY" app/seed.py --db app/orders.db )
    local here="$PWD"
    # 脱管包装壳：uvicorn 与故障代理（各一个包装壳） 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0（根除 Terminated 噪声）
    local app_dir; app_dir="$(cd "$SUT_DIR/app" && pwd)"
    nohup env APP_DIR="$app_dir" SUT_DB="$app_dir/orders.db" PY="$PY" PIDFILE="$here/.proxy.pid" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; "$PY" -m uvicorn main:app --host 127.0.0.1 --port 8899 </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > "$here/.sut.log" 2>&1 &
    cd "$here"
    nohup env PY="$PY" \
        bash -c 'trap "" TERM INT; "$PY" fault_proxy.py </dev/null & U=$!; wait $U; exit 0' \
        </dev/null > .proxy.log 2>&1 &
    for i in $(seq 1 40); do
        curl -sf -m 2 "http://127.0.0.1:8899/api/health" >/dev/null 2>&1 \
            && curl -sf -m 2 "http://127.0.0.1:8904/api/health" >/dev/null 2>&1 \
            && { echo "SUT 与故障代理就绪"; return 0; }
        sleep 0.25
    done
    echo "服务未就绪" >&2; tail -5 .proxy.log >&2; return 1
}

do_observe() {
    step "observe" "① 四阶段混沌实验：基线 → 延迟注入 → 持续 503 → 恢复（每阶段断言行为）"
    set +e
    "$PY" chaos_test.py
    rc=$?
    set -e
    [ "$rc" -eq 0 ] || { echo "❌ 实验存在失败阶段"; exit 1; }

    step "observe" "② 时间线报告（注入/熔断/恢复全程可审计）"
    cat reports/timeline.md
    echo ">>> 验收：延迟有界 ✅ 熔断打开+fallback ✅ 恢复闭合 ✅"
}

do_clean() {
    step "clean" "停服务、还原数据库、删产物"
    if [ -f .proxy.pid ]; then kill "$(cat .proxy.pid)" 2>/dev/null || true; rm -f .proxy.pid; fi
    lsof -ti :8899 2>/dev/null | xargs kill 2>/dev/null || true
    lsof -ti :8904 2>/dev/null | xargs kill 2>/dev/null || true
    rm -f .sut.log .proxy.log
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
