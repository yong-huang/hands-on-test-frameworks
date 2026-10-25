#!/usr/bin/env bash
# =============================================================================
# antipattern.sh — shiftleft 10 主演示脚本：坏样本靶场 → 好样本零误报 →
#                  labs 全量真实报告（只读）→ 清理
# 引擎 detector.py 纯标准库（ast + re），全程只读不修改任何被扫文件。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（纯标准库 ast/re，幂等）"
    "$PY" -c "import ast, re" && echo "依赖就绪（零第三方依赖）"
}

do_observe() {
    step "observe" "① 坏样本靶场：10 个埋点全部命中（≥9/10 达标）"
    "$PY" detector.py --path samples/bad --no-save 2>&1 | sed -n '1,3p;/规则命中统计/,$p'

    step "observe" "② 好样本零误报：断言精确的对照目录必须零命中（gate 模式）"
    "$PY" detector.py --path samples/good --no-save --gate
    echo ">>> 零误报 ✓"

    step "observe" "③ labs 全量真实报告（37 个测试文件，只读不修改）"
    "$PY" detector.py --path ../../labs 2>&1 | sed -n '1,3p;/规则命中统计/,$p'

    step "observe" "④ 产物清点"
    ls -l reports/
    echo ">>> labs 报告里的每一条都可以人工核对——真实资产的反模式是治理清单，不是分数"
}

do_clean() {  # 删报告与缓存（本实验不起服务、不改被扫文件）
    step "clean" "删报告与缓存——目录回到实验前状态"
    rm -rf reports .pytest_cache __pycache__ 2>/dev/null || true
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
