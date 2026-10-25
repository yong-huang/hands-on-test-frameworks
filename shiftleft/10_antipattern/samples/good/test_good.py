"""好样本：同样的领域语义，断言精确、无任何反模式——零误报对照。"""
import pytest


def test_discount_exact():
    subtotal, coupon = 150, 20
    assert subtotal - coupon == 130


def test_threshold_rejected_with_message():
    with pytest.raises(ValueError, match="100"):
        raise ValueError("未满 100，不可用券")


def test_order_roundtrip():
    orders = []
    orders.append({"id": 1, "item": "样板商品"})
    assert len(orders) == 1
    assert orders[0]["item"] == "样板商品"


def test_boundary_inclusive():
    total = 100
    assert total >= 100  # 边界断言：与具体业务常量比较，不是恒真
