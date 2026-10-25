#!/usr/bin/env bash
# =============================================================================
# canary_eval.sh — architect 18 主演示脚本：
# 起 baseline + 健康 canary → 判定放量 → 切劣化 canary → 判定回滚 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
SUT_DIR="$REPO/labs/11_sut_app"
PIDFILE=".providers.pid"

step() { echo; echo "=====> [$1] $2"; }

start_canary() {  # $1=ERR_RATE $2=LAT_MS
    local here="$PWD"
    # 脱管包装壳：canary 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0（根除 Terminated 噪声）
    nohup env ERR_RATE="$1" LAT_MS="$2" PORT=8903 PYTHONPATH="$SUT_DIR/app" APP_DIR="$SUT_DIR/app" \
        TARGET="$here/degrade_canary.py" PY="$PY" PIDFILE="$here/$PIDFILE" LOG="$here/.canary.log" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; "$PY" "$TARGET" </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > "$here/.canary.log" 2>&1 &
    cd "$here"
    for i in $(seq 1 40); do
        curl -sf -m 2 "http://127.0.0.1:8903/api/health" >/dev/null 2>&1 && { echo "canary 就绪"; return 0; }
        sleep 0.25
    done
    echo "canary 启动失败" >&2; tail -5 .canary.log >&2; return 1
}

stop_canary() {
    [ -f "$PIDFILE" ] && kill "$(cat "$PIDFILE")" 2>/dev/null || true
    lsof -ti :8903 2>/dev/null | xargs kill 2>/dev/null || true
    sleep 0.3
}

do_apply() {
    step "apply" "① 起 baseline（真 SUT :8899）与健康 canary（:8903，零劣化）"
    ( cd "$SUT_DIR" && rm -f app/orders.db && "$PY" app/seed.py --db app/orders.db )
    local here="$PWD"
    # 脱管包装壳：baseline uvicorn 的信号死亡被包装壳 wait 吸收、包装壳自身 exit 0（根除 Terminated 噪声）
    nohup env APP_DIR="$SUT_DIR/app" SUT_DB="$SUT_DIR/app/orders.db" PY="$PY" PIDFILE="$here/$PIDFILE" \
        bash -c 'trap "" TERM INT; cd "$APP_DIR" || exit 1; "$PY" -m uvicorn main:app --host 127.0.0.1 --port 8899 </dev/null & U=$!; echo $U > "$PIDFILE"; wait $U; exit 0' \
        </dev/null > "$here/.baseline.log" 2>&1 &
    cd "$here"
    for i in $(seq 1 40); do
        curl -sf -m 2 "http://127.0.0.1:8899/api/health" >/dev/null 2>&1 && break
        sleep 0.25
    done
    start_canary 0 0
}

do_observe() {
    step "observe" "① 健康灰度判定（应放量）"
    set +e
    "$PY" canary.py
    rc1=$?
    set -e
    [ "$rc1" -eq 0 ] || { echo "❌ 健康 canary 应判放量"; exit 1; }
    mv reports/canary_verdict.json reports/verdict_healthy.json

    step "observe" "② 切换劣化 canary（20% 错误率 + 300ms 延迟），重新判定"
    stop_canary
    start_canary 0.2 300
    set +e
    "$PY" canary.py
    rc2=$?
    set -e

    step "observe" "③ 验收断言：劣化实例必须被判回滚（相对+绝对双指标至少一项打穿）"
    "$PY" - <<'PYEOF'
import json
v = json.load(open("reports/canary_verdict.json", encoding="utf-8"))
assert "回滚" in v["verdict"], f"劣化实例未被拦截: {v['verdict']}"
fails = [c for c in v["checks"] if c.startswith("❌")]
print(f"劣化判定：{v['verdict']}；打穿的判定项：")
for c in fails: print(f"  {c}")
assert len(fails) >= 1
print("验收通过 ✅（健康放量 / 劣化回滚，判定有据）")
PYEOF
}

do_clean() {
    step "clean" "停服务、还原数据库、删产物"
    stop_canary
    if [ -f "$PIDFILE" ]; then kill "$(cat "$PIDFILE")" 2>/dev/null || true; rm -f "$PIDFILE"; fi
    lsof -ti :8899 2>/dev/null | xargs kill 2>/dev/null || true
    rm -f .baseline.log .canary.log
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
