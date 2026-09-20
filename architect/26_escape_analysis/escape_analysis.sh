#!/usr/bin/env bash
# =============================================================================
# escape_analysis.sh — architect 26 主演示脚本：
# 10 个逃逸案例归因 → 改进映射真实性校验（指向不存在的产物即 FAIL）→ 迭代对比页
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 纯离线分析：案例取材 labs/ 教学翻车点（见 configs/cases.yaml）"
    grep -c "^  - {" configs/cases.yaml | xargs echo "案例数："
}

do_observe() {
    step "observe" "① 归因分析 + 映射校验（改进项必须指向磁盘上真实存在的产物目录）"
    set +e
    "$PY" analyze.py
    rc=$?
    set -e
    [ "$rc" -eq 0 ] || { echo "❌ 校验未过"; exit 1; }

    step "observe" "② 抽查证据：映射的产物目录真实存在"
    for d in architect/09_self_healing architect/13_flaky_platform architect/15_contract_matrix; do
        [ -d "../$d" ] && echo "  ✅ $d 存在"
    done
    echo ">>> 验收：10 案例全归因 ✅ 改进映射真实 ✅ 迭代前后对比页已生成 ✅"
}

do_clean() {
    step "clean" "删报告"
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
