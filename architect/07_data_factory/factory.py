#!/usr/bin/env python3
"""factory.py — SUT 订单数据工厂：随机造数 + 命名空间打标 + 生命周期清理。

架构师视角的一句话：**测试数据问题的三种病各有药方**——
  数据越跑越多 → 生命周期清理（用例级 + 命名空间 GC 双层兜底）；
  用例相互污染 → 每次造数带唯一标记，断言只认自己造的数；
  造数效率低   → factory 默认值 + 覆盖式参数，一行造一条合理订单。

命名空间纪律：工厂造的所有订单 customer 一律以 `QA-` 前缀开头。
GC 只动这个命名空间——手工/生产的真实数据（无前缀）**永不触碰**，
这就是「清理脚本敢不敢在生产库跑」的答案。
"""
from __future__ import annotations

import random
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "labs" / "11_sut_app" / "app"))
import store  # noqa: E402

NAMESPACE = "QA-"
_CUSTOMERS = ["华东仓", "华南仓", "直营店", "加盟商", "大客户"]
_ITEMS = ["机械键盘", "无线鼠标", "显示器支架", "USB-C 扩展坞", "降噪耳机"]


class OrderFactory:
    """一次造数会话：随机生成合理订单，记录本会话产物，支持精确清理。"""

    def __init__(self, db):
        self.db = db
        self.run_id = uuid.uuid4().hex[:8]
        self.created: list[int] = []

    def create(self, customer: str | None = None, item: str | None = None,
               qty: int | None = None, price: float | None = None) -> dict:
        c = customer or f"{NAMESPACE}{self.run_id}-{random.choice(_CUSTOMERS)}客户{len(self.created)+1}"
        o = store.create_order(
            self.db, c,
            item or random.choice(_ITEMS),
            qty if qty is not None else random.randint(1, 5),
            price if price is not None else round(random.uniform(1, 99), 1))
        self.created.append(o["id"])
        return o

    def cleanup(self) -> int:
        """精确清理本会话产物（按 id 逐条删，不碰命名空间外的任何行）。"""
        n = 0
        for oid in self.created:
            n += 1 if store.delete_order(self.db, oid) else 0
        self.created.clear()
        return n


@contextmanager
def lifecycle(db) -> Iterator[OrderFactory]:
    """用例级生命周期：with 内造的数，退出时自动清光（fixture 底层也用它）。"""
    f = OrderFactory(db)
    try:
        yield f
    finally:
        f.cleanup()


def count(db) -> int:
    return store.count(db)


def count_namespace(db, prefix: str = NAMESPACE) -> int:
    rows, _ = store.list_orders(db, limit=100000)
    return sum(1 for r in rows if str(r["customer"]).startswith(prefix))
