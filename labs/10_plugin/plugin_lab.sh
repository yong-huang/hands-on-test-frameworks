#!/usr/bin/env bash
# =============================================================================
# plugin_lab.sh — lab 10 主演示脚本：装插件 → 四能力验证 → 跨项目复用
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "pip install -e . ——插件以可编辑模式装进共享 venv（pytest11 入口点自动加载）"
    "$PY" -m pip install -q -e .
    "$PY" -m pytest --co -q 2>/dev/null | head -1
    echo ">>> 上面 plugins 行出现 ministore-report-0.1.0 即安装成功（注意：不开 --ministore 它是隐形的）"

    step "apply" "收集演示用例"
    "$PY" -m pytest $INI --collect-only -q 2>/dev/null | tail -2
}

do_observe() {
    step "observe" "① 全量跑（含一条故意失败）：插件生成 ministore-report.json + contexts/*.json"
    set +e
    "$PY" -m pytest $INI --ministore -q 2>/dev/null | tail -4
    set -e
    echo "--- 报告内容："
    cat ministore-report.json
    echo "--- 失败上下文（节选）："
    grep -E "nodeid|exception" contexts/*.json | head -4

    step "observe" "② 慢用例自动打标：报告 slow 列表里是 test_slow_case（0.3s > 0.1s 阈值）"
    "$PY" -m pytest $INI --ministore --ministore-slow-threshold 0.05 -q -k slow_case 2>/dev/null | tail -2

    step "observe" "③ marker 校验：非法 tier='prod' 在收集期直接 UsageError（预期失败演示）"
    set +e
    "$PY" -m pytest $INI --ministore badcase/test_bad_marker.py 2>&1 | grep -E "ERROR|ministore" | head -3
    echo ">>> 退出码非 0：坏配置在跑任何用例之前就被拦下"
    set -e

    step "observe" "④ 跨项目复用：去 01_pytest_basics 直接用 --ministore（同 venv 无需再装）"
    (cd ../01_pytest_basics && set +e && "$PY" -m pytest -c configs/pytest.ini --rootdir=. --ministore -q 2>/dev/null | tail -2; set -e)
    echo "--- lab 01 目录里生成的报告（故意失败用例也被落了上下文）："
    grep -E '"failed"' -A3 ../01_pytest_basics/ministore-report.json | head -5
    rm -rf ../01_pytest_basics/ministore-report.json ../01_pytest_basics/contexts  # 复用演示后清理，不污染 01
}

do_clean() {
    step "clean" "清理本实验的产物与缓存（插件保留安装——不开 --ministore 无副作用）"
    rm -rf .pytest_cache tests/__pycache__ pytest_ministore_report/__pycache__ \
           contexts ministore-report.json *.egg-info
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
