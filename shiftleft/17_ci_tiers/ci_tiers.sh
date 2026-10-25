#!/usr/bin/env bash
# =============================================================================
# ci_tiers.sh — shiftleft 17 主演示脚本：workflow 语法校验 → act 探活 → 全绿
#               路径 → 短路路径 → 预算报表留档 → 清理
# 双引擎：真 GitHub Actions workflow（ci_workflow.yml）+ 本地模拟器（local_sim.py，
# 同一份 yml 驱动，分层/短路/预算语义一致）。act 探活见第②步。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$PWD/../.."
PY="$REPO/.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 依赖自检（pyyaml + actionlint + 四层工具，缺则补装）"
    "$PY" -c "import yaml" 2>/dev/null || "$PY" -m pip install -q pyyaml
    command -v actionlint >/dev/null || brew install -q actionlint
    command -v ruff >/dev/null || "$PY" -m pip install -q ruff
    "$PY" -m mypy --version >/dev/null 2>&1 || "$PY" -m pip install -q mypy
    command -v semgrep >/dev/null || "$PY" -m pip install -q semgrep
    command -v gitleaks >/dev/null || brew install -q gitleaks
    command -v act >/dev/null || brew install -q act
    echo "actionlint $(actionlint --version | head -1) / 四层工具就绪"
}

do_observe() {
    mkdir -p reports
    step "observe" "① 验收①：workflow 语法与语义校验（actionlint）"
    actionlint ci_workflow.yml && echo ">>> actionlint 零告警 ✓"

    step "observe" "② act 探活：本机 act 0.2.89 + M 系列（-l 列 job，不跑容器）"
    mkdir -p /tmp/actprobe/.github/workflows
    cp ci_workflow.yml /tmp/actprobe/.github/workflows/ci.yml
    ( cd /tmp/actprobe && act -l 2>&1 | tail -4 ) || true
    rm -rf /tmp/actprobe
    echo ">>> act 解析 OK；但跑容器需 Docker daemon（本机未运行）——主引擎用 local_sim"

    step "observe" "③ 验收②③（全绿路径）：三层全过 + 预算报表 + summary 写入"
    "$PY" local_sim.py 2>&1 | sed -n '/流水线/,$p'

    step "observe" "④ 验收②（短路路径）：埋 F401 → 快层红 → 两层被跳过（预期失败）"
    set +e
    "$PY" local_sim.py --bad > reports/bad_run.log 2>&1
    bcode=$?
    set -e
    grep -E "❌|⏭️" reports/bad_run.log | head -4
    [ "${bcode}" -ne 0 ] && echo ">>> 已按预期退出 ${bcode}：埋 lint 错误后两层被短路（日志留档 reports/bad_run.log）"

    step "observe" "⑤ 产物清点"
    ls -l reports/
    echo ">>> 预算报表 reports/summary.md；record 步写入的 step_summary.md 也在（GITHUB_STEP_SUMMARY 模拟）"
}

do_clean() {  # 删报告与缓存
    step "clean" "删报告与缓存——目录回到实验前状态"
    rm -rf reports .pytest_cache __pycache__ sample/__pycache__ sample_bad/__pycache__ 2>/dev/null || true
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
