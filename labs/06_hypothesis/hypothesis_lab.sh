#!/usr/bin/env bash
# =============================================================================
# hypothesis_lab.sh — lab 06 主演示脚本：性质测试 / 收缩 / 状态机
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "确认性质用例收集（收缩演示那条预期失败，先看清楚名单）"
    $PY -m pytest $INI --collect-only -q | tail -3
}

do_observe() {
    step "observe" "① 全量运行：只有埋雷的 buggy_mean 一条失败——其余性质全绿"
    # 预期失败（Falsifying example 被自动收缩成最小样例）——核心教学点，|| true 放行
    $PY -m pytest $INI -q 2>&1 | grep -E "passed|failed|Falsifying| Shrunk|False" | head -8 || true
    set +e
    $PY -m pytest $INI -k buggy_mean -q 2>&1 | sed -n '/Falsifying/,/^$/p;/Failing explicit/,/^$/p' | head -8
    echo ">>> 上面就是收缩后的最小复现（Falsifying example + Shrunk）"
    set -e

    step "observe" "② 修复版 stable_mean 的同性质用例应稳定通过（跑 2 遍证明不抖）"
    $PY -m pytest $INI -k stable_mean -q
    $PY -m pytest $INI -k stable_mean -q

    step "observe" "③ 状态机：随机规则序列 + 不变量实时校验"
    $PY -m pytest $INI -k stateful -q
}

do_clean() {
    step "clean" "清理缓存与 Hypothesis 例子数据库（.hypothesis/）"
    rm -rf .pytest_cache tests/__pycache__ __pycache__ .hypothesis
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
