#!/usr/bin/env bash
# =============================================================================
# async_lab.sh — lab 08 主演示脚本：异步重试 / 时间加速 / 超时取消
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "收集 8 条异步用例（asyncio_mode=auto 免去逐个打 mark）"
    $PY -m pytest $INI --collect-only -q | tail -2
}

do_observe() {
    step "observe" "① 全量运行：重试/退避/超时/取消/冻结一次全过"
    TIMEFORMAT='>>> 本套件真实耗时 %R s（其中一条用例名义上要退避 3.5 秒）'
    time $PY -m pytest $INI -q

    step "observe" "② 单跑'退避加速'用例：名义 3.5s、真实 <1s 的证据"
    $PY -m pytest $INI -k accelerated -v -q 2>&1 | grep -E "PASSED|passed" | head -3

    step "observe" "③ 异步错误归因：asyncio 报错能精确定位到测试行（看看回溯）"
    $PY -m pytest $INI -k exhausted -q 2>&1 | tail -3
}

do_clean() {
    step "clean" "清理缓存"
    rm -rf .pytest_cache tests/__pycache__ __pycache__
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
