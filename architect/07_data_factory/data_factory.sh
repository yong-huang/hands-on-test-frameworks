#!/usr/bin/env bash
# =============================================================================
# data_factory.sh — architect 07 主演示脚本：
# 基线巡检 → 工厂生命周期 → 3 轮套件行数不涨 → 孤儿清扫（真数据受保护） → 清理
# 全程进程内操作 SUT 数据层（sqlite），不需要起服务。
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

REPO="$(cd ../.. && pwd)"
PY="$REPO/.venv/bin/python"
[ -x "$PY" ] || PY=python3
DB="$REPO/labs/11_sut_app/app/orders.db"

step() { echo; echo "=====> [$1] $2"; }

do_apply() {
    step "apply" "① 种子数据建库（幂等：先删再种，基线 10 行）"
    rm -f "$DB" "$DB-journal"
    ( cd "$REPO/labs/11_sut_app" && "$PY" app/seed.py --db app/orders.db )
    "$PY" gc.py --db "$DB"
}

do_observe() {
    step "observe" "① 工厂生命周期：with 内造 5 条，退出自动清光"
    "$PY" - <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("factory.py").parent))
import factory
db = Path("../../labs/11_sut_app/app/orders.db").resolve()
before = factory.count(db)
with factory.lifecycle(db) as f:
    for _ in range(5):
        f.create()
    during = factory.count(db)
after = factory.count(db)
print(f"基线 {before} → 造数后 {during} → 自动清理后 {after}")
assert before == after, "生命周期清理失败"
print("用例级清理 ✅")
EOF

    step "observe" "② 连跑 3 轮演示套件，每轮后行数都必须回到基线"
    for i in 1 2 3; do
        "$PY" -m pytest tests -c configs/pytest.ini --rootdir=tests -q 2>&1 | tail -1
        "$PY" gc.py --db "$DB" | head -1
    done

    step "observe" "③ 孤儿清扫：模拟上次崩溃留下的 100 条 QA- 孤儿 + 1 条手工真实数据"
    "$PY" - <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("factory.py").parent))
import factory
db = Path("../../labs/11_sut_app/app/orders.db").resolve()
for i in range(100):
    store_db = db
    factory.OrderFactory(store_db).create(customer=f"QA-orphan-崩溃遗留{i:03d}")
store_order = factory.OrderFactory(db)
store_order.create(customer="手工真实订单-张三", item="真实商品", qty=1, price=66.6)
print("已插入 100 条 QA- 孤儿 + 1 条无前缀手工数据")
EOF
    "$PY" gc.py --db "$DB"

    step "observe" "④ sweep 清扫：孤儿 100 条清光，手工真实数据安然无恙"
    "$PY" gc.py --db "$DB" --sweep
    "$PY" - <<'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("factory.py").parent))
import factory
db = Path("../../labs/11_sut_app/app/orders.db").resolve()
rows, _ = __import__("store").list_orders(db, limit=100000)
manual = [r for r in rows if r["customer"] == "手工真实订单-张三"]
assert len(manual) == 1, "手工数据被误删——GC 安全边界失守！"
print("手工真实数据仍在 ✅（GC 只动 QA- 命名空间）")
EOF
    echo ">>> 验收：3 轮套件后行数=基线±0；GC 清 100 条孤儿且保护真数据"
}

do_clean() {
    step "clean" "删库与缓存——labs/11 数据库还原到无库状态"
    rm -rf reports tests/__pycache__ .pytest_cache __pycache__ "$DB" "$DB-journal"
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
