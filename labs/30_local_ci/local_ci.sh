#!/usr/bin/env bash
# =============================================================================
# local_ci.sh — lab 30 主演示脚本：make 快速流水线 → act 复跑同一 workflow
# act 前置：Docker + 本目录为 git 仓库（act 依赖 git 上下文）
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")/../.."     # 到仓库根：Makefile 与 .github 都在根上

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "检查 git 仓库状态（act 的硬前置；仓库由实验首次运行时初始化）"
    git rev-parse --is-inside-work-tree >/dev/null 2>&1 && echo "git 仓库 OK" || {
        echo "未发现 git 仓库——执行 git init（仅本地，不推送）"
        git init -q
    }
    command -v act >/dev/null && act --version | head -1
}

do_observe() {
    step "observe" "① make 快速流水线：unit → api（失败即阻断，语义同 CI）"
    make unit api

    step "observe" "② act 本地复跑 workflow 的 unit-core job（Docker 内执行，与 CI 同源）"
    # act 首跑要拉镜像 catthehacker/ubuntu:act-latest（约数百 MB，耐心）
    act push -j unit-core -P ubuntu-latest=catthehacker/ubuntu:act-latest 2>&1 | grep -E "✅|❌|Success|Failure|Run pytest" | head -10 || true

    step "observe" "③ GitHub 真流水线：push 后自动跑全部 6 层（本文件即是定义）"
    echo ">>> 完整分层见 .github/workflows/tests.yml"
    echo ">>> 全量本地等价：make quality（单测→API→E2E→k6→a11y 全跑，约 10 分钟）"
}

do_clean() {
    step "clean" "清理各层运行产物"
    make clean
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
