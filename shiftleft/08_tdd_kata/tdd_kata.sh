#!/usr/bin/env bash
# =============================================================================
# tdd_kata.sh — shiftleft 08 主演示脚本：TDD 操练全程回放 → git 历史纪律核验 →
#               提交序列清点 → 清理
# 操练在独立 git 仓库 ./repo 中进行（每次重跑重建），绝不触碰 labs/11。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（git + pytest，幂等）"
    command -v git >/dev/null && echo "git 就绪：$(git --version)"
    "$PY" -c "import pytest" 2>/dev/null && echo "pytest 就绪" || "$PY" -m pip install -q pytest
}

do_observe() {
    step "observe" "① TDD 操练全程回放：5 轮「红→绿」+ 1 次重构，每步提交并实测红绿"
    "$PY" kata.py

    step "observe" "② 纪律核验：git 历史顺序 + runs.log + 当场重跑，五条断言"
    "$PY" verify_history.py

    step "observe" "③ 提交序列清点（时间线）"
    git -C repo log --reverse --format='%h %s' | head -12
    echo ">>> 每个实现提交之前都有失败测试提交；重构提交后测试保持绿——这就是 TDD 的账本"
}

do_clean() {  # 删操练仓库与缓存（下次重跑自动重建）
    step "clean" "删操练仓库、报告与缓存——目录回到实验前状态"
    rm -rf repo reports .pytest_cache __pycache__ 2>/dev/null || true
    echo "已清理（labs/11 全程未被触碰）"
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
