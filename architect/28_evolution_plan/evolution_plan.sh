#!/usr/bin/env bash
# =============================================================================
# evolution_plan.sh — architect 28 主演示脚本（🏁 终极串联）：
# 生成全部数据源 → 跑 30 条证据复核（主张必须当场可证） → 输出方案文档 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 生成证据数据源（离线工具：01/02/03/13/17/26 六路）"
    "$PY" -c "import yaml" 2>/dev/null || "$PY" -m pip install -q pyyaml
    # 顺序有讲究：13 先产出 flaky 数据（quarantine 后口径 0%），03 门禁才不会按旧数据拦截
    ( cd "$REPO/architect/01_pyramid_audit" && "$PY" audit.py --no-timed >/dev/null )
    ( cd "$REPO/architect/02_risk_strategy" && "$PY" strategy.py >/dev/null )
    ( cd "$REPO/architect/13_flaky_platform" && "$PY" flaky_platform.py detect --rounds 3 >/dev/null 2>&1 )
    ( cd "$REPO/architect/03_quality_gate" && "$PY" gate.py >/dev/null )
    echo "六路数据源就绪（全部离线轻量模式）"
}

do_observe() {
    step "observe" "① 证据复核：30 条主张逐条当场证明（LIVE 重跑 + PROOF 结构证据）"
    set +e
    "$PY" verify.py
    rc=$?
    set -e
    [ "$rc" -eq 0 ] || { echo "❌ 存在未证实主张"; exit 1; }

    step "observe" "② 方案文档校验：路线图每一项都映射到 architect/ 真实产物"
    "$PY" - <<'PYEOF'
from pathlib import Path
import re
plan = Path("plan/evolution_plan.md").read_text(encoding="utf-8")
maps = re.findall(r"architect/\d{2}_[a-z_]+", plan)
missing = [m for m in set(maps) if not (Path("../..") / m).exists()]
assert maps, "路线图没有映射任何产物"
assert not missing, f"映射的产物不存在: {missing}"
print(f"路线图映射 {len(set(maps))} 个产物目录，全部真实存在 ✅")
PYEOF
    echo ">>> 验收：30 条主张 100% 有据 ✅ 路线映射真实 ✅"
}

do_clean() {
    step "clean" "删各项目生成的数据源与本目录产物"
    for d in 01_pyramid_audit 02_risk_strategy 03_quality_gate 13_flaky_platform; do
        rm -rf "../$d/reports"
    done
    rm -rf reports __pycache__
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
