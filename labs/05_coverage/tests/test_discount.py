"""基础用例集——只覆盖到约 70% 分支。

先只跑这一份，配合 --cov-fail-under=90 会看到门禁失败；
再跑 test_discount_extra.py 补漏后门禁通过。这就是"覆盖率驱动补测"的完整闭环。
"""
from discount import apply_discount, cart_subtotal, checkout, item_price


def test_item_price_weekday():
    assert item_price({"price": 100.0}) == 100.0


def test_cart_subtotal():
    cart = [{"price": 30.0}, {"price": 70.0}]
    assert cart_subtotal(cart) == 100.0


def test_discount_nothing():
    assert apply_discount(50.0) == 50.0


def test_checkout_basic_with_shipping():
    r = checkout([{"price": 60.0}])
    assert r == {"subtotal": 60.0, "total": 60.0, "shipping": 15.0, "grand": 75.0}


def test_checkout_free_shipping():
    r = checkout([{"price": 230.0}])
    assert r["shipping"] == 0.0
