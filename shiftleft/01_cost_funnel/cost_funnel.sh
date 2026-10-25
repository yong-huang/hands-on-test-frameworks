#!/usr/bin/env bash
# =============================================================================
# cost_funnel.sh — shiftleft 01 主演示脚本：依赖自检 → 跑六关漏斗 → 单关细看 →
#                  对照组 → 清理
# 漏斗引擎在 cost_funnel.py，六个检测器在 gates/，本脚本负责串出演示动线。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（venv + pyyaml/fastapi/uvicorn/requests/pytest，幂等）"
    "$PY" -c "import yaml, fastapi, uvicorn, requests, pytest" 2>/dev/null \
        && echo "依赖就绪" \
        || "$PY" -m pip install -q pyyaml fastapi uvicorn requests pytest
}

do_observe() {
    step "observe" "① 全量漏斗：缺陷实现（float 金额）过六关，应 6/6 拦截"
    "$PY" cost_funnel.py

    step "observe" "② 单关细看：静态分析关的完整检出报告（其余关同理：--gate N）"
    "$PY" gates/gate3_static.py

    step "observe" "③ 对照组：好实现（Decimal 金额）过同一漏斗，代码关应全放行"
    "$PY" cost_funnel.py --impl good

    step "observe" "④ 产物清点"
    ls -l reports/
    echo ">>> 完整成本表见 reports/cost_funnel.md；结构化数据在 reports/cost_funnel.json（喂后续度量项目 19）"
}

do_clean() {  # 删干净无残留：摘端口孤儿 + 删报告与缓存
    step "clean" "摘掉 mini API 端口残留（8931/8932），删报告与缓存"
    lsof -ti :8931 :8932 2>/dev/null | xargs kill 2>/dev/null || true
    rm -rf reports .pytest_cache __pycache__ gates/__pycache__ defect/__pycache__ \
        defect/.pytest_cache 2>/dev/null || true
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
