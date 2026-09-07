#!/usr/bin/env bash
# 00 环境体检：本实验只是 scripts/load_resources.sh 的入口演示
set -euo pipefail
cd "$(dirname "$0")/../.."

step() { echo; echo "=====> [$1] $2"; }

do_observe() {
    step "observe" "对 30 个实验的前置做一次全量体检"
    bash scripts/load_resources.sh check
    echo
    echo "提示：标记 ⚠️ 的项去对应实验前先 bash scripts/load_resources.sh 补齐"
}

main() {
    local target="${1:-observe}"
    case "${target}" in
        observe) do_observe ;;
        all)     do_observe ;;
        *) echo "可用: observe | all" >&2; exit 1 ;;
    esac
}
main "$@"
