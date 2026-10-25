#!/usr/bin/env bash
# =============================================================================
# mutation.sh — shiftleft 09 主演示脚本：第一轮弱测试体检 → 第二轮强测试对比 →
#               mutmut 生产工具对照 → 清理
# 引擎为自研 AST 变异器（stdlib），逐变异体替换被测模块跑测试；两轮 JSON 留档。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（pytest + 标准库 ast/jsonschema 无关，纯 stdlib 引擎；mutmut 为对照可选）"
    "$PY" -c "import pytest, ast, json" 2>/dev/null && echo "依赖就绪" \
        || "$PY" -m pip install -q pytest
}

do_observe() {
    step "observe" "① 第一轮：弱测试（全绿、断言稀薄）——变异体存活 ≥5 即『假测试实锤』"
    "$PY" run_mutation.py --tests tests/test_weak.py --round 1 --tag 弱测试 2>&1 | tail -12

    step "observe" "② 第二轮：强测试（针对性补断言）——score 提升 ≥20 个百分点"
    "$PY" run_mutation.py --tests tests/test_strong.py --round 2 --tag 强测试 2>&1 | tail -12

    step "observe" "③ 生产工具对照：mutmut 3.8.0 在 Python 3.13 实测可用（探活样例）"
    ( cd probe_mutmut && rm -rf mutants && "$PY" -m mutmut run 2>&1 | tail -2 )
    ( cd probe_mutmut && "$PY" -m mutmut results 2>/dev/null | head -2 )
    echo ">>> results 为空 = 全部变异体被杀死；mutmut 可用（配置键已更名 source_paths），"
    echo ">>> 本实验引擎选自研是为「双套件两轮 + JSON 可复算」完全可控"

    step "observe" "④ 产物清点"
    ls -l reports/
    echo ">>> 存活变异 = 断言缺口清单；唯一两轮都活的 #0 是等价变异（quantize 吸收 1 厘），理论边界"
}

do_clean() {  # 删报告与缓存；pricing.py 由引擎自行还原
    step "clean" "删报告与缓存——目录回到实验前状态"
    rm -rf reports .pytest_cache __pycache__ tests/__pycache__ \
        probe_mutmut/mutants probe_mutmut/.mutmut-cache 2>/dev/null || true
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
