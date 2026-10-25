#!/usr/bin/env bash
# 17_final_python.sh — 项目 17：🏁 终极套件（POM+数据驱动+多浏览器+留证+HTML 报告）
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起共享靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "① 回归套件 × 双浏览器（Chrome/Firefox；Safari 的 JS-click 兜底见项目 14）"
    cd "$SERIES"
    local rc=0
    for B in chrome firefox; do
        echo "    —— 浏览器: $B ——"
        SELENIUM_BROWSER=$B HEADLESS=1 "$PY" -m pytest 17_final_python -m regression \
            --html=17_final_python/reports/report_$B.html -q || rc=1
    done
    [ "$rc" = "0" ] || { echo "❌ 矩阵有红"; exit 1; }
    step "observe" "② 注入失败验证证据链（预期 1 failed，不计入套件红）"
    INJECT_FAILURE=1 "$PY" -m pytest 17_final_python/tests/test_regression.py::test_injectable_guard \
        --html=17_final_python/reports/report_inject.html -q || true
    "$PY" - <<'EOF'
import glob, os
out = os.path.join("17_final_python", "reports")
htmls = sorted(glob.glob(os.path.join(out, "report_*.html")))
fails = glob.glob(os.path.join(out, "FAIL_*.png"))
assert len(htmls) >= 3, f"HTML 报告不足: {htmls}"
assert fails, "注入失败未触发证据链"
print(f"✅ 终极套件核验：{len(htmls)} 份 HTML 报告 + 失败证据 {os.path.basename(fails[0])}")
EOF
}

do_clean() {
    step "clean" "清运行产物"
    rm -rf "$SERIES/17_final_python/reports" "$SERIES/17_final_python/__pycache__" \
           "$SERIES/17_final_python/pages/__pycache__" "$SERIES/17_final_python/tests/__pycache__" "$SERIES/__pycache__"
    echo "已清理"
}

main() { case "${1:-all}" in
    apply) do_apply ;; observe) do_apply; do_observe ;; clean) do_clean ;;
    all) do_apply; do_observe; do_clean ;;
    *) echo "可用: apply | observe | clean | all" >&2; exit 1;;
esac; }
main "$@"
