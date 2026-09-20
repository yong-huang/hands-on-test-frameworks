#!/usr/bin/env bash
# =============================================================================
# risk_strategy.sh — architect 02 主演示脚本：
# 基线策略 → 「改风险输入 → 策略随之变」变异演示 → 清理
# 纯离线工具（不依赖 SUT），apply 只做自检。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {  # 依赖自检 + 生成基线策略
    step "apply" "① 依赖自检（pyyaml，幂等）"
    "$PY" -c "import yaml" 2>/dev/null && echo "pyyaml 就绪" || "$PY" -m pip install -q pyyaml

    step "apply" "② 生成基线策略（输入 configs/features.yaml，10 个功能）"
    "$PY" strategy.py
}

do_observe() {
    step "observe" "① 基线策略核心表（看「订单数据导出」这行：P3，不设门禁）"
    grep -E "^\| (功能|创建|登录|订单|金额|Admin|健康|慢加载)" reports/strategy.md

    step "observe" "② 变异演示：假设「订单数据导出」转为核心功能（freq low→high, impact minor→critical）"
    "$PY" - <<'EOF'
import yaml
d = yaml.safe_load(open("configs/features.yaml", encoding="utf-8"))
for f in d["features"]:
    if f["id"] == "export":
        f["freq"], f["impact"] = "high", "critical"
        f["desc"] = "迭代转正：导出已成为客户合约承诺功能"
yaml.safe_dump(d, open("reports/features_mutated.yaml", "w", encoding="utf-8"),
               allow_unicode=True, sort_keys=False)
print("已生成变异输入 reports/features_mutated.yaml（原配置不动）")
EOF
    "$PY" strategy.py --features reports/features_mutated.yaml --out reports/mutated >/dev/null

    step "observe" "③ 对比两份策略：该功能的风险分/层级/优先级如何随之变化"
    echo "--- 基线 vs 变异（仅「订单数据导出」行）---"
    diff <(grep "^| 订单数据导出" reports/strategy.md) \
         <(grep "^| 订单数据导出" reports/mutated/strategy.md) || true

    step "observe" "④ 缺口分析汇总（目标层级 vs labs/ 现有资产）"
    sed -n '/## 缺口分析/,/^## 方法说明/p' reports/strategy.md | head -12
    echo ">>> 验收：输入 10 功能 → 风险分级策略；改 1 个功能的风险输入重跑 → 层级/优先级随之变化"
}

do_clean() {  # 删干净：报告与变异副本（原始配置永远不动）
    step "clean" "删报告、变异副本与缓存——目录回到实验前状态"
    rm -rf reports __pycache__ .pytest_cache
    echo "已清理（configs/ 原始输入全程未动）"
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
