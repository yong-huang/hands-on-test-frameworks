#!/usr/bin/env bash
# =============================================================================
# trace_matrix.sh — shiftleft 04 主演示脚本：依赖自检 → 覆盖套件自证 → 全量矩阵 →
#                   缺口门禁演示 → 产物清点 → 清理
# 引擎在 trace_matrix.py；需求/映射在 configs/；labs/11 全程只读（collect-only）。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（venv + pyyaml + pytest，幂等）"
    "$PY" -c "import yaml, pytest" 2>/dev/null \
        && echo "依赖就绪" \
        || "$PY" -m pip install -q pyyaml pytest
}

do_observe() {
    step "observe" "① 覆盖套件自证：8 条需求配的回归测试真的全绿（临时库，不碰 labs/11）"
    "$PY" -m pytest tests/ -q 2>&1 | tail -2

    step "observe" "② 全量追溯矩阵：12 测试 = 11 映射 + 1 孤儿，需求覆盖 8/8 → 放行"
    "$PY" trace_matrix.py

    step "observe" "③ 缺口门禁演示：删掉 REQ-003 的唯一覆盖 → 未覆盖需求 → 退出码 1（预期失败）"
    "$PY" trace_matrix.py --mapping configs/test_mapping_gap.yaml >/dev/null 2>&1 || \
        echo ">>> 已按预期退出非零：有需求没人测，此矩阵可直接当 CI 卡点"

    step "observe" "④ 产物清点"
    "$PY" trace_matrix.py >/dev/null
    ls -l reports/
    echo ">>> 结构化数据在 reports/trace_matrix.json（喂后续度量项目 19 的缺陷漏斗）"
}

do_clean() {  # 删产物、临时库与缓存；labs/11 全程未被写入
    step "clean" "删报告、临时 DB 与缓存——目录回到实验前状态"
    rm -rf reports .orders_tmp.db .pytest_cache __pycache__ tests/__pycache__ 2>/dev/null || true
    ( cd "$REPO/labs/11_sut_app" && rm -rf .pytest_cache tests/__pycache__ 2>/dev/null ) || true
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
