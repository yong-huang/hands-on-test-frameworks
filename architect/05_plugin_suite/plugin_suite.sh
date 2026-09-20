#!/usr/bin/env bash
# =============================================================================
# plugin_suite.sh — architect 05 主演示脚本：
# pip install -e 安装 qa_kit → 零侵入跑演示套件（evidence+慢排行+分层统计）
# → -m smoke 只跑冒烟层 → 卸载还原环境 → 清理
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① pip install -e qa_kit（entry point pytest11 自动加载，本地安装不联网）"
    "$PY" -m pip install -e qa_kit --no-build-isolation -q 2>&1 | tail -1 || true
    "$PY" -c "from importlib.metadata import entry_points; \
eps = [e for e in entry_points(group='pytest11') if e.name == 'qa_kit']; \
print('pytest11 entry point 已注册:', bool(eps)); import sys; sys.exit(0 if eps else 1)" \
        && echo "插件已被 pytest 识别 ✅"
}

do_observe() {
    step "observe" "① 零侵入跑演示套件：代码里没有任何 import qa_kit，能力全来自配置"
    set +e
    "$PY" -m pytest demo_tests -c demo_tests/pytest.ini --rootdir=demo_tests -q \
        --qa-evidence-dir=evidence --qa-slow-threshold=0.5 --qa-slow-report=reports/slow_tests.json
    rc=$?
    set -e
    echo ">>> 套件退出码 ${rc}（1 = 含故意失败用例，属演示设计）"

    step "observe" "② 失败留现场：evidence/ 目录里是失败用例的全套现场"
    ls evidence/
    head -7 evidence/*.txt | head -10

    step "observe" "③ 慢用例排行与分层统计"
    cat reports/slow_tests.json | "$PY" -c "import json,sys; d=json.load(sys.stdin); print('阈值:', d['threshold_s'], 's'); [print(f'  {t}s  {n}') for n, t in d['slow']]"

    step "observe" "④ -m smoke 只跑冒烟层（分层分发：PR 快反馈的选型基础）"
    "$PY" -m pytest demo_tests -c demo_tests/pytest.ini --rootdir=demo_tests -q -m smoke --qa-slow-threshold=0.5 2>&1 | tail -2
    echo ">>> 验收：pip install -e 后零侵入生效（evidence+慢排行+分层统计+smoke 圈选）"
}

do_clean() {
    step "clean" "卸载插件、删产物——环境与目录都回到实验前状态"
    "$PY" -m pip uninstall -y qa-kit -q 2>&1 | tail -1 || true
    rm -rf evidence reports demo_tests/__pycache__ demo_tests/.pytest_cache \
        qa_kit/src/qa_kit/__pycache__ qa_kit/*.egg-info
    echo "已清理（插件已卸载，venv 恢复原状）"
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
