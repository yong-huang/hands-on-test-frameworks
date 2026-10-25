#!/usr/bin/env bash
# =============================================================================
# perf_budget.sh — shiftleft 18 主演示脚本：正常 SUT 预算全绿 → 延迟注入变红
#                  （实测 vs 预算）→ pytest 包装 → 清理
# 预算引擎 perf_budget.py 读 configs/budget.yaml，对 labs/11 SUT 并发取样。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（httpx + pyyaml，缺则补装）"
    "$PY" -c "import httpx, yaml" 2>/dev/null || "$PY" -m pip install -q httpx pyyaml
    echo "httpx + pyyaml 就绪"
}

do_observe() {
    mkdir -p reports

    step "observe" "① 正常 SUT 预算全绿（3 接口 × 20 取样 × 10 并发，<60s）"
    start=$SECONDS
    "$PY" perf_budget.py 2>&1
    echo ">>> 全绿耗时 $((SECONDS - start))s（<60s 达标）"

    step "observe" "② 延迟注入演示：追加 /api/slow-config（1.5s 内建延迟）→ 报红 + 实测 vs 预算"
    set +e
    "$PY" perf_budget.py --include-slow > reports/slow_run.txt 2>&1
    rcode=$?
    set -e
    grep -E "⛔|❌|slow" reports/slow_run.txt | head -4
    [ "${rcode}" -ne 0 ] && echo ">>> 已按预期退出 ${rcode}（非零即红）：预算 200ms vs 实测 ~1500ms——这就是「预算即测试」"

    step "observe" "③ pytest 包装：CI 可直接用 pytest 退出码当门禁"
    ( cd "$REPO/shiftleft/18_perf_budget" && "$PY" -m pytest test_perf_budget.py -q ) 2>&1 | tail -1

    step "observe" "④ 产物清点"
    ls -l reports/
    echo ">>> 预算集中在 configs/budget.yaml——改预算重跑，红绿立即变化"
}

do_clean() {  # 删报告与缓存
    step "clean" "删报告与缓存——目录回到实验前状态"
    rm -rf reports .pytest_cache __pycache__ 2>/dev/null || true
    echo "已清理（labs/11 SUT 数据库由 conftest 种子/清理，无残留）"
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
