#!/usr/bin/env bash
# =============================================================================
# static_gate.sh — shiftleft 11 主演示脚本：全量拦截 → 干净放行 → 规则升降级三连
#                   → 清理
# 门禁引擎在 gate.py（ruff + mypy），分级表在 configs/（error 阻断 / warning 放行）。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（ruff + mypy，缺则装入仓库 venv，幂等）"
    "$PY" -c "import ruff" 2>/dev/null || "$PY" -m pip install -q ruff
    "$PY" -m mypy --version >/dev/null 2>&1 || "$PY" -m pip install -q mypy
    echo "$("$(command -v ruff)" --version) / $("$PY" -m mypy --version | head -1)"
}

do_observe() {
    step "observe" "① 全量 fixtures：3 个坏文件 4 个 error 级发现（B006/F821/mypy 类型）→ 阻断"
    "$PY" gate.py --path fixtures || true
    echo ">>> 已按预期阻断（exit 1）：规则码逐个列出，这就是门禁的『证据清单』"

    step "observe" "② 干净文件：零发现 → 放行"
    "$PY" gate.py --path fixtures/clean.py

    step "observe" "③ 升降级演示：bad_style 的 F401 默认只 warning（放行）→"
    "$PY" gate.py --path fixtures/bad_style.py 2>&1 | tail -1
    echo "    换严格档（F401 升 error）→"
    "$PY" gate.py --path fixtures/bad_style.py \
        --config configs/gate_rules_strict.toml 2>&1 | tail -1 || true
    echo "    回默认档（降级恢复）→"
    "$PY" gate.py --path fixtures/bad_style.py 2>&1 | tail -1
    echo ">>> 升降级只动 configs/ 的分级表，引擎零改动——分级即治理"
}

do_clean() {  # 删报告与缓存（.mypy_cache 一并清）
    step "clean" "删报告与缓存——目录回到实验前状态"
    rm -rf reports .pytest_cache __pycache__ .mypy_cache 2>/dev/null || true
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
