#!/usr/bin/env bash
# 17_panorama.sh — 项目 17：🏁 全景串联（Excel 读单 → API 建单 → Web 支付验证 → 结果回写 → rebot 合并）
set -euo pipefail
cd "$(dirname "$0")"
SERIES="$(cd .. && pwd)"
PY="$SERIES/../.venv/bin/python"
export PATH="$SERIES/../.venv/bin:$PATH"

step() { echo; echo "=====> [$1] $2"; }

do_apply() { step "apply" "拉起 Robot 靶场（幂等）"; bash "$SERIES/shop/shop.sh" apply; }

do_observe() {
    local out="$PWD/reports"
    rm -rf "$out"; mkdir -p "$out"

    step "observe" "① openpyxl 由 CSV 预制 xlsx 订单（10 行含 2 非法）"
    "$PY" - <<'PYEOF'
import openpyxl
wb = openpyxl.Workbook()
ws = wb.active; ws.title = "订单"
ws.append(["name", "customer", "product", "qty"])
for line in open("orders_source.csv", encoding="utf-8").read().strip().splitlines()[1:]:
    ws.append(line.split(","))
wb.save("reports/orders_input.xlsx")
print("    xlsx 就绪（10 行）")
PYEOF

    step "observe" "② 段一（RPA+API）：Excel 读单 → API 批量建单 → 订单清单落盘"
    "$PY" -m robot --outputdir "$out/seg1" --log none --report none --name 段一Excel与API seg1_excel_api.robot
    [ -f "$out/order_ids.json" ] && echo "    订单清单已落盘（$(../.venv/bin/python -c "import json;print(len(json.load(open('reports/order_ids.json'))))") 笔）"

    step "observe" "③ 段二（Web）：逐笔查询并支付（读段一订单清单）"
    "$PY" -m robot --outputdir "$out/seg2" --log none --report none --name 段二Web支付 seg2_web_pay.robot

    step "observe" "④ 段三（API）：终态复核 + 结果写回 Excel"
    "$PY" -m robot --outputdir "$out/seg3" --log none --report none --name 段三复核与回写 seg3_verify_writeback.robot

    step "observe" "⑤ rebot 合并三段出总报告（总数/通过率与各段一致）"
    rebot --output merged.xml --outputdir "$out" \
        "$out/seg1/output.xml" "$out/seg2/output.xml" "$out/seg3/output.xml" >/dev/null 2>&1 || true
    "$PY" - <<'PYEOF'
import json
from xml.etree import ElementTree as ET
merged = ET.parse("reports/merged.xml").getroot()
mst = merged.find(".//statistics/total/stat")
segs = {}
for seg in ("seg1", "seg2", "seg3"):
    st = ET.parse(f"reports/{seg}/output.xml").getroot().find(".//statistics/total/stat")
    segs[seg] = st
total = int(mst.attrib["pass"]) + int(mst.attrib["fail"])
seg_total = sum(int(s.attrib["pass"]) + int(s.attrib["fail"]) for s in segs.values())
assert total == seg_total, f"总账不平：merged {total} ≠ 分段 {seg_total}"
assert mst.attrib["fail"] == "0", "合并后应全绿"
ids = json.load(open("reports/order_ids.json"))
print(f"    总报告：{total} 条全绿；Excel 10 行 → 建单 {len(ids)} 笔 → 复核一致")
print("    ✅ 全景串联：Excel → API → Web → 回写 → 合并 五步闭环")
PYEOF
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
