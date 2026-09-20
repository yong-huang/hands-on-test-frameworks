#!/usr/bin/env bash
# =============================================================================
# quality_gate.sh — architect 03 主演示脚本：
# 默认规则跑出 PASS → 变异规则（覆盖率阈值 100%）跑出 FAIL → 清理
# 纯离线（门禁套件 labs/13 进程内跑，不需要起 SUT）。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（pyyaml + pytest-cov，幂等）"
    "$PY" -c "import yaml" 2>/dev/null && echo "pyyaml 就绪" || "$PY" -m pip install -q pyyaml
    "$PY" -c "import pytest_cov" 2>/dev/null && echo "pytest-cov 就绪" || "$PY" -m pip install -q pytest-cov

    step "apply" "② 默认规则跑门禁（应 PASS，退出码 0）"
    "$PY" gate.py
}

do_observe() {
    step "observe" "① 门禁报告关键表（每条规则：实测 vs 阈值）"
    sed -n '/| 规则/,/^$/p' reports/gate_report.md

    step "observe" "② 变异演示：覆盖率阈值 90 → 100（复制到 reports/，原配置不动）"
    "$PY" - <<'EOF'
import yaml
d = yaml.safe_load(open("configs/gate_rules.yaml", encoding="utf-8"))
for r in d["rules"]:
    if r["id"] == "coverage_total":
        r["threshold"] = 100
import os
os.makedirs("reports", exist_ok=True)
yaml.safe_dump(d, open("reports/rules_strict.yaml", "w", encoding="utf-8"),
               allow_unicode=True, sort_keys=False)
print("已生成严格规则 reports/rules_strict.yaml")
EOF
    set +e
    "$PY" gate.py --rules reports/rules_strict.yaml --out reports/strict
    rc=$?
    set -e
    echo ">>> 严格规则退出码 = ${rc}（非 0 即 CI 拦截）"

    step "observe" "③ 严格版报告：实测 98% vs 阈值 100% 的 FAIL 证据行"
    grep -E "coverage_total|verdict|裁决" reports/strict/gate_report.md | head -3
    echo ">>> 验收：默认规则 PASS(0)；阈值调 100% 后 FAIL(1) 且报告列出实测 vs 阈值"
}

do_clean() {
    step "clean" "删报告与变异副本——目录回到实验前状态"
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
