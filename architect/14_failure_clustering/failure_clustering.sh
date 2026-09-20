#!/usr/bin/env bash
# =============================================================================
# failure_clustering.sh — architect 14 主演示脚本：
# 生成 50 条模拟失败（3 个真实根因+噪声）→ 指纹聚类 → 验收断言 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$(cd ../.. && pwd)/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 纯离线实验，无外部依赖（50 条失败由固定种子生成，可复现）"
    echo "根因分布：gateway_timeout×60% / db_locked×30% / config_drift×10%"
}

do_observe() {
    step "observe" "① 指纹聚类：归一化（数字/路径/hex/引号内容→占位符）+ 相似度合并"
    set +e
    "$PY" cluster.py
    rc=$?
    set -e
    [ "$rc" -eq 0 ] || { echo "❌ 验收未过"; exit 1; }

    step "observe" "② 可复现性：换种子重跑（失败样例不同，根因簇数应稳定）"
    "$PY" cluster.py --n 60 --out reports/seed2 2>&1 | grep -E "根因簇|纯度|验收"
    echo ">>> 验收：50 条 3 根因聚成 ≤5 簇、最大簇纯度 ≥80%、先修排序可见"
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
