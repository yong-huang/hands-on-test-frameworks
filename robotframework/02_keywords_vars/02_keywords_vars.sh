#!/usr/bin/env bash
# 02_keywords_vars.sh — 项目 2：关键字宇宙与变量体系
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起 Robot 靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "① 正式跑：业务语言测试层 + FOR/IF"
    "$PY" -m robot --outputdir reports keywords_vars.robot
    step "observe" "② --dryrun 干跑（关键字引用完整性校验，不开浏览器）"
    "$PY" -m robot --dryrun --outputdir reports_dry keywords_vars.robot
    grep -E 'pass' reports_dry/output.xml >/dev/null && echo "    ✅ dryrun 通过"
}

do_clean() {
    step "clean" "清运行产物"
    rm -rf reports reports_dry
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
