#!/usr/bin/env bash
# 16_api_regression.sh — 项目 16：🏁 API 回归套件（≥20 条）
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起 Robot 靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "回归全集（正向/异常/Schema/状态机）"
    "$PY" -m robot --outputdir reports suites/
    "$PY" - <<'EOF'
from xml.etree import ElementTree as ET
r = ET.parse("reports/output.xml").getroot()
st = r.find(".//statistics/total/stat")
n = int(st.attrib["pass"]) + int(st.attrib["fail"])
print(f"    用例数 {n}（验收 ≥20）")
assert n >= 20, "用例数不足 20"
assert st.attrib["fail"] == "0"
print("    ✅ API 回归全集全绿且体量达标")
EOF
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
