#!/usr/bin/env bash
# =============================================================================
# dft_refactor.sh — shiftleft 07 主演示脚本：行为等价（双实现）→ 过期语义对照 →
#                   可测性度量报告 → 清理
# legacy/ 是 labs/11 会话语义的复刻（硬编码时钟/随机/模块级状态），
# refactored/ 是依赖注入版——labs/11 本体全程零改动。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（venv + pytest，幂等）"
    "$PY" -c "import pytest" 2>/dev/null && echo "依赖就绪" || "$PY" -m pip install -q pytest
}

do_observe() {
    step "observe" "① 行为等价：同一套 4 用例 × 两个实现（legacy 适配器 / DI 服务）全绿"
    "$PY" -m pytest tests/test_behavior.py -q 2>&1 | tail -1
    echo ">>> 双实现全绿 = 重构不改行为的证明；行为与机制（时间/随机/存储）已分离"

    step "observe" "② 过期语义对照：legacy 真睡 1 秒 vs fake clock 拨针（毫秒内）"
    "$PY" -m pytest tests/test_expiry.py -v 2>&1 | grep -E "PASSED|passed" | head -4

    step "observe" "③ 可测性度量报告：墙钟/全局触碰/行数/等价性，全部机械可复核"
    "$PY" measure_dft.py

    step "observe" "④ 产物清点"
    ls -l reports/
    echo ">>> labs/11 全程零改动（本目录 legacy/ 是语义复刻，非共享文件）"
}

do_clean() {  # 删报告与缓存，无进程残留（本实验不起服务）
    step "clean" "删报告与缓存——目录回到实验前状态"
    rm -rf reports .pytest_cache __pycache__ legacy/__pycache__ \
        refactored/__pycache__ tests/__pycache__ 2>/dev/null || true
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
