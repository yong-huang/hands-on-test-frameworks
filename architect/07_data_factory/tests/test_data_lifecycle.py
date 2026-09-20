"""演示套件：用例级生命周期清理——每条用例造的数在 teardown 自动清光。

三连跑后全表行数应与基线 ±0：这就是「数据越跑越多」的解药演示。
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from factory import OrderFactory, count, lifecycle  # noqa: E402


@pytest.fixture
def db():
    return Path(__file__).resolve().parents[3] / "labs" / "11_sut_app" / "app" / "orders.db"


@pytest.fixture
def factory(db):
    """用例级 factory：测试体随便造，teardown 自动清光（lifecycle 上下文管理器）。"""
    with lifecycle(db) as f:
        yield f


def test_批量造数并断言自身窗口(db, factory):
    baseline = count(db)
    made = [factory.create() for _ in range(4)]
    assert count(db) == baseline + 4          # 只看见自己的增量（相互污染的解药）
    assert all(str(m["customer"]).startswith("QA-") for m in made)


def test_覆盖默认值的定点造数(db, factory):
    o = factory.create(customer="QA-定点-大单", qty=99, price=0.1)
    assert o["qty"] == 99 and o["price"] == 0.1


def test_手动工厂清理(db):
    """不用 lifecycle 的场景：手动 cleanup 也能精确归还（等价 GC 的 id 级路径）。"""
    baseline = count(db)
    f = OrderFactory(db)
    for _ in range(3):
        f.create()
    assert count(db) == baseline + 3
    assert f.cleanup() == 3
    assert count(db) == baseline
