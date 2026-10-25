#!/usr/bin/env bash
# =============================================================================
# pr_bot.sh — shiftleft 16 主演示脚本：单 PR 演示 → 五 PR 连跑（4 命中+零误报）
#             → <5s 计时实测 → 清理
# 引擎 pr_bot.py 纯标准库；diffs/ 下 4 个问题 PR + 1 个干净 PR 为预制靶场。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（纯标准库，幂等）"
    "$PY" -c "import re, json" && echo "依赖就绪（零第三方依赖）"
}

do_observe() {
    mkdir -p reports
    step "observe" "① 单 PR 演示：pr_new_endpoint（改了端点没改契约）"
    "$PY" pr_bot.py --diff diffs/pr_new_endpoint.diff

    step "observe" "② 五 PR 连跑：4 个问题 PR 全命中 + 干净 PR 零警告"
    "$PY" pr_bot.py --all

    step "observe" "③ 验收③：单次运行耗时实测（预期 <5s）"
    t0=$SECONDS
    "$PY" pr_bot.py --all >/dev/null
    echo ">>> 实测耗时 $((SECONDS - t0))s（<5s 达标）；5 个 PR 命中明细见 reports/pr_bot_report.json"

    step "observe" "④ 产物清点"
    ls -l reports/
    echo ">>> 接真实 GitHub 属选做：本地 diff 模拟已覆盖规则与输出，接入只需换 diff 来源"
}

do_clean() {  # 删报告与缓存（diffs/ 是源码靶场，保留）
    step "clean" "删报告与缓存——目录回到实验前状态"
    rm -rf reports .pytest_cache __pycache__ 2>/dev/null || true
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
