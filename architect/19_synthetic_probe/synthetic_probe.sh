#!/usr/bin/env bash
# =============================================================================
# synthetic_probe.sh — architect 19 主演示脚本：
# 15 轮全绿落库 → 搞挂 SUT → 2 周期内告警触发 → 重启 SUT → 告警自动消除 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
SUT_DIR="$REPO/labs/11_sut_app"

step() { echo; echo "=====> [$1] $2"; }

start_sut() {
    local here="$PWD"
    ( cd "$SUT_DIR/app"
      SUT_DB="$PWD/orders.db" nohup "$PY" -m uvicorn main:app --host 127.0.0.1 --port 8899 \
          </dev/null > "$here/.sut.log" 2>&1 & echo $! > "$here/.sut.pid" )
    disown 2>/dev/null || true
    cd "$here"
    for i in $(seq 1 40); do
        curl -sf -m 2 "http://127.0.0.1:8899/api/health" >/dev/null 2>&1 && { echo "SUT 就绪"; return 0; }
        sleep 0.25
    done
    echo "SUT 启动失败" >&2; return 1
}

stop_sut() {
    if [ -f ".sut.pid" ]; then kill "$(cat .sut.pid)" 2>/dev/null || true; rm -f .sut.pid; fi
    lsof -ti :8899 2>/dev/null | xargs kill 2>/dev/null || true
    sleep 0.5
}

do_apply() {
    step "apply" "① 种子数据 + 起 SUT + 清空探针库"
    ( cd "$SUT_DIR" && rm -f app/orders.db && "$PY" app/seed.py --db app/orders.db )
    start_sut
    rm -rf reports
}

do_observe() {
    step "observe" "① 基线：15 轮探针全绿（成功率 100% 落库，验证验收线）"
    "$PY" probe.py run --rounds 15 --interval 0.5 2>&1 | tail -3
    "$PY" - <<'PYEOF'
import sys
sys.path.insert(0, ".")
from probe import stats
s = stats()
for probe, st in s.items():
    assert st["success_rate"] == 100.0, f"{probe} 成功率 {st['success_rate']}%"
    assert not st["alert_active"]
print(f"{len(s)} 条探针链路全部 100% 成功、无告警 ✅")
PYEOF

    step "observe" "② 搞挂 SUT：探针应在前 2 个周期内触发告警"
    stop_sut
    "$PY" probe.py run --rounds 4 --interval 0.5 2>&1 | grep -E "ALERT|round 4/4" | head -4
    "$PY" - <<'PYEOF'
import sys
sys.path.insert(0, ".")
from probe import stats
s = stats()
fired = {k: v for k, v in s.items() if v["alert_active"]}
print(f"告警活跃探针：{len(fired)} 条（预期 3 条全触发）")
assert len(fired) == 3, f"告警触发不全: {list(s)}"
print("告警触发 ✅")
PYEOF

    step "observe" "③ 重启 SUT：探针恢复，告警自动消除"
    start_sut
    "$PY" probe.py run --rounds 5 --interval 0.5 2>&1 | grep -E "RECOVERED" | head -3
    "$PY" - <<'PYEOF'
import sys
sys.path.insert(0, ".")
from probe import stats
s = stats()
active = [k for k, v in s.items() if v["alert_active"]]
assert not active, f"告警未消除: {active}"
print("恢复后告警全部自动消除 ✅")
PYEOF

    step "observe" "④ 探针报告"
    "$PY" probe.py report | sed -n '/合成探针报告/,$p' | head -6
    echo ">>> 验收：15 轮 100% ✅ 挂掉 2 周期内告警 ✅ 恢复后自动消除 ✅"
}

do_clean() {
    step "clean" "停 SUT、删探针库与日志"
    stop_sut
    rm -rf reports .sut.log .pytest_cache __pycache__ tests/__pycache__
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
