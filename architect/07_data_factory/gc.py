#!/usr/bin/env python3
"""gc.py — 测试数据 GC：命名空间清扫 + 真实数据保护。

两层清理策略（面试标准答案「数据越跑越多怎么治」）：
  1. 用例级（factory.cleanup）：精确按 id 删本会话产物——正常路径全靠它；
  2. 命名空间 GC（本脚本）：进程崩溃/断电留下的孤儿（同在 QA- 命名空间、
     失去了运行档案），sweep 一次清掉——异常路径的兜底。
安全边界：GC 的 SQL 只匹配 QA- 前缀，命名空间外的行（手工数据/生产数据）绝不触碰——
清理脚本的可信度来自「它永远不会删不该删的东西」，不是来自「它删得快」。

用法：
  python gc.py --db labs/11_sut_app/app/orders.db            # 巡检：报告两区行数
  python gc.py --db ... --sweep                              # 清扫 QA- 命名空间孤儿
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "labs" / "11_sut_app" / "app"))
import store  # noqa: E402

from factory import NAMESPACE, count, count_namespace  # noqa: E402


def sweep(db) -> int:
    rows, _ = store.list_orders(db, limit=100000)
    victims = [r["id"] for r in rows if str(r["customer"]).startswith(NAMESPACE)]
    for oid in victims:
        store.delete_order(db, oid)
    return len(victims)


def main() -> int:
    ap = argparse.ArgumentParser(description="测试数据 GC（命名空间清扫）")
    ap.add_argument("--db", required=True)
    ap.add_argument("--sweep", action="store_true", help="清扫 QA- 命名空间孤儿数据")
    args = ap.parse_args()

    total, qa = count(args.db), count_namespace(args.db)
    print(f"巡检：全表 {total} 行，其中 {NAMESPACE} 命名空间 {qa} 行，"
          f"命名空间外（受保护）{total - qa} 行")
    if not args.sweep:
        print("（--sweep 执行清扫；命名空间外的行永不在清扫范围内）")
        return 0
    removed = sweep(args.db)
    print(f"已清扫 {removed} 行孤儿数据；剩余全表 {count(args.db)} 行")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
