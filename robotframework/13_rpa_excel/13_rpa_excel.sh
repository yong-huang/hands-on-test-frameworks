#!/usr/bin/env bash
# 13_rpa_excel.sh — 项目 13：RPA——Excel 驱动批量下单
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起 Robot 靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    step "observe" "① openpyxl 由 CSV 预制 xlsx 输入（10 行订单）"
    "$PY" - <<'PYEOF'
import openpyxl
wb = openpyxl.Workbook()
ws = wb.active; ws.title = "订单"
ws.append(["name", "customer", "product", "qty"])
for line in open("orders_source.csv", encoding="utf-8").read().strip().splitlines()[1:]:
    ws.append(line.split(","))
wb.save("reports/orders_input.xlsx")
print("    xlsx 输入已预制")
PYEOF
    step "observe" "② 读 xlsx → 逐行下单（2 非法不中断）→ 结果写回 xlsx"
    # OUTPUT_DIR 与 reports 对齐，robot 里的 ${XLSX_IN} 指向预制文件
    mkdir -p reports
    "$PY" -m robot --outputdir reports rpa_excel.robot
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
