"""演示套件：SUT 数据层（store）的业务流 + 1 条故意失败 + 1 条慢用例 + 分层标记。

qa_kit 插件对这套代码**零侵入**：没有任何 import qa_kit——全部能力来自
pytest.ini / CLI 配置 + entry point 自动加载。这就是「公司级」的含义。
"""
import time

import pytest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "labs" / "11_sut_app" / "app"))
import store  # noqa: E402


@pytest.fixture
def db(tmp_path):
    path = tmp_path / "demo.db"
    store.init_db(path)
    return path


@pytest.mark.smoke
def test_create_order(db):
    order = store.create_order(db, "插件演示", "商品A", qty=2, price=9.9)
    assert order["id"] == 1


@pytest.mark.smoke
def test_list_orders(db):
    store.create_order(db, "客户1", "商品B", qty=1, price=1.0)
    rows, total = store.list_orders(db)
    assert total == 1 and rows[0]["customer"] == "客户1"


@pytest.mark.full
def test_delete_order(db):
    o = store.create_order(db, "客户2", "商品C", qty=1, price=2.0)
    assert store.delete_order(db, o["id"]) is True
    assert store.get_order(db, o["id"]) is None


@pytest.mark.full
def test_slow_report_query(db):
    """故意慢：0.6s 睡眠模拟慢查询，喂给 qa_kit 慢用例排行（阈值 0.5s）。"""
    store.create_order(db, "客户3", "商品D", qty=1, price=3.0)
    time.sleep(0.6)
    rows, total = store.list_orders(db)
    assert total == 1


def test_deliberate_failure(db):
    """故意失败：喂给 qa_kit 失败留现场（evidence/ 目录）。"""
    store.create_order(db, "客户4", "商品E", qty=1, price=4.0)
    _, total = store.list_orders(db)
    assert total == 999, "故意失败：演示 evidence 留现场"


@pytest.mark.full
def test_update_status_flow(db):
    o = store.create_order(db, "客户5", "商品F", qty=1, price=5.0)
    updated = store.update_status(db, o["id"], "paid")
    assert updated["status"] == "paid"
