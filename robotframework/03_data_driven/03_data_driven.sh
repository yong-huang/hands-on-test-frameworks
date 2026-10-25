#!/usr/bin/env bash
# 03_data_driven.sh — 项目 3：数据驱动两板斧
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起 Robot 靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "板斧一：[Template] 内联数据"
    "$PY" -m robot --outputdir reports/template template_style.robot
    step "observe" "板斧二：外部 CSV + FOR 循环驱动"
    "$PY" -m robot --outputdir reports/datadriven csv_loop_style.robot
    "$PY" - <<'EOF'
from xml.etree import ElementTree as ET
def kw_runs(path):
    r = ET.parse(path).getroot()
    return sum(1 for kw in r.iter("kw") if kw.attrib.get("name", "").endswith("下单并断言"))
tn = kw_runs("reports/template/output.xml")
dn = kw_runs("reports/datadriven/output.xml")
print(f"模板式数据组 {tn}；CSV 式数据组 {dn}")
assert tn >= 5 and dn >= 4, "数据组数不足"
print("✅ 两板斧数据量与负向断言达标")
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
