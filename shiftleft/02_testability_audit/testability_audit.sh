#!/usr/bin/env bash
# =============================================================================
# testability_audit.sh — shiftleft 02 主演示脚本：依赖自检 → 全量审计 → 单条深看
#                        → 规则单测 → 门禁演示 → 清理
# 审计引擎在 audit.py，规则与样例在 configs/，本脚本负责串出演示动线。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（venv + pyyaml + pytest，幂等）"
    "$PY" -c "import yaml, pytest" 2>/dev/null \
        && echo "依赖就绪" \
        || "$PY" -m pip install -q pyyaml pytest
}

do_observe() {
    step "observe" "① 全量审计：10 条样例故事（5 好 5 坏），坏故事逐条给改写建议"
    "$PY" audit.py --no-save

    step "observe" "② 单条深看：--story US-B4 的全部违规明细（其余同理换 ID）"
    "$PY" audit.py --story US-B4 --no-save | tail -12

    step "observe" "③ 规则引擎单测：每条规则「坏的查得出、好的零误报」"
    "$PY" -m pytest tests/ -q 2>&1 | tail -2

    step "observe" "③b AI 双引擎对比（默认走 AI；离线时加 --no-ai 跳过）"
    "$PY" audit.py --no-save 2>&1 | sed -n '/AI 双引擎对比/,$p' || true

    step "observe" "④ 门禁模式演示：存在「不可测」故事 → 退出码 1（预期失败）"
    "$PY" audit.py --no-save --gate >/dev/null 2>&1 || \
        echo ">>> 已按预期退出非零：需求评审会上这 5 条坏故事会被打回"

    step "observe" "⑤ 产物落盘并清点"
    "$PY" audit.py >/dev/null
    ls -l reports/
    echo ">>> 完整报告见 reports/testability_report.md；结构化数据喂后续追溯矩阵（项目 4）"
}

do_clean() {  # 删报告与缓存，无进程残留（本实验不起服务）
    step "clean" "删报告与缓存——目录回到实验前状态"
    rm -rf reports .pytest_cache tests/__pycache__ __pycache__ 2>/dev/null || true
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
