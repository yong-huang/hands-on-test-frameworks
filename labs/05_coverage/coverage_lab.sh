#!/usr/bin/env bash
# =============================================================================
# coverage_lab.sh — lab 05 主演示脚本：分支覆盖率 + 门禁 + HTML 报告
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."
export COVERAGE_RCFILE="$PWD/configs/.coveragerc"   # coverage.py 认这个环境变量

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "清空旧覆盖率数据，准备干净的度量环境"
    rm -rf reports .coverage coverage.xml
    echo "已清空旧报告"
}

do_observe() {
    step "observe" "① 只跑基础用例集 + 门禁 90%：故意看它失败（退出码非 0）"
    # 预期失败——门禁低于阈值就应当拦截，这正是教学点，|| true 放行
    set +e
    $PY -m pytest $INI tests/test_discount.py \
        --cov --cov-branch --cov-fail-under=90 -q 2>&1 | tail -13
    echo ">>> 退出码 = ${PIPESTATUS[0]:-?}（非 0 即 CI 会拦下这次提交）"
    set -e

    step "observe" "② 全量（基础+补漏）再跑：分支覆盖率 ≥90%，门禁放行"
    $PY -m pytest $INI --cov --cov-branch --cov-fail-under=90 -q 2>&1 | tail -5
    echo ">>> 退出码 = 0（门禁通过）"

    step "observe" "③ 生成 HTML 报告，浏览器打开可逐行着色查看"
    $PY -m coverage html -d reports/htmlcov
    $PY -m coverage xml -o reports/coverage.xml
    echo "报告已生成: reports/htmlcov/index.html, reports/coverage.xml"
}

do_clean() {
    step "clean" "清理覆盖率产物与缓存"
    rm -rf .pytest_cache tests/__pycache__ __pycache__ .coverage coverage.xml
    echo "已清理（保留 reports/ 供查看，可手动删除）"
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
