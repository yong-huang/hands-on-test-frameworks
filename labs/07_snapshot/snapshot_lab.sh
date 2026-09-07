#!/usr/bin/env bash
# =============================================================================
# snapshot_lab.sh — lab 07 主演示脚本：快照 破坏→红→更新→绿 完整闭环
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

PY="$PWD/../../.venv/bin/python"
INI="-c configs/pytest.ini --rootdir=."

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "首跑生成快照（相当于给当前输出'拍照存档'），然后验证全绿"
    if [ ! -f tests/__snapshots__/test_snapshot.ambr ]; then
        $PY -m pytest $INI --snapshot-update -q
        echo ">>> 快照已生成，先肉眼审查 __snapshots__ 内容再提交！"
    fi
    $PY -m pytest $INI -q
}

do_observe() {
    step "observe" "① '需求变了'：SNAP_BREAK=1 模拟输出被改（total +1 元、td→th）→ 快照变红"
    # 预期失败：快照 diff 正是审查工具——哪行变了看得一清二楚
    set +e
    SNAP_BREAK=1 $PY -m pytest $INI -q 2>&1 | grep -E "passed|failed|↓|↑|-\s|\+\s" | head -16
    echo ">>> 退出码非 0：输出与快照不一致，必须人审 diff"
    set -e

    step "observe" "② 确认这是'合法变更'后有意更新快照：--snapshot-update → 重新变绿"
    SNAP_BREAK=1 $PY -m pytest $INI --snapshot-update -q
    SNAP_BREAK=1 $PY -m pytest $INI -q

    step "observe" "③ 恢复正常输出，再次 --snapshot-update 存档'正确版本'，收尾全绿"
    $PY -m pytest $INI --snapshot-update -q
    $PY -m pytest $INI -q
}

do_clean() {
    step "clean" "清理缓存（保留 __snapshots__——快照应提交进版本库）"
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
