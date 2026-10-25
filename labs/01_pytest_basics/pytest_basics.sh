#!/usr/bin/env bash
# =============================================================================
# pytest_basics.sh — lab 01 主演示脚本
# 生命周期：apply(准备) → observe(观察运行规则) → clean(清理)
# 任意 cwd 运行都正确；全部命令真实执行，输出即教材。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

# 共享 venv（由 scripts/load_resources.sh 一次性创建，实验脚本只引用不重建）
PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."   # rootdir 固定在实验根，报告路径才可读

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "确认被测模块可导入 + 用例收集符合预期（开工第一步）"
    $PY -c "import temperature; print('被测模块 OK:', temperature.celsius_to_fahrenheit(100), '°F')"
    # --collect-only 先看"pytest 会收集哪些用例"，15 条 = 14 正常 + 1 故意失败
    $PY -m pytest $INI --collect-only -q | tail -3
}

do_observe() {
    step "observe" "① 全量运行：故意失败的用例如何被断言重写展开"
    # 预期失败（14 passed, 1 failed）——这正是教学点，故 || true 放行
    $PY -m pytest $INI || true

    step "observe" "② -k 圈选：把故意失败用例排除后应全绿"
    $PY -m pytest $INI -k "not regression_demo" -q

    step "observe" "③ -x 早停：第一个失败立即停下（后面用例不再执行）"
    # -x 会在 regression_demo 失败处刹车，属预期，|| true 放行
    $PY -m pytest $INI -x -q || true

    step "observe" "④ -s 捕获关闭：同一条命令，print 先被捕获吞掉、加 -s 后直达终端"
    $PY -m pytest $INI -k "thermostat_modes" -q
    echo ">>> 上一步看不到 print？默认输出捕获把它吞了。加 -s 关闭捕获看对比："
    $PY -m pytest $INI -k "thermostat_modes" -s -q
}

do_clean() {
    step "clean" "清理 pytest 缓存与字节码，目录回到实验前状态"
    rm -rf .pytest_cache tests/__pycache__ __pycache__
    echo "已清理 .pytest_cache / __pycache__"
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
