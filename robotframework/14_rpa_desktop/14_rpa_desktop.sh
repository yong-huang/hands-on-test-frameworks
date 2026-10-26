#!/usr/bin/env bash
# 14_rpa_desktop.sh — 项目 14：RPA——桌面应用自动化（macOS 计算器）
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 辅助功能权限自检（System Events 可控进程才跑得动）"
    if ! osascript -e 'tell application "System Events" to get name of first process' >/dev/null 2>&1; then
        echo "    ❌ 无辅助功能权限：系统设置 → 隐私与安全性 → 辅助功能，勾选运行本脚本的终端" >&2
        exit 1
    fi
    echo "    ✅ 辅助功能权限可用"
    step "apply" "② 计算器前台就绪"
    osascript -e 'tell application "Calculator" to activate' 2>/dev/null || { echo "❌ 计算器应用不存在" >&2; exit 1; }
}

do_observe() {
    step "observe" "计算器 5 道四则 + 剪贴板搬运（有头流程：屏幕上会看到计算器自己动）"
    "$PY" -m robot --outputdir reports rpa_desktop.robot
}

do_clean() {
    step "clean" "清运行产物（计算器保持打开，供人工复核）"
    rm -rf reports
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
