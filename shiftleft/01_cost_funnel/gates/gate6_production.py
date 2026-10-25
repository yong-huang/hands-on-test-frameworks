#!/usr/bin/env python3
"""关卡 6 · 生产模拟 —— 日结逐笔对账：系统册原始值 vs 支付册按分结算值。

生产环境的检出机制不再是断言，而是**对账**：系统侧记账保留计算原始值，
支付渠道按分（两位小数）结算，财务要求逐笔一致、零差异。float 脏值
在这里表现为「每笔都差一点点」，1000 笔订单的日结对账直接挂起告警工单。
真实代价不在检出（脚本秒级），而在值班排查链——见 costs.yaml 的 480 分钟。

复现：python gates/gate6_production.py
"""
import argparse
import importlib
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "defect"))
ITEMS = ["19.99", "80.10"]
N_ORDERS = 1000  # 模拟当日订单量


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--impl", choices=["good", "bad"], default="bad")
    args = ap.parse_args()
    pricing = importlib.import_module(f"pricing_{args.impl}")

    print(f"[关卡6 · 生产模拟] 日结对账 {N_ORDERS} 笔：系统册原始值 vs 支付册按分结算")
    mismatches = []
    for i in range(1, N_ORDERS + 1):
        raw = pricing.payable(pricing.cart_total(ITEMS), use_coupon=True)
        settled = float(Decimal(str(raw)).quantize(Decimal("0.01")))  # 渠道按分结算
        if float(raw) != settled:
            mismatches.append((i, float(raw), settled))

    if mismatches:
        i, raw, settled = mismatches[0]
        print(f"  ⛔ 第一笔差异：订单 #{i} 系统册 {raw!r} vs 支付册 {settled!r}")
        print(f"  ⛔ 全日差异笔数：{len(mismatches)}/{N_ORDERS}")
        print("  → 对账告警工单已生成：值班需排查支付渠道/幂等/金额计算，"
              "缺陷在生产层才被拦下")
        print("RESULT: INTERCEPTED")
    else:
        print(f"  → {N_ORDERS} 笔逐笔一致，日结平账：无缺陷可拦")
        print("RESULT: CLEAN_PASS")


if __name__ == "__main__":
    main()
