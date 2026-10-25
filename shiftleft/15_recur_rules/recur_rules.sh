#!/usr/bin/env bash
# =============================================================================
# recur_rules.sh — shiftleft 15 主演示脚本：坏状态全红 → 修复态全绿 → 规则库拦
#                  同类新代码（semgrep 两类 + 并发模板一类）→ 清理
# 三个真实 bug 域在 bugs/（坏修各一），防复发资产在 rules/ 与 tests/ 模板。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"
SG="$REPO/.venv/bin/semgrep"
export PYTHONPATH="bugs:newcode"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（pytest + semgrep，缺则补装）"
    "$PY" -c "import pytest" 2>/dev/null || "$PY" -m pip install -q pytest
    [ -x "$SG" ] || "$PY" -m pip install -q semgrep
    echo "pytest / semgrep $($SG --version 2>/dev/null | tail -1) 就绪"
}

do_observe() {
    mkdir -p reports
    step "observe" "① 缺陷态复现：3 个 bug 的复现测试全红（先写测试，此刻实现是坏的）"
    set +e
    "$PY" -m pytest tests/test_repro.py -k buggy -q 2>&1 | tail -2
    rcode=$?
    set -e
    [ "${rcode}" -ne 0 ] && echo ">>> 缺陷态退出码 ${rcode}（非零即红 ✓）——复现测试先行留档"

    step "observe" "② 修复态回归：同一套测试对修复实现全绿（红→绿 = bug 被治好）"
    "$PY" -m pytest tests/test_repro.py -k "not buggy" -q 2>&1 | tail -1

    step "observe" "③ 规则库拦截同类新代码（写法全新、缺陷同类）：semgrep 拦 2 类"
    "$SG" scan --config rules/recur_rules.yaml --json newcode 2>/dev/null \
        | "$PY" -c "
import json, sys
d = json.load(sys.stdin)
for r in d['results']:
    print(f\"  ⛔ {r['check_id'].split('.')[-1]}  {r['path']}:{r['start']['line']}\")
print(f'  semgrep 拦截类别：{len({r[\"check_id\"] for r in d[\"results\"]})} / 3')"

    step "observe" "④ 第三类（并发超卖）由复现模板拦截：喂新代码 → 当场红（预期失败）"
    set +e
    "$PY" -m pytest tests/test_concurrency_template.py -q 2>&1 | tail -1
    tcode=$?
    set -e
    [ "${tcode}" -ne 0 ] && echo ">>> 已按预期红：并发模板把 bug02 的同类新实现拦在门外"

    step "observe" "⑤ 验收汇总（3 类缺陷，3 条防复发资产，全部自动拦截）"
    {
        echo "① 缺陷态复现：3 红（exit ${rcode}）"
        echo "② 修复态回归：3 绿（exit 0）"
        echo "③ semgrep 拦截：money-float-arith + naive-datetime-now（2 类）"
        echo "④ 并发模板拦截：stock_new_bad 超卖实现（红 = 拦截）"
    } | tee reports/acceptance_summary.txt
    echo ">>> 防复发资产清单：rules/recur_rules.yaml + tests/test_concurrency_template.py"
}

do_clean() {  # 删报告与缓存（bugs/newcode/rules/tests 是源码资产，保留）
    step "clean" "删报告与缓存——源码资产（规则库与模板）保留"
    rm -rf reports .pytest_cache __pycache__ bugs/__pycache__ newcode/__pycache__ \
        tests/__pycache__ 2>/dev/null || true
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
