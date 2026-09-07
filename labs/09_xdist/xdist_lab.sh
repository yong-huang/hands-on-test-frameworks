#!/usr/bin/env bash
# =============================================================================
# xdist_lab.sh — lab 09 主演示脚本：并行加速 / 污染现形 / 修复验证 / 分层选跑
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "收集：确认 211 条用例在册（150 常规 + 50 重型 + 冒烟/污染/修复）"
    $PY -m pytest $INI --collect-only -q 2>/dev/null | tail -2
}

do_observe() {
    step "observe" "① 串行基线：150+50 条慢用例的真实耗时"
    T0=$(date +%s.%N); $PY -m pytest $INI -k "not pollution and not fixed and not smoke" 2>/dev/null | tail -1; T1=$(date +%s.%N)
    SERIAL=$(echo "$T1 $T0" | awk '{printf "%.1f", $1-$2}')
    echo ">>> 串行耗时 ${SERIAL}s"

    step "observe" "② -n auto 并行：同样的用例，时间除以核心数附近"
    T0=$(date +%s.%N); $PY -m pytest $INI -n auto -k "not pollution and not fixed and not smoke" 2>/dev/null | tail -1; T1=$(date +%s.%N)
    PAR=$(echo "$T1 $T0" | awk '{printf "%.1f", $1-$2}')
    echo ">>> 并行耗时 ${PAR}s（加速比约 $(echo "$SERIAL $PAR" | awk '{printf "%.1f", $1/$2}')x，结果与串行一致）"

    step "observe" "③ 反面教材：共享计数器在并行下现形（串行绿 → 并行红）"
    $PY -m pytest $INI -k "pollution and not fixed" 2>/dev/null | tail -1
    echo "--- 上面是串行：恰好全绿（顺序依赖被文件顺序掩护）---"
    set +e
    $PY -m pytest $INI -n auto -k "pollution and not fixed" 2>/dev/null | tail -2
    echo ">>> 并行下计数器被隔离，序号断言当场翻车（预期失败演示）"
    set -e

    step "observe" "④ 修复版：独立 fixture 的同款用例在并行下全绿"
    $PY -m pytest $INI -n auto -k "fixed" 2>/dev/null | tail -1

    step "observe" "⑤ marker 分层：-m smoke 只跑冒烟子集（秒级反馈）"
    T0=$(date +%s.%N); $PY -m pytest $INI -m smoke 2>/dev/null | tail -1; T1=$(date +%s.%N)
    echo ">>> 冒烟耗时 $(echo "$T1 $T0" | awk '{printf "%.1f", $1-$2}')s"

    step "observe" "⑥ --durations 找慢用例（-q 会吞表，用 -o addopts= 还原详细输出）"
    $PY -m pytest $INI -o addopts="" -k "test_case and not heavy" --durations=3 2>/dev/null | grep -A4 "slowest" | head -6
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
