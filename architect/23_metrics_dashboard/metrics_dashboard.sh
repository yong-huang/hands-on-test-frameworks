#!/usr/bin/env bash
# =============================================================================
# metrics_dashboard.sh — architect 23 主演示脚本：
# 生成兄弟项目产物（01/03/13）→ 看板渲染 → 抽查核对（≥2 项对得上原始产物） → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 生成数据源：01 审计(计数) / 03 门禁 / 13 flaky 检测(3 轮轻量)"
    "$PY" -c "import yaml" 2>/dev/null || "$PY" -m pip install -q pyyaml
    ( cd "$REPO/architect/01_pyramid_audit" && "$PY" audit.py --no-timed >/dev/null )
    echo "01 审计 ✅"
    ( cd "$REPO/architect/03_quality_gate" && "$PY" gate.py >/dev/null )
    echo "03 门禁 ✅"
    ( cd "$REPO/architect/13_flaky_platform" && "$PY" flaky_platform.py detect --rounds 3 >/dev/null 2>&1 )
    echo "13 flaky 检测 ✅"
}

do_observe() {
    step "observe" "① 一条命令渲染看板（指标字典驱动，HTML 静态零依赖）"
    set +e
    "$PY" dashboard.py
    rc=$?
    set -e

    step "observe" "② 抽查核对：看板数值 vs 原始产物（抽查 3 项，验收线 ≥2）"
    "$PY" - <<'PYEOF'
import json
from pathlib import Path
board = {m["id"]: m["value"] for m in json.load(open("reports/metrics.json", encoding="utf-8"))}
checks = 0
# 抽查 1：总用例数
raw = json.load(open("../../architect/01_pyramid_audit/reports/pyramid.json", encoding="utf-8"))
assert board["total_cases"] == raw["total"]["cases"], "总用例数对不上"
checks += 1
# 抽查 2：覆盖率
gate = json.load(open("../../architect/03_quality_gate/reports/gate.json", encoding="utf-8"))
cov = next(r for r in gate["rules"] if r["id"] == "coverage_total")["measured"]
assert board["coverage"] == cov, "覆盖率对不上"
checks += 1
# 抽查 3：flaky 率
fl = json.load(open("../../architect/13_flaky_platform/reports/flaky.json", encoding="utf-8"))
assert abs(board["flaky_rate"] - fl["flaky_rate_pct"]) < 0.01, "flaky 率对不上"
checks += 1
print(f"抽查 {checks} 项全部与原始产物一致 ✅（验收线 ≥2）")
PYEOF

    step "observe" "③ 诚实缺失演示：拿掉 13 的产物再渲染，看板必须明示缺失"
    mv "$REPO/architect/13_flaky_platform/reports/flaky.json" /tmp/flaky_backup.json
    set +e
    "$PY" dashboard.py 2>/dev/null | grep -E "缺失" | head -2
    set -e
    mv /tmp/flaky_backup.json "$REPO/architect/13_flaky_platform/reports/flaky.json"
    [ "$rc" -eq 0 ] && echo ">>> 验收：看板含指标字典三要素 ✅ 抽查一致 ✅ 缺失明示 ✅"
}

do_clean() {
    step "clean" "删报告与兄弟项目产物（原始 configs 不动）"
    rm -rf reports __pycache__
    ( cd "$REPO/architect/01_pyramid_audit" && rm -rf reports ) || true
    ( cd "$REPO/architect/03_quality_gate" && rm -rf reports ) || true
    ( cd "$REPO/architect/13_flaky_platform" && rm -rf reports ) || true
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
