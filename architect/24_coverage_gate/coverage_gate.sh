#!/usr/bin/env bash
# =============================================================================
# coverage_gate.sh — architect 24 主演示脚本：
# 造一版 50% 覆盖的 PR diff → bot 拦截+未覆盖行清单 → 豁免申请审批 → 放行留痕 → 还原
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
STORE="$REPO/labs/11_sut_app/app/store.py"
BAK="$STORE.pr_bak"

step() { echo; echo "=====> [$1] $2"; }
cleanup() {
    if [ -f "$BAK" ]; then
        cmp -s "$STORE" "$BAK" 2>/dev/null || cp "$BAK" "$STORE"
        rm -f "$BAK"
    fi
}
trap cleanup EXIT

do_apply() {
    step "apply" "① 建立 PR 前基线覆盖（labs/13 套件 × store）"
    "$PY" cov_gate.py refresh
}

do_observe() {
    step "observe" "① 模拟 PR：新增 apply_discount 折扣函数（无任何测试调用，仅 import 级覆盖）"
    cp "$STORE" "$BAK"
    STORE_PATH="$STORE" "$PY" - <<'PYEOF'
import os
from pathlib import Path
p = Path(os.environ["STORE_PATH"])
p.write_text(p.read_text(encoding="utf-8") + '''

def apply_discount(price: float, tier: str) -> float:
    """PR 新增逻辑：会员折扣（演示 diff 覆盖率卡点）。"""
    tiers = {"gold": 0.8, "silver": 0.9, "bronze": 0.95}
    if tier not in tiers:
        raise ValueError(f"unknown tier: {tier}")
    discounted = round(price * tiers[tier], 2)
    if discounted <= 0:
        raise ValueError("discounted price must be positive")
    return discounted
''', encoding="utf-8")
print("store.py 已新增 apply_discount 函数")
PYEOF
    # 「只写了一半的测试」：gold 分支被调用过（覆盖 3/6 行），silver/bronze/异常分支没人测
    ( cd "$REPO/labs/11_sut_app/app" && "$PY" -c "
import sys; sys.path.insert(0, '.')
import store
print('gold 分支自测:', store.apply_discount(100.0, 'gold'))" )
    "$PY" cov_gate.py refresh

    step "observe" "② CI bot 裁决：9% < 80% → 拦截 + 未覆盖行清单 + 整改建议"
    set +e
    "$PY" cov_gate.py check
    rc1=$?
    set -e
    [ "$rc1" -eq 1 ] || { echo "❌ 未达标 diff 应被拦截"; exit 1; }

    step "observe" "③ 豁免流：申请（附理由）→ qa-lead 审批 → 重新裁决放行"
    "$PY" cov_gate.py request --reason "大促热修，测试下迭代补齐（补偿计划已挂 JIRA-233）"
    "$PY" cov_gate.py approve
    "$PY" cov_gate.py check
    echo ">>> 豁免审计留痕："
    "$PY" -c "import json; [print(' ', a) for e in json.load(open('reports/exemptions.json')) for a in e['audit']]"

    step "observe" "④ 还原 store.py（trap 兜底）"
    cleanup
    echo ">>> 验收：未覆盖 diff 被拦截+行清单 ✅ 豁免走完放行且全程留痕 ✅"
}

do_clean() {
    step "clean" "删报告、豁免档案与覆盖数据"
    cleanup
    rm -rf reports __pycache__ .pytest_cache
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
