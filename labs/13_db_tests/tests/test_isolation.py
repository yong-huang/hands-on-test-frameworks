"""两种隔离策略跑同一组数据层操作——结果一致，速度不同"""
import pytest

import store


@pytest.mark.isolation("fresh")
def test_create_and_get_fresh(db):
    o = store.create_order(db, "隔离A", "商品", 2, 10.0)
    assert store.get_order(db, o["id"])["customer"] == "隔离A"


@pytest.mark.isolation("truncate")
def test_create_and_get_truncate(db):
    o = store.create_order(db, "隔离B", "商品", 2, 10.0)
    assert store.get_order(db, o["id"])["customer"] == "隔离B"


@pytest.mark.isolation("fresh")
def test_truncate_isolation_fresh(db):
    """fresh 策略下库里只可能有本用例的数据"""
    store.create_order(db, "唯一客", "x", 1, 1.0)
    orders, total = store.list_orders(db, limit=100)
    assert total == 1


@pytest.mark.isolation("truncate")
def test_truncate_isolation_truncate(db):
    """truncate 策略：即便上一条用例留了数据，setup 截表也救回来"""
    store.create_order(db, "唯一客", "x", 1, 1.0)
    orders, total = store.list_orders(db, limit=100)
    assert total == 1


@pytest.mark.isolation("truncate")
def test_update_and_delete_truncate(db):
    o = store.create_order(db, "增删改", "x", 1, 5.0)
    store.update_status(db, o["id"], "paid")
    assert store.get_order(db, o["id"])["status"] == "paid"
    assert store.delete_order(db, o["id"]) is True
    assert store.get_order(db, o["id"]) is None
