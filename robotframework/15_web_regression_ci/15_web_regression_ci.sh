#!/usr/bin/env bash
# 15_web_regression_ci.sh — 项目 15：🏁 Web 回归套件 + act 本地 CI
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起 Robot 靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "① 本地：回归套件 --include regression 一条命令全绿"
    "$PY" -m robot --include regression --outputdir reports suites/
    step "observe" "② act 本地真跑 workflow 的 regression job（Docker 内，与 CI 同源）"
    if command -v act >/dev/null 2>&1; then
        # act 跑整个仓库的 workflow；只挑本项目的 job 名，日志过滤到关键行
        (cd "$SERIES/.." && act push -j regression \
            -P ubuntu-latest=catthehacker/ubuntu:act-latest \
            -W "$SERIES/15_web_regression_ci/.github/workflows/regression.yml" 2>&1 | grep -E '✅|❌|Success|Failure|robot-web-regression' | head -6) \
            || echo "    （act 跑法见 README 踩坑：镜像拉取/权限问题时的降级口径）"
    else
        echo "    act 未安装（brew install act）；workflow 语法用 actionlint 校验"
        command -v actionlint >/dev/null 2>&1 && actionlint .github/workflows/regression.yml && echo "    ✅ actionlint 零告警"
    fi
}

do_clean() {
    step "clean" "清运行产物"
    rm -rf reports
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
